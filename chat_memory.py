import sqlite3, aiogram
from datetime import datetime
from functools import singledispatchmethod

from hehbot.client import Person, repo_user

async def get_history(group_id: int, limit: int = 10):
    msgs = repo_msg.get_all_messages_by_group(group_id, limit)
    
    history = []
    for i, message in enumerate(msgs):
        person = repo_user.by_number(message.user_number)
        if person.number == -2:
            person.name = 'Gemini'

        if person.name and message.text:
            # Якщо це останнє повідомлення, додаємо спеціальний префікс
            if i == len(msgs) - 1:
                history.append(f" {person.name}: {message.text}")
            else:
                history.extend([person.name, message.text])

    return history

class DiscordMessage:
    def __init__(self) -> None:
        self.text = ''
        self.date = datetime.now()
        self.id = -1

class ChatMessage:
    @singledispatchmethod
    def __init__(self, msg):
        # Ця версія __init__ буде викликана, якщо не знайдено підходящого перевантаження
        raise NotImplementedError("Cannot create ChatMessage with type", type(msg))

    @__init__.register(aiogram.types.Message)
    def _from_telegram(self, msg: aiogram.types.Message):
        # Ініціалізація зі Telegram
        self.text = msg.text
        self.date = msg.date
        self.tg_group = msg.chat.id
        self.tg = msg.from_user.id
        
        n = repo_user.by_tg_message(msg).number
        self.user_number = n if n else -1

    @__init__.register(DiscordMessage)
    def _from_discord(self, msg: DiscordMessage):
        # Ініціалізація з Discord
        pass
    
    @__init__.register(dict)
    def _from_dict(self, msg: dict):
        # Ініціалізація з словнику
        self.text = msg.get('text')
        self.date = datetime.now()
        self.tg = msg.get('tg')
        self.user_number = msg.get('number')
        self.tg_group = msg.get('tg_group')


    
class ChatMessageRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    user_number INTEGER NOT NULL,
                    user_id INTEGER DEFAULT -1,
                    message_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_text TEXT,
                    group_id INTEGER DEFAULT -1
                )
            ''')
            conn.commit()

    def add_message(self, msg: ChatMessage):
        with sqlite3.connect(self.db_path) as conn:
            n = msg.user_number
            tg = msg.tg if hasattr(msg, 'tg') else -1
            tg_group = msg.tg_group if hasattr(msg, 'tg_group') else -1

            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_messages (user_number, user_id, message_date, message_text, group_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (n, tg, msg.date, msg.text, tg_group))
            conn.commit()

    def get_last_messages_by_user(self, user_number: int, group_id: int, limit: int = 10) -> list[ChatMessage]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_number, group_id, message_text, message_date FROM chat_messages
                WHERE user_number = ? AND group_id = ?
                ORDER BY message_date DESC
                LIMIT ?
            ''', (user_number, group_id, limit))
            messages = []
            for row in cursor.fetchall():
                # Припустимо, що message_date в базі даних зберігається у форматі, сумісному з datetime.now()
                msg_dict = {
                    'text': row[3],
                    'tg_group': row[2],
                    'number': row[1],
                    'tg': None  # Тут можна встановити відповідне значення, якщо воно доступне
                }
                messages.append(ChatMessage(msg_dict))
            return messages

    def get_all_messages_by_group(self, group_id: int, limit: int = 10) -> list[ChatMessage]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_number, group_id, message_text, message_date FROM chat_messages
                WHERE group_id = ?
                ORDER BY message_date DESC
                LIMIT ?
            ''', (group_id, limit))
            messages = []
            for row in cursor.fetchall():
                msg_dict = {
                    'text': row[2],
                    'tg_group': row[1],
                    'number': row[0],
                    'tg': None
                }
                messages.append(ChatMessage(msg_dict))
            return messages
        

repo_msg = ChatMessageRepository('data/msg.db')