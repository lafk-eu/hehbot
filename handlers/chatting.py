from heh_bot import dp, bot, user_repo, chat_repo
from aiogram import types
from aiogram.utils.chat_action import ChatActionSender

import datetime

from chatgpt.chatting import generate_text
from chatgpt.commands import ChatCommandManager
from chatgpt.chat_memory import ChatMessage, Dialog

@dp.message()
async def handler_filter_message(message: types.Message) -> None:
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):

        user = user_repo.get_person(message.from_user.id)
        if not user:
            await message.answer("Ви не зареєстровані в системі.")
            return
        
        if message.chat.type == "private":
            print(chat_repo.get_dialogues_by_group_id(message.chat.id))

            chat_message = ChatMessage(text=message.text, date=message.date, user_id=str(message.from_user.id))
            # Створюємо діалог без відповіді чатбота і з одним повідомленням користувача
            dialog = Dialog(group_id=message.chat.id, chatbot_msg=ChatMessage(text="", date=message.date, user_id="0"), users_msgs=[chat_message])
            chat_repo.add_dialog(dialog)
            
            # Перевіряємо, чи досягнуто максимальну кількість повідомлень
            dialogs = chat_repo.get_dialogues_by_group_id(group_id=message.chat.id)
            if any(d.length() >= Dialog.MAX_MESSAGES for d in dialogs):
                response = generate_text(message.chat.id)
                dialog.chatbot_msg = ChatMessage(response, message.date, '0')

        elif message.chat.type in ["group", "supergroup"]:
            group_id = message.chat.id
            await handler_admin(message)

        else:
            await message.answer("Це повідомлення не відповідає жодному з очікуваних типів чату, іді нахуй.")

async def bot_mentioned(message: types.Message) -> None:
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        #answer = await generate_text(message.text)
        if "хех" in message.text.lower():
            await message.answer('іді в попу') 
        else:
            await message.answer('juj. ' + str(message.from_user.id)) 

async def handler_admin(message: types.Message) -> None:
    if user_repo.get_person(str(message.from_user.id)):
        command = ChatCommandManager()
        answer = command.exe_html(message.text)
        await message.answer(str(answer))
    else:
        await message.answer('ти не адмін') 