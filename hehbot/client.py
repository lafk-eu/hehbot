import sqlite3, aiogram
from abc import ABC, abstractmethod
from typing import List

import random

class Person:
    def __init__(self, id: int, name: str = '', number: int = -1, score: int = 0, cooldown: str = '') -> None:
        self.id = id
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
    def update_score(self, person: Person) -> None:
        pass

    @abstractmethod
    def update_name(self, person: Person) -> None:
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
                name TEXT,
                id INTEGER UNIQUE,
                score INTEGER NOT NULL DEFAULT 0,
                cooldown TEXT DEFAULT ''
            )
        ''')
        conn.commit()
        conn.close()

        self.add_or_get_bot()

    def add_or_get_bot(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Спробуємо знайти персону з id = -2
        cursor.execute('SELECT * FROM person WHERE id = -2')
        bot = cursor.fetchone()

        if bot is None:
            # Якщо персона не знайдена, створюємо нову
            cursor.execute('''
                INSERT INTO person (number, name, id, score, cooldown)
                VALUES (?, ?, ?, ?, ?)
            ''', (-2, 'Gemini', -2, 0, ''))
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
            INSERT INTO person (name, id, score, cooldown)
            VALUES (?, ?, ?, ?)
        ''', (person.name, person.id, person.score, person.cooldown))
        conn.commit()
        person.number = cursor.lastrowid
        conn.close()

    def by_tg_message(self, msg: aiogram.types.Message) -> Person | None:
        if not msg.from_user.username:
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, name, id, score, cooldown FROM person WHERE id = ?', (msg.from_user.id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            person = Person(id=row[2], name=row[1], number=row[0], score=row[3], cooldown=row[4])

            if person.name != msg.from_user.username:
                person.name = msg.from_user.username
                repo_user.update_name(person)
        else:
            # Якщо персона не знайдена, створюємо нову з заданим tg_id і дефолтними значеннями
            person = Person(msg.from_user.id, name=msg.from_user.username)
            self.add(person)  # Викликаємо метод add для додавання нової персони
        return person

    def by_tg(self, tg_id: int) -> Person:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, name, id, score, cooldown FROM person WHERE id = ?', (tg_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            person = Person(id=row[2], name=row[1], number=row[0], score=row[3], cooldown=row[4])
            return person
        return None
        
    def by_number(self, number: int) -> Person:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, name, id, score, cooldown FROM person WHERE number = ?', (number,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Person(id=row[2], name=row[1], number=row[0], score=row[3], cooldown=row[4])
        return None
    
    def by_name(self, name: str) -> Person:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT number, name, id, score, cooldown FROM person WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Person(id=row[2], name=row[1], number=row[0], score=row[3], cooldown=row[4])
        return None


    def update_score(self, tg_id: int, new_score: int) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE person
            SET score = ?
            WHERE id = ?
        ''', (new_score, tg_id))
        conn.commit()
        conn.close()

    def update_name(self, tg_id: int, new_name: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE person
            SET name = ?
            WHERE id = ?
        ''', (new_name, tg_id))
        conn.commit()
        conn.close()

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