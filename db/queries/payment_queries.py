import logging
import random

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import (CardItem, Games, PayItem, Player, PlayerPick, UserCard,
                       UserPacks)
from db.queries.games_queries import get_game
from db.queries.global_queries import get_or_add_userpacks
from utils.misc import card_rarity_randomize, get_new_pass_date


async def cancel_payment(ssn: AsyncSession, pay_id, user_id):
    await ssn.execute(update(PayItem).filter(
        PayItem.id == pay_id).values(status="canceled"))
    await ssn.commit()
    logging.info(f"User {user_id} canceled payment {pay_id}")

    user_q = await ssn.execute(
        select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    place_q = await ssn.execute(select(Player.id).filter(
        Player.id != user_id).filter(
            Player.season_rating > user.season_rating))
    place = place_q.scalars().all()

    return user, len(place) + 1


async def add_new_payment(ssn: AsyncSession, user_id, label, url, kind, amount):
    pay = await ssn.merge(PayItem(
        label=label, url=url, user_id=user_id, amount=amount, kind=kind))
    await ssn.commit()
    return pay.id


async def get_payment_info(ssn: AsyncSession, pay_id):
    pay_q = await ssn.execute(select(PayItem).filter(PayItem.id == pay_id))
    pay = pay_q.fetchone()[0]
    return pay


async def add_ls_after_pay(ssn: AsyncSession, user_id, pay_id, quant):
    await ssn.execute(update(PayItem).filter(
        PayItem.id == pay_id).values(status="paid"))

    if quant == 9:
        await ssn.execute(update(Player).filter(
            Player.id == user_id).values(
                lucky_quants=Player.lucky_quants + 9,
                transactions=Player.transactions + 1,
                lucky_shots_plus=Player.lucky_shots_plus + 9))
    else:
        await ssn.execute(update(Player).filter(
            Player.id == user_id).values(
                lucky_quants=Player.lucky_quants + quant,
                transactions=Player.transactions + 1))
    await ssn.commit()


async def add_player_pick_pack(ssn: AsyncSession, user_id, pay_id):
    await ssn.execute(update(PayItem).filter(
        PayItem.id == pay_id).values(status="paid"))
    await get_or_add_userpacks(ssn, user_id)

    await ssn.execute(update(UserPacks).filter(
        UserPacks.id == user_id).values(
            player_pick=UserPacks.player_pick + 1))
    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
            transactions=Player.transactions + 1))
    await ssn.commit()
    return "done"


async def add_cards_pack(ssn: AsyncSession, user_id, quant, pay_id):
    await ssn.execute(update(PayItem).filter(
        PayItem.id == pay_id).values(status="paid"))
    await get_or_add_userpacks(ssn, user_id)

    print(quant, type(quant))
    
    if quant == 30:
        print("if quant == 30:")
        await ssn.execute(update(UserPacks).filter(
            UserPacks.id == user_id).values(
                thirty_pack=UserPacks.thirty_pack + 1))
    elif quant == 20:
        await ssn.execute(update(UserPacks).filter(
            UserPacks.id == user_id).values(
                twenty_pack=UserPacks.twenty_pack + 1))
    elif quant == 10:
        await ssn.execute(update(UserPacks).filter(
            UserPacks.id == user_id).values(
                ten_pack=UserPacks.ten_pack + 1))
    else:
        await ssn.execute(update(UserPacks).filter(
            UserPacks.id == user_id).values(
                five_pack=UserPacks.five_pack + 1))
    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
            transactions=Player.transactions + 1))
    await ssn.commit()
    return "done"


async def update_fint_pass(ssn: AsyncSession, user_id, pay_id):
    await ssn.execute(update(PayItem).filter(
        PayItem.id == pay_id).values(status="paid"))

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

    return card, pick_id, pick_cards


async def add_darts_after_pay(ssn: AsyncSession, user_id, pay_id, quant):
    await ssn.execute(update(PayItem).filter(
        PayItem.id == pay_id).values(status="paid"))

    game: Games = await get_game(ssn, user_id, "darts")

    await ssn.execute(update(Games).filter(
        Games.id == game.id).values(attempts=Games.attempts + quant))
    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(transactions=Player.transactions + 1))
    await ssn.commit()


async def add_casino_after_pay(ssn: AsyncSession, user_id, pay_id, quant):
    await ssn.execute(update(PayItem).filter(
        PayItem.id == pay_id).values(status="paid"))

    game: Games = await get_game(ssn, user_id, "casino")

    await ssn.execute(update(Games).filter(
        Games.id == game.id).values(curr_casino=Games.curr_casino + quant*3))
    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(transactions=Player.transactions + 1))
    await ssn.commit()
