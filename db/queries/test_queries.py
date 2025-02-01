import asyncio
import datetime as dt
import logging
import random

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, CardPack, CardXPack, PayItem, Player, UserCard


async def redb(db, quant):
    ssn: AsyncSession
    async with db() as ssn:
        # old_cards_q = await ssn.execute(
        #     select(Card).order_by(Card.card_id).filter(Card.card_id != 12340000000004321))
        # old_cards = old_cards_q.scalars().all()

        rarities = {
            "0": "ОБЫЧНАЯ",
            "1": "НЕОБЫЧНАЯ",
            "2": "ЭПИЧЕСКАЯ",
            "3": "УНИКАЛЬНАЯ",
            "4": "ЛЕГЕНДАРНАЯ",
            "5": "РЕДКАЯ",
            "6": "ЭКСКЛЮЗИВНАЯ",
            "7": "МИФИЧЕСКАЯ"
        }

        # old_card: Card
        # for old_card in old_cards:
        #     await ssn.merge(CardItem(
        #         old_id=old_card.card_id, name=old_card.player_name,
        #         nickname=old_card.player_nickname, team=old_card.team,
        #         rarity=rarities.get(str(old_card.rareness)),
        #         image=old_card.photo_id, points=old_card.points))
        # await ssn.commit()

        # old_user_cards_q = await ssn.execute(
        #     select(CardsOfUser).filter(
        #         CardsOfUser.card_key > quant).order_by(CardsOfUser.card_key))
        # old_user_cards = old_user_cards_q.scalars().all()

        # oucard: CardsOfUser
        # for oucard in old_user_cards[:10000]:
        #     card_q = await ssn.execute(
        #         select(CardItem).filter(CardItem.old_id == oucard.card_id))
        #     card: CardItem = card_q.fetchone()[0]
        #     usercard_q = await ssn.execute(select(UserCard).filter(
        #         UserCard.user_id == oucard.tele_id).filter(
        #         UserCard.card_id == oucard.card_id))
        #     user_card_res = usercard_q.fetchone()
        #     if user_card_res is None:
        #         duplicate = 0
        #     else:
        #         duplicate = 1
        #     await ssn.merge(UserCard(
        #         user_id=oucard.tele_id, card_id=card.id, points=card.points,
        #         card_rarity=card.rarity,
        #         duplicate=duplicate, old_id=oucard.card_key))

        #     # print(f"{oucard.card_key} done")
        # await ssn.commit()
        # if len(old_user_cards[:10000]) < 10000:
        #     return 0
        # return oucard.card_key

        # old_users_q = await ssn.execute(select(User))
        # old_users = old_users_q.scalars().all()
        # count = len(old_users)

        # old_user: User
        # for num, old_user in enumerate(old_users):
        #     if old_user.register_at:
        #         reg_date_ts = int(old_user.register_at.timestamp())
        #         reg_date_str = old_user.register_at.strftime("%d.%m.%Y %H:%M")
        #     else:
        #         reg_date_ts = 0
        #         reg_date_str = "unknown_date"

        #     if old_user.free_card:
        #         f_date_ts = int(old_user.free_card.timestamp())
        #     else:
        #         f_date_ts = 0

        #     username = f"@{old_user.username}" if old_user.username else f"user{old_user.tele_id}"
        #     await ssn.merge(Player(
        #         id=old_user.tele_id, username=username, card_quants=old_user.card_num,
        #         rating=old_user.card_rating, penalty_rating=old_user.penalty_rating,
        #         last_open=f_date_ts + 86400, transactions=old_user.transactions,
        #         joined_at_ts=reg_date_ts, joined_at_txt=reg_date_str))
        #     if ((num + 1) % 10) == 0:
        #         print(f"{num+1}/{count}")
        # await ssn.commit()


async def gghh(db):
    ssn: AsyncSession
    async with db() as ssn:
        users_q = await ssn.execute(select(Player))
        users = users_q.scalars()

        txt = ""
        user: Player
        for user in users:
            txt += f"\n{user.id} {user.rating} {user.penalty_rating}"

        with open("1.txt", "w") as file:
            file.write(txt)


async def update_new_rating(db):
    # with open("1.txt") as file:
    #     file_data = file.read()

    ssn: AsyncSession
    async with db() as ssn:
        await ssn.execute(update(Player).values(
            prev_season_rating=Player.rating,
            prev_season_penalty=Player.penalty_rating,
            season_rating=0, season_penalty=0))
        await ssn.commit()

    #     data = file_data.split("\n")
    #     last = len(data)
    #     for num, item in enumerate(data):
    #         items = item.split()
    #         print(f"user {items[0]} {num+1}/{last}")

    #         user_q = await ssn.execute(
    #             select(Player).filter(Player.id == int(items[0])))
    #         user: Player = user_q.fetchone()[0]

    #         s_rating = user.rating - int(items[1])
    #         if s_rating < 0:
    #             s_rating = 0

    #         p_rating = user.penalty_rating - int(items[2])
    #         if p_rating < 0:
    #             p_rating = 0

    #         await ssn.execute(update(Player).filter(
    #             Player.id == int(items[0])).values(
    #                 season_rating=s_rating, season_penalty=p_rating,
    #                 prev_season_rating=int(items[1]),
    #                 prev_season_penalty=int(items[2])))
    #     await ssn.commit()

        # await ssn.execute(update(Player).filter(
        #     Player.season_rating == 0).values(season_rating=Player.rating))
        # await ssn.commit()

        # await ssn.execute(update(Player).filter(
        #     Player.season_penalty == 0).values(season_penalty=Player.penalty_rating))
        # await ssn.commit()
