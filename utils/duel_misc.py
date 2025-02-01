import asyncio
import datetime
import logging
from textwrap import dedent

from aiogram import Bot

from db.models import PackBattle
from db.queries.pack_battle_qs import (check_pack_battle, get_active_battles,
                                       update_owner_battle_msg_id_db)
from keyboards.main_kbs import to_main_btn
from keyboards.packs_kb import no_opp_battle_kb, pack_battle_kb
from keyboards.pay_kbs import cards_pack_btn
from utils.const import images


async def resent_battle_lobby_info(bot: Bot, battle: PackBattle, kind, text, markup):
    if kind == "owner":
        user_id = battle.owner
        del_msg_id = battle.owner_msg_id
    else:
        user_id = battle.target
        del_msg_id = battle.target_msg_id

    msg_id = del_msg_id
    try:
        msg = await bot.send_message(user_id, text, reply_markup=markup)
        msg_id = msg.message_id
    except Exception as error:
        logging.error(f"Send error | chat {user_id}\n{error}")

    try:
        await bot.delete_message(user_id, del_msg_id)
    except Exception as error:
        logging.error(f"Delete error | chat {user_id}\n{error}")

    return msg_id


async def re_check_active_battles(db, bot):
    date = datetime.datetime.now()
    date_ts = int(date.timestamp())
    battles = await get_active_battles(db)
    if len(battles) > 0:
        battle: PackBattle
        for num, battle in enumerate(battles):
            if battle.owner_ts > 0:
                delay = battle.owner_ts - date_ts
                if delay <= 0:
                    delay = num + 1
                asyncio.create_task(check_battle_timer(
                    db, bot, battle.id, "owner", battle.owner, battle.owner_ts, delay))
            elif battle.target_ts > 0:
                delay = battle.target_ts - date_ts
                if delay <= 0:
                    delay = num + 1
                asyncio.create_task(check_battle_timer(
                    db, bot, battle.id, "target", battle.target, battle.target_ts, delay))

            await asyncio.sleep(.001)


async def check_battle_timer(db, bot: Bot, battle_id, kind, user_id, date_ts, delay):
    await asyncio.sleep(delay)

    res = await check_pack_battle(db, battle_id, kind, user_id, date_ts)
    if res != "finished":
        battle: PackBattle = res[0]
        if res[1] == "owner_timeout":
            try:
                await bot.delete_message(battle.owner, battle.owner_msg_id)
            except Exception as error:
                logging.error(f"Delete error | chat {battle.owner}\n{error}")
            try:
                await bot.delete_message(battle.target, battle.target_msg_id)
            except Exception as error:
                logging.error(f"Delete error | chat {battle.target}\n{error}")

            await asyncio.sleep(.01)

            txt = f"""
            🎪 Текущее лобби удалено

            🟣 {battle.owner_username} долго бездействовал, лобби было удалено
            """

            try:
                await bot.send_message(battle.owner, dedent(txt), reply_markup=pack_battle_kb)
            except Exception as error:
                logging.error(f"Send error | chat {battle.owner}\n{error}")
            try:
                await bot.send_message(battle.target, dedent(txt), reply_markup=pack_battle_kb)
            except Exception as error:
                logging.error(f"Send error | chat {battle.target}\n{error}")
        elif res[1] == "target_timeout":
            try:
                await bot.delete_message(battle.owner, battle.owner_msg_id)
            except Exception as error:
                logging.error(f"Delete error | chat {battle.owner}\n{error}")
            try:
                await bot.delete_message(res[2], res[3])
            except Exception as error:
                logging.error(f"Delete error | chat {battle.target}\n{error}")

            await asyncio.sleep(.01)

            txt = f"🟠 {res[4]} долго бездействовал и был удален из лобби"
            try:
                await bot.send_message(battle.owner, txt)
            except Exception as error:
                logging.error(f"Send error | chat {battle.owner}\n{error}")

            await asyncio.sleep(.01)

            duel_txt = f"""
            🎪 Ваше лобби:

            Пак на текущую дуэль: {"Легендарный пак" if battle.quant == 0 else f"{battle.quant} карт"}
            🟣 {battle.owner_username}
            
            Статус лобби - Ожидание соперника
            """
            try:
                msg = await bot.send_message(
                    battle.owner, dedent(duel_txt), reply_markup=no_opp_battle_kb(battle_id))
                await update_owner_battle_msg_id_db(db, battle_id, msg.message_id)
            except Exception as error:
                logging.error(f"Send error | chat {battle.owner}\n{error}")


