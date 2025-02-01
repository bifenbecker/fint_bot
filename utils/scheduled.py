import asyncio
import datetime as dt
import logging

from aiogram import Bot

from db.models import Games, Penalty, Player
from db.queries.penalty_queries import check_penalty, get_active_penalties
from db.queries.scheduled_queries import (
    check_trade_count,
    clear_user_trade_table,
    get_free_card_notity_users,
    remove_premium_from_users,
)
from keyboards.games_kbs import after_penalty_kb
from keyboards.main_kbs import to_main_btn
from keyboards.scheduled_kbs import (
    scheduled_darts_btn,
    scheduled_freecard_btn,
    scheduled_ls_btn,
)


async def get_free_card_and_ls_notify(db, bot: Bot):
    date = dt.datetime.now()
    now_ts = int(date.timestamp())

    res = await get_free_card_notity_users(db, now_ts)

    if len(res[0]) > 0:
        f_user: Player
        for f_user in res[0]:
            delay = f_user.last_open - now_ts
            asyncio.create_task(send_free_card_notify(bot, f_user.id, delay))

    if len(res[1]) > 0:
        l_user: Player
        for l_user in res[1]:
            delay = l_user.last_lucky - now_ts
            asyncio.create_task(send_lucky_shot_notify(bot, l_user.id, delay))

    if len(res[2]) > 0:
        darts: Games
        for darts in res[2]:
            delay = darts.last_free - now_ts
            asyncio.create_task(send_darts_notify(bot, darts.id, delay))


async def reset_player_trade_count(db, bot):
    await check_trade_count(db)
    await clear_user_trade_table(db)


async def send_free_card_notify(bot: Bot, user_id, delay):
    await asyncio.sleep(delay)
    try:
        await bot.send_message(
            user_id,
            "Привет! Ты можешь забрать свою бесплатную карту! 🎁",
            reply_markup=scheduled_freecard_btn,
        )
    except Exception as error:
        logging.error(f"Send free card notify error | chat {user_id}\n{error}")


async def send_lucky_shot_notify(bot: Bot, user_id, delay):
    await asyncio.sleep(delay)
    try:
        await bot.send_message(
            user_id,
            "Привет! Ты можешь проверить свою удачу в удачном ударе! ☘️",
            reply_markup=scheduled_ls_btn,
        )
    except Exception as error:
        logging.error(f"Send lucky shot notify error | chat {user_id}\n{error}")


async def send_darts_notify(bot: Bot, user_id, delay):
    await asyncio.sleep(delay)
    try:
        await bot.send_message(
            user_id,
            "Привет! Ты можешь проверить свою удачу бросив дротик в игре Дартс! ☘️",
            reply_markup=scheduled_darts_btn,
        )
    except Exception as error:
        logging.error(f"Send lucky shot notify error | chat {user_id}\n{error}")


async def re_check_active_penalties(db, bot):
    date = dt.datetime.now()
    date_ts = int(date.timestamp())
    penalties = await get_active_penalties(db)
    if len(penalties) > 0:
        penalty: Penalty
        for num, penalty in enumerate(penalties):
            delay = penalty.last_action - date_ts
            if delay <= 0:
                delay = num + 1
            asyncio.create_task(
                check_penalty_timer(db, penalty.id, penalty.last_action, delay, bot)
            )
            await asyncio.sleep(0.001)


async def check_penalty_timer(db, penalty_id, date_ts, delay, bot: Bot):
    await asyncio.sleep(delay)
    penalty = await check_penalty(db, int(penalty_id), date_ts)
    if penalty:
        if penalty.kicker == penalty.keeper == 0:
            if penalty.target_card_id == 0:
                del_id = penalty.target
                del_msg_id = penalty.target_msg_id
                u_id = penalty.owner
            else:
                del_id = penalty.owner
                del_msg_id = penalty.owner_msg_id
                u_id = penalty.target

            try:
                await bot.delete_message(del_id, del_msg_id)
            except Exception as error:
                logging.error(f"Delete error | chat {del_id}\n{error}")

            await asyncio.sleep(0.2)

            txt = "К сожалению, ваш оппонент не принял игру за минуту"
            try:
                await bot.send_message(u_id, txt, reply_markup=to_main_btn)
            except Exception as error:
                logging.error(f"Send error | chat {u_id}\n{error}")

        else:
            try:
                await bot.delete_message(penalty.owner, penalty.owner_msg_id)
            except Exception as error:
                logging.error(f"Delete error | chat {penalty.owner}\n{error}")
            await asyncio.sleep(0.03)
            try:
                await bot.delete_message(penalty.target, penalty.target_msg_id)
            except Exception as error:
                logging.error(f"Delete error | chat {penalty.target}\n{error}")

            if penalty.turn_user_id == penalty.owner:
                owner_txt = "Тебя слишком долго не было в игре, поэтому тебе засчитано поражение"
                target_txt = f"Игрок {penalty.owner_username} слишком долго не отвечал, вы победили!"
            else:
                owner_txt = f"Игрок {penalty.target_username} слишком долго не отвечал, вы победили!"
                target_txt = "Тебя слишком долго не было в игре, поэтому тебе засчитано поражение"

            try:
                await bot.send_message(
                    penalty.owner, owner_txt, reply_markup=after_penalty_kb
                )
            except Exception as error:
                logging.error(f"Send error | chat {penalty.owner}\n{error}")

            await asyncio.sleep(0.2)

            try:
                await bot.send_message(
                    penalty.target, target_txt, reply_markup=after_penalty_kb
                )
            except Exception as error:
                logging.error(f"Send error | chat {penalty.target}\n{error}")


async def check_premiums(db, bot: Bot):
    date_ts = int(dt.datetime.now().timestamp()) + 30
    await remove_premium_from_users(db, date_ts)
