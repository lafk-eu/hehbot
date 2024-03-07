from hehbot.client import repo_user, Person
from hehbot.admin import repo_staff

from hehbot.base_command import BotCommand
from datetime import datetime

import re

def find_english_word(text: str) -> str:
    match = re.search(r'\b[a-zA-Z_]+\b', text)
    return match.group(0) if match else None

def find_first_number(text: str) -> int:
    match = re.search(r'[+-]?\d+', text)
    return int(match.group(0)) if match else None

class SetCreditCommand(BotCommand):
    description = "Додай або віднімай: /give username -300 (або 300)"

    @classmethod
    def command_name(cls) -> str:
        return "give"

    @classmethod
    def execute(self, person: Person, args, by_str: str = None) -> str:
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
    description = "Кількість соціальних кредитів користувача: /credit username"

    @classmethod
    def command_name(cls) -> str:
        return "credit"

    @classmethod
    def execute(cls, person, args, by_str: str = None):
        # Перевіряємо наявність аргументів спочатку
        if args:
            user = repo_user.by_name(args[0])
            if user:
                return cls.execute_finished(user.name + " має " + str(user.score) + " соціальних кредитів")
            elif not by_str:  # Якщо не знайдено за аргументом і by_str не надано
                return cls.execute_stopped('через неправильне або неіснуюче ім\'я')

        # Якщо аргументи відсутні або пошук за аргументами не вдався, і надано by_str
        if by_str:
            name = find_english_word(by_str)
            if name:
                user = repo_user.by_name(name)
                if user:
                    return cls.execute_finished(user.name + " має " + str(user.score) + " соціальних кредитів")
                else:
                    return cls.execute_stopped('через неправильне або неіснуюче ім\'я')

        # Якщо не надано аргументів і by_str пустий, повертаємо кредити поточного користувача
        if not args:
            return cls.execute_finished(str(person.score))

        # Загальна відмова, якщо жоден з вище наведених випадків не спрацював
        return cls.execute_stopped('Помилка у виконанні команди')


class BestCommand(BotCommand):
    description = "Кращі: ТОП користувачів з найвищим рейтингом."

    @classmethod
    def command_name(cls) -> str:
        return "best"

    @classmethod
    def execute(self, person, args, by_str: str = None):
        p_list = repo_user.with_highest_scores(10)
        best_str = '\n'.join(f'{i + 1}. {p.name}: {p.score}' for i, p in enumerate(p_list))
        return self.execute_finished(best_str)
    
class BaffleCommand(BotCommand):
    description = "Гірші: ТОП користувачів з найгіршим рейтингом."

    @classmethod
    def command_name(cls) -> str:
        return "lowscore"

    @classmethod
    def execute(self, person, args, by_str: str = None):
        p_list = repo_user.with_lowest_scores(10)
        baffle_str = '\n'.join(f'{i + 1}. {p.name}: {p.score}' for i, p in enumerate(p_list))
        return self.execute_finished(baffle_str)
    
class DateCommand(BotCommand):
    description = "Поточна дату."

    @classmethod
    def command_name(cls) -> str:
        return "date"

    @classmethod
    def execute(self, person, args, by_str: str = None):
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