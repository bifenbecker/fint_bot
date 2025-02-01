import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import Message as Mes
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Games, Player
from db.queries.admin_queries import ban_user
from filters.filters import IsAdmin

flags = {"throttling_key": "default"}
router = Router()


@router.message(Command("ban"), IsAdmin(), flags=flags)
async def ban_cmd(m: Mes, state: FSM, ssn, banned: list):
    await state.clear()

    m_data = m.text.split()
    if len(m_data) != 2:
        await m.reply("⚠️ Команда должна иметь вид /ban @username или ID")
    else:
        res = await ban_user(ssn, m_data[1], "banned")
        if res == "not_found":
            await m.reply("⚠️ Такой пользователь не найден")
        else:
            banned.append(res)
            logging.info(f"Admin {m.from_user.id} banned user {res}")
            await m.reply("✅ Пользователь забанен")


@router.message(Command("unban"), IsAdmin(), flags=flags)
async def ban_cmd(m: Mes, state: FSM, ssn, banned: list):
    await state.clear()

    m_data = m.text.split()
    if len(m_data) != 2:
        await m.reply("⚠️ Команда должна иметь вид /unban @username или ID")
    else:
        res = await ban_user(ssn, m_data[1], "not_banned")
        if res == "not_found":
            await m.reply("⚠️ Такой пользователь не найден")
        else:
            if res in banned:
                banned.remove(res)

            logging.info(f"Admin {m.from_user.id} unbanned user {res}")
            await m.reply("✅ Пользователь разбанен")


# Добавление удачных ударов пользователю
@router.message(Command("addluckyshot"), IsAdmin(), flags=flags)
async def add_lucky_shot_cmd(m: Mes, state: FSM, ssn):
    await state.clear()
    try:
        m_data = m.text.split()
        if len(m_data) != 3:
            await m.reply(
                "⚠️ Команда должна иметь вид /addluckyshot @username(или ID) Количество"
            )
        else:
            res = await add_lucky_shot(ssn, m_data[1], m_data[2])
            if res == "not_found":
                await m.reply("⚠️ Такой пользователь не найден")
            else:
                logging.info(
                    f"Admin {m.from_user.id} added {m_data[2]} good hits to the user {res}"
                )
                await m.reply(
                    f"✅ Пользователю {m_data[1]} было начислено {m_data[2]} удачных ударов"
                )
    except Exception as e:
        print(e)


# Вычитание удачных ударов пользователю
@router.message(Command("subtractluckyshot"), IsAdmin(), flags=flags)
async def subtract_lucky_shot_cmd(m: Mes, state: FSM, ssn):
    await state.clear()

    m_data = m.text.split()
    if len(m_data) != 3:
        await m.reply(
            "⚠️ Команда должна иметь вид /subtractluckyshot @username(или ID) Количество"
        )
    else:
        res = await subtract_lucky_shot(ssn, m_data[1], m_data[2])
        if res == "not_found":
            await m.reply("⚠️ Такой пользователь не найден")
        else:
            logging.info(
                f"Admin {m.from_user.id} subtract {res[1]} good hits from user {res[0]}"
            )
            await m.reply(
                f"✅ У пользователя {m_data[1]} было вычтено {res[1]} удачных ударов"
            )


@router.message(Command("adddarts"), IsAdmin(), flags=flags)
async def add_darts_cmd(m: Mes, state: FSM, ssn):
    await state.clear()
    try:
        m_data = m.text.split()
        if len(m_data) != 3:
            await m.reply(
                "⚠️ Команда должна иметь вид /adddarts @username(или ID) Количество"
            )
        else:
            res = await add_darts(ssn, m_data[1], m_data[2])
            if res == "not_found":
                await m.reply("⚠️ Такой пользователь не найден")
            else:
                logging.info(
                    f"Admin {m.from_user.id} added {m_data[2]} good hits to the user {res}"
                )
                await m.reply(
                    f"✅ Пользователю {m_data[1]} было начислено {m_data[2]} бросков дартс"
                )
    except Exception as e:
        print(e)


@router.message(Command("subtractdarts"), IsAdmin(), flags=flags)
async def subtract_darts_cmd(m: Mes, state: FSM, ssn):
    await state.clear()

    m_data = m.text.split()
    if len(m_data) != 3:
        await m.reply(
            "⚠️ Команда должна иметь вид /subtractdarts @username(или ID) Количество"
        )
    else:
        res = await subtract_darts(ssn, m_data[1], m_data[2])
        if res == "not_found":
            await m.reply("⚠️ Такой пользователь не найден")
        else:
            logging.info(
                f"Admin {m.from_user.id} subtract {res[1]} good hits from user {res[0]}"
            )
            await m.reply(
                f"✅ У пользователя {m_data[1]} было вычтено {res[1]} бросков дартс"
            )


