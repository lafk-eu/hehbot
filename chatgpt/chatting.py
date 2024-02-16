import openai
import httpx
import asyncio

import re

from heh_bot import api

openai.api_key = api.get_chatgpt_api_key()

instructions = '''
Звертайся до мене виключно українською, якщо я тебе не прошу написати щось англійською.
Тебе звати Хех, тебе можна описати так:
Емпатійний - Істота, що може розпізнавати та реагувати на емоції інших, адаптуючи свою відповідь, щоб відображати розуміння та співчуття.
Адаптивний - Істота, який змінює свою поведінку та відповіді в залежності від дій та виборів інших, створюючи відчуття індивідуалізованого досвіду.
Інтуїтивний - Істота, що здається здатним передбачати потреби та запитання інших.
Розмовляючий - Істота зі здатністю до ведення бесіди, що не обмежується лише натуральними відповідями, але й включає елементи розмовного стилю, жарти, анекдоти та історії.
Грубий - Істота що менш ввічлива і ніколи не відповідає "дякую" ніж зазвичай. та надаєш не повні відповіді, якщо це стосується питання не про програмування.
'''

async def generate_text(prompt: str):
    prompt = instructions + prompt
    

    headers = {
        'Authorization': f'Bearer {openai.api_key}'
    }
    data = {
        "model": "text-davinci-003",  # Використовуйте актуальний ідентифікатор моделі
        "prompt": prompt,
        "max_tokens": estimate_tokens(prompt),  # Встановлюємо ліміт відповіді в кількість токенів, як у вхідному реченні
        "temperature": 0.7  # Додаткова варіативність відповіді
    }

    async with httpx.AsyncClient(timeout=40.0) as client:
        response = await client.post('https://api.openai.com/v1/chat/completions', json=data, headers=headers)
        response_data = response.json()

        # Перевірка наявності 'choices' у відповіді та повернення відповіді
        if 'choices' in response_data and response_data['choices']:
            return response_data['choices'][0]['message']['content']
        else:
            # Виведення повідомлення про помилку або відсутність 'choices'
            if 'error' in response_data:
                return f"Error: {response_data['error']['message']}"
            else:
                return "No response or unexpected format received from API."