import sqlite3, re
from aiogram import types
from datetime import datetime

class ChatMessage:
    def __init__(self, text: str, date: types.DateTime, user_id: str) -> None:
        self.text = text
        self.date = date
        self.user_id = user_id

async def estimate_tokens(text):
    # Розділяємо текст на слова та знаки пунктуації
    tokens = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
    return len(tokens) + 5

class Dialog:
    MAX_MESSAGES = 5  # Максимальна кількість повідомлень від користувачів
    
    def __init__(self, group_id: str, chatbot_msg: ChatMessage, users_msgs: list[ChatMessage]) -> None:
        self.group_id = group_id
        self.chatbot_msg = chatbot_msg
        self.users_msgs = users_msgs
        self.first_date = users_msgs[0].date
        self.second_date = chatbot_msg.date

    def str_date(self, date) -> str:
        return date.strftime('%Y-%m-%d %H:%M:%S')

    def get_conversation(self) -> str:
        # Форматування діалогу
        conversation = []
        for message in self.users_messages[:self.MAX_MESSAGES]:
            text = message.text
            if len(text) > 200:
                # Знаходження першого речення, яке менше або дорівнює 200 символам
                sentences = re.split(r'(?<=[.!?]) +', text)
                sentence = next((s for s in sentences if len(s) <= 200), text[:200])
                text = sentence
            conversation.append(text)
        
        # Додавання повідомлення від бота
        conversation.append(self.chatbot_message.text)
        
        return '\n'.join(conversation)

    def length(self) -> int:
        return len(self.users_messages)
    
class DialogRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY,
                group_id TEXT NOT NULL,
                text TEXT NOT NULL,
                date TEXT NOT NULL,
                user_id TEXT NOT NULL,
                is_bot_message INTEGER NOT NULL
            )
        """)
        conn.commit()

    def add_dialog(self, dialog: Dialog) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for message in dialog.users_messages + [dialog.chatbot_message]:
                cursor.execute("""
                    INSERT INTO chat_messages (group_id, text, date, user_id, is_bot_message)
                    VALUES (?, ?, ?, ?, ?)
                """, (dialog.group_id, message.text, message.str_date(message.date), message.user_id, isinstance(message, type(dialog.chatbot_message))))
            conn.commit()

    def get_dialogues_by_group_id(self, group_id: str) -> list[Dialog]:
        dialogs = []
        with sqlite3.connect(self.db_path) as conn: # {
            cursor = conn.cursor()
            cursor.execute("""
                SELECT text, date, user_id, is_bot_message FROM chat_messages
                WHERE group_id = ?
                ORDER BY date
            """, (group_id,))
            rows = cursor.fetchall()

            # Відновлення повідомлень як об'єктів ChatMessage
            messages = [ChatMessage(text=row[0], date=datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S'), user_id=row[2]) for row in rows if not row[3]]

            # Відновлення повідомлень від бота як об'єктів ChatMessage
            bot_messages = [ChatMessage(text=row[0], date=datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S'), user_id=row[2]) for row in rows if row[3]]

            # Групування повідомлень користувачів у діалоги з урахуванням MAX_MESSAGES
            for bot_message in bot_messages:
                # Знаходження повідомлень користувачів, які передують кожному повідомленню від бота
                user_msgs = messages[:Dialog.MAX_MESSAGES]
                messages = messages[Dialog.MAX_MESSAGES:]

                dialog = Dialog(group_id=group_id, chatbot_message=bot_message, users_messages=user_msgs)
                dialogs.append(dialog)

                # Якщо усі повідомлення користувачів були використані, завершуємо цикл
                if not messages:
                    break
        # } with sqlite3.connect(self.db_path) as conn:
        return dialogs