from hehbot.client import repo_user
from hehbot.admin import repo_staff

from hehbot.base_command import BotCommand
from datetime import datetime

from hehbot.decoration import create_credit_image_async, get_credit_image_async
from mbot import bot

import aiogram

import re

def find_username(text: str) -> str:
    match = re.search(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)
    return match.group(0) if match else None

def find_number(text: str) -> int:
    match = re.search(r'[+-]?\d+', text)
    return int(match.group(0)) if match else None

def remove_english_words(text: str) -> str:
    # Визначаємо регулярний вираз для пошуку англійських слів.
    # Слово може починатися і закінчуватися англійською літерою або символом "_",
    # і містити в середині англійські літери та "_".
    pattern = r'\b[a-zA-Z_]+\b'
    
    # Використовуємо re.sub() для заміни всіх знайдених англійських слів на пустий рядок.
    result = re.sub(pattern, '', text)
    
    # Повертаємо результат після видалення англійських слів.
    return result

class SetCreditCommand(BotCommand):
    description = "Видай/Дай/Відбери/Сошіал кредит/Соціальний кредит"

    @classmethod
    def command_name(cls) -> str:
        return "give"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None) -> str:
        staff = repo_staff.get_by_id(msg.from_user.id)

        if not staff or not staff.admin:
            return cls.execute_stopped(f'через відсутність прав')

        if args:
            username = args[0]
            amount_str = args[1]
        elif by_str:
            username = find_username(by_str)
            amount_str = find_number(by_str)
        else:
            return cls.execute_stopped('не вказано ім\'я користувача або суму')

        p = repo_user.by_name(username)
        if not p:
            return cls.execute_stopped(f'користувача {username} не знайдено')

        try:
            amount = int(amount_str)
        except:
            return cls.execute_stopped(f'через неправильний формат числа кредитів')

        await repo_user.update_person(p.id, score=p.score + amount)


        photo = await get_credit_image_async(repo_user.by_tg(p.id))

        await bot.send_photo(msg.chat.id, aiogram.types.FSInputFile(photo))
        return None


class MyCreditCommand(BotCommand):
    description = "Покажи/Скільки/Кредити"

    @classmethod
    def command_name(cls) -> str:
        return "credit"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None):
        # Перевіряємо наявність аргументів спочатку
        if args:
            user = repo_user.by_name(args[0])
            if user:
                
                return None
            elif not by_str:  # Якщо не знайдено за аргументом і by_str не надано
                return cls.execute_stopped('через неправильне або неіснуюче ім\'я')

        # Якщо аргументи відсутні або пошук за аргументами не вдався, і надано by_str
        if by_str:
            words = by_str.split(" ", 1)  # Розділяємо рядок на дві частини: перше слово та решту рядка
            if len(words) > 1:
                by_str = " ".join(words[1:])  # Видаляємо перше слово

            name = find_username(by_str)
            if name:
                user = repo_user.by_name(name)
                if user:
                    photo = await get_credit_image_async(user)

                    await bot.send_photo(msg.chat.id, aiogram.types.FSInputFile(photo))
                    return None
                else:
                    return cls.execute_stopped('через неправильне або неіснуюче ім\'я')

        # Якщо не надано аргументів і by_str пустий, повертаємо кредити поточного користувача
        if not args:
            user = repo_user.by_tg(msg.from_user.id)
            photo = await get_credit_image_async(user)
            await bot.send_photo(msg.chat.id, aiogram.types.FSInputFile(photo))
            return None

        # Загальна відмова, якщо жоден з вище наведених випадків не спрацював
        return cls.execute_stopped('Помилка у виконанні команди')


class HighscoreCommand(BotCommand):
    description = "Кращі: ТОП користувачів з найвищим рейтингом."

    @classmethod
    def command_name(cls) -> str:
        return "best"

    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None):
        p_list = repo_user.with_highest_scores(10)
        best_str = '\n'.join(f'{i + 1}. {p.name}: {p.score}' for i, p in enumerate(p_list))
        return self.execute_finished(best_str)
    
class LowscoreCommand(BotCommand):
    description = "Гірші: ТОП користувачів з найгіршим рейтингом."

    @classmethod
    def command_name(cls) -> str:
        return "lowscore"

    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None):
        p_list = repo_user.with_lowest_scores(10)
        baffle_str = '\n'.join(f'{i + 1}. {p.name}: {p.score}' for i, p in enumerate(p_list))
        return self.execute_finished(baffle_str)
    
class DateCommand(BotCommand):
    description = "Поточна дата."

    @classmethod
    def command_name(cls) -> str:
        return "date"

    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None):
        # Отримуємо поточну дату та час
        now = datetime.now()
        # Форматуємо дату та час у рядок за шаблоном 'YYYY-MM-DD HH:MM:SS'
        date_str = f'Зараз час: {now.strftime('%Y-%m-%d %H:%M:%S')}'
        return self.execute_finished(date_str)
    
class HelpCommand(BotCommand):
    description = 'Допомога: про мене інфо та шо я можу.'

    @classmethod
    def command_name(cls) -> str:
        return 'help'
    
    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None):
        cmds = '\n'.join(self.get_commands_description())
        print(cmds)
        return f'''Я можу виконувати команди, якщо звернешся через слово "суд" або відповіси на моє повідомлення. 

Я вмію в:
{cmds}

Також я вмію розпізнавати текст на наявність команд.'''
    

# Ініціалізація команд
help_command = HelpCommand()
check_credit_command = MyCreditCommand()
highscore_command = HighscoreCommand()
lowscore_command = LowscoreCommand()
date_command = DateCommand()
change_credit_command = SetCreditCommand()

BotCommand.get_commands_description()