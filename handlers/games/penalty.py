import asyncio
import logging
from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.models import Penalty, Player
from db.queries.penalty_queries import (cancel_pen_queue, cancel_penalty,
                                        check_for_active_penalty,
                                        create_new_penalty, find_penalty_opp,
                                        get_user_penalty_info, keeper_action,
                                        kicker_action, penalty_switch,
                                        start_penalty, get_penalty_access_user)
from keyboards.games_kbs import (after_penalty_kb, cancel_penalty_queue_btn,
                                 draw_penalty_kb, games_kb, penalty_kind_kb,
                                 penalty_opp_kb, to_games_btn)
from keyboards.main_kbs import to_main_btn
from middlewares.actions import ActionMiddleware
from utils.format_texts import (format_penalty_final_result_text,
                                format_penalty_round_result_text)
from utils.scheduled import check_penalty_timer
from utils.states import UserStates
from sqlalchemy import select

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "penalty", flags=flags)
async def penalty_cmd(c: CQ, action_queue, ssn):
    access_status: str = await get_penalty_access_user(ssn, c.from_user.id)
    if access_status == "not":
        try:
            del action_queue[str(c.from_user.id)]
        except Exception as error:
            logging.info(f"Action delete error\n{error}")
        await c.answer("Вам заблокирован доступ к пенальти", show_alert=True)
    else:
        res = await get_user_penalty_info(ssn, c.from_user.id)
        try:
            del action_queue[str(c.from_user.id)]
        except Exception as error:
            logging.info(f"Action delete error\n{error}")

        user: Player = res[0]
        txt = f"""
        ⚽️Статистика игр:
        🟢 Побед: {user.pen_wins}
        🔴 Поражений: {user.pen_loses}
        📈 Процент побед: {0 if user.pen_wins == 0 else int(user.pen_wins / (user.pen_wins + user.pen_loses) * 100)}%
        🏆 Место в сезонном рейтинге: {res[1]}
        📊 Сезонный рейтинг: {user.season_penalty} 
    
        👇Выберите формат игры
        """
        await c.message.edit_text(dedent(txt), reply_markup=penalty_kind_kb)


