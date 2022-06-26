import re
import time

from aiogram import types

from communication.base import BusDir, BusMessage
from communication.mixins import BusMixin
from db.messaging import ChatMessage
from db.website import TOKEN_KEY, get_full_token, get_full_session_key
from telegram.base import TelegramBotMixin

TOKEN_TXT = 'WSID: '
SESSION_TXT = 'ID: '
USER_TXT = 'User: '
TEXT_TXT = 'Wrote: '


class TelegramBot(BusMixin, TelegramBotMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, sub_dir=BusDir.COM, pub_dir=BusDir.TG, **kwargs)

    async def on_bus_message(self, message: BusMessage):
        chat_message: ChatMessage = ChatMessage.from_dict(message.data)
        token_id = f'{TOKEN_TXT}{chat_message.token[-12:]}'
        session_id = f'{SESSION_TXT}{chat_message.session[-12:]}'
        user = f'{USER_TXT}<b>{chat_message.user if chat_message.user else "Unknown"}</b>'
        text = f'{TEXT_TXT}<b>{chat_message.text}</b>'
        return await self.send_tg_message(message.data[TOKEN_KEY], '\n'.join([token_id, session_id, user, text]))

    async def handle_reply(self, message: types.Message):
        try:
            parent_text = message.reply_to_message.text
            token_end = re.search(f'^{TOKEN_TXT}([^\n]+)', parent_text, re.M).group(1)
            session_key_end = re.search(f'^{SESSION_TXT}([^\n]+)', parent_text, re.M).group(1)
            token = get_full_token(token_end)
            session_key = get_full_session_key(token, session_key_end)
            data = ChatMessage(token=token,
                               text=message.text,
                               timestamp=int(time.time()),
                               session=session_key,
                               user=message.from_user.first_name,
                               username=message.from_user.username)
            self.send_bus_message(token, data.to_dict())
        except AttributeError:
            await self._bot.send_message(chat_id=message.from_user.id,
                                         text='Message you replied to is incorrect and does not belong to any chat',
                                         disable_notification=True)
