from key_api import APIHolder

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

# Отримання токена бота зі змінної середовища
api = APIHolder()
TOKEN = api.get_bot_api_key()

# Створення диспетчера та bot
dp = Dispatcher()
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)

from handlers import *

# Функція для обробки команди /start
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Привіт, {hbold(message.from_user.full_name)}!")
