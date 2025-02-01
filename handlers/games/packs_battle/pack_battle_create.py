import logging
from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery as CQ

from db.queries.pack_battle_qs import (
    check_for_pack_battle_available,
    create_default_pack_battle,
    create_leg_pack_battle,
    owner_card_battle_cancel,
)
from keyboards.main_kbs import to_main_btn
from keyboards.packs_kb import create_pack_battle_kb, no_opp_battle_kb, pack_battle_kb
from middlewares.actions import ActionMiddleware

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "packbattlecreate", flags=flags)
async def create_duel_cmd(c: CQ, action_queue, ssn):
    res = await check_for_pack_battle_available(ssn, c.from_user.id)
    if res == "already_battle_playing":
        txt = "Вы не можете участвовать в битве, так как не завершили предыдущую битву паков"
        await c.answer(txt, show_alert=True)
    elif res == "no_packs":
        txt = "У вас нет ниодного пака, чтобы поставить его на кон"
        await c.answer(txt, show_alert=True)
    else:
        txt = "🃏 Выберите пак, на который хотите сыграть"
        await c.message.edit_text(txt, reply_markup=create_pack_battle_kb(res))

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("crtpbttl_"), flags=flags)
async def pack_selected_cmd(c: CQ, action_queue, ssn):
    quant = c.data.split("_")[-1]

    if c.from_user.username:
        username = f"@{c.from_user.username}"
    else:
        username = c.from_user.mention_html()

    if quant == "leg":
        res = await create_leg_pack_battle(
            ssn, c.from_user.id, c.message.message_id, username
        )
    else:
        res = await create_default_pack_battle(
            ssn, c.from_user.id, c.message.message_id, username, int(quant)
        )

    if res == "already_battle_playing":
        txt = "Вы не можете участвовать в битве, так как не завершили предыдущую битву паков"
        await c.answer(txt, show_alert=True)
    elif res == "no_packs":
        txt = "У вас нет этого пака, чтобы поставить его на кон"
        await c.answer(txt, show_alert=True)
    else:
        txt = f"""
        🎪 Ваше лобби создано:

        Пак на текущую дуэль: {"Легендарный пак" if quant == "leg" else f"{quant} карт"}
        🟣 {res.owner_username}

        Статус лобби - Ожидание соперника
        """
        await c.message.edit_text(dedent(txt), reply_markup=no_opp_battle_kb(res.id))

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("ownrcancelpbttl_"), flags=flags)
async def owner_pack_battle_cancel_cmd(c: CQ, ssn, bot: Bot, action_queue):
    battle_id = int(c.data.split("_")[-1])
    battle = await owner_card_battle_cancel(ssn, battle_id)
    if battle == "not_active":
        txt = "Возникла ошибка! Попробуйте позже"
        await c.message.edit_text(txt, reply_markup=to_main_btn)
    else:
        await c.message.edit_text(
            "🎪 Текущее лобби удалено", reply_markup=pack_battle_kb
        )
        if battle.target != 0:
            try:
                await bot.delete_message(battle.target, battle.target_msg_id)
            except Exception as error:
                logging.info(f"Delete error | chat {battle.target}\n{error}")
            try:
                await bot.send_message(
                    battle.target,
                    "🎪 Текущее лобби удалено",
                    reply_markup=pack_battle_kb,
                )
            except Exception as error:
                logging.info(f"Send error | chat {battle.target}\n{error}")

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
