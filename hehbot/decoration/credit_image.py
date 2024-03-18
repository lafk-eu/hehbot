from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np
import aiogram, asyncio
from io import BytesIO
import os
from hehbot import bot, repo_user, Person

async def adjust_brightness(image, factor):
    def blocking_adjust_brightness():
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)
    return await asyncio.to_thread(blocking_adjust_brightness)

async def get_dominant_color_async(image_bytes, brightness_adjustment=False) -> tuple[int, int, int]:
    async def blocking_operations(img):
        if brightness_adjustment:
            img = await adjust_brightness(img, 0.75)  # Зменшуємо яскравість на 40%
        img = img.resize((140, 140))
        img = img.convert('RGB')

        pixels = np.array(img)

        def is_not_gray_or_white(color):
            r, g, b = map(int, color)  # Переконайтесь, що r, g, b є цілими числами
            gray_threshold = 10
            white_threshold = 200
            # Використання np.abs для уникнення переповнення при відніманні
            if np.abs(r - g) < gray_threshold and np.abs(g - b) < gray_threshold and np.abs(r - b) < gray_threshold:
                return False
            if r > white_threshold and g > white_threshold and b > white_threshold:
                return False
            return True


        colors, counts = np.unique(pixels.reshape(-1, 3), axis=0, return_counts=True)
        filtered_colors = [(color, count) for color, count in zip(colors, counts) if is_not_gray_or_white(color)]

        if filtered_colors:
            dominant_color = max(filtered_colors, key=lambda x: x[1])[0]
            return (dominant_color[0], dominant_color[1], dominant_color[2])
        else:
            return (24, 27, 33)

    with Image.open(image_bytes) as img:
        if not brightness_adjustment:
            # Спробуйте без зменшення яскравості
            result = await blocking_operations(img)
            if result == (24, 27, 33):  # Якщо не вдалося знайти, спробуйте зі зменшеною яскравістю
                return await get_dominant_color_async(image_bytes, brightness_adjustment=True)
            return result
        else:
            # Зменшення яскравості вже було застосовано
            return await blocking_operations(img)
        
async def get_avatar_id_async(user_id: int) -> str | None:
    try:
        photos = await bot.get_user_profile_photos(user_id)
    except:
        return None
    if photos.photos:
        # Вибираємо останню фотографію (найновішу)
        photo = photos.photos[0][0]
        return photo.file_id
    return None

async def download_profile_photo_async(person) -> BytesIO | None:
    # Отримуємо список фотографій профілю
    ava = await get_avatar_id_async(person.id)
    if ava:
        # Отримуємо файл
        try:
            file = await bot.get_file(ava)
        except:
            return None
        # Завантажуємо файл
        file_path = file.file_path
        file_content = await bot.download_file(file_path)
        if isinstance(file_content, BytesIO):  # Перевіряємо, чи це об'єкт BytesIO
            file_content = file_content.getvalue()  # Якщо так, читаємо байти
    else:
        # Якщо аватар відсутній, завантажуємо стандартне зображення
        try:
            with open('img/no_avatar.jpg', 'rb') as f:
                file_content = f.read()
        except FileNotFoundError:
            return None  # або повертайте спеціальне зображення помилки

    # Зберігаємо в об'єкт байтів
    bytes_io = BytesIO()
    bytes_io.write(file_content)  # Тепер file_content гарантовано є байтами
    bytes_io.seek(0)
    
    return bytes_io

async def get_credit_image_async(person, update = False):
    output_path = f"img/credits/{str(person.id)}.jpeg"
    if os.path.exists(output_path) and not update:
        # Якщо зображення існує, повертаємо шлях
        return output_path
    else:
        # Якщо зображення не існує, викликаємо створення зображення
        return await create_credit_image_async(person)

async def create_credit_image_async(person_object) -> str:
    # Встановлення розмірів зображення
    image_width = 600
    image_height = 140

    # Виконуємо блокуючі операції з PIL в окремому потоці
    def create_image(person, avatar: BytesIO, dominant_color: tuple[int, int, int]):
        MAX_INT_VALUE = 9223372036854775807
        MIN_INT_VALUE = -9223372036854775808
        # Створення нового зображення з чорним фоном
        image = Image.new('RGB', (image_width, image_height), color=dominant_color)
        draw = ImageDraw.Draw(image)

        # Відкриття та вставка аватара
        avatar = Image.open(avatar).resize((140, 140))
        image.paste(avatar, (0, 0))  # Вставка зліва зверху

        # Налаштування шрифту
        font_path = "font/DejaVuSans.ttf"
        font = ImageFont.truetype(font_path, 24)
        grey_font = ImageFont.truetype(font_path, 20)

        # Якщо треба центрувати текст горизонтально
        #text_width = draw.textlength(balance_text, font=font)
        #draw.text(((image_width - text_width) / 2, 70), balance_text, fill="white", font=font)

        # Додавання інформації про користувача
        if person.score > MAX_INT_VALUE / 1000 or person.score < MIN_INT_VALUE / 1000:
            font = ImageFont.truetype(font_path, 20)

        if person.score == MAX_INT_VALUE or person.score == MIN_INT_VALUE:
            draw.text(
                (160, 110), 
                '(макс.)' if person.score == MAX_INT_VALUE else '(мін.)', 
                fill="white", 
                font=font
            )
        
        balance_text = f"Соц. Кредитів: {person.score}"

        draw.text((160, 80), balance_text, fill="white", font=font)
        draw.text((160, 10), person.fullname, fill="white", font=font)
        draw.text((160, 40), '@'+person.name, fill="grey", font=grey_font)

        # Збереження зображення
        output_path = f"img/credits/{str(person.id)}.jpeg"
        image.save(output_path, format='JPEG')

        return output_path
    
    ava = await download_profile_photo_async(person_object)
    color = await get_dominant_color_async(ava)

    output_path = await asyncio.to_thread(create_image, person_object, ava, color)
    print('generated user image')
    return output_path

