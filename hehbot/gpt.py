import aiogram

from hehbot.memory import repo_msg, ChatMessage, get_history
from hehbot.key_api import api
from hehbot.client import repo_user
from hehbot.command import BotCommand

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
    return f'Тебе звати Хех: можемо говорити про відеоігри, де нам обом доступні запити: {BotCommand.get_commands_description(include_nothing=say_about_nothing)}' 

def say_about_channel():
    return """User: Також ми говоримо про відеоігрову тематику. Це чат ютубера Платона Дубашидзе.
User: Які жанри фокусується YouTube канал Платона Дубашидзе? контекст: Ласкаво просимо на мій канал! Тут ви знайдете різноманітні оригінальні відео, головним чином присвячені відеоігровій тематиці, оглядам ігор, і звичайно, жартам категорії Б, бо що б це було без них. Про мене: за освітою режисер, за покликанням розробник ігор, на ділі аматор.
User: Який фон у Платона Дубашидзе? контекст: Ласкаво просимо на мій канал! Тут ви знайдете різноманітні оригінальні відео, головним чином присвячені відеоігровій тематиці, оглядам ігор, і звичайно, жартам категорії Б, бо що б це було без них. Про мене: за освітою режисер, за покликанням розробник ігор, на ділі аматор.
User: Як Платон Дубашидзе описує свій YouTube контент? контекст: Ласкаво просимо на мій канал! Тут ви знайдете різноманітні оригінальні відео, головним чином присвячені відеоігровій тематиці, оглядам ігор, і звичайно, жартам категорії Б, бо що б це було без них. Про мене: за освітою режисер, за покликанням розробник ігор, на ділі аматор.
відеоігрові теми, огляди ігор, жарти категорії Б."""

def say_to_db(tg_msg: aiogram.types.Message, text: str):
    m = ChatMessage({'tg': -2, 
         'text': text,
         'number': -2,
         'tg_group': tg_msg.chat.id})
    repo_msg.add_message(m)