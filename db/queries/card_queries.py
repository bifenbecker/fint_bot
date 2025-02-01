import datetime as dt
import logging
import random

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import (CardItem, Player, PromoCode, PromoUser, UserCard,
                       UserPacks)
from db.queries.global_queries import get_or_add_userpacks, promocode_fint_pass
from db.queries.payment_queries import update_fint_pass
from utils.const import rarities
from utils.misc import card_rarity_randomize


async def get_free_card(ssn: AsyncSession, user_id):
    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    if user.last_open < date_ts:
        status = "available"
    else:
        if user.open_count > 0:
            status = "available"
        else:
            status = "not_available"

    if status == "available":
        rarity = await card_rarity_randomize("card")
        cards_q = await ssn.execute(select(CardItem).filter(
            CardItem.rarity == rarity).filter(
            CardItem.status == "on"))
        cards = cards_q.scalars().all()

        if len(cards) == 0:
            return "no_cards"

        card: CardItem = random.choice(cards)

        usercard_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.card_id == card.id))
        user_card_res = usercard_q.fetchone()
        if user_card_res is None:
            duplicate = 0
        else:
            duplicate = 1

        await ssn.merge(UserCard(
            user_id=user_id, card_id=card.id, points=card.points,
            card_rarity=card.rarity, duplicate=duplicate))

        if user.last_open < date_ts:
            if user.game_pass == "yes":
                new_delay = 43200
            else:
                new_delay = 86400
            await ssn.execute(update(Player).filter(
                Player.id == user_id).values(
                last_open=date_ts + new_delay,
                rating=Player.rating + card.points,
                card_quants=Player.card_quants + 1,
                season_rating=Player.season_rating + card.points))
        else:
            await ssn.execute(update(Player).filter(
                Player.id == user_id).values(
                open_count=Player.open_count - 1,
                rating=Player.rating + card.points,
                card_quants=Player.card_quants + 1,
                season_rating=Player.season_rating + card.points))
        await ssn.commit()
        return card

    else:
        return user.last_open - date_ts


async def use_promo(ssn: AsyncSession, user_id, promocode):
    promo_q = await ssn.execute(
        select(PromoCode).filter(PromoCode.promo.ilike(promocode)))
    promo_res = promo_q.fetchone()
    if promo_res is None:
        return "not_found"

    promo: PromoCode = promo_res[0]

    promo_user_q = await ssn.execute(select(PromoUser.id).filter(
        PromoUser.promo_id == promo.id).filter(
            PromoUser.user_id == user_id))
    promo_user_res = promo_user_q.fetchone()
    if promo_user_res is not None:
        return "already_used"

    await get_or_add_userpacks(ssn, user_id)

    if promo.users == "new":
        date = dt.datetime.now()
        old_date_ts = int(date.timestamp()) - 604800

        user_q = await ssn.execute(
            select(Player).filter(Player.id == user_id))
        user: Player = user_q.fetchone()[0]
        if user.joined_at_ts < old_date_ts:
            return "only_newbee_promo"

    if promo.kind == "card":
        if promo.card_id == 0:
            rarity = await card_rarity_randomize("card")
            cards_q = await ssn.execute(select(CardItem).filter(
                CardItem.rarity == rarity).filter(
                    CardItem.status == "on"))
            cards = cards_q.scalars().all()

            if len(cards) == 0:
                return "no_cards"

            card: CardItem = random.choice(cards)
        else:
            card_q = await ssn.execute(
                select(CardItem).filter(CardItem.id == promo.card_id))
            card: CardItem = card_q.fetchone()[0]

        usercard_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
            UserCard.card_id == card.id))
        user_card_res = usercard_q.fetchone()
        if user_card_res is None:
            duplicate = 0
        else:
            duplicate = 1

        await ssn.merge(UserCard(
            user_id=user_id, card_id=card.id, points=card.points,
            card_rarity=card.rarity, duplicate=duplicate))

        await ssn.execute(update(Player).filter(
            Player.id == user_id).values(
            rating=Player.rating + card.points,
            card_quants=Player.card_quants + 1,
            season_rating=Player.season_rating + card.points))

        res = "card", card

    elif promo.kind == "pick":
        await ssn.execute(update(UserPacks).filter(
            UserPacks.id == user_id).values(
            player_pick=UserPacks.player_pick + 1))

        res = "added", "added"

    elif promo.kind == 'pass':
        res = await promocode_fint_pass(ssn, user_id)
        # return res
    else:
        quant = int(promo.kind[4:])
        if quant == 20:
            await ssn.execute(update(UserPacks).filter(
                UserPacks.id == user_id).values(
                    twenty_pack=UserPacks.twenty_pack + 1))
        elif quant == 10:
            await ssn.execute(update(UserPacks).filter(
                UserPacks.id == user_id).values(
                    ten_pack=UserPacks.ten_pack + 1))
        elif quant == 30:
            await ssn.execute(update(UserPacks).filter(
                UserPacks.id == user_id).values(
                    thirty_pack=UserPacks.thirty_pack + 1))
        else:
            await ssn.execute(update(UserPacks).filter(
                UserPacks.id == user_id).values(
                    five_pack=UserPacks.five_pack + 1))

        res = "added", "added"

    await ssn.commit()
    await ssn.merge(PromoUser(promo_id=promo.id, user_id=user_id))

    if promo.quant <= 1:
        await ssn.execute(delete(PromoCode).filter(PromoCode.id == promo.id))
    else:
        await ssn.execute(update(PromoCode).filter(
            PromoCode.id == promo.id).values(quant=PromoCode.quant - 1))

    await ssn.commit()
    logging.info(f"User {user_id} used promo {promocode} ({promo.id})")

    return res


async def get_user_card_rarities(ssn: AsyncSession, user_id):
    cards_q = await ssn.execute(
        select(UserCard.card_rarity).filter(UserCard.user_id == user_id))
    cards = cards_q.scalars().all()
    user_rarities = set(cards)
    result = []
    for rarity in rarities:
        if rarity in user_rarities:
            result.append(rarity)

    return result
