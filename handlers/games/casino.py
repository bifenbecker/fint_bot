import asyncio
import logging
from textwrap import dedent

from aiogram import F, Router
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ

from db.models import CardItem, Games
from db.queries.games_queries import hit_casino, hit_darts
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.games_kbs import buy_casino_kb, casino_kb, no_casino_kb
from keyboards.pay_kbs import player_pick_kb
from middlewares.actions import ActionMiddleware
from utils.format_texts import (format_new_free_card_text,
                                format_view_my_cards_text)
from utils.misc import format_delay_text
from utils.states import UserStates

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "casino", flags=flags)
async def casino_cmd(c: CQ, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    txt = """
    Добро пожаловать в мир казино. Здесь у тебя есть 3 попытки выбить одинаковые символы, самые удачные игроки получат карты высокой редкости (от Unique и выше) 
    Цена игры 150 руб
    """
    await c.message.edit_text(dedent(txt), reply_markup=casino_kb)


@router.callback_query(F.data == "hitcasino", flags=flags)
async def hit_hitcasino_cmd(c: CQ, ssn, action_queue, bot, state: FSM):
    res = await hit_casino(ssn, c.from_user.id, bot)
    if res == "no_attempts":
        txt = "Ты недавно пробовал проверить свою удачу! Для продолжения игры, нужно купить дополнительные попытки!"
        await c.message.edit_text(dedent(txt), reply_markup=no_casino_kb)
    else:
        try:
            await c.message.delete()
        except Exception as error:
            logging.error(f"Del error | chat {c.from_user.id}\n{error}")

        await asyncio.sleep(3)
        if res[0] == "win":
            card: CardItem = res[1]
            txt = await format_new_free_card_text(card)
            await c.message.answer_photo(
                card.image, txt, reply_markup=accept_new_card_btn)

        else:
            game: Games = res[1]
            if game.curr_casino > 0:
                txt = "Неудача! Попробуй еще"
                await c.message.answer(txt, reply_markup=casino_kb)
            else:
                txt = "Сегодня ☘️ удача не на твоей стороне, но ты можешь испытать ее еще раз"
                # if game.attempts < 1:
                await c.message.answer(txt, reply_markup=buy_casino_kb)
                # else:
                #     await c.message.answer(txt, reply_markup=casino_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data == "buycasino", flags=flags)
async def buy_casino_menu(c: CQ, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    await c.message.edit_reply_markup(reply_markup=no_casino_kb)
