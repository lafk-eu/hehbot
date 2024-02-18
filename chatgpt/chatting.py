import openai
import httpx
import asyncio
import sqlite3

import re

from heh_bot import api, chat_repo

openai.api_key = api.get_chatgpt_api_key()

instructions = '''
Якщо ти швидше за все не зрозумів контекст питання (або вислови які потрібно підтвердити), 
то висловлюйся так ніби я щось упустив і не розповів тобі.

ти повинен відповідати лише у вигляді HTML розмітки, оскільки твоє повідомлення транслюється 
як розмітка HTML для aiogram фреймворку, а тому важливо ніколи не порушувати це правило.
ось теги які можна використовувати (їх потрібно буде закривати):

<b> для жирного тексту.
<i> для курсиву.
<u> для підкресленого тексту.
<s> для тексту, що перекреслений.
<tg-spoiler> для тексту спойлера.
<a href="URL"> для посилань.
<pre language="python"> для моноширинного блоку тексту, фрагментів коду (якщо я прошу написати код).

<exe com='command-name' arg='argument'></exe> для виконання команд (теги exe можуть містити в своєму тілі лише теги exe або бути порожніми). Результат команди узнаєш в наступному моєму запиті.
список команд:
'remember', де arg - дата в форматі '%Y-%m-%d %H:%M:%S';
'view_members', де arg - це айді користувача.
'get_id', де arg - ім'я користувача, яке вказано.
'''

# Припустимо, що це глобальна змінна для зберігання історії діалогу

async def generate_text(group_id: int):
    conn = sqlite3.connect(chat_repo.db_path)
    cursor = conn.cursor()

    # Вибірка історії діалогу за поточний день за group_id
    cursor.execute("""
        SELECT text, is_bot_message FROM chat_messages
        WHERE id = ? AND DATE(date) = DATE('now')
        ORDER BY date ASC
    """, (group_id,))
    history = cursor.fetchall()

    # Формування повного prompt з історії
    full_prompt = "\n".join([f"{'AI' if entry[1] else 'User'}: {entry[0]}" for entry in history])



    headers = {
        'Authorization': f'Bearer {openai.api_key}'
    }
    data = {
        "model": "gpt-3.5-turbo",  # Актуалізуйте ідентифікатор моделі за потребою
        "prompt": full_prompt,
        "max_tokens": 150,  # Приклад ліміту, адаптуйте під свої потреби
        "temperature": 0.926  # Контроль варіативності відповіді
    }

    async with httpx.AsyncClient(timeout=40.0) as client:
        response = await client.post('https://api.openai.com/v1/chat/completions', json=data, headers=headers)
        response_data = response.json()

        if 'choices' in response_data and response_data['choices']:
            # Отримання відповіді моделі
            ai_response = response_data['choices'][0]['text'].strip()
            
            return ai_response
        else:
            if 'error' in response_data:
                return f"Error: {response_data['error']['message']}"
            else:
                return "No response or unexpected format received from API."