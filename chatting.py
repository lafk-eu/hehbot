from mbot import bot, dp
from hehbot.decoration.credit_image import get_avatar_id_async

from aiogram import types
from aiogram.utils.chat_action import ChatActionSender

from hehbot.client import *
from hehbot.memory import *
import hehbot.gpt as gpt 
from hehbot.base_command import BotCommand

from time import sleep

from google.api_core.exceptions import ResourceExhausted

allowed_chats = [-1002131963990, 788237639, -1001909232100, -1001568642353, -1001947307140]
command_said = False

user_message_times = {}

async def get_mentioned_user(msg: types.Message):
    if msg.reply_to_message:
        if msg.reply_to_message.from_user:
            if msg.reply_to_message.from_user.username:
                return f' (${msg.reply_to_message.from_user.username})'
    return ''

async def do_command(msg: types.Message) -> ChatMessage | None:
    # process user's text if has commands

    if BotCommand.count_commands(msg.text) == 1:
        cmd_result = await BotCommand.cmd_by_text(msg, msg.text + await get_mentioned_user(msg))
        if cmd_result:
            m = await ChatMessage.from_telegram(msg)
            m.text = cmd_result
            await repo_msg.add_message(m)
            return m
    
    return None


@dp.message()
async def handler_filter_message(msg: types.Message) -> None:

    
    # person create or update and get
    person = await verify_user(msg)
    if not person:
        return # person was notified
    
    #await msg.reply(await gpt.generate_text(msg))

    if str(msg.text).startswith('/'):
        cmd_msg = await do_command(msg)
        if cmd_msg:
            await msg.reply(cmd_msg.text)    
        return
    
    repo_user.delete(-2)

    async with ChatActionSender.typing(msg.chat.id, bot):
        # find command by AI and send if True
        cmd = await BotCommand.compare_async(msg.text) 

        if cmd:
            execution = await cmd.execute(msg, '', msg.text + await get_mentioned_user(msg))
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

    if msg.is_automatic_forward or msg.forward_from or msg.forward_from_message_id or msg.forward_origin:
        return None
    
    if not msg.text:
        return None
    
    if str(msg.text).lower().startswith('суд') or str(msg.text).startswith('/'):
        # message has text
        if len(str(msg.text)) > 40:
            await msg.answer("Я не читаю повідомлення в яких більше 8 літер.")
            return None
    elif msg.reply_to_message and msg.reply_to_message.from_user.id == bot.id:
            idi = await BotCommand.compare_async(msg.text)
            if idi and idi.command_name() == 'idi_nakhuy':
                await idi.execute(msg, [], '')
            return None
    else:
        return None
    
    # chat id in whitelist
    if msg.chat.id not in allowed_chats:
        await msg.answer("Цей чат не зареєстрований в системі.")
        print(f'намагалися писати в чаті: {msg.chat.id}')
        return None

    # person: create or update
    person = await repo_user.by_tg_message(msg)

    # person cannot be created or received
    if not person:
        await msg.answer("Ви не зареєстровані в системі. Я зареєструю самостійно, якщо у вашому профілі буде ім'я та нікнейм.")
        return None
    
    can_send = await repo_msg.can_send_message(person.number, msg.chat.id)
    if not can_send:
        await msg.reply("Без флуду, будь ласка.")
        return None
    
    await repo_msg.add_message(ChatMessage(msg.text, msg.date, msg.chat.id, person.id, person.number))
    
    return person