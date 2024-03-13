from hehbot.client import repo_user
from hehbot.admin import repo_staff, StaffPerson

from hehbot.base_command import BotCommand
from datetime import datetime

from hehbot.decoration import create_credit_image_async, get_credit_image_async, send_credit_image
from mbot import bot

import aiogram

import re

def find_username(text: str) -> str:
    # Спочатку шукаємо ім'я, яке починається з "@" або "$"
    special_match = re.search(r'\b[@$][a-zA-Z_][a-zA-Z0-9_]*\b', text)
    if special_match:
        return special_match.group(0)

    # Якщо таке ім'я не знайдено, шукаємо ім'я за існуючим патерном
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
    description = "+300 соціальних кредитів"

    @classmethod
    def command_name(cls) -> str:
        return "give"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None) -> str:
        
        staff = repo_staff.get_by_id(msg.from_user.id)
        if not staff:
            return cls.execute_stopped(f'через відсутність прав')
        
        if by_str:
            username = find_username(by_str)
            amount_str = find_number(by_str)
        else:
            return cls.execute_stopped('не вказано ім\'я користувача або суму')

        p = repo_user.by_name(username)
        if not p:
            return cls.execute_stopped(f'користувача {username} не знайдено в базі даних')

        try:
            amount = int(amount_str)
        except:
            return cls.execute_stopped(f'через неправильний формат числа кредитів')
        
        if staff.credits <= 0:
            return f'Насьогодні твоя особиста роздача кредитів вичерпана :('
        if staff.credits < amount:
            return f'Сьогодні тобі можна задати кредитів на: {staff.credits}. Зменш кількість видачі.'
        
        if not staff.admin:
            staff.credits -= abs(amount)
            repo_staff.update(staff)

        await repo_user.update_person(p.id, score=p.score + amount)

        return await send_credit_image(repo_user.by_tg(p.id), msg.chat.id)


class MyCreditCommand(BotCommand):
    description = "Покажи/Скільки баланс кредитів"

    @classmethod
    def command_name(cls) -> str:
        return "credit"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None):
        # Перевіряємо наявність аргументів спочатку
        if args:
            user = repo_user.by_name(find_username(args[0]))
            if user:
                return await send_credit_image(user, msg.chat.id)
            elif not by_str:  # Якщо не знайдено за аргументом і by_str не надано
                return cls.execute_stopped(f'користувача {args[0]} не знайдено в базі даних')

        # Якщо аргументи відсутні або пошук за аргументами не вдався, і надано by_str
        if by_str:
            words = by_str.split(" ", 1)  # Розділяємо рядок на дві частини: перше слово та решту рядка
            if len(words) > 1:
                by_str = " ".join(words[1:])  # Видаляємо перше слово

            name = find_username(by_str)
            if name:
                user = repo_user.by_name(name)
                if user:
                    return await send_credit_image(user, msg.chat.id)
                else:
                    return cls.execute_stopped('через неправильне або неіснуюче ім\'я')

        # Якщо не надано аргументів і by_str пустий, повертаємо кредити поточного користувача
        if not args:
            return await send_credit_image(repo_user.by_tg(msg.from_user.id), msg.chat.id)

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
    #description = "Поточна дата."

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
    description = 'Допомога або команди'

    @classmethod
    def command_name(cls) -> str:
        return 'help'
    
    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None):
        commands = self.get_commands_description()

        if not repo_staff.get_by_id(msg.from_user.id):
            commands = [command for command in commands if not command.startswith("/give")]

        cmd_list_str = '\n'.join(commands)
        return f'''Я можу виконувати команди, якщо звернешся через слово "суд" або відповіси на моє повідомлення. 

Я вмію в:
{cmd_list_str}

Також я вмію розпізнавати текст на наявність команд.'''
    
class AddAdminCommand(BotCommand):
    @classmethod
    def command_name(cls) -> str:
        return "new_admin"

    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None):
        async def get_error() -> str:
            return '''через неправильні аргументи. Очікувалось: 
/new_admin @username число_прав(0 - для модера, 1 - для адміна) максимальна_щоденна_видача_кредитів(якщо модер)
(особа також повинна бути в БД бота)'''

        staff = repo_staff.get_by_id(msg.from_user.id)
        if staff and staff.admin:
            print(args)
            if args and len(args) >= 3:
                username = find_username(args[0])
                if not username:
                    return self.execute_stopped('через невірне або неіснуюче ім\'я')
                
                try:
                    perm = int(args[1])
                    if perm < 0 or perm > 1:
                        raise ValueError
                except:
                    return self.execute_stopped('через невірний формат числа прав (0 або 1)')
                
                try:
                    change = int(args[2])
                    if change < 1 or change > 100000:
                        raise ValueError
                except:
                    return self.execute_stopped('через невірний формат числа щоденної видачі кредитів (від 1 до 100000)')
                
                new_person = repo_user.by_name(username)

                if not new_person:
                    return self.execute_stopped(f'користувач {username} відсутній в БД. Нехай щось напише мені')

                new_staff = StaffPerson(id=new_person.id, admin=perm, credits=change, max_credit=change)
                repo_staff.add(new_staff)

                if perm:
                    return f'Адміністратор @{new_person.name} ({new_person.fullname}) успішно доданий.'
                else:
                    return f'Модератор @{new_person.name} ({new_person.fullname}) успішно доданий.'
            else:
                return self.execute_stopped(await get_error())
        else:
            return None
        
class DeleteAdminCommand(BotCommand):
    @classmethod
    def command_name(cls) -> str:
        return "delete_admin"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None):
        async def get_error() -> str:
            return '''через неправильні аргументи. Очікувалось: 
/delete_admin @username (або айді особи)'''

        if not args or len(args) != 1:
            return cls.execute_stopped(await get_error())

        identifier = args[0]
        if identifier.startswith('@'):
            user = repo_user.by_name(identifier[1:])  # Видалення символу '@' з імені користувача
            if not user:
                return cls.execute_stopped('користувач не знайдений в БД.')
            id_to_delete = user.id
        else:
            try:
                id_to_delete = int(identifier)
            except ValueError:
                return cls.execute_stopped('ID має бути числом.')

        staff_member = repo_staff.get_by_id(id_to_delete)
        if staff_member:
            repo_staff.delete(id_to_delete)
            return f'Адміністратор з ID {id_to_delete} успішно видалений.'
        else:
            return cls.execute_stopped('Адміністратор не знайдений.')
        
class GetAdminListCommand(BotCommand):
    @classmethod
    def command_name(cls) -> str:
        return "admin_list"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None):
        staff_sender = repo_staff.get_by_id(msg.from_user.id)
        if staff_sender:
            member_list = []

            def staff_info(member: StaffPerson) -> str:
                if not member.admin:
                    return f'модер ({member.credits} кредитів на сьогодні з {member.max_credits})'
                else:
                    return 'адмін'

            members = repo_staff.get_all()
            for member in members:
                person = repo_user.by_tg(member.id)

                member_list.append(f'{person.fullname} (@{person.name}) - {staff_info(member)}')
            
            return '\n'.join(member_list)
        return None

# Ініціалізація команд
    
# client commands
help_command = HelpCommand()
check_credit_command = MyCreditCommand()
highscore_command = HighscoreCommand()
lowscore_command = LowscoreCommand()
#date_command = DateCommand()

# mod command
change_credit_command = SetCreditCommand()

# admin commands
add_admin_command = AddAdminCommand()
delete_admin_command = DeleteAdminCommand()
admin_list_command = GetAdminListCommand()

BotCommand.get_commands_description()