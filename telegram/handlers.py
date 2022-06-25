from aiogram import types, Dispatcher


class BaseBotMixin:
    _handlers = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        if 'handler' in kwargs and 'commands' in kwargs and 'state' in kwargs:
            cls._handlers.append([cls, kwargs['handler'], kwargs['commands'], kwargs['state']])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _handle_caller(self, handler: str):
        return getattr(self, handler)

    def add_handlers(self, dispatcher: Dispatcher):
        for subcls, handler, commands, state in self._handlers:
            if subcls in self.__class__.mro():
                dispatcher.register_message_handler(self._handle_caller(handler), commands=commands, state=state)


class BotStartHandleMixin(BaseBotMixin,
                          handler='handle_start',
                          commands=['start'],
                          state=None):

    async def handle_start(self, message: types.Message):
        await message.answer('Welcome to Telegram Chat Bot!')


# Should be at the very bottom to handle other stuff
class BotMessageHandleMixin(BaseBotMixin,
                            handler='handle_message',
                            commands=None,
                            state=None):

    async def handle_reply(self, message: types.Message):
        await message.answer(message.text)

    async def handle_direct(self, message: types.Message):
        await message.answer('Reply to a message in order to send it to webchat')

    async def handle_message(self, message: types.Message):
        if message.reply_to_message:
            await self.handle_reply(message)
        else:
            await self.handle_direct(message)
