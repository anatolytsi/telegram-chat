import asyncio
from abc import abstractmethod
from typing import Dict

from aiogram import Bot, Dispatcher, executor

from communication.base import CHANNEL_KEY
from communication.manager import Bus
from db.website import get_website_hosts, get_website_subscribers, USER_CHANNEL_KEY, TOKEN_KEY, HOST_KEY
from telegram_chat.handlers import BotStartHandleMixin, BotMessageHandleMixin


class BusMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bus: Bus = Bus()
        self._bus_websites: Dict[str, str] = {}
        self._subscribe_to_all_buses()
        self._event_loop = asyncio.get_event_loop()

    def _subscribe_to_all_buses(self):
        websites = get_website_hosts()
        for website in websites:
            token = website[TOKEN_KEY]
            host = website[HOST_KEY]
            self._subscribe_bus(host, token)

    def _subscribe_bus(self, host: str, token: str):
        self._bus_websites[token] = host
        self._bus.subscribe(token, lambda msg: self._on_bus_message(msg))

    async def _on_bus_message(self, message: any):
        # if self.verify_bus_sender(message[DATA_KEY][HOST_KEY], message[CHANNEL_KEY]):
        #     # TODO: send an error message?
        #     return await self.on_bus_message(message)
        return await self.on_bus_message(message)

    def verify_bus_sender(self, host: str, token: str):
        if token in self._bus_websites and self._bus_websites[token] == host:
            return True
        print(f'Token and/or host are incorrect')
        return False

    @abstractmethod
    async def on_bus_message(self, message: any):
        pass

    def send_bus_message(self, token: str, message: any):
        return self._bus.publish(token, message)

    @staticmethod
    def get_bus_channel(message: any):
        return message[CHANNEL_KEY]


class TelegramBotMixin(BotStartHandleMixin, BotMessageHandleMixin):
    def __init__(self, *args, tg_token, **kwargs):
        super().__init__(*args, **kwargs)
        self._bot: Bot = Bot(token=tg_token)
        self._dispatcher: Dispatcher = Dispatcher(bot=self._bot)
        for handler, commands in self._handlers:
            self._dispatcher.register_message_handler(self._handle_caller(handler), commands=commands)

    def run(self):
        executor.start_polling(self._dispatcher, skip_updates=True)
        asyncio.get_event_loop().run_forever()

    async def send_tg_message(self, token: str, msg: str):
        subscribers = get_website_subscribers(token)
        # return await self._bot.send_message(chat_id=subscribers[0][USER_CHANNEL_KEY], text=msg, disable_notification=True)
        # Send message to all the subscribers
        return await asyncio.gather(
            *[self._bot.send_message(chat_id=sub[USER_CHANNEL_KEY], text=msg, disable_notification=True)
              for sub in subscribers])
