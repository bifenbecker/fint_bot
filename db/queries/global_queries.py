import datetime as dt
import logging
import random

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Player, UserCard, UserPacks, Games, CardItem, PlayerPick, PayItem
from utils.misc import card_rarity_randomize, get_new_pass_date


async def check_and_add_user(ssn: AsyncSession, user_id, username):
    user_q = await ssn.execute(select(Player).filter(Player.id == user_id))
    user_res = user_q.fetchone()
    if user_res is None:
        date = dt.datetime.now()
        date_ts = int(date.timestamp())
        date_str = date.strftime("%d.%m.%Y %H:%M")

        await ssn.merge(Player(
            id=user_id, joined_at_ts=date_ts, joined_at_txt=date_str,
            username=username, last_open=date_ts - 86500))
        await ssn.commit()
        logging.info(f"New User {username} ({user_id})")
    else:
        res: Player = user_res[0]
        if res.username != username:
            await ssn.execute(update(Player).filter(
                Player.id == res.id).values(username=username))
            await ssn.commit()


async def get_user_info(ssn: AsyncSession, user_id):
    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    return user


async def get_top_rating(ssn: AsyncSession, user_id):
    top_q = await ssn.execute(
        select(Player).order_by(Player.season_rating.desc()).limit(10))
    top = top_q.scalars().all()

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    user_top_q = await ssn.execute(select(Player.id).filter(
        Player.season_rating >= user.season_rating).filter(
            Player.id != user_id))
    user_top = user_top_q.scalars().all()
    place = len(user_top) + 1

    return top, user, place


async def get_all_time_rating(ssn: AsyncSession, user_id):
    top_q = await ssn.execute(
        select(Player).order_by(Player.rating.desc()).limit(10))
    top = top_q.scalars().all()

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    user_top_q = await ssn.execute(select(Player.id).filter(
        Player.rating >= user.rating).filter(
            Player.id != user_id))
    user_top = user_top_q.scalars().all()
    place = len(user_top) + 1

    return top, user, place


async def get_top_penalty(ssn: AsyncSession, user_id):
    top_q = await ssn.execute(
        select(Player).order_by(Player.season_penalty.desc()).limit(10))
    top = top_q.scalars().all()

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    user_top_q = await ssn.execute(select(Player.id).filter(
        Player.season_penalty >= user.season_penalty).filter(
            Player.id != user_id))
    user_top = user_top_q.scalars().all()
    place = len(user_top) + 1

    return top, user, place


async def get_all_time_penalty(ssn: AsyncSession, user_id):
    top_q = await ssn.execute(
        select(Player).order_by(Player.penalty_rating.desc()).limit(10))
    top = top_q.scalars().all()

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    user_top_q = await ssn.execute(select(Player.id).filter(
        Player.penalty_rating >= user.penalty_rating).filter(
            Player.id != user_id))
    user_top = user_top_q.scalars().all()
    place = len(user_top) + 1

    return top, user, place


async def update_user_info(ssn: AsyncSession, user_id):
    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == user_id).options(
        selectinload(UserCard.card)))
    cards = cards_q.scalars().all()

    rating = 0
    card: UserCard
    for card in cards:
        rating += card.card.points

        if card.points != card.card.points:
            await ssn.execute(update(UserCard).filter(
                UserCard.id == card.id).values(
                    points=card.card.points, card_rarity=card.card.rarity))

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    # old_diff = rating - user.prev_season_rating
    # if old_diff < 0:
    #     new_s_rating = 0
    # else:
    #     new_s_rating = old_diff

    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
            rating=rating,
            card_quants=len(cards)))
    await ssn.commit()

    place_q = await ssn.execute(select(Player.id).filter(
        Player.id != user_id).filter(
            Player.season_rating > user.season_rating))
    place = place_q.scalars().all()

    return user, len(place) + 1


async def get_or_add_userpacks(ssn: AsyncSession, user_id):
    upacks_q = await ssn.execute(
        select(UserPacks).filter(UserPacks.id == user_id))
    upacks_res = upacks_q.fetchone()
    if upacks_res is None:
        await ssn.merge(UserPacks(id=user_id))
        await ssn.commit()
        upacks_q = await ssn.execute(
            select(UserPacks).filter(UserPacks.id == user_id))
        upacks = upacks_q.fetchone()[0]
    else:
        upacks = upacks_res[0]

    return upacks


async def promocode_fint_pass(ssn: AsyncSession, user_id):
    days = 30

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    data = get_new_pass_date(days, user.pass_until, user.pass_ts)

    cards_q = await ssn.execute(select(CardItem).filter(
        CardItem.rarity == "Limited").filter(
        CardItem.status == "on"))
    cards = cards_q.scalars().all()

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

    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
            pass_ts=data[0], pass_until=data[1], game_pass="yes",
            transactions=Player.transactions + 1,
            rating=Player.rating + card.points,
            card_quants=Player.card_quants + 1,
            season_rating=Player.season_rating + card.points,
            last_open=Player.last_open - 43200,
            last_lucky=Player.last_lucky - 7200))
    await ssn.execute(update(Games).filter(
        Games.user_id == user_id).filter(
            Games.kind == "darts").values(
                last_free=Games.last_free - 172800))

    pick_cards = []
    for _ in range(3):
        rarity = await card_rarity_randomize("pick")
        cards_q = await ssn.execute(select(CardItem).filter(
            CardItem.rarity == rarity).filter(
            CardItem.status == "on"))
        cards = cards_q.scalars().all()
        pick_card: CardItem = random.choice(cards)
        pick_cards.append(pick_card)

    new_pick = await ssn.merge(PlayerPick(
        user_id=user_id, card_one=pick_cards[0].id,
        card_two=pick_cards[1].id, card_three=pick_cards[2].id))
    await ssn.commit()
    pick_id = new_pick.id

    logging.info(f"User {user_id} bought fint pass for {days} days")

    return 'fintpass', card, pick_id, pick_cards