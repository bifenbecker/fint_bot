import asyncio
import datetime
import logging
from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery as CQ

from db.models import PackBattle, Player
from db.queries.pack_battle_qs import (
    join_pack_battle,
    target_card_battle_cancel,
    update_owner_battle_msg_id,
)
from keyboards.main_kbs import main_kb, to_main_btn
from keyboards.packs_kb import no_opp_battle_kb, opp_battle_kb
from middlewares.actions import ActionMiddleware
from utils.duel_misc import check_battle_timer, resent_battle_lobby_info

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data.startswith("joinpbttl_"), flags=flags)
async def join_pack_battle_cmd(c: CQ, action_queue, ssn, bot: Bot, db):
    battle_id = int(c.data.split("_")[-1])

    if c.from_user.username:
        username = f"@{c.from_user.username}"
    else:
        username = c.from_user.mention_html()

    battle: PackBattle = await join_pack_battle(
        ssn, c.from_user.id, username, battle_id, c.message.message_id
    )
    if battle == "already_battle_playing":
        txt = "Вы не можете участвовать в битве, так как не завершили предыдущую битву паков"
        await c.answer(txt, show_alert=True)
    elif battle == "not_available":
        txt = "Это лобби больше недоступно"
        await c.answer(txt, show_alert=True)
    elif battle == "no_packs":
        txt = "У вас нет этого пака, чтобы поставить его на кон"
        await c.answer(txt, show_alert=True)
    else:
        logging.info(f"User {c.from_user.id} joined pack battle {battle_id}")
        txt = f"""
        🎪 Ваше лобби:

        Пак на текущую дуэль: {"Легендарный пак" if battle.quant == 0 else f"{battle.quant} карт"}
        🟣 {battle.owner_username}
        🟠 {battle.target_username}
        """
        await c.message.edit_text(
            dedent(txt), reply_markup=opp_battle_kb(battle_id, "target", 0)
        )

        try:
            await bot.send_message(battle.owner, "🟠 Соперник зашел в лобби!")
        except Exception as error:
            logging.error(f"Send error | chat {battle.owner}\n{error}")

        msg_id = await resent_battle_lobby_info(
            bot, battle, "owner", dedent(txt), opp_battle_kb(battle_id, "owner", 0)
        )
        await update_owner_battle_msg_id(ssn, battle_id, msg_id)
        asyncio.create_task(
            check_battle_timer(
                db, bot, battle_id, "target", c.from_user.id, battle.target_ts, 60
            )
        )
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("targetcancelpbttl_"), flags=flags)
async def target_pack_battle_cancel_cmd(c: CQ, ssn, bot: Bot, action_queue):
    battle_id = int(c.data.split("_")[-1])
    res = await target_card_battle_cancel(ssn, battle_id, c.from_user.id)
    if res == "not_active":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=to_main_btn)
    else:
        user: Player = res[1]
        date = datetime.datetime.now()
        date_ts = int(date.timestamp())
        txt = f"""
        Твои достижения:

        👀 Дней в игре: {(date_ts - user.joined_at_ts) // 86400}

        🃏 Собранное количество карточек: {user.card_quants}
        🏆 Рейтинг собранных карточек: {user.rating}
        🧩 Сезонный рейтинг коллекционера: {user.season_rating}

        ⚽️ Рейтинг в игре Пенальти: {user.penalty_rating}
        🏵 Сезонный рейтинг по Пенальти: {user.season_penalty}
        """

        await c.message.edit_text(dedent(txt), reply_markup=main_kb)

        battle = res[0]
        owner_txt = f"""
        🎪 Ваше лобби:

        🟣 {battle.owner_username}

        Статус лобби - Ожидание соперника
        """
        msg_id = await resent_battle_lobby_info(
            bot, battle, "owner", dedent(owner_txt), no_opp_battle_kb(battle_id)
        )
        await update_owner_battle_msg_id(ssn, battle_id, msg_id)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
