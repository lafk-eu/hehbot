from hehbot import bot, dp
from hehbot.decoration import get_avatar_id_async

from aiogram import types
from aiogram.utils.chat_action import ChatActionSender

from hehbot.client import *
from hehbot.memory import *
import hehbot.gpt as gpt 
from hehbot.base_command import BotCommand

from time import sleep

from google.api_core.exceptions import ResourceExhausted

allowed_chats = [-4139370527, -1001947307140, 788237639]
command_said = False

async def do_command(person: Person, msg: types.Message) -> ChatMessage | None:
    # process user's text if has commands

    if BotCommand.count_commands(msg.text) == 1 and msg.text.startswith('/'):
        cmd_result = BotCommand.cmd_by_text(person, msg.text)
        if cmd_result:
            m = await ChatMessage.from_telegram(msg)
            m.text = cmd_result
            repo_msg.add_message(m)
            return m
    
    return None


@dp.message()
async def handler_filter_message(msg: types.Message) -> None:
    global command_said
    async with ChatActionSender.typing(msg.chat.id, bot):
        # person create or get
        person = await verify_user(msg)
        if not person:
            return # person was notified
        
        print('cnota')

        # find command by AI and send if True
        cmd = await BotCommand.compare_async(msg.text) 

        # save user message
        #repo_msg.add_message(ChatMessage(msg))

        #if BotCommand.count_commands(text) > 0:
        #    command_said = True
        #else:
        #    command_said = False
        if cmd:
            execution = await cmd.execute(msg, '', msg.text)
            if execution:
                await msg.answer(execution)

async def generate_answer(msg: types.Message, command_said_before: bool = False) -> None:
    response = await gpt.generate_text(msg)
    
    if not response:
        return 'Вибачаюсь, сталася помилка'
    
    if BotCommand.count_commands(response) > 0:
        await do_command(await repo_user.by_tg_message(msg), msg)
    
    # save bot message
    gpt.say_to_db(msg, response)
     
    return response



async def verify_user(msg: types.Message) -> Person | None:

    if msg.reply_to_message is not None and msg.reply_to_message.from_user.id == bot.id:
        pass
    elif msg.text and str(msg.text).startswith('суд'):
        pass
    else:
        return None

    # ignore rogulyaky group
    #if msg.chat.id == -1001947307140:
    #    return None

    # message has text
    if not msg.text:
        return None

    # person: create or update
    person = await repo_user.by_tg_message(msg)

    # person cannot be created or received
    if not person:
        await msg.answer("Ви не зареєстровані в системі. Я зареєструю самостійно, якщо у вашому профілі буде ім'я та нікнейм.")
        return None
    
    # update user info in data base
    u = msg.from_user
    await repo_user.update_person(u.id, u.full_name, await get_avatar_id_async(u.id), u.username)

    # chat id in whitelist
    if msg.chat.id not in allowed_chats:
        await msg.answer("Цей чат не зареєстрований в системі.")
        print(f'намагалися писати в чаті: {msg.chat.id}')
        return None
    
    return person