# Ограничение обмена картами пользователю
@router.message(Command("bantpd"), IsAdmin(), flags=flags)
async def ban_trade_cmd(m: Mes, state: FSM, ssn):
    await state.clear()

    m_data = m.text.split()
    if len(m_data) != 2:
        await m.reply("⚠️ Команда должна иметь вид /bantpd @username(или ID)")
    else:
        res = await update_access_tpd(ssn, m_data[1], "not")
        if res == "not_found":
            await m.reply("⚠️ Такой пользователь не найден")
        else:
            logging.info(
                f"Admin {m.from_user.id} has restricted access trade, penalty, duel to user {res}"
            )
            await m.reply(
                f"✅ Пользователю {m_data[1]} было ограничен доступ к обмену, пенальти."
            )


# Доступ обмена картами пользователю
@router.message(Command("unbantpd"), IsAdmin(), flags=flags)
async def unban_trade_cmd(m: Mes, state: FSM, ssn):
    await state.clear()

    m_data = m.text.split()
    if len(m_data) != 2:
        await m.reply("⚠️ Команда должна иметь вид /unbantpd @username(или ID)")
    else:
        res = await update_access_tpd(ssn, m_data[1], "yes")
        if res == "not_found":
            await m.reply("⚠️ Такой пользователь не найден")
        else:
            logging.info(
                f"Admin {m.from_user.id} has given access trade, penalty, duel to user {res}"
            )
            await m.reply(
                f"✅ Пользователю {m_data[1]} было дан доступ к обмену, пенальти, дуэлям"
            )


# Добавляет удачные удары


async def add_lucky_shot(ssn: AsyncSession, username, quants):
    if username.isdigit():
        user_q = await ssn.execute(select(Player).filter(Player.id == int(username)))
        user_res = user_q.fetchone()
    else:
        user_q = await ssn.execute(
            select(Player).filter(Player.username.ilike(username))
        )
        user_res = user_q.fetchone()

    if user_res is None:
        return "not_found"

    user_id = user_res[0].id
    await ssn.execute(
        update(Player)
        .filter(Player.id == user_id)
        .values(
            lucky_quants=Player.lucky_quants + int(quants),
            lucky_shots_plus=Player.lucky_shots_plus + int(quants),
        )
    )
    await ssn.commit()

    return user_id


# Вычитает удачные удары


async def subtract_lucky_shot(ssn: AsyncSession, username, quants):
    if username.isdigit():
        user_q = await ssn.execute(select(Player).filter(Player.id == int(username)))
        user_res = user_q.fetchone()
    else:
        user_q = await ssn.execute(
            select(Player).filter(Player.username.ilike(username))
        )
        user_res = user_q.fetchone()

    if user_res is None:
        return "not_found"

    user = user_res[0]

    quants = int(quants)

    if user.lucky_quants - quants < 0:
        actual_subtracted = user.lucky_quants
        await ssn.execute(
            update(Player)
            .filter(Player.id == user.id)
            .values(
                lucky_quants=0,
                lucky_shots_plus=0,
            )
        )
        await ssn.commit()
        return user.id, actual_subtracted

    await ssn.execute(
        update(Player)
        .filter(Player.id == user.id)
        .values(
            lucky_quants=Player.lucky_quants - quants,
            lucky_shots_plus=Player.lucky_shots_plus - quants,
        )
    )
    await ssn.commit()

    return user.id, quants


# Обновляет доступ к минииграм


async def update_access_tpd(ssn: AsyncSession, username, status):
    try:
        if username.isdigit():
            user_q = await ssn.execute(
                select(Player).filter(Player.id == int(username))
            )
            user_res = user_q.fetchone()
        else:
            user_q = await ssn.execute(
                select(Player).filter(Player.username.ilike(username))
            )
            user_res = user_q.fetchone()

        if user_res is None:
            return "not_found"

        user_id = user_res[0].id
        await ssn.execute(
            update(Player).filter(Player.id == user_id).values(access_minigame=status)
        )
        await ssn.commit()

        return user_id
    except Exception as e:
        print(e)


async def add_darts(ssn: AsyncSession, username, quants):
    if username.isdigit():
        user_q = await ssn.execute(select(Player).filter(Player.id == int(username)))
        user_res = user_q.fetchone()
    else:
        user_q = await ssn.execute(
            select(Player).filter(Player.username.ilike(username))
        )
        user_res = user_q.fetchone()

    if user_res is None:
        return "not_found"

    user_id = user_res[0].id
    await ssn.execute(
        update(Games)
        .filter(
            Games.user_id == user_id,
            Games.kind == "darts",
        )
        .values(free_quant=Games.free_quant + int(quants))
    )
    await ssn.commit()

    return user_id