async def create_changed_credit_image_async(person_object, added_credits: int) -> str:
    # Встановлення розмірів зображення
    image_width = 600
    image_height = 140

    # Виконуємо блокуючі операції з PIL в окремому потоці
    def create_image(person, added_credits: int, avatar: BytesIO, dominant_color: tuple[int, int, int]):
        # Створення нового зображення з чорним фоном
        image = Image.new('RGB', (image_width, image_height), color=dominant_color)
        draw = ImageDraw.Draw(image)

        # Відкриття та вставка аватара
        avatar = Image.open(avatar).resize((140, 140))
        image.paste(avatar, (0, 0))  # Вставка зліва зверху

        # Налаштування шрифту
        font_path = "font/DejaVuSans.ttf"
        font_size = 24
        font = ImageFont.truetype(font_path, font_size)
        grey_font = ImageFont.truetype(font_path, 20)

        # Якщо треба центрувати текст горизонтально
        #text_width = draw.textlength(balance_text, font=font)
        #draw.text(((image_width - text_width) / 2, 70), balance_text, fill="white", font=font)

        # Додавання інформації про користувача
        balance_text = f"{person.score}"
        draw.text((160, 80), balance_text, fill="white", font=font)
        pos_for_changed_credits = draw.textlength(balance_text)
        
    
        credit_str = str(added_credits)
        if added_credits >= 0:
            credit_str_color = (0, 255, 0)
            
            credit_str = f'+{added_credits}'
            draw.text((180 + pos_for_changed_credits * 2.5, 80), f'↑ {credit_str}', fill=credit_str_color, font=font)
        else:
            credit_str_color = (255, 0, 0)
            draw.text((180 + pos_for_changed_credits * 2.5, 80), f'↓ {credit_str}', fill=credit_str_color, font=font)

        draw.text((160, 10), person.fullname, fill="white", font=font)
        draw.text((160, 40), '@'+person.name, fill="grey", font=grey_font)

        # Збереження зображення
        output_path = f"img/changed_credit/{str(person.id)}.jpeg"
        image.save(output_path, format='JPEG')

        return output_path
    
    ava = await download_profile_photo_async(person_object)
    color = await get_dominant_color_async(ava)

    output_path = await asyncio.to_thread(create_image, person_object, added_credits, ava, color)
    print('generated user image')
    return output_path




async def send_credit_image(person_object, chat_id: int):
    photo = await get_credit_image_async(person_object)
    await bot.send_photo(chat_id, aiogram.types.FSInputFile(photo))
    return None

async def send_changed_credit_image(person_object, added_credits: int, chat_id: int):
    await bot.send_photo(chat_id, aiogram.types.FSInputFile(await create_changed_credit_image_async(person_object, added_credits)))
    return None

async def send_highscore_image(chat_id: int, limit: int = 5):
    users = repo_user.with_highest_scores(limit)
    image_paths = await asyncio.gather(*(get_credit_image_async(user) for user in users))
    
    total_height = 140 * len(users)
    combined_image = Image.new('RGB', (600, total_height))
    
    for index, image_path in enumerate(image_paths):
        user_image = Image.open(image_path)
        combined_image.paste(user_image, (0, 140 * index))
    
    output_path = "img/highscore.jpeg"
    combined_image.save(output_path, format='JPEG')
    
    await bot.send_photo(chat_id, aiogram.types.FSInputFile(output_path))

async def send_lowscore_image(chat_id: int, limit: int = 5):
    users = repo_user.with_lowest_scores(limit)
    image_paths = await asyncio.gather(*(get_credit_image_async(user) for user in users))
    
    total_height = 140 * len(users)
    combined_image = Image.new('RGB', (600, total_height))
    
    for index, image_path in enumerate(image_paths):
        user_image = Image.open(image_path)
        combined_image.paste(user_image, (0, 140 * index))
    
    output_path = "img/lowscore.jpeg"
    combined_image.save(output_path, format='JPEG')
    
    await bot.send_photo(chat_id, aiogram.types.FSInputFile(output_path))