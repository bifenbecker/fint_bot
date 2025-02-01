import asyncio
import logging
from textwrap import dedent

from aiogram import F, Router
from aiogram.types import CallbackQuery as CQ

from db.models import PackBattle
from db.queries.pack_battle_qs import (battle_user_ready,
                                       get_active_pack_battle_lobbies,
                                       update_owner_battle_msg_id,
                                       update_target_battle_msg_id)
from keyboards.packs_kb import (opp_battle_kb, pack_battle_kb,
                                pack_battle_lobbies_kb)
from middlewares.actions import ActionMiddleware
from utils.duel_misc import (check_battle_timer, resent_battle_lobby_info,
                             send_battle_finish_messages)

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "packbattle", flags=flags)
async def pack_battle_cmd(c: CQ, action_queue):
    txt = """
    ⚖️ В битве паков ты ставишь свои паки на кон против других игроков.

    За победу ты получаешь карты противника, которые он достал из пака.
    За поражение - теряешь свои, которые он достал из пака.

    Ты можешь либо создать свое лобби, либо войти в лобби другого игрока
    """
    await c.message.edit_text(dedent(txt), reply_markup=pack_battle_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data == "packbattlelobbies", flags=flags)
async def pack_battle_rooms_cmd(c: CQ, ssn, action_queue):
    battles = await get_active_pack_battle_lobbies(ssn)
    if len(battles) > 0:
        txt = "🎪 Список активных лобби:"
        await c.message.edit_text(
            txt, reply_markup=pack_battle_lobbies_kb(battles))
    else:
        await c.answer(
            "В данный момент нет активных лобби", show_alert=True)
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("rdypbttl_"), flags=flags)
async def pack_battle_ready_cmd(c: CQ, action_queue, ssn, bot, db):
    battle_id = int(c.data.split("_")[-1])
    res = await battle_user_ready(ssn, c.from_user.id, battle_id)
    if res == "not_available":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=pack_battle_kb)
    elif res == "already_ready":
        await c.answer("Вы уже подтвердили готовность!")
    else:
        if res[1] == "not_ready":
            battle: PackBattle = res[0]
            txt = f"""
            🎪 Ваше лобби:

            Пак на текущую дуэль: {"Легендарный пак" if battle.quant == 0 else f"{battle.quant} карт"}
            🟣 {battle.owner_username}
            🟠 {battle.target_username}
            """
            if res[0].owner == c.from_user.id:
                await c.message.edit_reply_markup(
                    reply_markup=opp_battle_kb(battle_id, "owner", 1))
                msg_id = await resent_battle_lobby_info(
                    bot, battle, "target", dedent(txt),
                    opp_battle_kb(battle_id, "target", 1))
                await update_target_battle_msg_id(ssn, battle_id, msg_id)
            else:
                await c.message.edit_reply_markup(
                    reply_markup=opp_battle_kb(battle_id, "target", 1))
                msg_id = await resent_battle_lobby_info(
                    bot, res[0], "owner", dedent(txt),
                    opp_battle_kb(battle_id, "owner", 1))
                await update_owner_battle_msg_id(ssn, battle_id, msg_id)
                asyncio.create_task(check_battle_timer(
                    db, bot, battle_id, "owner", res[0].owner, res[0].owner_ts, 60))
        else:
            await send_battle_finish_messages(res[0], bot, res[2], res[3])

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
