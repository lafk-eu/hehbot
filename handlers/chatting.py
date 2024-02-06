from heh_bot import dp, bot
from aiogram import types
from aiogram.utils.chat_action import ChatActionSender

from chatgpt.chatting import generate_text

# Функція для обробки повідомлень, що містить "хех"
@dp.message(lambda message: "хех" in message.text.lower() if message.text else False)
async def handler_bot_mentioned(message: types.Message) -> None:
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        answer = await generate_text(message.text)
        await message.answer(answer)