import re
import time

from aiogram import types
from aiogram.dispatcher import FSMContext

from communication.base import BusDir, BusMessage, CHANNEL_KEY
from communication.mixins import BusMixin
from db.messaging import ChatMessage
from db.website import TOKEN_KEY, get_full_session_key, get_host_from_token, get_token_from_host, is_user_subscribed, \
    get_website_subscribers
from telegram.base import TelegramBotMixin

REPLY_TXT = 'Reply from @'
HOST_TXT = ''
TOKEN_TXT = 'WSID: '
SESSION_TXT = 'ID: '
USER_TXT = 'User: '
TEXT_TXT = '\n'


def format_host(host: str) -> str:
    return f'{HOST_TXT}<b>{host}</b>'


def format_session(session: str) -> str:
    return f'{SESSION_TXT}{session}'


def format_user(user: str) -> str:
    return f'{USER_TXT}<b>{user if user else "Unknown"}</b>'


def format_text(text: str) -> str:
    return f'{TEXT_TXT}<b>{text}</b>'


def format_reply_username(username: str) -> str:
    return f'{REPLY_TXT}{username}'


class TelegramBot(BusMixin, TelegramBotMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, sub_dir=BusDir.COM, pub_dir=BusDir.TG, **kwargs)

    async def on_bus_message(self, message: BusMessage):
        await super().on_bus_message(message)
        chat_message: ChatMessage = ChatMessage.from_dict(message.data)
        host = format_host(get_host_from_token(chat_message.token))
        # token_id = f'{TOKEN_TXT}{chat_message.token[-12:]}'
        session_id = format_session(chat_message.session[-12:])
        user = format_user(chat_message.user)
        text = format_text(chat_message.text)
        return await self.send_tg_message(message.data[TOKEN_KEY], '\n'.join([host, session_id, user, text]))

    async def handle_reply(self, message: types.Message):
        try:
            parent_text = message.reply_to_message.text
            if REPLY_TXT in parent_text:
                return
            host = parent_text.split('\n')[0]
            # token_end = re.search(f'^{TOKEN_TXT}([^\n]+)', parent_text, re.M).group(1)
            session_key_end = re.search(f'^{SESSION_TXT}([^\n]+)', parent_text, re.M).group(1)
            token = get_token_from_host(host)
            chat = message.from_user.username if message.chat.type == 'private' else message.chat.title
            if not is_user_subscribed(chat, token):
                await message.reply('You are no longer subscribed to this website!')
                return
            # token = get_full_token(token_end)
            session_key = get_full_session_key(token, session_key_end)
            data = ChatMessage(token=token,
                               text=message.text,
                               timestamp=int(time.time()),
                               session=session_key,
                               user=message.from_user.first_name,
                               username=message.from_user.username)
            self.send_bus_message(token, data.to_dict())
            channels = [sub[CHANNEL_KEY] for sub in get_website_subscribers(token)
                        if sub[CHANNEL_KEY] != message.chat.id]
            user = re.search(f'^{USER_TXT}([^\n]+)', parent_text, re.M).group(1)
            user_txt = re.search(f'^{USER_TXT}[^\n]+\\s+(.+)', parent_text, re.M).group(1)
            text_to_others = f'{format_reply_username(message.from_user.username)}' \
                             f'{format_text(message.text)}\n\nto\n' \
                             f'{format_host(host)}\n{format_session(session_key_end)}\n' \
                             f'{format_user(user)}\n{user_txt}'
            await self._send_to_channels(channels, text_to_others)
        except AttributeError:
            await self._bot.send_message(chat_id=message.chat.id,
                                         text='Message you replied to is incorrect and does not belong to any chat',
                                         disable_notification=True)

    async def handle_add_pass(self, message: types.Message, state: FSMContext):
        await super().handle_add_pass(message, state)
        self._update_websites()

    async def handle_remove_pass(self, message: types.Message, state: FSMContext):
        await super().handle_add_pass(message, state)
        self._update_websites()
