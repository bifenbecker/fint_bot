import datetime
import os

import pandas as pd
from aiogram import types
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from openpyxl.styles import Alignment
from db.models import Games, Player, Season, Trade, UserTrade
from utils.const import channel_trade_info


async def get_free_card_notity_users(db, now_ts):
    next_ts = now_ts + 300

    ssn: AsyncSession
    async with db() as ssn:
        card_users_q = await ssn.execute(select(Player).filter(
            Player.last_open > now_ts).filter(
            Player.last_open < next_ts))
        card_users = card_users_q.scalars().all()

        ls_users_q = await ssn.execute(select(Player).filter(
            Player.last_lucky > now_ts).filter(
            Player.last_lucky < next_ts))
        ls_users = ls_users_q.scalars().all()

        darts_users_q = await ssn.execute(select(Games).filter(
            Games.kind == "darts").filter(
            Games.last_free > now_ts).filter(
            Games.last_free < next_ts))
        darts_users = darts_users_q.scalars().all()

        return card_users, ls_users, darts_users


async def check_trade_count(db):
    ssn: AsyncSession
    async with db() as ssn:
        await ssn.execute(update(Player).values(trade_count=0))
        await ssn.commit()


async def clear_user_trade_table(db):
    ssn: AsyncSession
    async with db() as ssn:
        await ssn.execute(delete(UserTrade))
        await ssn.commit()


async def get_banned_users(db):
    ssn: AsyncSession
    async with db() as ssn:
        banned_q = await ssn.execute(select(Player.id).filter(
            Player.ban_status == "banned"))
        banned = banned_q.scalars().all()

    return banned


async def get_seven_notify_users(db):
    date = datetime.datetime.now()
    old_date_ts = int(date.timestamp()) - 518400

    ssn: AsyncSession
    async with db() as ssn:
        users_q = await ssn.execute(select(Player.id).filter(
            Player.last_open <= old_date_ts).filter(
            Player.seven_days == 1))
        users = users_q.scalars().all()

        await ssn.execute(update(Player).filter(
            Player.id.in_(users)).values(
            seven_days=0, lucky_quants=Player.lucky_quants + 5))
        await ssn.commit()

        return users


async def get_fourteen_notify_users(db):
    date = datetime.datetime.now()
    old_date_ts = int(date.timestamp()) - 1123200

    ssn: AsyncSession
    async with db() as ssn:
        users_q = await ssn.execute(select(Player.id).filter(
            Player.last_open <= old_date_ts).filter(
            Player.fourteen_days == 1))
        users = users_q.scalars().all()

        await ssn.execute(update(Player).filter(
            Player.id.in_(users)).values(
            fourteen_days=0, lucky_quants=Player.lucky_quants + 10))
        await ssn.commit()

        return users


async def new_season(db):
    ssn: AsyncSession
    async with db() as ssn:
        date = datetime.datetime.now()
        date_str = date.strftime("%d.%m.%Y")

        top_r_q = await ssn.execute(
            select(Player).order_by(Player.season_rating.desc()).limit(20))
        top_rs = top_r_q.scalars().all()

        top_r: Player
        for top_r in top_rs:
            await ssn.merge(Season(
                user_id=top_r.id, username=top_r.username,
                kind="rating", rating=top_r.season_rating, date_str=date_str))
        await ssn.commit()

        top_p_q = await ssn.execute(
            select(Player).order_by(Player.season_penalty.desc()).limit(20))
        top_ps = top_p_q.scalars().all()

        top_p: Player
        for top_p in top_ps:
            await ssn.merge(Season(
                user_id=top_p.id, username=top_p.username,
                kind="penalty", rating=top_p.season_penalty, date_str=date_str))
        await ssn.commit()

        await ssn.execute(update(Player).values(
            prev_season_rating=Player.rating,
            prev_season_penalty=Player.season_penalty,
            season_rating=0, season_penalty=0))
        await ssn.commit()


async def remove_premium_from_users(db, date_ts):
    ssn: AsyncSession
    async with db() as ssn:
        users_q = await ssn.execute(
            select(Player.id).filter(
                Player.pass_ts <= date_ts).filter(Player.game_pass == "yes"))
        users = users_q.scalars().all()

        if len(users) > 0:
            await ssn.execute(update(Player).filter(
                Player.id.in_(users)).values(
                game_pass="no", pass_ts=0, pass_until="nopass"))
            await ssn.commit()

        return users


async def get_all_trade_for_information(db, bot):
    ssn: AsyncSession
    async with db() as ssn:
        result = await ssn.execute(select(Trade))
        all_trades = result.scalars().all()

        list_all_trades = [
            ["id", "status", "quant", "owner", "owner_username",
             "owner_card_id", "target", "target_username", "target_card_id"]
        ]

        for trade in all_trades:
            list_all_trades.append([
                trade.id,
                trade.status,
                trade.quant,
                trade.owner,
                trade.owner_username,
                trade.owner_card_id,
                trade.target,
                trade.target_username,
                trade.target_card_id
            ])

    df = pd.DataFrame(list_all_trades[1:], columns=list_all_trades[0])

    # Проверяем и создаем директорию, если она не существует
    output_dir = 'trades_info'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, 'trades.xlsx')

    # Сохраняем файл в Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Trades')
        worksheet = writer.sheets['Trades']

        for column in worksheet.columns:
            for cell in column:
                cell.alignment = Alignment(horizontal='center')

            worksheet.column_dimensions[column[0].column_letter].width = 20

    # Отправляем файл через бота
    input_file = types.input_file.FSInputFile(output_file)
    await bot.send_document(channel_trade_info, input_file)