from hehbot.client import repo_user, Person, CooldownType, Cooldown
from hehbot.admin import repo_staff, StaffPerson

from hehbot.base_command import BotCommand
from datetime import datetime

from hehbot.decoration.credit_image import send_credit_image, send_highscore_image, send_lowscore_image, send_changed_credit_image
from mbot import bot, dp

import aiogram, asyncio
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.utils.markdown import hbold
from aiogram.utils.keyboard import InlineKeyboardBuilder

import re

def safe_telegram_request(retry_seconds=5.0):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            while True:
                try:
                    return await func(*args, **kwargs)
                except TelegramRetryAfter as e:
                    print(f"Попередження: контроль за частотою запитів від Telegram, чекаємо {e.retry_after} секунди.")
                    await asyncio.sleep(e.retry_after)
                except TelegramAPIError as e:
                    print(f"Помилка Telegram API: {e}")
                    break  # or raise e to propagate the error after logging
        return wrapper
    return decorator

def find_username(text: str) -> str | None:
    # Спочатку шукаємо ім'я, яке починається з "@" або "$"
    special_match = re.search(r'\b[@$][a-zA-Z_][a-zA-Z0-9_]*\b', text)
    if special_match:
        return special_match.group(0)

    # Якщо таке ім'я не знайдено, шукаємо ім'я за існуючим патерном
    match = re.search(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)
    return match.group(0) if match else None

def find_number(text: str) -> int:
    match = re.search(r'(?<!\w)[+-]?\d+', text)
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
    description = "+300 рейтингу (видати кредити)"
    info = "Видати кредити; потрібні нік та число."

    @classmethod
    def command_name(cls) -> str:
        return "give"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None) -> str:
        MAX_INT_VALUE = 9223372036854775807
        MIN_INT_VALUE = -9223372036854775808
        
        staff = repo_staff.get_by_id(msg.from_user.id)
        amount = None

        if not staff:
            return cls.execute_stopped(f'через відсутність прав')
        
        if by_str:
            username = find_username(by_str)
            amount = find_number(by_str)
        else:
            return cls.execute_stopped('не вказано ім\'я користувача або суму')

        target = repo_user.by_name(username)
        if not target:
            target_msg = msg.reply_to_message
        
            if target_msg:
                target = await repo_user.by_tg_message(target_msg)
                
                if not target:
                    return cls.execute_stopped(f'Щось пішло не так під час додавання {target_msg.from_user.full_name if target_msg.from_user else "(Не можу вимовити ім'я)"} в мою базу даних.')
            else:
                return cls.execute_stopped(f'користувача {username} не знайдено в базі даних: можеш відповісти на його повідомлення щоб додати.')

        if amount:
            print('число: ', amount)
            print('рядок: ', by_str)
            new_score = target.score + amount

            if new_score > MAX_INT_VALUE:
                new_score = MAX_INT_VALUE
            elif new_score < MIN_INT_VALUE:
                new_score = MIN_INT_VALUE
            
        else:
            return cls.execute_stopped(f'через неправильний формат числа кредитів')
        
        if not staff.admin:
            if staff.credits <= 0:
                return f'Насьогодні твоя особиста роздача кредитів вичерпана 😢'
            if staff.credits < amount:
                return f'Сьогодні тобі можна задати кредитів на: {staff.credits}. Зменш кількість видачі.'

            staff.credits -= abs(amount)
            repo_staff.update(staff)

            if repo_staff.get_by_id(target.id):
                return f'Не можна видавати сошіал кредити іншим інспекторам сошіал кредиту! 😡😡😡'

        await send_changed_credit_image(repo_user.by_tg(target.id), amount, msg)
        await repo_user.update_person(id=target.id, score=new_score)

        return None


