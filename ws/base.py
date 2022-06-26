import asyncio
import json
from typing import Dict

from websockets import serve
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
from websockets.legacy.server import WebSocketServerProtocol

from communication.base import BusDir, BusMessage
from communication.mixins import BusMixin
from db.messaging import ChatMessage, add_message, get_messages
from db.website import TOKEN_KEY, create_session_website, validate_website_session

SESSION_KEY = 'session'
HISTORY_KEY = 'history'


class WebsocketServer(BusMixin):
    def __init__(self, *args, host: str, port: int, is_standalone: bool = False, **kwargs):
        super().__init__(*args, sub_dir=BusDir.TG, pub_dir=BusDir.COM, **kwargs)
        self.host = host
        self.port = port
        self.is_standalone = is_standalone
        self._connections: Dict[str, WebSocketServerProtocol] = {}

    @staticmethod
    def _decode_msg(msg: str) -> dict:
        try:
            return json.loads(msg)
        except json.decoder.JSONDecodeError:
            return {}

    async def _verify_msg(self, websocket: WebSocketServerProtocol, message: dict) -> bool:
        if not message or TOKEN_KEY not in message:
            await websocket.send('The website is not available')
            await websocket.close()
            return False
        host = websocket.origin if websocket.origin != 'null' else '127.0.0.1'
        if not self.verify_bus_sender(host, message[TOKEN_KEY]):
            await websocket.send('Token or host is incorrect')
            await websocket.close()
            return False
        return True

    @staticmethod
    def _request_session_key(token: str) -> str:
        return create_session_website(token)

    @staticmethod
    def _request_history(token: str, session_key: str) -> list:
        messages = get_messages(token, session_key)
        return [msg.to_dict() for msg in messages]

    async def on_bus_message(self, message: BusMessage):
        chat_message = ChatMessage(**message.data)
        add_message(chat_message)
        if message.data[SESSION_KEY] in self._connections:
            await self._connections[message.data[SESSION_KEY]].send(chat_message.to_json())
        else:
            reply_message = {**chat_message.to_dict(), 'text': 'User has already left'}
            self.send_bus_message(chat_message.token, reply_message)

    async def _session_established(self, websocket: WebSocketServerProtocol) -> str:
        message = self._decode_msg(await websocket.recv())
        if not await self._verify_msg(websocket, message):
            return ''

        if SESSION_KEY in message and message[SESSION_KEY] and \
                validate_website_session(message[TOKEN_KEY], message[SESSION_KEY]):
            session_key = message[SESSION_KEY]
        else:
            session_key = self._request_session_key(message[TOKEN_KEY])
            if not session_key:
                await websocket.send('Internal error')
                await websocket.close()
                return ''
            await websocket.send(json.dumps({SESSION_KEY: session_key}))
        history = self._request_history(message[TOKEN_KEY], session_key)
        await websocket.send(json.dumps({HISTORY_KEY: history}))
        self._connections[session_key] = websocket
        return session_key

    async def _worker(self, websocket: WebSocketServerProtocol):
        session_key = ''
        try:
            session_key = await self._session_established(websocket)
            if not session_key:
                return

            while True:
                message = self._decode_msg(await websocket.recv())
                if not await self._verify_msg(websocket, message):
                    return
                chat_message = ChatMessage.from_dict(message)
                add_message(chat_message)
                self.send_bus_message(chat_message.token, chat_message.to_dict())
                print(chat_message)
        except (ConnectionClosedOK, ConnectionClosedError):
            if session_key:
                del self._connections[session_key]

    def start(self):
        server = serve(lambda websocket: self._worker(websocket), self.host, self.port)
        asyncio.get_event_loop().run_until_complete(server)
        if self.is_standalone:
            asyncio.get_event_loop().run_forever()
