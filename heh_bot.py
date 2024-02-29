from key_api import APIHolder

from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from hehbot.client import repo_user
from hehbot.coms import BotCommand

# Отримання токена бота зі змінної середовища
api = APIHolder()
TOKEN = api.get_bot_api_key()

# Створення диспетчера та bot
dp = Dispatcher()
bot = Bot(TOKEN)

from chatting import *
