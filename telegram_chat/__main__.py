import os
from dotenv import load_dotenv

from telegram_chat.bot import TelegramBot

load_dotenv()

bot = TelegramBot(tg_token=os.environ.get('TG_TOKEN'))
bot.run()