@router.callback_query(F.data == "pengame_rating", flags=flags)
async def rating_pen_game_cmd(c: CQ, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    txt = "⚽️ Выберите соперника"
    await c.message.edit_text(txt, reply_markup=penalty_opp_kb)


@router.callback_query(F.data == "penopp_target", flags=flags)
async def target_pen_game_cmd(c: CQ, action_queue, state: FSM, ssn):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    res = await check_for_active_penalty(ssn, c.from_user.id)
    if res == "already_playing":
        txt = "Вы уже состоите в игре, закончите ее, чтобы начать следующую"
        await c.message.edit_text(txt, reply_markup=to_games_btn)
    elif res == "already_duel_playing":
        txt = "Вы не можете сыграть в пенальти, так как не завершили игру в дуэли"
        await c.message.edit_text(txt, reply_markup=to_games_btn)
    else:
        txt = "✉️ Напишите @username пользователя, которому хотите предложить игру в Пенальти"
        await c.message.edit_text(txt, reply_markup=to_games_btn)
        await state.set_state(UserStates.target_penalty)


@router.callback_query(F.data == "penopp_random", flags=flags)
async def random_pen_game_cmd(c: CQ, action_queue, ssn, bot, db):
    res = await find_penalty_opp(ssn, c.from_user.id, bot)
    if res == "already_playing":
        txt = "Вы уже состоите в игре, закончите ее, чтобы начать следующую"
        await c.message.edit_text(txt, reply_markup=to_games_btn)
    elif res == "already_duel_playing":
        txt = "Вы не можете сыграть в пенальти, так как не завершили игру в дуэли"
        await c.message.edit_text(txt, reply_markup=to_games_btn)
    elif res == "error":
        txt = "Возникла ошибка! Попробуйте снова"
        await c.message.edit_text(txt, reply_markup=to_games_btn)
    elif res == "queue_on":
        txt = "🔍 Ищем соперника..."
        await c.message.edit_text(txt, reply_markup=cancel_penalty_queue_btn)
    else:
        txt = f"📩Ваш соперник - {res[2]}!\nОжидание ответа от соперника"
        await c.message.edit_text(txt)
        asyncio.create_task(check_penalty_timer(db, res[0], res[1], 60, bot))
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data == "penqueuecancel", flags=flags)
async def cancel_pen_queue_cmd(c: CQ, action_queue, ssn):
    await cancel_pen_queue(ssn, c.from_user.id)
    txt = "Тут находятся мини-игры, в которые можешь поиграть с друзьями и выяснить, кто из вас лучший🥇"
    await c.message.edit_text(txt, reply_markup=games_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.message(StateFilter(UserStates.target_penalty), F.text, flags=flags)
async def save_target_penalty_username_cmd(m: Mes, state: FSM, ssn, bot: Bot, db):
    await state.clear()

    target = m.text

    if m.from_user.username:
        username = f"@{m.from_user.username}"
    else:
        username = m.from_user.mention_html()

    res = await create_new_penalty(ssn, m.from_user.id, username, target, bot)
    if res == "already_playing":
        txt = "Вы уже состоите в игре, закончите ее, чтобы начать следующую"
        await m.answer(txt, reply_markup=to_games_btn)
    elif res == "already_duel_playing":
        txt = "Вы не можете сыграть в пенальти, так как не завершили игру в дуэли"
        await m.answer(txt, reply_markup=to_games_btn)
    elif res == "rating_diff":
        txt = f"Ты не можешь сыграть в пенальти с {target} из-за большой разницы в рейтинге☹️"
        await m.answer(txt, reply_markup=to_main_btn)
    elif res == "rating_diff":
        txt = f"Этому пользователю нельзя предложить игру в Пенальти ☹️\nОн уже находится в игре, дождитесь конца или предложите игру кому-нибудь другому"
        await m.answer(txt, reply_markup=to_main_btn)
    elif res == "self_error":
        txt = f"Нельзя играть с самим собой ☹️"
        await m.answer(txt, reply_markup=to_main_btn)
    elif res in ("not_found", "error"):
        txt = "Этому пользователю нельзя отправить предложение сыграть, попробуйте снова"
        await m.answer(txt, reply_markup=to_main_btn)
    else:
        txt = f"📩Ваше предложение сыграть в Пенальти было отправлено {target}!"
        await m.answer(txt)
        asyncio.create_task(check_penalty_timer(db, res[0], res[1], 60, bot))


@router.callback_query(F.data.startswith("pencancel_"), flags=flags)
async def decline_penalty_cmd(c: CQ, ssn, bot: Bot, action_queue):
    pen_id = int(c.data.split("_")[-1])

    penalty = await cancel_penalty(ssn, pen_id)
    await c.message.delete()
    await c.message.answer(
        "❌ Вы отклонили игру в пенальти", reply_markup=to_main_btn)

    if penalty != "not_active":
        if penalty.target == c.from_user.id:
            await bot.send_message(
                penalty.owner, f"❌ {penalty.target_username} отклонил предложение игры",
                reply_markup=to_main_btn)
        else:
            await bot.send_message(
                penalty.target, f"❌ {penalty.owner_username} отклонил встречное предложение игры",
                reply_markup=to_main_btn)
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("penstart_"), flags=flags)
async def start_penalty_cmd(c: CQ, ssn, bot: Bot, action_queue, db):
    pen_id = int(c.data.split("_")[-1])
    await c.message.delete_reply_markup()

    res = await start_penalty(ssn, pen_id, bot)
    if res in ("not_active", "error", "already_duel_playing"):
        await c.message.answer(
            "❌ Эта игра больше недоступна", reply_markup=to_main_btn)
    asyncio.create_task(check_penalty_timer(db, pen_id, res, 60, bot))

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("pnactn_kicker"), flags=flags)
async def kicker_penalty_cmd(c: CQ, ssn, action_queue, db, bot):
    data = c.data.split("_")
    pen_id = int(data[2])
    corner = int(data[3])

    res = await kicker_action(ssn, pen_id, c.from_user.id, corner)
    if res == "not_active":
        await c.message.delete()
        await c.message.answer(
            "❌ Эта игра больше недоступна", reply_markup=to_main_btn)
    else:
        txt = f"Ваш выбор - {corner}\nОжидайте хода второго игрока"
        await c.message.edit_caption(caption=txt)
        asyncio.create_task(check_penalty_timer(
            db, pen_id, res[0], res[1], bot))
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("pnactn_keeper"), flags=flags)
async def keeper_penalty_cmd(c: CQ, ssn, bot: Bot, action_queue, db):
    data = c.data.split("_")
    pen_id = int(data[2])
    corner = int(data[3])

    res = await keeper_action(ssn, pen_id, c.from_user.id, corner)
    if res == "not_active":
        await c.message.delete()
        await c.message.answer(
            "❌ Эта игра больше недоступна", reply_markup=to_main_btn)
    elif res == "not_ready":
        await c.answer("Твой соперник еще не сделал удар.", show_alert=True)
    else:
        penalty: Penalty = res[0]
        txt = f"Ваш выбор - {corner}"
        await c.message.edit_caption(caption=txt)

        if penalty.status == "finished":
            if penalty.winner == 0:
                keyboard = draw_penalty_kb
            else:
                keyboard = after_penalty_kb

            txt = await format_penalty_final_result_text(res[0])
            await c.message.answer(txt, reply_markup=keyboard)

            await bot.send_message(penalty.kicker, txt, reply_markup=keyboard)

        else:
            asyncio.create_task(check_penalty_timer(
                db, pen_id, res[2], res[3], bot))
            texts = await format_penalty_round_result_text(res[0], res[1])

            await c.message.answer(texts[0])
            await asyncio.sleep(.01)

            await bot.send_message(penalty.keeper, texts[1])

            await asyncio.sleep(.01)
            await penalty_switch(ssn, pen_id, res[2], bot)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
