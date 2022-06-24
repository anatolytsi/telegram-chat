from communication.base import DATA_KEY, BusDir
from communication.mixins import BusMixin
from db.website import TOKEN_KEY
from telegram.base import TelegramBotMixin


class TelegramBot(BusMixin, TelegramBotMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, sub_dir=BusDir.COM, pub_dir=BusDir.TG, **kwargs)

    async def on_bus_message(self, message: any):
        return await self.send_tg_message(message[DATA_KEY][TOKEN_KEY], message[DATA_KEY])
