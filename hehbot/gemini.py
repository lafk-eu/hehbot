import vertexai, aiogram
from vertexai.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models

from hehbot.command import BotCommand
from client import repo_user
from client import Person
from os import system
from typing import Union, Iterable

from chat_memory import repo_msg, ChatMessage, get_history

# Initialize Vertex AI
vertexai.init(project='hehbot', location='europe-west4')
    
# Load the model

async def find_commands(person: Person, chat_id: int, text: str = ''):
    config = {
        "max_output_tokens": 256,
        "temperature": 0.864,
        "top_p": 0.33,
        "top_k": 40
    }

    multimodal_model = GenerativeModel("text-bison")

    # Query the model
    return await multimodal_model.generate_content_async(
        [
        "User: Скільки соціальних кредитів я маю?", "/mycredit",
        "User: Скільки в мене?", "/mycredit",
        "User: Скільки SOME_NAME має?", "/mycredit SOME_NAME",
        "User: а скільки SOME_NAME?",  "/mycredit SOME_NAME",
    
        "User: додай 400 для SOME_NAME",  "/credit SOME_NAME 400",
        "User: +400 для SOME_NAME",  "/credit SOME_NAME 400",
        "User: відніми 200 у SOME_NAME",  "/credit SOME_NAME -200",
        "User: -300 соціальних кредитів в SOME_NAME",  "/credit SOME_NAME -300",
        "Історія: ['SOME_NAME: всім привітик!', 'Gemini: Привітик!']. User: Дай останньому 50 кредитів", '/credit SOME_NAME 50'

        "User: топ", "/highscore",
        "User: топ найкращих", "/highscore",
        "User: топ найгірших", "/lowscore",

        'Asking about not commands', '/nothing',
        

        #f'Історія: {str(await get_history(chat_id, 4))}. User {person.name}: {text}',
        'Про що можемо поспілкуватися?', say_game(say_about_nothing=True),
        f'User {person.name}: {text}',
        #'What commands do you know?',

        ],

    generation_config=config, safety_settings=
    {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    })


model = GenerativeModel("text-bison")
chat = model.start_chat()

async def generate_text(chat_id: int, command_said: bool = False):

    config = {
        "max_output_tokens": 2048,
        "temperature": 0.864,
        "top_p": 0.7,
        "top_k": 40
    }

    return await chat.send_message_async(f"""
{await get_history(chat_id, 2) if command_said else await get_history(chat_id, 1)}

""", generation_config=config, safety_settings={
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    })

def say_game(say_about_nothing: bool = False):
    return f'граємо в Telegram: можемо говорити про відеоігри, де нам обом доступні запити: {BotCommand.get_commands_description(include_nothing=say_about_nothing)}' 

def say_about_channel():
    return """User: Також ми говоримо про відеоігрову тематику. Це чат ютубера Платона Дубашидзе.
User: Які жанри фокусується YouTube канал Платона Дубашидзе? контекст: Ласкаво просимо на мій канал! Тут ви знайдете різноманітні оригінальні відео, головним чином присвячені відеоігровій тематиці, оглядам ігор, і звичайно, жартам категорії Б, бо що б це було без них. Про мене: за освітою режисер, за покликанням розробник ігор, на ділі аматор.
User: Який фон у Платона Дубашидзе? контекст: Ласкаво просимо на мій канал! Тут ви знайдете різноманітні оригінальні відео, головним чином присвячені відеоігровій тематиці, оглядам ігор, і звичайно, жартам категорії Б, бо що б це було без них. Про мене: за освітою режисер, за покликанням розробник ігор, на ділі аматор.
User: Як Платон Дубашидзе описує свій YouTube контент? контекст: Ласкаво просимо на мій канал! Тут ви знайдете різноманітні оригінальні відео, головним чином присвячені відеоігровій тематиці, оглядам ігор, і звичайно, жартам категорії Б, бо що б це було без них. Про мене: за освітою режисер, за покликанням розробник ігор, на ділі аматор.
відеоігрові теми, огляди ігор, жарти категорії Б."""

chat.send_message(f'{say_game()}')

def say_to_db(tg_msg: aiogram.types.Message, text: str):
    m = ChatMessage({'tg': -2, 
         'text': text,
         'number': -2,
         'tg_group': tg_msg.chat.id})
    repo_msg.add_message(m)