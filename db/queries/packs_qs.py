import logging
import random

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import (CardItem, CardPack, CardXPack, Player, PlayerPick,
                       UserCard, UserPacks)
from db.queries.global_queries import get_or_add_userpacks
from utils.misc import card_rarity_randomize


async def open_default_pack(ssn: AsyncSession, user_id, quant):
    upacks: UserPacks = await get_or_add_userpacks(ssn, user_id)
    if (upacks.five_pack < 1) and (quant == 5):
        return "no_packs"
    elif (upacks.ten_pack < 1) and (quant == 10):
        return "no_packs"
    elif (upacks.twenty_pack < 1) and (quant == 20):
        return "no_packs"
    elif (upacks.thirty_pack < 1) and (quant == 30):
        return "no_packs"


    points = 0
    u_cards_ids = []
    
    if quant == 5:
        kind = "card"
    elif (quant == 10) or (quant == 20):
        kind = "pack_10_20"
    elif quant == 30:
        print("elif quant == 30:")
        kind = "pack_30"
    

    for _ in range(quant):
        print("for _ in range(quant):")
        rarity = await card_rarity_randomize(kind)
        print(rarity)
        cards_q = await ssn.execute(select(CardItem).filter(
            CardItem.rarity == rarity).filter(
                CardItem.status == "on"))
        cards = cards_q.scalars().all()
        card: CardItem = random.choice(cards)
        print(card.name, card.rarity)
        print(card)
        points += card.points
        usercard_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.card_id == card.id))
        user_card_res = usercard_q.fetchone()
        if user_card_res is None:
            duplicate = 0
        else:
            duplicate = 1

        user_card = await ssn.merge(UserCard(
            user_id=user_id, card_id=card.id, points=card.points,
            card_rarity=card.rarity, duplicate=duplicate))
        await ssn.commit()
        u_cards_ids.append(user_card.id)

    new_pack = await ssn.merge(CardPack(user_id=user_id))
    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
        rating=Player.rating + points,
        card_quants=Player.card_quants + quant,
        season_rating=Player.season_rating + points))

    if quant == 5:
        print(f"if quant == 5 {quant}")
        await ssn.execute(update(UserPacks).filter(
            UserPacks.id == user_id).values(five_pack=UserPacks.five_pack - 1))
    elif quant == 10:
        print(f"elif quant == 10 {quant}")
        await ssn.execute(update(UserPacks).filter(
            UserPacks.id == user_id).values(ten_pack=UserPacks.ten_pack - 1))
    elif quant == 20:
        print(f"elif quant == 20 {quant}")
        await ssn.execute(update(UserPacks).filter(
            UserPacks.id == user_id).values(twenty_pack=UserPacks.twenty_pack - 1))
    else:
        print(f"else{quant}")
        await ssn.execute(update(UserPacks).filter(
            UserPacks.id == user_id).values(thirty_pack=UserPacks.thirty_pack - 1))

    await ssn.commit()
    pack_id = new_pack.id

    for u_id in u_cards_ids:
        await ssn.merge(CardXPack(pack_id=pack_id, user_card_id=u_id))

    await ssn.commit()
    logging.info(f"User {user_id} used pack{quant} pack_id {pack_id}")

    return pack_id


async def open_player_pick(ssn: AsyncSession, user_id):
    upacks: UserPacks = await get_or_add_userpacks(ssn, user_id)
    if upacks.player_pick < 1:
        return "no_packs"

    pick_cards = []
    for _ in range(3):
        rarity = await card_rarity_randomize("pick")
        cards_q = await ssn.execute(select(CardItem).filter(
            CardItem.rarity == rarity).filter(
            CardItem.status == "on"))
        cards = cards_q.scalars().all()
        card: CardItem = random.choice(cards)
        pick_cards.append(card)

    new_pick = await ssn.merge(PlayerPick(
        user_id=user_id, card_one=pick_cards[0].id,
        card_two=pick_cards[1].id, card_three=pick_cards[2].id))
    await ssn.execute(update(UserPacks).filter(
        UserPacks.id == user_id).values(
            player_pick=UserPacks.player_pick - 1))
    await ssn.commit()
    pick_id = new_pick.id

    logging.info(f"User {user_id} used player pick pick_id {pick_id}")

    return pick_id, pick_cards


async def save_player_pick(ssn: AsyncSession, user_id, pick_id, card_id):
    pick_q = await ssn.execute(select(
        PlayerPick).filter(PlayerPick.id == pick_id))
    pick: PlayerPick = pick_q.fetchone()[0]

    if pick.card_pick != 0:
        return "not_active"

    card_q = await ssn.execute(
        select(CardItem).filter(CardItem.id == card_id))
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

    await ssn.execute(update(PlayerPick).filter(
        PlayerPick.id == pick_id).values(card_pick=card_id))
    await ssn.execute(update(Player).filter(
        Player.id == user_id).values(
        rating=Player.rating + card.points,
        card_quants=Player.card_quants + 1,
        season_rating=Player.season_rating + card.points))
    await ssn.commit()

    logging.info(
        f"User {user_id} pick card {card_id} from player pick {pick_id}")
