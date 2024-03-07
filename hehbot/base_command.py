import re
import sys
import json
import hehbot.gpt as gpt

from pathlib import Path
from hehbot.embedding import get_embedding_async

from typing import Optional
from scipy.spatial.distance import cosine

sys.path.append(str(Path(__file__).parent.parent / 'hehbot'))



class BotCommand:
    BOT_NAME = 'hehabot_bot'
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
    def execute(self, person, args, by_str: str = None) -> str:
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
    def check_min_args(args: str, min_args: int, cls) -> str | list[str]:
        args_list = args.strip().split()

        if len(args_list) < min_args:
            # Викликаємо метод для повернення повідомлення про помилку
            return BotCommand.return_not_enough_args(cls, min_args)
        else:
            return args_list

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
    def process_text(person, text) -> str:
        # Шукаємо всі згадки команд у тексті
        pattern = re.compile(r"/(\w+)(?:@(\w+))?\s*(.*)")

        matches = pattern.finditer(text)

        for match in matches:
            command_name, bot_name, args = match.groups()
            if bot_name and bot_name != BotCommand.BOT_NAME:  # перевіряємо, чи вказане ім'я бота відповідає поточному
                continue

            command = BotCommand.commands.get(command_name)

            if command:
                # Виконуємо команду і замінюємо шаблон на результат
                result = command.execute(person, args.strip())  # Припускаємо, що команда визначена як функція
                text = text.replace(match.group(), result, 1)
                break
            else:
                # Якщо команда не знайдена, вилучаємо шаблон з тексту
                text = text.replace(match.group(), "", 1)

        return text
    
    # commands

    @staticmethod
    def count_commands(text) -> int:
        pattern = re.compile(r"/(\w+)(?:@(\w+))?\s*(.*)")
        return len(pattern.findall(text))

    @staticmethod
    def get_commands_description():
        descriptions = []
        for cls in BotCommand.__subclasses__():
            descriptions.append(f"/{cls.command_name()} - {cls.description}")
        return descriptions
    

    # embeddings


    @classmethod
    async def initialize_embeddings(cls) -> None:
        # Спробуйте завантажити кешовані embeddings
        cached_embeddings = cls.load_embeddings_from_file()

        # Визначаємо, чи потрібно оновити кеш
        needs_update = False

        for subclass in cls.__subclasses__():
            cmd_name = subclass.command_name()
            if not subclass.description:
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
        with open('data/emb_com.json', 'w') as file:
            json.dump(embeddings_dict, file)

    @staticmethod
    def load_embeddings_from_file() -> dict:
        try:
            with open('data/emb_com.json', 'r') as file:
                embeddings_dict = json.load(file)
                return embeddings_dict
        except FileNotFoundError:
            print("Файл не знайдено. Спочатку згенеруйте embeddings.")
            return {}
    
    @classmethod 
    async def compare_async(cls, text: str) -> Optional[type]:
        max_similarity = -1  # Початкове значення для максимальної схожості
        most_similar = None  # Початкове значення для найбільш схожого класу
        processed_subclasses = set()  # Для відстеження вже оброблених класів

        embedding1 = await get_embedding_async(text)

        for subclass in cls.__subclasses__():
            if subclass.__name__ in processed_subclasses:
                continue  # Якщо клас вже був оброблений, пропускаємо його
            processed_subclasses.add(subclass.__name__)

            if hasattr(subclass, 'embedding'):
                embedding2 = subclass.embedding
                distance = cosine(embedding1, embedding2)
                similarity = 1 - distance
                print(f"Команда: {subclass.command_name()}, Схожість: {similarity:.2f}")  # Виводимо назву команди та схожість
                if similarity > max_similarity and similarity >= 0.2:  # Перевіряємо поріг схожості
                    max_similarity = similarity
                    most_similar = subclass

        return most_similar

