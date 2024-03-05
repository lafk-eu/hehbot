import re
from datetime import datetime

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'hehbot'))

from client import repo_user
from client import Person

from hehbot.admin import repo_staff

class BotCommand:
    BOT_NAME = 'hehabot_bot'
    commands = {}

    def __init__(self):
        # Автоматична реєстрація команди при створенні об'єкту дочірнього класу
        # Використовуйте self.__class__ для доступу до поточного класу і викликайте класовий метод
        BotCommand.commands[self.__class__.command_name()] = self

    @classmethod
    def command_name(cls) -> str:
        raise NotImplementedError("This method should be implemented by subclasses.")

    def execute(self, person, args) -> str:
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def execute_finished(self, response: str) -> str:
        '''
            Запит "{self.command_name()}" успішно виконано з результатом: {response}.
            or
            Викликана неіснуюча команда.'''
        if hasattr(self, 'command_name'):
            return f'Запит "{self.command_name()}" успішно виконано з результатом: \n{response}.'
        return "Викликана неіснуюча команда."

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

    @staticmethod
    def count_commands(text) -> int:
        pattern = re.compile(r"/(\w+)(?:@(\w+))?\s*(.*)")
        return len(pattern.findall(text))

    @staticmethod
    def get_commands_description(include_nothing: bool = False):
        descriptions = []
        for cls in BotCommand.__subclasses__():
            if cls.command_name() == 'nothing' and not include_nothing:
                continue
            descriptions.append(f"/{cls.command_name()} - {cls.description}")
        return "\n".join(descriptions)
    
class SetCreditCommand(BotCommand):
    description = "Додай або віднімай кредити за проханням. приклад який віднімає (або додає): /credit username -300 (або 300)"

    @classmethod
    def command_name(cls) -> str:
        return "credit"

    def execute(self, person: Person, args) -> str:
        staff = repo_staff.get_by_id(person.id)

        if not staff or not staff.admin:
            return self.execute_stopped(f'через відсутність прав.')

        result = BotCommand.check_min_args(args, 2, self)

        if isinstance(result, str):
            return result

        p = repo_user.by_name(result[0])
        if p:
            try:
                score_increment = int(result[1])  # Спробуйте конвертувати рядок в ціле число
                repo_user.update_score(p.id, p.score + score_increment)
            except ValueError:
                # Якщо конвертація не вдалась, значить рядок не є коректним цілим числом
                return self.execute_stopped(f'через неправильний формат числа кредитів: "{result[1]}"')
        else:
            return self.execute_stopped(f'користувача {result[0]} не знайдено')

        return self.execute_finished(f'де аргументи: {result}. Відтепер {p.name} має {p.score + int(result[1])} кредитів')


class MyCreditCommand(BotCommand):
    description = "Показує кількість соціальних кредитів користувача. приклад: /mycredit username"

    @classmethod
    def command_name(cls) -> str:
        return "mycredit"

    def execute(self, person, args):
        if not args:
            return self.execute_finished(str(person.score))

        result = BotCommand.check_min_args(args, 1, self)

        if isinstance(result, str):
            return result
        
        user_set = repo_user.by_name(result[0])
        if user_set:
            return self.execute_finished(user_set.name + " має " + str(user_set.score) + " соціальних кредитів")
        else:
            return self.execute_stopped('через неправильне або неіснуюче ім\'я')

class BestCommand(BotCommand):
    description = "Виводить ТОП користувачів з найвищим рейтингом."

    @classmethod
    def command_name(cls) -> str:
        return "best"

    def execute(self, person, args):
        p_list = repo_user.with_highest_scores(10)
        best_str = '\n'.join(f'{i + 1}. {p.name}: {p.score}' for i, p in enumerate(p_list))
        return self.execute_finished(best_str)
    
class BaffleCommand(BotCommand):
    description = "Виводить ТОП користувачів з найгіршим рейтингом."

    @classmethod
    def command_name(cls) -> str:
        return "lowscore"

    def execute(self, person, args):
        p_list = repo_user.with_lowest_scores(10)
        baffle_str = '\n'.join(f'{i + 1}. {p.name}: {p.score}' for i, p in enumerate(p_list))
        return self.execute_finished(baffle_str)
    
class DateCommand(BotCommand):
    description = "Виводить поточну дату."

    @classmethod
    def command_name(cls) -> str:
        return "date"

    def execute(self, person, args):
        # Отримуємо поточну дату та час
        now = datetime.now()
        # Форматуємо дату та час у рядок за шаблоном 'YYYY-MM-DD HH:MM:SS'
        date_str = f'Зараз час: {now.strftime('%Y-%m-%d %H:%M:%S')}'
        return self.execute_finished(date_str)
    

# Ініціалізація команд
mycredit_command = MyCreditCommand()
highscore_command = BestCommand()
lowscore_command = BaffleCommand()
date_command = DateCommand()
credit_command = SetCreditCommand()