from main import dp, bot

from aiogram import types
from aiogram.utils.chat_action import ChatActionSender

import datetime
from chat_memory import ChatMessage, repo_msg
from hehbot.admin import repo_staff
from hehbot.client import repo_user, Person

from hehbot import gemini
from hehbot.command import BotCommand
from time import sleep

from google.api_core.exceptions import ResourceExhausted

allowed_chats = [-4139370527, -1001947307140]
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
    global command_said
    async with ChatActionSender.typing(bot=bot, chat_id=msg.chat.id):
        # person create or get
        person = await verify_user(msg)
        if not person:
            return # person was notified
        
        com = await do_command(person, msg)
        if com:
            print('user command')
            command_said = True
            repo_msg.add_message(com)
            return # command written by user were handled and sent


        # if user text contains >1 commands or <1

        # save user message
        repo_msg.add_message(ChatMessage(msg))

        # find command by AI and send if True
        text = await send_text(msg, command_said) 

        if BotCommand.count_commands(text) > 0:
            command_said = True
        else:
            command_said = False
        
        await msg.answer(text)

        


async def send_commands(person: Person, msg: types.Message) -> bool:
    # generate and process answer (first, generate for commands)
    try:
        response = await gemini.find_commands(person, msg.text)
    except ResourceExhausted:
        await msg.answer('Забагато запитів.')
        return
    
    generated = False

    try:
        generated = response.text
        print("text command: ", generated)
    except ValueError:
        await msg.answer('Вибачаюсь, сталася помилка.')
        print('text command: refused by empty generation')
        return True
    
    if generated.find('/nothing') != -1:
        print('text command: refused by /nothing')
        return False
    
    gemini.say_to_db(msg, generated)
    
    answer = BotCommand.process_text(person, generated)
    if answer:     
        # if has commands
        await msg.answer(answer)
        return True
    print('find command refused: did\'nt see purpose in the text')
    return False


            
async def send_text(msg: types.Message, command_said_before: bool = False) -> None:
    # generate new text which non-commands about
    try:
        response = await gemini.generate_text(
            msg.chat.id, 
            command_said=command_said_before
            )
    except ResourceExhausted:
        return 'Забагато запитів.'
    
    generated = False

    if response:
        generated = response.candidates[-1].content.text
    if not generated:
        return 'Вибачаюсь, сталася помилка'
    
    if BotCommand.count_commands(generated) > 0:
        await do_command(repo_user.by_tg_message(msg), msg)
    
    # save bot message
    gemini.say_to_db(msg, generated)
     
    #generated_corrected = await convert_text_to_markdown_corrected(generated)
    return generated
    #except:
    #    print('cannot send within Markdown parsing')
    #    await msg.answer(generated)

async def convert_text_to_markdown_corrected(text):
    # Split the text into sections based on the double newline as a delimiter
    sections = text.split("\n\n")
    
    # Initialize an empty list to hold the markdown converted sections
    markdown_sections = []
    
    for section in sections:
        # Split each section into lines
        lines = section.split("\n")
        # Process the first line as a header, making it bold
        header = f"**{lines[0]}**"
        # Process the remaining lines as list items, prefixing each with a hyphen
        list_items = "\n".join([f"- {line.strip('* ')}" for line in lines[1:] if line.strip()])
        # Combine the header and the list items, and append to the markdown sections list
        markdown_section = f"{header}\n\n{list_items}"
        markdown_sections.append(markdown_section)
    
    # Join all markdown sections with two newlines as a delimiter
    markdown_text = "\n\n".join(markdown_sections)
    return markdown_text



async def verify_user(msg: types.Message) -> Person | None:
    # check non rogulyaky group
    #if msg.chat.id == -1001947307140:
    #    return None

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