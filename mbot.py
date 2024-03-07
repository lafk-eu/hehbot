from aiogram import Bot, Dispatcher
from hehbot.key_api import api

TOKEN = api.bot

# Створення диспетчера та bot
dp = Dispatcher()
bot = Bot(TOKEN)