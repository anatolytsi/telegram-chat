from communication.base import CHANNEL_KEY, DATA_KEY
from telegram.base import BusMixin, TelegramBotMixin


class TelegramBot(BusMixin, TelegramBotMixin):
    async def on_bus_message(self, message: any):
        return await self.send_tg_message(message[CHANNEL_KEY], message[DATA_KEY])
