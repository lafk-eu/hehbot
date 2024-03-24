import re
import sys
import json
import hehbot.gpt as gpt
import aiogram

from pathlib import Path
from hehbot.embedding import get_embedding_async

from typing import Optional
from scipy.spatial.distance import cosine

import aiogram

sys.path.append(str(Path(__file__).parent.parent / 'hehbot'))



class BotCommand:
    BOT_NAME = 'PlatoJudge_bot'
    commands = {}

    def __init__(self):
        # Автоматична реєстрація команди при створенні об'єкту дочірнього класу
        # Використовуйте self.__class__ для доступу до поточного класу і викликайте класовий метод
        BotCommand.commands[self.__class__.command_name()] = self


    # subclasses methods

    @classmethod
    def command_name(cls) -> str:
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None) -> str:
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    @classmethod
    def execute_finished(self, response: str) -> str:
        '''
            Запит "{self.command_name()}" успішно виконано з результатом: {response}.
            or
            Викликана неіснуюча команда.'''
        if hasattr(self, 'command_name'):
            return f'Запит "{self.command_name()}" успішно виконано з результатом: \n{response}.'
        return "Викликана неіснуюча команда."

    @classmethod
    def execute_stopped(self, response: str) -> str:
        '''
            Запит "{self.command_name()}" не виконано: {response}.
            or
            Викликана неіснуюча команда.'''
        if hasattr(self, 'command_name'):
            return f'Запит "{self.command_name()}" не виконано: {response}.'
        return "Викликана неіснуюча команда."

        
    @staticmethod
    async def get_args(args: str) -> list[str]:
        # Розділяємо вхідний рядок на частини за пробілами
        parts = args.split()

        # Фільтруємо список, відкидаючи елемент, який починається на "/"
        # Залишаємо усі інші елементи як аргументи
        arguments = [part for part in parts if not part.startswith("/")]

        return arguments


    @staticmethod
    def return_not_enough_args(cls, args_needed: int) -> str:
        # Перевіряємо, чи клас має атрибут command_name
        if hasattr(cls, "command_name"):
            # Використовуємо метод command_name класу для отримання назви команди
            command_name = cls.command_name()
            return f"Запит \"{command_name}\" не виконано через відсутність необхідних {args_needed} аргументів для виклику."
        else:
            return "Викликана неіснуюча команда."

    
    # process commands in text
            

    @staticmethod
    async def cmd_by_text(msg: aiogram.types.Message, text: str) -> str:
        parts = msg.text.split()
        
        # Видалення імені бота з команди, якщо воно є
        command_part = parts[0].split('@')[0]  # Видаляємо все, що йде після @
        
        # Видалення слеша з початку команди
        command_name = command_part.lstrip('/')
        
        command = BotCommand.commands.get(command_name.strip())

        if command:
            print('args: ', await BotCommand.get_args(text))
            print('text: ', text)
            args = await BotCommand.get_args(text)
            by_str = ' '.join(args)
            return await command.execute(msg, args, by_str)  # Припускаємо, що команда визначена як функція

        return None
    
    # commands

    @staticmethod
    def count_commands(text) -> int:
        pattern = re.compile(r"/(\w+)(?:@(\w+))?\s*(.*)")
        return len(pattern.findall(text))

    @staticmethod
    def get_commands_description():
        commands_dict = {}
        for cls in BotCommand.__subclasses__():
            command_name = cls.command_name()
            # Перевірка, чи вже існує запис у словнику, щоб уникнути дублів
            if command_name not in commands_dict:
                if hasattr(cls, 'description'):
                    commands_dict[command_name] = cls.description
        
        # Сортування команд за назвою для забезпечення визначеного порядку
        sorted_commands = sorted(commands_dict.items(), key=lambda item: item[0])
        
        # Формування списку описів команд
        descriptions = [f"/{command} - {description}" for command, description in sorted_commands]
        return descriptions
    
    @staticmethod
    def get_commands_info():
        commands_dict = {}
        for cls in BotCommand.__subclasses__():
            command_name = cls.command_name()
            # Перевірка, чи вже існує запис у словнику, щоб уникнути дублів
            if command_name not in commands_dict:
                if hasattr(cls, 'info'):
                    commands_dict[command_name] = cls.info
        
        # Сортування команд за назвою для забезпечення визначеного порядку
        sorted_commands = sorted(commands_dict.items(), key=lambda item: item[0])
        
        # Формування списку описів команд
        infos = [f"/{command} - {info}" for command, info in sorted_commands]
        return infos


    

    # embeddings


    @classmethod
    async def initialize_embeddings(cls) -> None:
        # Спробуйте завантажити кешовані embeddings
        cached_embeddings = cls.load_embeddings_from_file()

        # Визначаємо, чи потрібно оновити кеш
        needs_update = False

        for subclass in cls.__subclasses__():
            cmd_name = subclass.command_name()
            if not hasattr(subclass, 'description'):
                if not hasattr(subclass, 'ignore'):
                    print(f'WARNING: BotCommand subclass {cmd_name} hasn\'t description.')
                continue
            if cmd_name not in cached_embeddings:
                # Якщо команда відсутня в кеші, генеруємо її embedding і позначаємо, що кеш потребує оновлення
                embedding = await get_embedding_async(subclass.description)
                cached_embeddings[cmd_name] = embedding
                needs_update = True

        # Оновлюємо файл лише якщо були зміни
        if needs_update:
            cls.save_embeddings_to_file(cached_embeddings)

        # Встановлення embeddings для кожного дочірнього класу
        for subclass in cls.__subclasses__():
            cmd_name = subclass.command_name()
            if cmd_name in cached_embeddings:
                subclass.embedding = cached_embeddings[cmd_name]
    
    @staticmethod
    def save_embeddings_to_file(embeddings_dict) -> None:
        with open('data/embeddings.json', 'w') as file:
            json.dump(embeddings_dict, file)

    @staticmethod
    def load_embeddings_from_file() -> dict:
        try:
            with open('data/embeddings.json', 'r') as file:
                embeddings_dict = json.load(file)
                return embeddings_dict
        except FileNotFoundError:
            print("Файлу з embeddings не знайдено. Спочатку генерую embeddings.")
            return {}
    
    @classmethod 
    async def compare_async(cls, text: str) -> Optional[type]:
        max_similarity = -1  # Початкове значення для максимальної схожості
        most_similar = None  # Початкове значення для найбільш схожого класу
        processed_subclasses = set()  # Для відстеження вже оброблених класів

        def remove_court_and_username(text: str) -> str:
            # Спочатку видаляємо слово "суд"
            text_without_court = re.sub(r'\bсуд,\s*|\bсуд\b', '', text, flags=re.IGNORECASE)

            # Потім шукаємо та видаляємо нікнейм
            # Нікнейм визначаємо як слово, яке починається з "@" або "$"
            text_final = re.sub(r'\b[@$][a-zA-Z_][a-zA-Z0-9_]*\b', '', text_without_court)

            return text_final.strip()

        embedding1 = await get_embedding_async(remove_court_and_username(text))

        for subclass in cls.__subclasses__():
            if subclass.__name__ in processed_subclasses:
                continue  # Якщо клас вже був оброблений, пропускаємо його
            processed_subclasses.add(subclass.__name__)

            if hasattr(subclass, 'embedding'):
                embedding2 = subclass.embedding
                distance = cosine(embedding1, embedding2)
                similarity = 1 - distance

                # Якщо дочірний клас є MyCreditCommand, збільшуємо схожість на 0.3
                if subclass.__name__ == 'MyCreditCommand':
                    similarity += 0.033

                print(f"Команда: {subclass.command_name()}, Схожість: {similarity:.2f}")  # Виводимо назву команди та схожість
                if similarity > max_similarity and similarity >= 0.26:  # Перевіряємо поріг схожості
                    if not hasattr(subclass, 'min_similarity') or similarity >= subclass.min_similarity:
                        max_similarity = similarity
                        most_similar = subclass
        return most_similar

