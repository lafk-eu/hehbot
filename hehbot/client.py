import sqlite3, aiogram, asyncio
from abc import ABC, abstractmethod
from typing import List
from hehbot.admin import repo_staff
from enum import Enum

import random

class Person:
    def __init__(self, id: int, fullname: str = '', avatar: str = '', name: str = '', number: int = -1, score: int = 1000, cooldown: str = '') -> None:
        self.id = id
        self.fullname = fullname
        self.avatar = avatar
        self.name = name
        self.number = number
        self.score = score
        self.cooldown = cooldown

class CooldownType(Enum):
    SLOTS = 'slots'
    BET = 'bet'
    IDI = 'idi'

class Cooldown:
    def __init__(self, person: Person) -> None:
        self.cooldowns = person.cooldown.split() if person.cooldown else []

    async def get_cooldown(self, cooldown_type: CooldownType) -> str:
        if cooldown_type == CooldownType.SLOTS:
            return 'slots' if 'slots' in self.cooldowns else None
        elif cooldown_type == CooldownType.IDI:
            return 'idi' if 'idi' in self.cooldowns else None
        elif cooldown_type == CooldownType.BET:
            for i in range(1, 4):
                if f'bet{i}' in self.cooldowns:
                    return f'bet{i}'
            return None

    async def update_cooldown(self, cooldown_type: CooldownType, usage_count: int) -> None:
        # Створюємо значення кулдауну. Для SLOTS і, потенційно, IDI кількість використань не враховуємо.
        cooldown_value = f'{cooldown_type.value}'
        if cooldown_type == CooldownType.BET:
            # Для BET додаємо кількість використань, якщо вона більше 1
            cooldown_value += f'{"" if usage_count == 1 else usage_count}'
        
        # Видаляємо попередні кулдауни того ж типу
        self.cooldowns = [cd for cd in self.cooldowns if not cd.startswith(cooldown_type.value)]
        
        # Додаємо новий кулдаун
        self.cooldowns.append(cooldown_value)

    async def get_usage_count(self, cooldown_type: CooldownType) -> int:
        for cooldown in self.cooldowns:
            if cooldown.startswith(cooldown_type.value):
                if cooldown_type == CooldownType.SLOTS:
                    return 1
                # Для BET визначаємо кількість використань
                if cooldown_type == CooldownType.BET and len(cooldown) > 3:
                    return int(cooldown[3:])
                return 1
        return 0
    

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

    async def update_person(self, id: int, fullname: str = None, avatar: str = None, name: str = None, score: int = None, cooldown: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        fields_to_update = []
        values = []

        old = repo_user.by_tg(id)

        is_credit_image_update = False
        
        if fullname is not None and old.fullname != fullname:
            fields_to_update.append("fullname = ?")
            values.append(fullname)
            is_credit_image_update = True
        if avatar is not None and old.avatar != avatar:
            fields_to_update.append("avatar = ?")
            values.append(avatar)
            print(f'avatar: {avatar}, old.avatar: {old.avatar}')
            is_credit_image_update = True
        if name is not None and old.name != name:
            fields_to_update.append("name = ?")
            values.append(name)
            is_credit_image_update = True
        if score is not None and old.score != score:
            fields_to_update.append("score = ?")
            values.append(score)
            is_credit_image_update = True
            print(f'score: {score}, old.score: {old.score}')
        if cooldown is not None:
            fields_to_update.append("cooldown = ?")
            values.append(cooldown)
        
        values.append(id) # ID для умови WHERE
        
        if fields_to_update:
            update_stmt = f"UPDATE person SET {', '.join(fields_to_update)} WHERE id = ?"
            cursor.execute(update_stmt, values)
            conn.commit()
            
        conn.close()

        # оновлюємо фотку кредитів користувача
        if is_credit_image_update:
            print('user update image')
            from hehbot.decoration.credit_image import create_credit_image_async
            await create_credit_image_async(repo_user.by_tg(id))

    def add(self, person: Person) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO person (fullname, avatar, name, id, score, cooldown)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (person.fullname, person.avatar, person.name, person.id, person.score, person.cooldown))
        conn.commit()
        conn.close()

    async def by_tg_message(self, msg: aiogram.types.Message, update=True) -> Person | None:
        p = msg.from_user
        
        from hehbot.decoration.credit_image import get_avatar_id_async, create_credit_image_async

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
                score = 1000,
                cooldown = '')
            self.add(person)  # Викликаємо метод add для додавання нової персони
            await create_credit_image_async(person)
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

        staff = repo_staff.get_by_id(tg)
        if staff:
            repo_staff.delete(tg)

    def with_lowest_scores(self, limit: int) -> List[Person]:
        excluded_names = ('llafk', 'GroupAnonymousBot', 'Channel_Bot')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Виключення користувачів з певними іменами з результатів
        cursor.execute('''
            SELECT id FROM person 
            WHERE name NOT IN (?, ?, ?)
            ORDER BY score ASC 
            LIMIT ?
        ''', (*excluded_names, limit))
        rows = cursor.fetchall()
        conn.close()
        return [self.by_tg(row[0]) for row in rows]

    def with_highest_scores(self, limit: int) -> List[Person]:
        excluded_names = ('llafk', 'GroupAnonymousBot', 'Channel_Bot')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Виключення користувачів з певними іменами з результатів
        cursor.execute('''
            SELECT id FROM person 
            WHERE name NOT IN (?, ?, ?)
            ORDER BY score DESC 
            LIMIT ?
        ''', (*excluded_names, limit))
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

    async def update_cooldown(self, person_id: int, cooldown: Cooldown) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''UPDATE person SET cooldown = ? WHERE id = ?''', 
        (' '.join(cooldown.cooldowns), person_id))
        conn.commit()
        conn.close()
    
repo_user = PersonRepository('data/user.db')