from heh_bot import dp, bot
from aiogram import types

import re

# Функція для обробки повідомлень, що містять лише англійські літери
@dp.message(lambda message: re.match(r"^[A-Za-z ]+$", message.text))
async def handler_improve_english(message: types.Message) -> None:
    await message.answer("Your message contains only English letters.")