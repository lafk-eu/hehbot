from key_api import APIHolder

from aiogram import Bot, Dispatcher

import asyncio
import logging
import sys

# Отримання токена бота зі змінної середовища
api = APIHolder()
TOKEN = api.get_bot_api_key()

# Створення диспетчера та bot
dp = Dispatcher()
bot = Bot(TOKEN)

from hehbot.chatting import *

# Головна асинхронна функція для запуску бота
async def main() -> None:
    await bot.delete_webhook(True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())