class MyCreditCommand(BotCommand):
    description = "Покажи/Скільки який баланс кредитів"
    info = "Баланс; можна дізнатися чужий."

    @classmethod
    def command_name(cls) -> str:
        return "credit"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None):
        # Перевіряємо наявність аргументів спочатку
        if args:
            user = repo_user.by_name(find_username(args[0]))
            if user:
                return await send_credit_image(user, msg)
            elif not by_str:  # Якщо не знайдено за аргументом і by_str не надано
                return cls.execute_stopped(f'користувача {args[0]} не знайдено в базі даних')

        # Якщо аргументи відсутні або пошук за аргументами не вдався, і надано by_str
        if by_str:
            words = by_str.split(" ", 1)  # Розділяємо рядок на дві частини: перше слово та решту рядка
            if len(words) > 1:
                by_str = " ".join(words[1:])  # Видаляємо перше слово

            name = find_username(by_str)
            if name:
                target = repo_user.by_name(name)
                if target:
                    return await send_credit_image(target, msg)
                
                else:
                    target_msg = msg.reply_to_message
        
                    if target_msg:
                        target = await repo_user.by_tg_message(target_msg)
                
                        if not target:
                            return cls.execute_stopped(f'Щось пішло не так під час додавання {target_msg.from_user.full_name if target_msg.from_user else "(Не можу вимовити ім'я)"} в мою базу даних.')
                        return await send_credit_image(target, msg)
                    else:
                        return cls.execute_stopped(f'{name} не знайдено: можеш відповісти на його повідомлення щоб додати.')

        # Якщо не надано аргументів і by_str пустий, повертаємо кредити поточного користувача
        if not args:
            return await send_credit_image(repo_user.by_tg(msg.from_user.id), msg)

        # Загальна відмова, якщо жоден з вище наведених випадків не спрацював
        return cls.execute_stopped(f'Користувача {name if name else ''} не знайдено')


class HighscoreCommand(BotCommand):
    description = "Кращі: ТОП користувачів з найвищим рейтингом."
    info = "Кращі: ними пишається партія."

    @classmethod
    def command_name(cls) -> str:
        return "best"

    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None):
        try:
            limit = int(args[0])
        except:
            try:
                limit = int(find_number(by_str))
            except:
                limit = 5

        if limit > 9:
            return 'Не можна більше 9-ти користувачів'
            #return 'Не можна більше 9-ти користувачів, бо ти мій єдиний займаєш там, останнє, 10 місце ❤️'
        elif limit < 1:
            return 'Не можна менше одного користувача.'

        await send_highscore_image(msg, limit=limit)
        return None
        #p_list = repo_user.with_highest_scores(10)
        #best_str = '\n'.join(f'{i + 1}. {p.name}: {p.score}' for i, p in enumerate(p_list))
        #return self.execute_finished(best_str)
    
class LowscoreCommand(BotCommand):
    description = "Гірші: ТОП користувачів з найгіршим рейтингом."
    info = "Гірші: перешкоди партії."

    @classmethod
    def command_name(cls) -> str:
        return "lowscore"

    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None):
        try:
            limit = int(args[0])
        except:
            try:
                limit = int(find_number(by_str))
            except:
                limit = 5

        if limit > 9:
            return 'Не можна більше 9-ти користувачів.'
        elif limit < 1:
            return 'Не можна менше одного користувача.'

        await send_lowscore_image(msg, limit=limit)
        return None
    
class IdiNakhuyCommand(BotCommand):
    description = "іді нахуй"
    ignore = True
    min_similarity = 0.70

    @classmethod
    def command_name(cls) -> str:
        return "idi_nakhuy"

    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None):
        person = repo_user.by_tg(msg.from_user.id)
        cooldown = Cooldown(person)

        if await cooldown.get_usage_count(CooldownType.IDI):
            await msg.reply('Сам іді')
            return
        
        await cooldown.update_cooldown(CooldownType.IDI, 1)
        
        score_change = 300 if person.score < 0 else -300

        await send_changed_credit_image(person, score_change, msg, caption='Сам іді')
        await repo_user.update_person(person.id, score=person.score+score_change)
        await repo_user.update_cooldown(person.id, cooldown)

    
class DateCommand(BotCommand):
    #description = "Поточна дата."
    ignore = True

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
    info = "Команда для цього повідомлення."

    @classmethod
    def command_name(cls) -> str:
        return 'help'
    
    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None):
        commands = self.get_commands_info()

        if not repo_staff.get_by_id(msg.from_user.id):
            commands = [command for command in commands if not command.startswith("/give")]

        cmd_list_str = '\n'.join(commands)
        return f'''
Для команд, де потрібен нік, можна обійтися відповіддю на чуже повідомлення.

{cmd_list_str}

Можу розпізнавати команди в тексті, якщо перше слово "суд".'''
    
