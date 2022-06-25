import os
from dotenv import load_dotenv

from ws.base import WebsocketServer

load_dotenv()

WS_HOST = os.environ.get('WS_HOST')
WS_PORT = int(os.environ.get('WS_PORT'))

ws_server = WebsocketServer(host=WS_HOST, port=WS_PORT, is_standalone=True)
ws_server.start()
