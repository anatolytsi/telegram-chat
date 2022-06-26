from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from db.website import HOST_KEY, ALIAS_KEY, PASSWORD_KEY, add_website, TOKEN_KEY, subscribe_website, \
    unsubscribe_website, remove_website


class BaseBotMixin:
    _msg_handlers = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        if 'handler' in kwargs and 'commands' in kwargs and 'state' in kwargs:
            cls._msg_handlers.append([cls, kwargs['handler'], kwargs['commands'], kwargs['state']])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _handle_caller(self, handler: str):
        return getattr(self, handler)

    def add_msg_handlers(self, dispatcher: Dispatcher):
        for subcls, handler, commands, state in self._msg_handlers:
            if subcls in self.__class__.mro():
                dispatcher.register_message_handler(self._handle_caller(handler), commands=commands, state=state)


class BotStartHandleMixin(BaseBotMixin,
                          handler='handle_start',
                          commands=['start'],
                          state=None):

    async def handle_start(self, message: types.Message):
        await message.answer('Welcome to Telegram Chat Bot!')


class AddWebsiteForm(StatesGroup):
    host = State()
    alias = State()
    password = State()


class AddWebsiteEntry(BaseBotMixin,
                      handler='handle_add_website',
                      commands=['add_website'],
                      state=None):

    async def handle_add_website(self, message: types.Message):
        await AddWebsiteForm.host.set()
        await message.reply('What is your website host?')


class AddHostHandle(BaseBotMixin,
                    handler='handle_add_host',
                    commands=None,
                    state=AddWebsiteForm.host):

    async def handle_add_host(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data[HOST_KEY] = message.text

        await AddWebsiteForm.next()
        await message.reply('What is your public alias for this website?')


class AddAliasHandle(BaseBotMixin,
                     handler='handle_add_alias',
                     commands=None,
                     state=AddWebsiteForm.alias):

    async def handle_add_alias(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data[ALIAS_KEY] = message.text

        await AddWebsiteForm.next()
        await message.reply('What will be your password to subscribe to this website?')


class AddPassHandle(BaseBotMixin,
                    handler='handle_add_pass',
                    commands=None,
                    state=AddWebsiteForm.password):

    async def handle_add_pass(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data[PASSWORD_KEY] = message.text
            token = add_website(message.chat.username, message.chat.id, **dict(data))
            markup = types.ReplyKeyboardRemove()
            if token:
                await message.answer(f'Success!\n'
                                     f'Website <b>{data[ALIAS_KEY]}</b> was added!\n'
                                     f'Your token is <b>{token}</b>\n'
                                     f'Your password is <b>{data[PASSWORD_KEY]}</b>\n'
                                     f'You can now allow other users to subscribe to it!',
                                     parse_mode='HTML', reply_markup=markup)
            else:
                await message.answer(f'Unfortunately, something went wrong :(', reply_markup=markup)
        await state.finish()


class BotAddWebsiteMixin(AddWebsiteEntry, AddHostHandle, AddAliasHandle, AddPassHandle):
    pass


class RemoveWebsiteForm(StatesGroup):
    token = State()
    password = State()


class RemoveWebsiteEntry(BaseBotMixin,
                         handler='handle_remove_website',
                         commands=['remove_website'],
                         state=None):

    async def handle_remove_website(self, message: types.Message):
        await RemoveWebsiteForm.token.set()
        await message.reply('What is your website token that you want to remove?')


class RemoveTokenHandle(BaseBotMixin,
                        handler='handle_remove_token',
                        commands=None,
                        state=RemoveWebsiteForm.token):

    async def handle_remove_token(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data[TOKEN_KEY] = message.text

        await RemoveWebsiteForm.next()
        await message.reply('What is the public password to subscribe to this website?')


class RemovePassHandle(BaseBotMixin,
                       handler='handle_remove_pass',
                       commands=None,
                       state=RemoveWebsiteForm.password):

    async def handle_remove_pass(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data[PASSWORD_KEY] = message.text
            alias = remove_website(message.chat.username, **dict(data))
            markup = types.ReplyKeyboardRemove()
            if alias:
                await message.answer(f'Success!\n'
                                     f'You have successfully deleted <b>{alias}</b>!\n',
                                     parse_mode='HTML', reply_markup=markup)
            else:
                await message.answer(f'Token or password is incorrect. Try again!', reply_markup=markup)
        await state.finish()


class BotRemoveWebsiteMixin(RemoveWebsiteEntry, RemoveTokenHandle, RemovePassHandle):
    pass


class SubWebsiteForm(StatesGroup):
    token = State()
    password = State()


class SubWebsiteEntry(BaseBotMixin,
                      handler='handle_sub_website',
                      commands=['sub_website'],
                      state=None):

    async def handle_sub_website(self, message: types.Message):
        await SubWebsiteForm.token.set()
        await message.reply('What is your website token that you want to unsubscribe from?')


class SubTokenHandle(BaseBotMixin,
                     handler='handle_sub_token',
                     commands=None,
                     state=SubWebsiteForm.token):

    async def handle_sub_token(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data[TOKEN_KEY] = message.text

        await SubWebsiteForm.next()
        await message.reply('What is the public password to subscribe to this website?')


class SubPassHandle(BaseBotMixin,
                    handler='handle_sub_pass',
                    commands=None,
                    state=SubWebsiteForm.password):

    async def handle_sub_pass(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data[PASSWORD_KEY] = message.text
            alias = subscribe_website(message.chat.username, message.chat.id, **dict(data))
            markup = types.ReplyKeyboardRemove()
            if alias:
                await message.answer(f'Success!\n'
                                     f'You have subscribed to <b>{alias}</b>!\n',
                                     parse_mode='HTML', reply_markup=markup)
            else:
                await message.answer(f'Token or password is incorrect. Try again!', reply_markup=markup)
        await state.finish()


class BotSubWebsiteMixin(SubWebsiteEntry, SubTokenHandle, SubPassHandle):
    pass


class UnsubWebsiteForm(StatesGroup):
    token = State()
    password = State()


class UnsubWebsiteEntry(BaseBotMixin,
                        handler='handle_unsub_website',
                        commands=['unsub_website'],
                        state=None):

    async def handle_unsub_website(self, message: types.Message):
        await UnsubWebsiteForm.token.set()
        await message.reply('What is your website token?')


class UnsubTokenHandle(BaseBotMixin,
                       handler='handle_unsub_token',
                       commands=None,
                       state=UnsubWebsiteForm.token):

    async def handle_unsub_token(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data[TOKEN_KEY] = message.text

        await UnsubWebsiteForm.next()
        await message.reply('What is the public password to subscribe to this website?')


class UnsubPassHandle(BaseBotMixin,
                      handler='handle_unsub_pass',
                      commands=None,
                      state=UnsubWebsiteForm.password):

    async def handle_unsub_pass(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data[PASSWORD_KEY] = message.text
            alias = unsubscribe_website(message.chat.username, **dict(data))
            markup = types.ReplyKeyboardRemove()
            if alias:
                await message.answer(f'Success!\n'
                                     f'You have successfully unsubscribed from <b>{alias}</b>!\n',
                                     parse_mode='HTML', reply_markup=markup)
            else:
                await message.answer(f'Token or password is incorrect. Try again!', reply_markup=markup)
        await state.finish()


class BotUnsubWebsiteMixin(UnsubWebsiteEntry, UnsubTokenHandle, UnsubPassHandle):
    pass


class BotWebsitesMixin(BotAddWebsiteMixin, BotRemoveWebsiteMixin,
                       BotSubWebsiteMixin, BotUnsubWebsiteMixin):
    pass


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