async def subtract_darts(ssn: AsyncSession, username, quants):
    if username.isdigit():
        user_q = await ssn.execute(select(Player).filter(Player.id == int(username)))
        user_res = user_q.fetchone()
    else:
        user_q = await ssn.execute(
            select(Player).filter(Player.username.ilike(username))
        )
        user_res = user_q.fetchone()

    if user_res is None:
        return "not_found"

    user = user_res[0]
    game_q = await ssn.execute(
        select(Games).filter(Games.user_id == user.id, Games.kind == "darts")
    )
    game = game_q.fetchone()[0]
    quants = int(quants)

    if game.free_quant - quants < 0:
        actual_subtracted = game.free_quant
        await ssn.execute(
            update(Games)
            .filter(Games.user_id == user.id, Games.kind == "darts")
            .values(free_quant=0)
        )
        await ssn.commit()
        return user.id, actual_subtracted

    await ssn.execute(
        update(Games)
        .filter(Games.user_id == user.id, Games.kind == "darts")
        .values(free_quant=Games.free_quant - quants)
    )
    await ssn.commit()

    return user.id, quants


# ____________________________________________________


@router.message(Command("addcasino"), IsAdmin(), flags=flags)
async def add_darts_cmd(m: Mes, state: FSM, ssn):
    await state.clear()
    try:
        m_data = m.text.split()
        if len(m_data) != 3:
            await m.reply(
                "⚠️ Команда должна иметь вид /addcasino @username(или ID) Количество"
            )
        else:
            res = await add_attempts_casino(ssn, m_data[1], m_data[2])
            if res == "not_found":
                await m.reply("⚠️ Такой пользователь не найден")
            else:
                logging.info(
                    f"Admin {m.from_user.id} added {m_data[2]} good hits to the user {res}"
                )
                await m.reply(
                    f"✅ Пользователю {m_data[1]} было начислено {m_data[2]} попыток в казино"
                )
    except Exception as e:
        print(e)


@router.message(Command("subtractcasino"), IsAdmin(), flags=flags)
async def subtract_darts_cmd(m: Mes, state: FSM, ssn):
    await state.clear()

    m_data = m.text.split()
    if len(m_data) != 3:
        await m.reply(
            "⚠️ Команда должна иметь вид /subtractcasino @username(или ID) Количество"
        )
    else:
        res = await subtract_attempts_casino(ssn, m_data[1], m_data[2])
        if res == "not_found":
            await m.reply("⚠️ Такой пользователь не найден")
        else:
            logging.info(
                f"Admin {m.from_user.id} subtract {res[1]} good hits from user {res[0]}"
            )
            await m.reply(
                f"✅ У пользователя {m_data[1]} было вычтено {res[1]} попыток в казино"
            )


async def add_attempts_casino(ssn: AsyncSession, username, quants):
    if username.isdigit():
        user_q = await ssn.execute(select(Player).filter(Player.id == int(username)))
        user_res = user_q.fetchone()
    else:
        user_q = await ssn.execute(
            select(Player).filter(Player.username.ilike(username))
        )
        user_res = user_q.fetchone()

    if user_res is None:
        return "not_found"

    user_id = user_res[0].id
    await ssn.execute(
        update(Games)
        .filter(
            Games.user_id == user_id,
            Games.kind == "casino",
        )
        .values(attempts=Games.attempts + int(quants))
    )
    await ssn.commit()

    return user_id


async def subtract_attempts_casino(ssn: AsyncSession, username, quants):
    if username.isdigit():
        user_q = await ssn.execute(select(Player).filter(Player.id == int(username)))
        user_res = user_q.fetchone()
    else:
        user_q = await ssn.execute(
            select(Player).filter(Player.username.ilike(username))
        )
        user_res = user_q.fetchone()

    if user_res is None:
        return "not_found"

    user = user_res[0]
    game_q = await ssn.execute(
        select(Games).filter(Games.user_id == user.id, Games.kind == "casino")
    )
    game = game_q.fetchone()[0]
    quants = int(quants)

    if game.attempts - quants < 0:
        actual_subtracted = game.attempts
        await ssn.execute(
            update(Games)
            .filter(Games.user_id == user.id, Games.kind == "casino")
            .values(attempts=0)
        )
        await ssn.commit()
        return user.id, actual_subtracted

    await ssn.execute(
        update(Games)
        .filter(Games.user_id == user.id, Games.kind == "casino")
        .values(attempts=Games.attempts - quants)
    )
    await ssn.commit()

    return user.id, quants