async def send_battle_finish_messages(battle: PackBattle, bot: Bot, pack_one, pack_two):
    try:
        await bot.delete_message(battle.owner, battle.owner_msg_id)
    except Exception as error:
        logging.error(f"Delete error | chat {battle.owner}\n{error}")
    try:
        await bot.delete_message(battle.target, battle.target_msg_id)
    except Exception as error:
        logging.error(f"Delete error | chat {battle.target}\n{error}")

    await asyncio.sleep(.01)

    if battle.winner == 0:
        txt = f"""
        ⚔️ Битва окончена!

        🟣 {battle.owner_username} набирает <b>{battle.owner_points}</b> очков
        🟠 {battle.target_username} набирает <b>{battle.target_points}</b> очков

        Результат: <b>Ничья</b>
        """
    else:
        txt = f"""
        ⚖️ Битва окончена!

        🟣 {battle.owner_username} набирает <b>{battle.owner_points}</b> очков
        🟠 {battle.target_username} набирает <b>{battle.target_points}</b> очков

        🏆 Победитель: {battle.owner_username if battle.winner == battle.owner else battle.target_username}

        🃏 Коллекции карт обновлены.
        """

        if battle.winner == battle.owner:
            owner_sticker = images.get("duelwin")
            target_sticer = images.get("duellose")
        else:
            owner_sticker = images.get("duellose")
            target_sticer = images.get("duelwin")

        try:
            await bot.send_sticker(battle.owner, owner_sticker)
        except Exception as error:
            logging.error(f"Send error | chat {battle.owner}\n{error}")
        try:
            await bot.send_sticker(battle.target, target_sticer)
        except Exception as error:
            logging.error(f"Send error | chat {battle.target}\n{error}")

        await asyncio.sleep(.2)

    owner_pack_txt = f"🟣 Пак {battle.owner_username}"
    target_pack_txt = f"🟠 Пак {battle.target_username}"

    try:
        await bot.send_message(
            battle.owner, owner_pack_txt, reply_markup=cards_pack_btn(pack_one))
    except Exception as error:
        logging.error(f"Send error | chat {battle.owner}\n{error}")

    await asyncio.sleep(.1)

    try:
        await bot.send_message(
            battle.target, owner_pack_txt, reply_markup=cards_pack_btn(pack_one))
    except Exception as error:
        logging.error(f"Send error | chat {battle.owner}\n{error}")

    await asyncio.sleep(.1)

    try:
        await bot.send_message(
            battle.owner, target_pack_txt, reply_markup=cards_pack_btn(pack_two))
    except Exception as error:
        logging.error(f"Send error | chat {battle.target}\n{error}")

    await asyncio.sleep(.1)

    try:
        await bot.send_message(
            battle.target, target_pack_txt, reply_markup=cards_pack_btn(pack_two))
    except Exception as error:
        logging.error(f"Send error | chat {battle.target}\n{error}")

    await asyncio.sleep(.2)

    try:
        await bot.send_message(
            battle.owner, dedent(txt), reply_markup=to_main_btn)
    except Exception as error:
        logging.error(f"Send error | chat {battle.owner}\n{error}")
    try:
        await bot.send_message(
            battle.target, dedent(txt), reply_markup=to_main_btn)
    except Exception as error:
        logging.error(f"Send error | chat {battle.target}\n{error}")
