import asyncio
import logging
import sys

from heh_bot import *

# Головна асинхронна функція для запуску бота
async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())