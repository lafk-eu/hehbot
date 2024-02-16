from heh_bot import dp, bot, user_repo, chat_repo
from aiogram import types
from aiogram.utils.chat_action import ChatActionSender

from chatgpt.chatting import generate_text

@dp.message()
async def handler_filter_message(message: types.Message) -> None:
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        if message.chat.type == "private":
            await bot_mentioned(message)
        elif message.chat.type in ["group", "supergroup"]:
            await bot_mentioned(message)
        else:
            await message.answer("Це повідомлення не відповідає жодному з очікуваних типів чату, іді нахуй.")

async def bot_mentioned(message: types.Message) -> None:
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        #answer = await generate_text(message.text)
        if "хех" in message.text.lower():
            await message.answer('іді в попу') 
        elif "адмін" in message.text.lower():
            if user_repo.get_person(str(message.from_user.id)):
                await message.answer('ого, ти адмін')
            else:
                await message.answer('ти не адмін') 
        else:
            await message.answer('теж') 
