from aiogram import types


class BaseBotMixin:
    _handlers = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        if 'handler' in kwargs and 'commands' in kwargs:
            cls._handlers.append([kwargs['handler'], kwargs['commands']])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _handle_caller(self, handler: str):
        return getattr(self, handler)


class BotStartHandleMixin(BaseBotMixin, handler='handle_start', commands=['start']):
    async def handle_start(self, message: types.Message):
        await message.answer('Welcome to Telegram Chat Bot!')
        # await message.reply('Welcome to Telegram Chat Bot!')


class BotMessageHandleMixin(BaseBotMixin, handler='handle_message', commands=None):
    async def handle_reply(self, message: types.Message):
        await message.answer(message.text)

    async def handle_direct(self, message: types.Message):
        await message.answer('Its just text!')

    async def handle_message(self, message: types.Message):
        if message.reply_to_message:
            await self.handle_reply(message)
        else:
            await self.handle_direct(message)
