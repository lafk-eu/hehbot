from heh_bot import dp, bot

from aiogram import types
from aiogram.utils.chat_action import ChatActionSender

import datetime
from chat_memory import ChatMessage, repo_msg
from hehbot.adminc import repo_staff
from hehbot.client import repo_user, Person

from hehbot import gemini
from hehbot.coms import BotCommand
from time import sleep

allowed_chats = [-4139370527, -1001947307140]
is_first_message = True
command_said = False

async def do_command(person: Person, msg: types.Message) -> ChatMessage | None:
    # process user's text if has commands

    if BotCommand.count_commands(msg.text) == 1 and msg.text.startswith('/'):
        m = ChatMessage(msg)
        m.text = BotCommand.process_text(person, msg.text)
        repo_msg.add_message(m)
        await bot.send_message(msg.chat.id, m.text)
        return m
    
    return None


@dp.message()
async def handler_filter_message(msg: types.Message) -> None:
    async with ChatActionSender.typing(bot=bot, chat_id=msg.chat.id):
        # person create or get
        person = await verify_user(msg)
        if not person:
            return # person was notified
        
        com = await do_command(person, msg)
        if com:
            print('user command')
            command_said = True
            return # command written by user were handled and sent


        # if user text contains >1 commands or <1

        # save user message
        repo_msg.add_message(ChatMessage(msg))

        # find command by AI and send if True
        if not await send_commands(person, msg):
            # not found. entertain user.
            await send_text(msg, command_said) 
            print('generated text')
            command_said = False   
        else:
            print('generated command')
            command_said = True 
        

async def send_commands(person: Person, msg: types.Message) -> bool:
    # generate and process answer (first, generate for commands)
    command_answer = await gemini.find_commands(person, msg.text)

    proc_command = BotCommand.process_text(person, command_answer.text)
    if proc_command:     
        # if has commands
        await msg.answer(proc_command)
        return True
    return False
            
async def send_text(msg: types.Message, command_said_before: bool = False) -> None:
    global is_first_message
    # generate new text which non-commands about
    response = await gemini.generate_text(
        msg.chat.id, 
        include_commands=is_first_message, 
        command_said=command_said_before
        )
    
    is_first_message = False
    generated = False

    if response:
        generated = response.candidates[-1].content.text
    if not generated:
        await bot.send_message(msg.chat.id, text='Вибачаюсь, сталася помилка')
        return
    
    # save bot message
    gemini.say_to_db(msg, generated)
            
    await bot.send_message(msg.chat.id, text=generated, parse_mode='Markdown')
    #except Exception as e:
        #await message.answer("Вибачаюсь, сталася помилка.")
    
async def verify_user(msg: types.Message) -> Person | None:
    # check non rogulyaky group
    if msg.chat.id == -1001947307140:
        return None

    # message has text
    if not msg.text:
        return None

    # person create or get
    person = repo_user.by_tg_message(msg)

    # person cannot be created or received
    if not person:
        await msg.answer("Ви не зареєстровані в системі. Я зареєструю самостійно якщо у вашому профілі буде нікнейм")
        return None

    # chat id in whitelist
    if msg.chat.id not in allowed_chats:
        await msg.answer("Цей чат не зареєстрований в системі.")
        print(f'намагалися писати в чаті: {msg.chat.id}')
        return None
    
    # answer in groups only
    if not msg.chat.type in ['group', 'supergroup']:
        await msg.answer("Цей чат не зареєстрований в системі.")
        return None
    
    return person