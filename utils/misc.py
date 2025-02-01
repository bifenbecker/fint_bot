import datetime
import logging
import random

from aiogram import Bot
from aiogram.types import FSInputFile

from db.models import UserCard
from keyboards.games_kbs import (card_penalty_answer_kb, card_penalty_offer_kb,
                                 penalty_action_kb, penalty_offer_kb)
from utils.const import images


async def card_rarity_randomize(kind):
    if kind == "card":
        rarities = ["Common", "Uncommon", "Rare", "Very rare", "Coach", 
                    "Epic", "Unique", "Flashback", "Legendary", "Heroes", 
                    "Icons"]
        chances = [30, 21.4, 15, 10, 8, 7, 5, 2, 1, 0.5, 0.1]
        
    elif kind == "pick":
        rarities = ["Rare", "Very rare", "Coach", "Epic", "Unique", 
                    "Flashback", "Legendary", "Heroes", "Icons"]
        chances = [34, 25.3, 17, 9, 7, 4, 2.2, 1, 0.5]
        
    elif kind == "ls":
        rarities = ["Common", "Uncommon", "Rare", "Very rare", "Coach", 
                    "Epic", "Unique", "Flashback", "Moments", 
                    "Heroes", "Icons"]
        chances = [35, 21.7, 13, 10, 9, 5, 3, 2, 1, 0.2, 0.1]
        
    elif kind == "lsplus":
        rarities = ["Common", "Uncommon", "Rare", "Very rare", "Coach", 
                    "Epic", "Unique", "Flashback", "Moments", 
                    "Heroes", "Icons"]
        chances = [35, 20, 13, 10, 9, 5, 3.5, 2, 1, 0.8, 0.7]
        
    elif kind == "casino":
        rarities = ["Unique", "Flashback", "Legendary", "Moments", "Heroes", 
                    "Icons"]
        chances = [54, 23, 11, 6, 4, 2]
        
    elif kind == "darts":
        rarities = ["Common", "Uncommon", "Rare", "Very rare", "Coach", 
                    "Epic", "Unique", "Flashback", "Moments", "Heroes", "Icons"]
        chances = [28, 16, 12, 10, 9, 8, 7, 6, 2, 1.8, 0.2]
        
    elif kind == "pack_10_20":
        rarities = ["Common", "Uncommon", "Rare", "Very rare", "Coach", 
                    "Epic", "Unique", "Flashback", "Legendary", "Heroes", 
                    "Icons"]
        chances = [25, 15, 13, 11, 10, 9, 7, 5, 2.25, 1.5, 1.25]
        
    elif kind == "pack_30":
        rarities = ["Rare", "Very rare", "Coach", "Epic", "Unique", 
                    "Flashback", "Legendary", "Heroes", "Icons"]
        chances = [30, 21, 14, 12, 10, 6, 3, 2.3, 1.7]

    result = random.choices(rarities, chances, k=1)
    return result[0]


async def format_delay_text(delay):
    if delay >= 86400:
        days = delay // 86400
        hours = (delay % 86400) // 3600
        minutes = ((delay % 86400) % 3600) // 60
        txt = f"{days}дн {hours}ч {minutes}мин"
    elif delay >= 3600:
        hours = delay // 3600
        minutes = (delay % 3600) // 60
        txt = f"{hours}ч {minutes}мин"
    else:
        minutes = delay // 60
        txt = f"{minutes}мин"

    return txt


async def calc_cards_quant(cards):
    data = {}
    card: UserCard
    for card in cards:
        if str(card.card_id) in data:
            quant = data[str(card.card_id)]['quant']
            quant += 1
            data[str(card.card_id)]['quant'] = quant
        else:
            data[str(card.card_id)] = {
                'card_name': card.card.card_name,
                'rating': card.points, 'quant': 1
            }

    return data


async def send_action_emoji(bot: Bot, user_id, emoji):
    msg = await bot.send_dice(user_id, emoji=emoji)
    value = msg.dice.value

    return value


async def send_penalty_offer(bot: Bot, user_id, username, pen_id):
    txt = f"{username} предлагает вам сыграть в Пенальти!"

    msg_id = 0
    try:
        msg = await bot.send_message(
            user_id, txt, reply_markup=penalty_offer_kb(pen_id))
        msg_id = msg.message_id
    except Exception as error:
        logging.error(f"Send error | chat {user_id}\n{error}")

    return msg_id


async def send_card_penalty_offer(bot: Bot, user_id, username, pen_id, image):
    txt = f"{username} предлагает вам сыграть в Пенальти!"

    msg_id = 0
    try:
        msg = await bot.send_photo(
            user_id, image, caption=txt, reply_markup=card_penalty_offer_kb(pen_id))
        msg_id = msg.message_id
    except Exception as error:
        logging.error(f"Send error | chat {user_id}\n{error}")

    return msg_id


async def send_card_penalty_answer(bot: Bot, user_id, username, pen_id, image):
    txt = f"{username} поставил эту карту в Пенальти!"

    msg_id = 0
    try:
        msg = await bot.send_photo(
            user_id, image, caption=txt,
            reply_markup=card_penalty_answer_kb(pen_id))
        msg_id = msg.message_id
    except Exception as error:
        logging.error(f"Send error | chat {user_id}\n{error}")

    return msg_id


async def send_random_penalty_offer(bot: Bot, user_id, username, pen_id):
    txt = f"Соперник найден!\nВаш соперник - {username}"

    msg_id = 0
    try:
        msg = await bot.send_message(
            user_id, txt, reply_markup=penalty_offer_kb(pen_id))
        msg_id = msg.message_id
    except Exception as error:
        logging.error(f"Send error | chat {user_id}\n{error}")

    return msg_id


async def send_penalty_action(bot: Bot, user_id, pen_id, kind):
    if kind == "kicker":
        txt = f"Выбери угол, в который хочешь ударить"
    else:
        txt = f"Выбери угол, в который хочешь прыгнуть"

    img = images.get("penalty")
    msg_id = 0
    try:
        msg = await bot.send_photo(chat_id=user_id, photo=FSInputFile(img), caption=txt,
                                   reply_markup=penalty_action_kb(pen_id, kind))
        msg_id = msg.message_id
    except Exception as error:
        logging.error(f"Send error | chat {user_id}\n{error}")

    return msg_id


def get_new_pass_date(days, old_str, old_ts):
    if old_str == "nopass":
        now_ts = int(datetime.datetime.now().timestamp())
        new_ts = now_ts + days * 86400
    else:
        new_ts = old_ts + days * 86400

    new_date = datetime.datetime.fromtimestamp(new_ts)
    new_str = new_date.strftime("%d.%m.%Y %H:%M")

    return new_ts, new_str
