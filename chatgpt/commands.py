from heh_bot import dp, bot, user_repo
from aiogram import types
from abc import ABC, abstractmethod

import re

class ChatCommand(ABC):
    def __init__(self, name: str, argument: str, about: str) -> None:
        self.name = name
        self.argument = argument
        self.about = about
    
    @abstractmethod
    def execute(self) -> str:
        return ''

class RememberCommand(ChatCommand):
    def __init__(self, argument: str) -> None:
        super().__init__('remember', argument, "дата в форматі '%Y-%m-%d %H:%M:%S'")
    
    def execute(self) -> str:
        return 'Не знайдено діалогів за цей час'

class ViewMembersCommand(ChatCommand):
    def __init__(self, argument: str) -> None:
        super().__init__('view_members', argument, "необов'язковий аргумент: айді користувача")
    
    def execute(self) -> str:
        return user_repo.get_all_person_names()

class GetUserIdCommand(ChatCommand):
    def __init__(self, argument: str) -> None:
        super().__init__('user_id', argument, "відоме ім'я користувача")
    
    def execute(self) -> str:
        person = user_repo.get_person_by_name(self.argument)
        if person:
            return person.id
        else:
            return 'Не знайдено людини за вказаним ім\'ям.'

class ChatCommandManager:
    def __init__(self) -> None:
        self.commands = {
            'remember': RememberCommand,
            'view_members': ViewMembersCommand,
            'get_id': GetUserIdCommand
        }
        self.last_result = None

    def execute(self, command_name, argument):
        if command_name in self.commands:
            command = self.commands[command_name](argument)
            self.last_result = command.execute()
            return self.last_result
        else:
            print("Невідома команда.")
            return "Невідома команда."

    def exe_html(self, html: str):
        # Регулярний вираз для пошуку команди та аргументів
        pattern = re.compile(r"<exe com=['\"](.*?)['\"] arg=['\"](.*?)['\"]>(.*?)</exe>")
        match = pattern.search(html)
        if match:
            command_name, argument, text = match.groups()
            # Виконання зовнішньої команди з аргументом
            return self.execute(command_name, argument)
        else:
            return "Команда не знайдена."
        
    # Допустимо, ми маємо HTML рядок:
    # html_str = '<exe com="user_id"</exe>"></exe>'

    # Створення і використання
    # command = ChatCommandManager()
    # answer = command.exe_html(html_str)
    # await message.answer(str(answer))