import asyncio
import logging
from textwrap import dedent

from aiogram import F, Router
from aiogram.types import CallbackQuery as CQ
from aiogram.types.input_file import FSInputFile

from db.models import CardItem, Player
from db.queries.games_queries import lucky_shot
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.games_kbs import games_kb, lucky_shot_btn, no_free_ls_btn
from middlewares.actions import ActionMiddleware
from utils.format_texts import format_new_free_card_text
from utils.misc import format_delay_text

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "games", flags=flags)
async def games_cmd(c: CQ, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    txt = "Тут находятся мини-игры, в которые можешь поиграть с друзьями и выяснить, кто из вас лучший🥇"
    await c.message.edit_text(txt, reply_markup=games_kb)


@router.callback_query(F.data == "back_to_games", flags=flags)
async def back_to_games_cmd(c: CQ, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    txt = "Тут находятся мини-игры, в которые можешь поиграть с друзьями и выяснить, кто из вас лучший🥇"
    await c.message.delete()
    await c.message.answer(txt, reply_markup=games_kb)


@router.callback_query(F.data == "luckystrike", flags=flags)
async def lucky_shot_cmd(c: CQ, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
    txt = "☘️ Удачный удар - это мини-игра, в которой ты делаешь 1 удар по воротам. Если забиваешь - получаешь одну рандомную карточку. Если не забиваешь - пробуешь еще через время"
    await c.message.edit_text(txt, reply_markup=lucky_shot_btn)


@router.callback_query(F.data == "hitls", flags=flags)
async def hit_lucky_shot_cmd(c: CQ, ssn, action_queue, bot):
    res = await lucky_shot(ssn, c.from_user.id, bot)
    if isinstance(res, int):
        time = await format_delay_text(res)
        txt = f"""
        🍀 Ты недавно пробовал проверить свою удачу!
        Приходи через {time} ⏱ или приобретай дополнительные удары!

        💰 3 удара - 125 руб
        💰 6 ударов - 235 руб
        💰 9 ударов (Повышенный шанс) - 350 руб

        Если у вас не получается оплатить, то оплату можно провести через нашего администратора - @fintsupport
        """
        await c.message.edit_text(dedent(txt), reply_markup=no_free_ls_btn)
    elif res == "no_cards":
        await c.answer("⚠️ Возникла ошибка! Попробуй позже")
    else:
        try:
            await c.message.delete()
        except Exception as error:
            logging.error(f"Del error | chat {c.from_user.id}\n{error}")

        await asyncio.sleep(4.5)
        card: CardItem = res[0]
        user: Player = res[1]
        if card == "lose":
            if user.lucky_quants > 0:
                txt = f"☘️ Ты испытал удачу и сейчас тебе не повезло😔\n Количество оставшихся попыток - {user.lucky_quants}"
                await c.message.answer(txt, reply_markup=lucky_shot_btn)
            else:
                txt = f"☘️ Ты испытал удачу и сейчас тебе не повезло😔\nПопробуй еще раз через 6 часов или получи 3 удара за 125 рублей!"
                await c.message.answer(txt, reply_markup=no_free_ls_btn)
        else:
            txt = "☘️ Ты испытал удачу и выиграл одну случайную карточку!\n\n"
            card_txt = await format_new_free_card_text(card)
            await c.message.answer_photo(
                card.image, txt + card_txt, reply_markup=accept_new_card_btn)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
