import re
import time

from aiogram import types
from aiogram.dispatcher import FSMContext

from communication.base import BusDir, BusMessage
from communication.mixins import BusMixin
from db.messaging import ChatMessage
from db.website import TOKEN_KEY, get_full_session_key, get_host_from_token, get_token_from_host, is_user_subscribed
from telegram.base import TelegramBotMixin

HOST_TXT = ''
TOKEN_TXT = 'WSID: '
SESSION_TXT = 'ID: '
USER_TXT = 'User: '
TEXT_TXT = '\n'


class TelegramBot(BusMixin, TelegramBotMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, sub_dir=BusDir.COM, pub_dir=BusDir.TG, **kwargs)

    async def on_bus_message(self, message: BusMessage):
        await super().on_bus_message(message)
        chat_message: ChatMessage = ChatMessage.from_dict(message.data)
        host = f'{HOST_TXT}<b>{get_host_from_token(chat_message.token)}</b>'
        # token_id = f'{TOKEN_TXT}{chat_message.token[-12:]}'
        session_id = f'{SESSION_TXT}{chat_message.session[-12:]}'
        user = f'{USER_TXT}<b>{chat_message.user if chat_message.user else "Unknown"}</b>'
        text = f'{TEXT_TXT}<b>{chat_message.text}</b>'
        return await self.send_tg_message(message.data[TOKEN_KEY], '\n'.join([host, session_id, user, text]))

    async def handle_reply(self, message: types.Message):
        try:
            parent_text = message.reply_to_message.text
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
