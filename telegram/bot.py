from communication.base import CHANNEL_KEY, DATA_KEY
from communication.mixins import BusMixin
from telegram.base import TelegramBotMixin


class TelegramBot(BusMixin, TelegramBotMixin):
    async def on_bus_message(self, message: any):
        return await self.send_tg_message(message[CHANNEL_KEY], message[DATA_KEY])
