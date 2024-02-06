from heh_bot import dp, bot
from aiogram.utils.chat_action import ChatActionSender
from aiogram.types import Message, FSInputFile, InputMediaPhoto
from aiogram import Bot

import os, aiofiles

# from chatgpt.photo import gen_image     # нема реалізації


# file_path той що зберігається в:
# file_id =  message.photo[-1].file_id
# file = await bot.get_file(file_id)
# >>> file.file_path
async def download_and_save_file(file_path, full_path):

    file_data = await bot.download_file(file_path)
    
    async with aiofiles.open(full_path, 'wb') as f:
        await f.write(file_data.getvalue())  # Якщо file_data є BytesIO об'єктом

# бере найякіснішу фотку користувача і присилає її, зберігаючи локально
@dp.message(lambda message: message.photo if message else False)
async def photo_handler(message: Message):

    # Підготовка директорії для завантаження
    download_path = "downloads"
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    # Отримання шляху до файлу
    photo_id =  message.photo[-1].file_id
    file = await bot.get_file(photo_id)

    # Збереження файлу локально
    full_path = os.path.join(download_path, f"{message.photo[-1].file_unique_id}.jpg")
    await download_and_save_file(file.file_path, full_path)

    # Куди зберігати
    download_path = "downloads"
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    # відправити фото
    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.chat.id):

        await bot.send_photo(message.chat.id, FSInputFile(full_path), caption='your photo!')

    #os.rmdir(full_path)