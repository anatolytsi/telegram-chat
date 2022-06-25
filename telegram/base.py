import asyncio

from aiogram import Bot, Dispatcher, executor

from db.website import get_website_subscribers, USER_CHANNEL_KEY
from telegram.handlers import BotStartHandleMixin, BotMessageHandleMixin


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
            *[self._bot.send_message(chat_id=sub[USER_CHANNEL_KEY],
                                     text=msg, disable_notification=True, parse_mode='HTML')
              for sub in subscribers])
