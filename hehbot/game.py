from aiogram import Router, F
from aiogram.enums import DiceEmoji
from aiogram.types import Message
from hehbot import dp, repo_user
import asyncio
from hehbot.decoration.slot_machine import send_slot_machine, CASINO_EMOJI

def decode_slot_machine_value(value: int) -> list[str]:
    value -= 1
    result = []
    for _ in range(3):
        result.append(CASINO_EMOJI[value % 4])
        value //= 4
    return result

@dp.message(
    F.dice[F.emoji == DiceEmoji.SLOT_MACHINE].value.cast(decode_slot_machine_value).as_("slots")
)
async def handle_slot_machine(msg: Message, slots: list[str]):
    person = repo_user.by_tg(msg.from_user.id)
    if person and not msg.is_automatic_forward and not msg.forward_origin:
        result = await send_slot_machine(msg, slots)
        if result:
            await msg.reply(result)
        

        #await repo_user.update_person(person.id, score=person.score + score_change)