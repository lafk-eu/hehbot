import vertexai, aiogram
from vertexai.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models

from coms import BotCommand
from client import repo_user
from client import Person
from os import system
from typing import Union, Iterable

from chat_memory import repo_msg, ChatMessage, get_history

# Initialize Vertex AI
vertexai.init(project='hehbot', location='europe-west9')
    
# Load the model
multimodal_model = GenerativeModel("gemini-pro")

async def find_commands(person: Person, text: str = ''):
    config = {
        "max_output_tokens": 2048,
        "temperature": 0.864,
        "top_p": 0.98,
        "top_k": 40
    }

    # Query the model
    return await multimodal_model.generate_content_async(
        [
        "User: How many social credits does I have? context: In the context of our application, social credit is a measure of a user's contribution and behavior within the community. Each user starts with a default value zero and it can increase or decrease based on their actions.",
        "/mycredit",
    
        "User: How many social credits does USERNAME have? context: Social credits are awarded to users based on their contributions to the community, such as posting useful content, helping others, or participating in community events.",
        "/mycredit USERNAME",
    
        "User: increase 400 social credits for USERNAME? context: Users can increase their social credits by actively participating in the community, contributing valuable content, and engaging positively with other members.",
        "/credit USERNAME 400",
    
        "User: decrease 200 social credits for USERNAME? context: Social credits can decrease as a result of negative actions within the community, such as posting inappropriate content, being disrespectful to others, or violating community guidelines.",
        "/credit USERNAME -200",
    
        "User: add -300 credits for USERNAME? context: Social credits can decrease as a result of negative actions within the community, such as posting inappropriate content, being disrespectful to others, or violating community guidelines.",
        "/credit USERNAME -300",

        "User: Who are the top users by social credit? context: The community platform ranks users based on their social credit score, highlighting those who contribute positively and engage constructively with the community.",
        "/highscore",

        "User: Who are the lowest ranked users by social credit? context: Users with the lowest social credit scores are often those who have violated community guidelines or have had a negative impact on the community through their actions.",
        "/lowscore",

        "User: some text? context: asking with no context",
        "/nothing",
        
        'User: What are commands do you know?',
        await say_commands(),

        f'User "{person.name}": {text}',
        ],
    generation_config=config, safety_settings={
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    })


model = GenerativeModel("gemini-1.0-pro-001")
chat = model.start_chat()

async def generate_text(chat_id: int, include_commands: bool = False, command_said: bool = False):

    config = {
        "max_output_tokens": 2048,
        "temperature": 0.864,
        "top_p": 0.98,
        "top_k": 40
    }

    return await chat.send_message_async(f"""
{await say_commands() + '\n' + await say_about_channel() if include_commands else ""}

{await get_history(chat_id, 2) if command_said else await get_history(chat_id, 1)}

""", generation_config=config, safety_settings={
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    })

async def say_commands(ignore_non_commands_msgs: bool = False):
    return f'граємо в Telegram: говоримо про відеоігрову тематику в основному. Можна також дізнатися доступні команди через: /about' 

async def say_about_channel():
    return """User: Також ми говоримо про відеоігрову тематику. Це чат ютубера Платона Дубашидзе.
User: What genres does Platon Dubashydze's YouTube channel focus on? context: Welcome to my channel! Here you will find various original videos mainly dedicated to gaming themes, game reviews, and of course, Category B jokes, because what would it be without them. About me: a director by education, a game developer at heart, an amateur in fact.
gaming themes, game reviews, Category B jokes.
User: What is Platon Dubashydze's background? context: Welcome to my channel! Here you will find various original videos mainly dedicated to gaming themes, game reviews, and of course, Category B jokes, because what would it be without them. About me: a director by education, a game developer at heart, an amateur in fact.
director by education, game developer at heart, amateur in fact
User: How does Platon Dubashydze describe his YouTube content? context: Welcome to my channel! Here you will find various original videos mainly dedicated to gaming themes, game reviews, and of course, Category B jokes, because what would it be without them. About me: a director by education, a game developer at heart, an amateur in fact.
various original videos, mainly gaming, reviews, Category B jokes"""


def say_to_db(tg_msg: aiogram.types.Message, text: str):
    m = ChatMessage({'tg': -2, 
         'text': text,
         'number': -2,
         'tg_group': tg_msg.chat.id})
    repo_msg.add_message(m)