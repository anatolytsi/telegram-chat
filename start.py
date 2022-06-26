import os
from dotenv import load_dotenv

from telegram.bot import TelegramBot
from ws.base import WebsocketServer

load_dotenv()

TG_TOKEN = os.environ.get('TG_TOKEN')
WS_HOST = os.environ.get('WS_HOST')
WS_PORT = int(os.environ.get('WS_PORT'))

bot = TelegramBot(tg_token=TG_TOKEN)
ws_server = WebsocketServer(host=WS_HOST, port=WS_PORT, is_standalone=False)
ws_server.start()
bot.run()
