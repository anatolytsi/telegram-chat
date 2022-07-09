import time

from aiogram import types
from aiogram.dispatcher import FSMContext

from communication.base import BusDir, BusMessage, CHANNEL_KEY
from communication.mixins import BusMixin
from db.messaging import ChatMessage
from db.website import TOKEN_KEY, get_full_session_key, get_host_from_token, get_token_from_host, is_user_subscribed, \
    get_website_subscribers
from telegram.base import TelegramBotMixin
from telegram.formatter import create_formatted_user_text, REPLY_TXT, get_session_end_from_msg, \
    create_formatted_reply_text, get_user_from_msg, get_user_txt_from_msg, get_host_from_msg


class TelegramBot(BusMixin, TelegramBotMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, sub_dir=BusDir.COM, pub_dir=BusDir.TG, **kwargs)

    async def on_bus_message(self, message: BusMessage):
        await super().on_bus_message(message)
        chat_message: ChatMessage = ChatMessage.from_dict(message.data)
        formatted_text = create_formatted_user_text(get_host_from_token(chat_message.token),
                                                    chat_message.session[-12:],
                                                    chat_message.user,
                                                    chat_message.text)
        return await self.send_tg_message(message.data[TOKEN_KEY], formatted_text)

    async def handle_reply(self, message: types.Message):
        try:
            parent_text = message.reply_to_message.text
            if REPLY_TXT in parent_text:
                return
            host = get_host_from_msg(parent_text)
            # token_end = re.search(f'^{TOKEN_TXT}([^\n]+)', parent_text, re.M).group(1)
            session_key_end = get_session_end_from_msg(parent_text)
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
            user = get_user_from_msg(parent_text)
            user_txt = get_user_txt_from_msg(parent_text)

            text_to_others = create_formatted_reply_text(message.from_user.username, message.text,
                                                         host, session_key_end,
                                                         user, user_txt)
            await self._send_to_channels(channels, text_to_others)
        except AttributeError:
            await self._bot.send_message(chat_id=message.chat.id,
                                         text='Message you replied to is incorrect and does not belong to any chat',
                                         disable_notification=False)

    async def handle_add_pass(self, message: types.Message, state: FSMContext):
        await super().handle_add_pass(message, state)
        self._update_websites()

    async def handle_remove_pass(self, message: types.Message, state: FSMContext):
        await super().handle_add_pass(message, state)
        self._update_websites()
