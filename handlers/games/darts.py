import asyncio
import logging
from textwrap import dedent

from aiogram import F, Router
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ

from db.models import CardItem, Games
from db.queries.games_queries import hit_darts
from keyboards.games_kbs import darts_kb, no_free_darts_kb
from keyboards.pay_kbs import cards_pack_btn, player_pick_kb
from middlewares.actions import ActionMiddleware
from utils.format_texts import format_view_my_cards_text
from utils.misc import format_delay_text
from utils.states import UserStates

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "darts", flags=flags)
async def darts_cmd(c: CQ, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    txt = """
    Готов ли ты проверить свою меткость и получить приз? 
    Раз в 4 дня ты можешь сделать это бесплатно, за отдельную плату ты можешь получить дополнительные попытки
    При попадании в центр - выдается 3 карты
    Цена 3 попыток 150 руб
    """
    await c.message.edit_text(dedent(txt), reply_markup=darts_kb)


@router.callback_query(F.data == "hitdarts", flags=flags)
async def hit_darts_cmd(c: CQ, ssn, action_queue, bot, state: FSM):
    res = await hit_darts(ssn, c.from_user.id, bot)
    if isinstance(res, int):
        time = await format_delay_text(res)
        txt = f"""
        Ты недавно пробовал проверить свою удачу!
        Приходи через {time} ⏱ или приобретай дополнительные броски!

        Если у вас не получается оплатить, то оплату можно провести через нашего администратора - @fintsupport
        """
        await c.message.edit_text(dedent(txt), reply_markup=no_free_darts_kb)
    else:
        try:
            await c.message.delete()
        except Exception as error:
            logging.error(f"Del error | chat {c.from_user.id}\n{error}")

        await asyncio.sleep(4)
        if res[0] == "win":
            pack_id = res[1]
            txt = "🎯 В яблочко!. Теперь ты можешь посмотреть полученные карты"
            await c.message.answer(txt, reply_markup=cards_pack_btn(pack_id))

        else:
            txt = "В этот раз ☘️ удача не на твоей стороне, но ты можешь испытать ее еще раз"
            game: Games = res[1]
            if (game.free_quant < 1) and (game.attempts < 1):
                await c.message.answer(txt, reply_markup=no_free_darts_kb)
            else:
                await c.message.answer(txt, reply_markup=darts_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data == "buydarts", flags=flags)
async def buy_darts_menu(c: CQ, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    await c.message.edit_reply_markup(reply_markup=no_free_darts_kb)