class AddAdminCommand(BotCommand):
    ignore = True

    @classmethod
    def command_name(cls) -> str:
        return "new_admin"

    @classmethod
    async def execute(self, msg: aiogram.types.Message, args, by_str: str = None):
        async def get_error() -> str:
            return '''через неправильні аргументи. Очікувалось: 
/new_admin @username число_прав(0 - для інспектора, 1 - для голови) максимальна_щоденна_видача_кредитів(якщо інспектор)
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
                    return f'Голова @{new_person.name} ({new_person.fullname}) успішно доданий.'
                else:
                    return f'Інспектор @{new_person.name} ({new_person.fullname}) успішно доданий.'
            else:
                return self.execute_stopped(await get_error())
        else:
            return None
        
class DeleteAdminCommand(BotCommand):
    ignore = True

    @classmethod
    def command_name(cls) -> str:
        return "delete_admin"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None):
        staff_sender = repo_staff.get_by_id(msg.from_user.id)
        if not staff_sender:
            return
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
            return f'Голова/інспектор @{user.name} з ID {id_to_delete} успішно видалений.'
        else:
            return cls.execute_stopped('Голова не знайдений.')
        
class GetAdminListCommand(BotCommand):
    ignore = True

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
                    return f'інспектор ({member.credits} кредитів на сьогодні з {member.max_credits})'
                else:
                    return 'голова'

            members = repo_staff.get_all()
            for member in members:
                person = repo_user.by_tg(member.id)

                member_list.append(f'{person.fullname} (@{person.name}) - {staff_info(member)}')
            
            return '\n'.join(member_list)
        return None
    
class DeleteUserCommand(BotCommand):
    ignore = True

    @classmethod
    def command_name(cls) -> str:
        return "delete_user"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None):
        staff_sender = repo_staff.get_by_id(msg.from_user.id)
        if not staff_sender or not staff_sender.admin:
            return
        async def get_error() -> str:
            return '''через неправильні аргументи. Очікувалось: 
/delete_user @username (або айді особи)'''

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

        ex_member = repo_user.by_tg(id_to_delete)
        if ex_member:
            repo_user.delete(id_to_delete)
            return f'користувач @{user.name} з ID {id_to_delete} успішно видалений.'
        else:
            return cls.execute_stopped('Користувач не знайдений.')
        









class MakebetCommand(BotCommand):
    description = "Зіграти ставку / укласти парі"
    info = '''Зробити ставку (укласти парі) і зіграти.
