import datetime as dt
import logging

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, Player, PromoCode, UserCard


async def get_user_role(ssn: AsyncSession, user_id):
    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    return user.role


async def add_new_card(ssn: AsyncSession, data: dict, image):
    card = await ssn.merge(CardItem(
        name=data['name'], team=data['team'], card_name=data['card_name'],
        image=image, rarity=data['rarity'], points=data['points'],
        league=data['league']))
    await ssn.commit()
    logging.info(f"Added new card {card.id}")


async def update_card_image(ssn: AsyncSession, card_id, image):
    await ssn.execute(update(CardItem).filter(
        CardItem.id == card_id).values(image=image))
    await ssn.commit()


async def update_card_text(
        ssn: AsyncSession, card_id, name, card_name, team, league, rarity, points):
    await ssn.execute(update(CardItem).filter(
        CardItem.id == card_id).values(
            name=name, card_name=card_name, league=league,
            team=team, rarity=rarity, points=points))
    await ssn.execute(update(UserCard).filter(
        UserCard.card_id == card_id).values(
            points=points, card_rarity=rarity))
    await ssn.commit()


async def add_new_promo(ssn: AsyncSession, card_id, text, kind, uses, users):
    await ssn.merge(PromoCode(
        promo=text, card_id=card_id, kind=kind, quant=uses, users=users))
    await ssn.commit()


async def get_promos(ssn: AsyncSession):
    promos_q = await ssn.execute(select(PromoCode).order_by(PromoCode.id))
    promos = promos_q.scalars().all()
    return promos


async def delete_promo(ssn: AsyncSession, promo_id):
    await ssn.execute(delete(PromoCode).filter(PromoCode.id == promo_id))
    await ssn.commit()

    promos_q = await ssn.execute(select(PromoCode).order_by(PromoCode.id))
    promos = promos_q.scalars().all()
    return promos


async def get_adm_user_info(ssn: AsyncSession, username):
    if username.isdigit():
        user_q = await ssn.execute(
            select(Player).filter(Player.id == int(username)))
        user_res = user_q.fetchone()
    else:
        user_q = await ssn.execute(
            select(Player).filter(Player.username.ilike(username)))
        user_res = user_q.fetchone()

    if user_res is None:
        res = "not_found"
    else:
        res = user_res[0]

    return res


async def update_card_status(ssn: AsyncSession, card_id, status, rarity):
    await ssn.execute(update(CardItem).filter(
        CardItem.id == card_id).values(status=status))
    await ssn.commit()

    if rarity == "all":
        cards_q = await ssn.execute(select(CardItem).order_by(CardItem.id))
    else:
        cards_q = await ssn.execute(select(CardItem).filter(
            CardItem.rarity == rarity).order_by(CardItem.id))
    cards = cards_q.scalars().all()

    return cards


async def ban_user(ssn: AsyncSession, username, status):
    if username.isdigit():
        user_q = await ssn.execute(
            select(Player).filter(Player.id == int(username)))
        user_res = user_q.fetchone()
    else:
        user_q = await ssn.execute(
            select(Player).filter(Player.username.ilike(username)))
        user_res = user_q.fetchone()

    if user_res is None:
        return "not_found"

    user_id = user_res[0].id
    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(ban_status=status))
    await ssn.commit()

    return user_id
