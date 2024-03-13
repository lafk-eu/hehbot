import sqlite3, aiogram, asyncio
from abc import ABC, abstractmethod
from typing import List

import random

class Person:
    def __init__(self, id: int, fullname: str = '', avatar: str = '', name: str = '', number: int = -1, score: int = 0, cooldown: str = '') -> None:
        self.id = id
        self.fullname = fullname
        self.avatar = avatar
        self.name = name
        self.number = number
        self.score = score
        self.cooldown = cooldown

class IPersonRepository(ABC):
    @abstractmethod
    def add(self, person: Person) -> None:
        pass

    @abstractmethod
    def by_tg(self, tg_id: int) -> Person:
        pass

    @abstractmethod
    def by_number(self, number: int) -> Person:
        pass

    @abstractmethod
    async def update_person(self, id: int, fullname: str = None, avatar: str = None, name: str = None, score: int = None, cooldown: str = None) -> None:
        pass

    @abstractmethod
    def delete(self, tg_id: int) -> None:
        pass

    @abstractmethod
    def with_lowest_scores(self, limit: int) -> List[Person]:
        pass

    @abstractmethod
    def with_highest_scores(self, limit: int) -> List[Person]:
        pass

    @abstractmethod
    def reset_cooldowns(self) -> None:
        pass

class PersonRepository(IPersonRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table()

    def _create_table(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS person (
                number INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT,
                avatar TEXT,
                name TEXT,
                id INTEGER UNIQUE,
                score INTEGER NOT NULL DEFAULT 0,
                cooldown TEXT DEFAULT ''
            )
        ''')
        conn.commit()
        conn.close()

        self.add_or_get_bot()

    async def update_person(self, id: int, fullname: str = None, avatar: str = None, name: str = None, score: int = None, cooldown: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        fields_to_update = []
        values = []

        old = repo_user.by_tg(id)
        
        if fullname is not None:
            fields_to_update.append("fullname = ?")
            values.append(fullname)
        if avatar is not None:
            fields_to_update.append("avatar = ?")
            values.append(avatar)
        if name is not None:
            fields_to_update.append("name = ?")
            values.append(name)
        if score is not None:
            fields_to_update.append("score = ?")
            values.append(score)
        if cooldown is not None:
            fields_to_update.append("cooldown = ?")
            values.append(cooldown)
        
        values.append(id) # ID для умови WHERE
        
        update_stmt = f"UPDATE person SET {', '.join(fields_to_update)} WHERE id = ?"
        cursor.execute(update_stmt, values)
        
        conn.commit()
        conn.close()

        # оновлюємо фотку кредитів користувача
        if fullname != old.fullname or name != old.name or avatar != old.avatar or score != old.score:
            from hehbot.decoration import create_credit_image_async
            await create_credit_image_async(repo_user.by_tg(id))

    def add_or_get_bot(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Спробуємо знайти персону з id = -2
        cursor.execute('SELECT * FROM person WHERE id = -2')
        bot = cursor.fetchone()

        if bot is None:
            # Якщо персона не знайдена, створюємо нову
            cursor.execute('''
                INSERT INTO person (number, fullname, avatar, name, id, score, cooldown)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (-2, 'Assistent', None, 'Bot', -2, 0, ''))
            conn.commit()

            # Повертаємо новостворену персону
            cursor.execute('SELECT * FROM person WHERE id = -2')
            bot = cursor.fetchone()

        conn.close()
        return bot

    def add(self, person: Person) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO person (fullname, avatar, name, id, score, cooldown)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (person.fullname, person.avatar, person.name, person.id, person.score, person.cooldown))
        conn.commit()
        person.number = cursor.lastrowid
        conn.close()

    async def by_tg_message(self, msg: aiogram.types.Message, update=True) -> Person | None:
        p = msg.from_user
        if not p.username or not p.full_name:
            return None
        
        from hehbot.decoration import get_avatar_id_async, create_credit_image_async

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, fullname, avatar, name, id, score, cooldown FROM person WHERE id = ?', (msg.from_user.id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            person = Person(id=row[4], fullname=row[1], name=row[3], number=row[0], score=row[5], cooldown=row[6])
            if update:
                await repo_user.update_person(
                    id = p.id, 
                    fullname = p.full_name, 
                    avatar = await get_avatar_id_async(p.id), 
                    name = p.username,
                    score = person.score,
                    cooldown = person.cooldown)
        else:
            # Якщо персона не знайдена, створюємо нову з заданим tg_id і дефолтними значеннями
            person = Person(
                id = p.id, 
                fullname = p.full_name, 
                avatar = await get_avatar_id_async(p.id), 
                name = p.username,
                score = 0,
                cooldown = '')
            await create_credit_image_async(person)
            self.add(person)  # Викликаємо метод add для додавання нової персони
        return person

    def by_tg(self, tg_id: int) -> Person:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, fullname, avatar, name, id, score, cooldown FROM person WHERE id = ?', (tg_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            person = Person(id=row[4], fullname=row[1], name=row[3], number=row[0], score=row[5], cooldown=row[6])
            return person
        return None
        
    def by_number(self, number: int) -> Person:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, fullname, avatar, name, id, score, cooldown FROM person WHERE number = ?', (number,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Person(id=row[4], fullname=row[1], name=row[3], number=row[0], score=row[5], cooldown=row[6])
        return None
    
    def by_name(self, name: str) -> Person | None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, fullname, avatar, name, id, score, cooldown FROM person WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Person(id=row[4], fullname=row[1], name=row[3], number=row[0], score=row[5], cooldown=row[6])
        return None

    def delete(self, tg: int) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM person WHERE id = ?', (tg,))
        conn.commit()
        conn.close()

    def with_lowest_scores(self, limit: int) -> List[Person]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM person ORDER BY score ASC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [self.by_tg(row[0]) for row in rows]

    def with_highest_scores(self, limit: int) -> List[Person]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM person ORDER BY score DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [self.by_tg(row[0]) for row in rows]

    def reset_cooldowns(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE person
            SET cooldown = ''
        ''')
        conn.commit()
        conn.close()
    
repo_user = PersonRepository('data/user.db')