Якщо без ніку, то будь-хто може прийняти.
Макс. ставка — 300 кредитів. Якщо учасники мають більше, ліміт збільшується.'''

    @classmethod
    def command_name(cls) -> str:
        return "bet"

    @classmethod
    async def execute(cls, msg: aiogram.types.Message, args, by_str: str = None):
        person = repo_user.by_tg(msg.from_user.id)
        if not person:
            return cls.execute_stopped('Я тебе не знаю')
        
        target = None
        target_username = find_username(by_str)
        amount = find_number(by_str)

        if target_username:
            target = repo_user.by_name(target_username)
        if not target:
            target_msg = msg.reply_to_message
        
            if target_msg:
                target = await repo_user.by_tg_message(target_msg)
            
                if not target:
                    return cls.execute_stopped(f'щось пішло не так під час додавання {target_msg.from_user.full_name if target_msg.from_user else "(Не можу вимовити ім'я)"} в мою базу даних')

        if not amount:
            return cls.execute_stopped(f'через неправильний формат числа кредитів')

        if amount < 10:
            return f'Давай нормально грати: які ще {amount} кредитів? Я приймаю лише 10 і більше'
        
        if amount > 300:
            if person.score < amount:
                return f'Нє, так діло не піде. 300 кредитів на одну ставку. Якби в тебе було більше ніж {amount} кредитів, то тоді так.'
            elif target and target.score < amount:
                return f'Бачу в твого дружка менше {amount} кредитів. Гра піде, якщо 300 кредитів на одну ставку.'
            

        cd = Cooldown(person)
        bet_count = await cd.get_usage_count(CooldownType.BET)

        if bet_count >= 3:
            return f'Сьогодні ти не можеш укладати парі, лише приймати.'
        
        bet_count += 1
        await cd.update_cooldown(CooldownType.BET, bet_count)
        await repo_user.update_cooldown(person.id, cd)
        
        if target:
            # Логіка для приватної гри
            bet_message = await msg.answer(f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nі запрошує {target.fullname} (@{target.name})", parse_mode='html')
            
            keyboard = InlineKeyboardBuilder()

            keyboard.button(text="Ігнорувати",
                callback_data=f"ignore:{person.id}:{target.id}:{msg.chat.id}:{bet_message.message_id}"),
            
            keyboard.button(text="Прийняти",
                callback_data=f"accept:{amount}:{person.id}:{target.id}:{msg.chat.id}:{bet_message.message_id}")

            await bet_message.edit_text(f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nі запрошує {target.fullname} (@{target.name})", 
                reply_markup=keyboard.as_markup(), 
                parse_mode='html')
            
            # Функція для оновлення повідомлення з таймером
            async def update_message():
                for remaining in range(60, -1, -5):  # хвилина з оновленням кожні 5 секунд
                    if remaining % 15 == 0:  # Оновлення тексту повідомлення кожні 15 секунд для зменшення навантаження на API
                        try:
                            await bet_message.edit_text(
                                f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nі запрошує {target.fullname} (@{target.name})\nЗалишилося: {remaining} секунд", 
                                reply_markup=keyboard.as_markup(), 
                                parse_mode='html')
                        except:
                            return                
                    await asyncio.sleep(5)
                await msg.delete()
                try:
                    await bet_message.delete()  # Видалення повідомлення після завершення часу очікування

                    await cd.update_cooldown(CooldownType.BET, bet_count-1)
                    await repo_user.update_cooldown(person.id, cd)
                except:
                    pass   # it's okay
            
            # Запуск функції оновлення повідомлення з таймером
            asyncio.create_task(update_message())

        else:
            disclaimer_text = f'Можуть приймати ті, в кого є {amount} кредитів.\n' if amount > 300 else ''

            # Логіка для публічної гри
            bet_message = await msg.answer(f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nЧи хтось хоче прийняти виклик?{disclaimer_text}", parse_mode='html')
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="Прийняти виклик", 
                callback_data=f"accept:{amount}:{person.id}:0:{msg.chat.id}:{bet_message.message_id}")

            await bet_message.edit_text(f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nЧи хтось хоче прийняти виклик?{disclaimer_text}", 
                reply_markup=keyboard.as_markup(), 
                parse_mode='html')
            
            # Функція для оновлення повідомлення з таймером
            async def update_message():
                for remaining in range(60, -1, -5):  # хвилина з оновленням кожні 5 секунд
                    if remaining % 15 == 0:  # Оновлення тексту повідомлення кожні 15 секунд для зменшення навантаження на API
                        try:
                            await bet_message.edit_text(
                                f"{hbold(f'{person.fullname} укладає парі на {amount} кредитів')}\nЧи хтось хоче прийняти виклик?\n{disclaimer_text}Залишилося: {remaining} секунд", 
                                reply_markup=keyboard.as_markup(), 
                                parse_mode='html')
                        except:
                            return                
                    await asyncio.sleep(5)
                await msg.delete()
                try:
                    await bet_message.delete()  # Видалення повідомлення після завершення часу очікування

                    await cd.update_cooldown(CooldownType.BET, bet_count-1)
                    await repo_user.update_cooldown(person.id, cd)
                except:
                    pass   # it's okay
            
            # Запуск функції оновлення повідомлення з таймером
            asyncio.create_task(update_message())
        return None
    
async def safe_send_dice(chat_id: int, emoji: str):
    try:
        msg = await bot.send_dice(chat_id, emoji=emoji)
        return msg
    except TelegramRetryAfter as e:
        print(f"Спроба перевищила ліміт, чекаємо {e.retry_after} секунд.")
        await asyncio.sleep(e.retry_after)  # Чекаємо рекомендований час
        await safe_send_dice(chat_id)  # Спроба відправити ще раз після паузи
    except TelegramAPIError as e:
        print(f"Сталася помилка Telegram API: {e}")

async def safe_send_text(chat_id: int, text: str, parse_mode = None):
    try:
        msg = await bot.send_message(chat_id, text=text)
        return msg
    except TelegramRetryAfter as e:
        print(f"Спроба перевищила ліміт, чекаємо {e.retry_after} секунд.")
        await asyncio.sleep(e.retry_after)  # Чекаємо рекомендований час
        await safe_send_dice(chat_id)  # Спроба відправити ще раз після паузи
    except TelegramAPIError as e:
        print(f"Сталася помилка Telegram API: {e}")

async def safe_answer_callback_query(callback_query_id):
    try:
        callback = await bot.answer_callback_query(callback_query_id)
        return callback
    except TelegramRetryAfter as e:
        print(f"Спроба перевищила ліміт, чекаємо {e.retry_after} секунд.")
        await asyncio.sleep(e.retry_after)  # Чекаємо рекомендований час
        await safe_answer_callback_query(callback_query_id)  # Спроба відправити ще раз після паузи
    except TelegramAPIError as e:
        print(f"Сталася помилка Telegram API: {e}")

@dp.callback_query(lambda c: c.data and c.data.startswith('accept'))
async def handle_accept(callback_query: aiogram.types.CallbackQuery):
    await safe_answer_callback_query(callback_query.id)

    print(callback_query.data.split(':'))
    _, amount, user_id, target_id, chat_id, bet_message_id = callback_query.data.split(':')
    amount, user_id, target_id, chat_id, bet_message_id = int(amount), int(user_id), int(target_id), int(chat_id), int(bet_message_id)
    
    if target_id == 0:
        pass
    elif not target_id == callback_query.from_user.id:
        return None
    
    target = repo_user.by_tg(callback_query.from_user.id)
    if target:
        if target.id == user_id:
            return None
    else:
        t = callback_query.from_user
        target = Person(t.id, t.full_name, name=t.username)
        repo_user.add(target)
    
    if amount > 300 and target.score < amount:
        return None
    
    person = repo_user.by_tg(user_id)

    # Оновлення тексту повідомлення ставки, повідомляючи, що ставку прийнято
    await bot.delete_message(chat_id=chat_id, message_id=bet_message_id)

    await safe_send_text(chat_id=chat_id, text=f"Ставку прийнято користувачем {target.fullname} (@{target.name}).", parse_mode='HTML')
    
    # Тут логіка обробки прийняття ставки...
    # Відправка кубиків
    await asyncio.sleep(2)  # Затримка перед відправленням другого кубика
    msg1 = await safe_send_dice(chat_id, emoji="🎲")
    await asyncio.sleep(2)  # Затримка перед відправленням другого кубика
    msg2 = await safe_send_dice(chat_id, emoji="🎲")
    await asyncio.sleep(2)
        
    #await cd.update_cooldown(CooldownType.BET, bet_count+1)

    target_credits = 0
    person_credits = 0

    #await repo_user.update_cooldown(cd)
    if msg1.dice.value > msg2.dice.value:
        person_credits = amount
        target_credits = -amount

    elif msg1.dice.value < msg2.dice.value:
        person_credits = -amount
        target_credits = amount
    else:
        n = msg1.dice.value
        if n == 1:
            person_credits = -100
            target_credits = -100
        if n == 6:
            person_credits = +100
            target_credits = +100
        else:
            await safe_send_text(chat_id=chat_id, text='Ніхто не переміг: кредити не переписані.')
            return None

    async def give(person: Person, credits: int):
        await repo_user.update_person(person.id, score=person.score+credits)
        
    await give(person, person_credits)
    await give(target, target_credits)

    await safe_send_text(chat_id=chat_id, text=f'''
