import asyncio
from typing import List

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from db.website import get_website_subscribers, USER_CHANNEL_KEY
from telegram.handlers import BotStartHandleMixin, BotMessageHandleMixin, BotWebsitesMixin, BotCancelStateHandleMixin, \
    BotBanningMixin


class TelegramBotMixin(BotStartHandleMixin, BotMessageHandleMixin, BotWebsitesMixin, BotCancelStateHandleMixin,
                       BotBanningMixin):
    def __init__(self, *args, tg_token, **kwargs):
        super().__init__(*args, **kwargs)
        self._storage = MemoryStorage()
        self._bot: Bot = Bot(token=tg_token)
        self._dispatcher: Dispatcher = Dispatcher(bot=self._bot, storage=self._storage)
        self.add_msg_handlers(self._dispatcher)

    def run(self):
        asyncio.get_event_loop().run_until_complete(self.set_commands(self._bot))
        executor.start_polling(self._dispatcher, skip_updates=True)
        asyncio.get_event_loop().run_forever()

    async def _send_to_channels(self, channels: List[str], msg: str):
        return await asyncio.gather(
            *[self._bot.send_message(chat_id=channel,
                                     text=msg, disable_notification=False, parse_mode='HTML')
              for channel in channels])

    async def send_tg_message(self, token: str, msg: str):
        subscribers = get_website_subscribers(token)
        # return await self._bot.send_message(chat_id=subscribers[0][USER_CHANNEL_KEY], text=msg, disable_notification=True)
        # Send message to all the subscribers
        return await self._send_to_channels([sub[USER_CHANNEL_KEY] for sub in subscribers], msg)
