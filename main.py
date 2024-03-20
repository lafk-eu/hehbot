from mbot import bot, dp
from hehbot.game import *
from chatting import *

# Головна асинхронна функція для запуску бота
async def main() -> None:
    await BotCommand.initialize_embeddings()
    await bot.delete_webhook(True)
    await dp.start_polling(bot)

import asyncio
import logging
import sys

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())