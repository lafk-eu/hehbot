from random import randint
from hehbot import repo_user, Person
import aiogram, asyncio
from aiogram.enums import DiceEmoji
from collections import Counter
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
import numpy as np

slot_machine_path = 'img/slot_machine/'

# bar, grape, lemon, seven
CASINO_EMOJI = ["🅱️", "🍇", "🍋", "7️⃣"]

async def draw_slot_machine_image_async(user_id: int, reward: int, randomized_reward: int):        
    # Виконуємо блокуючі операції з PIL в окремому потоці
    def create_animated_gif(user_id: int, reward: int):
        if reward < 0:
            reward_str = 'm' + str(abs(reward))
            color = (200, 50, 50)
        else:
            reward_str = str(reward)
            color = (50, 200, 50)

        image_path = f"{slot_machine_path}{reward_str}.jpg"
        base_image = Image.open(image_path).resize((320, 180))
        
        text = str(randomized_reward) if randomized_reward < 0 else '+' + str(randomized_reward)
        font_path = "font/impact.ttf"
        frames, duration = 24, 1000 // 24
        min_font_size, max_font_size = 24, 36
        animated_frames = []
        
        outline_thickness, outline_color = 1, (0, 0, 0)
        
        for i in range(frames):
            font_size = int(min_font_size + (max_font_size - min_font_size) * (0.5 + 0.5 * np.sin(np.pi * 2 * i / frames)))
            frame = base_image.copy()
            draw = ImageDraw.Draw(frame)
            font = ImageFont.truetype(font_path, font_size)
            text_width = draw.textlength(text, font=font)
            text_position = ((frame.width - text_width) // 1.5, (frame.height - font_size) // 2.6)

            for x in range(-outline_thickness, outline_thickness + 1):
                for y in range(-outline_thickness, outline_thickness + 1):
                    draw.text((text_position[0] + x, text_position[1] + y), text, font=font, fill=outline_color)
            
            draw.text(text_position, text, font=font, fill=color)
            animated_frames.append(frame)

        output_path = f"{slot_machine_path}users/{user_id}.gif"
        animated_frames[0].save(output_path, save_all=True, append_images=animated_frames[1:], duration=duration, loop=0, format='GIF')

        return output_path

    return await asyncio.to_thread(create_animated_gif, user_id, reward)
    #except:
        #return None

async def is_jackpot() -> bool:
    return randint(1, 150) == 1

# Перевірка на наявність двох однакових емодзі в ряду
def has_two_in_a_row(slots, emojis):
    for emoji in emojis:
        if slots.count(emoji) >= 2 and (slots[0] == slots[1] == emoji or slots[1] == slots[2] == emoji):
            return True
    return False

async def check_reward(reward: int) -> bool:
    if reward == 100 or reward == 500 or reward == 1000 or reward >= 5000:
        return True
    return False

async def send_slot_machine(msg: aiogram.types.Message, slots: list[str]):    
    # Ініціалізація зміни балансу
    score_change = 0
        
    # Перевірка на спеціальні комбінації
    if slots == ["🍋", "🍋", "🍋"] or slots == ["🅱️", "🅱️", "🅱️"]:
        score_change = -5000
        if await is_jackpot():
            score_change = -100000
    elif slots == ["🍇", "🍇", "🍇"] or slots == ["7️⃣", "7️⃣", "7️⃣"]:
        score_change = 5000
        if await is_jackpot():
            score_change = 100000
    elif has_two_in_a_row(slots, ["🍋", "🅱️"]):
        score_change = -1000
    elif has_two_in_a_row(slots, ["🍇", "7️⃣"]):
        score_change = 1000
    else:
        counts = Counter(slots)
        # Додаткові умови для двох однакових емодзі
        if counts["🍋"] == 2 or counts["🅱️"] == 2:
            score_change = -500
        elif counts["🍇"] == 2 or counts["7️⃣"] == 2:
            score_change = 500
        else:
            await asyncio.sleep(2)
            # Врахування інших комбінацій
            if counts["🍋"] > 0 and counts["🅱️"] > 0:
                score_change = -100
            else:
                score_change = 100

    async def randomize(reward: int):
        if reward == 0:
            return 0
        elif reward >= 100000:
            return 100000
        elif reward <= -100000:
            return -100000
        elif reward > 0:
            # Для позитивних нагород, рандомізуємо між 1 і початковим значенням нагороди
            return reward + randint(-int(reward / 2), int(reward / 2))
        else:
            # Для від'ємних нагород, рандомізуємо між початковим значенням нагороди і -1
            return reward + randint(int(reward / 2), -int(reward / 2))

    user = repo_user.by_tg(msg.from_user.id)
    randomized_score = await randomize(score_change)

    if score_change == 100000:
        await msg.reply_photo(photo=aiogram.types.FSInputFile(slot_machine_path+'jackpot.jpg'), caption='Це — скарб!')
        
    elif score_change == -100000:
        await msg.reply_photo(photo=aiogram.types.FSInputFile(slot_machine_path+'mjackpot.jpg'), 
                              caption='''
Приношу свої щирі вибачення за невдачу в грі, що сталася внаслідок рандомізованих елементів. 
Розуміємо, що це може викликати розчарування.''')

    elif score_change != 0:
        if score_change >= 250 or score_change <= -250:
            img_path = await draw_slot_machine_image_async(user.id, score_change, randomized_score)
            if img_path:
                await msg.reply_animation(aiogram.types.FSInputFile(img_path), caption= 'Нова спроба завтра.')
                await repo_user.update_person(user.id, score=user.score + randomized_score)
                return None
        await msg.reply(f'Отримано {randomized_score} соціальних кредитів за вашу гру! Нова спроба завтра.')
        
    else:
        return 'Отакої! Отримано 0 кредитів! Нова спроба завтра'
    
    await repo_user.update_person(user.id, score=user.score + randomized_score)
    return None