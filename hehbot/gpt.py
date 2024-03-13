import aiogram

from hehbot.memory import repo_msg, ChatMessage, get_history
from hehbot.key_api import api
from hehbot.client import repo_user
from hehbot.command import BotCommand
from hehbot import bot

from openai import OpenAIError
from requests.exceptions import RequestException

from openai import AsyncOpenAI
async_client = AsyncOpenAI(api_key=api.chatgpt)

async def generate_text(msg: aiogram.types.Message):
    #try:        
        history_messages = await get_history(msg.chat.id, 2)
            
        chat_completion = await async_client.chat.completions.create(
            messages=history_messages + [
            {
                "role": "system",
                "content": await say_game(),
            }
            ] + [
            {
                "role": "user",
                "content": f'{repo_user.by_tg(msg.from_user.id).name}: {msg.text}',
            }
            ],
            model="gpt-3.5-turbo-instruct",
            #temperature=0.7,
            max_tokens=100,
            #top_p=1.0,
            #frequency_penalty=0.0,
            #presence_penalty=0.0,
            
        )

        return chat_completion.choices[0].message.content
    #except RequestException:
    #    return "У мене обрізали кабель інтернету (пишу через мобільний)."
    #except OpenAIError:
    #    return "Сталася помилка."

async def say_game(say_about_nothing: bool = False):
    return f'Тебе звати Кайфо-Суддя. Можемо говорити про відеоігри, де нам обом доступні команди: {BotCommand.get_commands_description(include_nothing=say_about_nothing)}' 

def say_about_channel():
    return """Це чат ютубера Платона Дубашидзе.
Які жанри фокусується YouTube канал Платона Дубашидзе? 
Різноманітні оригінальні відео, головним чином присвячені відеоігровій тематиці, оглядам ігор, і звичайно, жартам категорії Б, бо що б це було без них.
Який фон у Платона Дубашидзе? 
Платон за освітою режисер, за покликанням розробник ігор, на ділі аматор.
"""

def say_to_db(tg_msg: aiogram.types.Message, text: str):
    m = ChatMessage.from_dict({'tg': bot.id, 
         'text': text,
         'number': -1,
         'tg_group': tg_msg.chat.id})
    repo_msg.add_message(m)