from aiogram import types, Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from db.website import HOST_KEY, ALIAS_KEY, PASSWORD_KEY, add_website, TOKEN_KEY, subscribe_website, \
    unsubscribe_website, remove_website, get_token_from_host, get_full_session_key, ban_session, unban_session
from helpers.parsing import extract_host
from telegram.formatter import REPLY_TXT, get_host_from_msg, get_session_end_from_msg, get_user_from_msg


class BaseBotMixin:
    _msg_handlers = []
    _commands = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        if 'handler' in kwargs and 'commands' in kwargs and 'state' in kwargs:
            cls._msg_handlers.append([cls, kwargs['handler'], kwargs['commands'], kwargs['state']])
            if 'description' in kwargs and 'commands' in kwargs:
                cls._commands.append(types.BotCommand(kwargs['commands'][0], kwargs['description']))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _handle_caller(self, handler: str):
        return getattr(self, handler)

    def add_msg_handlers(self, dispatcher: Dispatcher):
        for subcls, handler, commands, state in self._msg_handlers:
            if subcls in self.__class__.mro():
                dispatcher.register_message_handler(self._handle_caller(handler), commands=commands, state=state)

    async def set_commands(self, bot: Bot):
        await bot.set_my_commands(self._commands)


# State groups
class AddWebsiteForm(StatesGroup):
    host = State()
    alias = State()
    password = State()


class RemoveWebsiteForm(StatesGroup):
    token = State()
    password = State()


class SubWebsiteForm(StatesGroup):
    token = State()
    password = State()


class UnsubWebsiteForm(StatesGroup):
    token = State()
    password = State()


class BotStartHandleMixin(BaseBotMixin,
                          handler='handle_start',
                          commands=['start'],
                          description='Starts the bot',
                          state=None):

    async def handle_start(self, message: types.Message):
        await message.answer('Welcome to Telegram Chat Bot!')


class BotCancelStateHandleMixin(BaseBotMixin,
                                handler='handle_cancel',
                                commands=['cancel'],
                                description='Cancel current operation',
                                state='*'):
    async def handle_cancel(self, message: types.Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state is None:
            return

        await state.finish()
        # And remove keyboard (just in case)
        await message.reply('Operation cancelled', reply_markup=types.ReplyKeyboardRemove())


class BotBanHandleMixin(BaseBotMixin,
                        handler='handle_ban',
                        commands=['ban'],
                        description='Ban user by reply',
                        state=None):

    async def handle_ban(self, message: types.Message):
        try:
            if message.reply_to_message:
                parent_text = message.reply_to_message.text
                if REPLY_TXT in parent_text:
                    await message.reply('Select a message reply from user')
                    return
                host = get_host_from_msg(parent_text)
                session_key_end = get_session_end_from_msg(parent_text)
                user = get_user_from_msg(parent_text)
                token = get_token_from_host(host)
                session_key = get_full_session_key(token, session_key_end)
                if ban_session(token, session_key):
                    await message.reply(f'User {user} was banned!')
                else:
                    await message.reply(f'Session not found')
            else:
                await message.reply('Select a message reply from user')
        except Exception as e:
            print(e)
            await message.reply('Incorrect message selected')


class BotUnbanHandleMixin(BaseBotMixin,
                          handler='handle_unban',
                          commands=['unban'],
                          description='Unban user by reply',
                          state=None):

    async def handle_unban(self, message: types.Message):
        try:
            if message.reply_to_message:
                parent_text = message.reply_to_message.text
                if REPLY_TXT in parent_text:
                    await message.reply('Select a message reply from user')
                    return
                host = get_host_from_msg(parent_text)
                session_key_end = get_session_end_from_msg(parent_text)
                user = get_user_from_msg(parent_text)
                token = get_token_from_host(host)
                session_key = get_full_session_key(token, session_key_end)
                if unban_session(token, session_key):
                    await message.reply(f'User {user} was unbanned!')
                else:
                    await message.reply(f'Session not found')
            else:
                await message.reply('Select a message reply from user')
        except Exception as e:
            print(e)
            await message.reply('Incorrect message selected')


class BotBanningMixin(BotBanHandleMixin, BotUnbanHandleMixin):
    pass


class AddWebsiteEntry(BaseBotMixin,
                      handler='handle_add_website',
                      commands=['add_website'],
                      description='Add new website to app',
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
            data[HOST_KEY] = extract_host(message.text)

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
            if message.chat.type == 'private':
                token = add_website(message.chat.username, message.chat.id, **dict(data))
            else:
                token = add_website(message.chat.title, message.chat.id, **dict(data))
            markup = types.ReplyKeyboardRemove()
            if token:
                await message.answer(f'Success!🥳\n'
                                     f'Website <b>{data[ALIAS_KEY]}</b> was added!\n'
                                     f'Your token is \n  <code>{token}</code>\n'
                                     f'Your password is \n  <code>{data[PASSWORD_KEY]}</code>\n'
                                     f'You can now allow other users to subscribe to it!\n'
                                     f'Don\'t loose this data!😉',
                                     parse_mode='HTML', reply_markup=markup)
            else:
                await message.answer(f'Unfortunately, something went wrong :(\n'
                                     f'Could be that a website with this domain was already added before',
                                     reply_markup=markup)
        await state.finish()


class BotAddWebsiteMixin(AddWebsiteEntry, AddHostHandle, AddAliasHandle, AddPassHandle):
    pass


class RemoveWebsiteEntry(BaseBotMixin,
                         handler='handle_remove_website',
                         commands=['remove_website'],
                         description='Remove existing website from app',
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
            if message.chat.type == 'private':
                alias = remove_website(message.chat.username, **dict(data))
            else:
                alias = remove_website(message.chat.title, **dict(data))
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


class SubWebsiteEntry(BaseBotMixin,
                      handler='handle_sub_website',
                      commands=['sub_website'],
                      description='Subscribe to an existing website',
                      state=None):

    async def handle_sub_website(self, message: types.Message):
        await SubWebsiteForm.token.set()
        await message.reply('What is your website token that you want to subscribe to?')


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
            if message.chat.type == 'private':
                alias = subscribe_website(message.chat.username, message.chat.id, **dict(data))
            else:
                alias = subscribe_website(message.chat.title, message.chat.id, **dict(data))
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


class UnsubWebsiteEntry(BaseBotMixin,
                        handler='handle_unsub_website',
                        commands=['unsub_website'],
                        description='Unsubscribe from an existing website',
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
            if message.chat.type == 'private':
                alias = unsubscribe_website(message.chat.username, **dict(data))
            else:
                alias = unsubscribe_website(message.chat.title, **dict(data))
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