Результат:
{person.fullname} має {person.score} і отримує {person_credits}
{target.fullname} має {target.score} і отримує {target_credits}''', parse_mode='html')

@dp.callback_query(lambda c: c.data and c.data.startswith('ignore'))
async def handle_ignore(callback_query: aiogram.types.CallbackQuery):
    await safe_answer_callback_query(callback_query.id)
    _, user_id, target_id, chat_id, bet_message_id = callback_query.data.split(':')
    user_id, target_id, chat_id, bet_message_id = int(user_id), int(target_id), int(chat_id), int(bet_message_id)

    if target_id == 0 or not callback_query.from_user.id == target_id:
        return None
    
    try:
        await safe_send_text(chat_id, text=f"Ставку проігноровано користувачем.", parse_mode='HTML')
        # Оновлення тексту повідомлення ставки, повідомляючи, що ставку ігнорують
        await bot.delete_message(chat_id=chat_id, message_id=bet_message_id)

    except TelegramRetryAfter as e:
        print(f"Спроба перевищила ліміт, чекаємо {e.retry_after} секунд.")
        await asyncio.sleep(e.retry_after)  # Чекаємо рекомендований час
        await bot.edit_message_text(chat_id=chat_id, message_id=bet_message_id,
            text=f"Ставку проігноровано користувачем.", parse_mode='HTML')

        

# Ініціалізація команд
    
# client commands
help_command = HelpCommand()
check_credit_command = MyCreditCommand()
highscore_command = HighscoreCommand()
lowscore_command = LowscoreCommand()
makebet_command = MakebetCommand()
idi_nakhuy_command = IdiNakhuyCommand()
#date_command = DateCommand()

# mod command
change_credit_command = SetCreditCommand()

# admin commands
add_admin_command = AddAdminCommand()
delete_admin_command = DeleteAdminCommand()
admin_list_command = GetAdminListCommand()
delete_user_command = DeleteUserCommand()

BotCommand.get_commands_description()