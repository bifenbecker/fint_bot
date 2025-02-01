import datetime
import logging
import random

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    CardItem,
    CardPack,
    CardXPack,
    PackBattle,
    Player,
    UserCard,
    UserPacks,
)
from db.queries.global_queries import get_or_add_userpacks
from utils.misc import card_rarity_randomize


async def get_active_pack_battle_lobbies(ssn: AsyncSession):
    battles_q = await ssn.execute(
        select(PackBattle)
        .filter(PackBattle.target == 0)
        .filter(PackBattle.status == "active")
        .order_by(PackBattle.quant)
    )
    battles = battles_q.scalars().all()
    return battles


async def check_for_pack_battle_available(ssn: AsyncSession, user_id):
    battle_q = await ssn.execute(
        select(PackBattle)
        .filter(or_(PackBattle.target == user_id, PackBattle.owner == user_id))
        .filter(PackBattle.status == "active")
    )
    battle_res = battle_q.fetchone()
    if battle_res is not None:
        return "already_battle_playing"

    upacks: UserPacks = await get_or_add_userpacks(ssn, user_id)
    if upacks.five_pack == upacks.ten_pack == upacks.twenty_pack == 0:
        return "no_packs"

    return upacks


async def create_leg_pack_battle(ssn: AsyncSession, user_id, msg_id, username):
    battle_q = await ssn.execute(
        select(PackBattle)
        .filter(or_(PackBattle.target == user_id, PackBattle.owner == user_id))
        .filter(PackBattle.status == "active")
    )
    battle_res = battle_q.fetchone()
    if battle_res is not None:
        return "already_battle_playing"

    upacks: UserPacks = await get_or_add_userpacks(ssn, user_id)
    if upacks.leg_pack < 1:
        return "no_packs"

    new_battle = await ssn.merge(
        PackBattle(
            owner_msg_id=msg_id,
            owner_points=0,
            owner=user_id,
            owner_username=username,
            quant=0,
        )
    )
    await ssn.execute(
        update(UserPacks)
        .filter(UserPacks.id == user_id)
        .values(leg_pack=UserPacks.leg_pack - 1)
    )
    await ssn.commit()

    logging.info(
        f"User {user_id} ({username}) created leg pack battle lobby {new_battle.id}"
    )
    battle_q = await ssn.execute(
        select(PackBattle).filter(PackBattle.id == new_battle.id)
    )
    battle = battle_q.fetchone()[0]
    return battle


async def create_default_pack_battle(
    ssn: AsyncSession, user_id, msg_id, username, quant
):
    battle_q = await ssn.execute(
        select(PackBattle)
        .filter(or_(PackBattle.target == user_id, PackBattle.owner == user_id))
        .filter(PackBattle.status == "active")
    )
    battle_res = battle_q.fetchone()
    if battle_res is not None:
        return "already_battle_playing"

    upacks: UserPacks = await get_or_add_userpacks(ssn, user_id)
    if (upacks.five_pack < 1) and (quant == 5):
        return "no_packs"
    elif (upacks.ten_pack < 1) and (quant == 10):
        return "no_packs"
    elif (upacks.twenty_pack < 1) and (quant == 20):
        return "no_packs"

    new_battle = await ssn.merge(
        PackBattle(
            owner_msg_id=msg_id,
            owner_points=0,
            owner=user_id,
            owner_username=username,
            quant=quant,
        )
    )

    if quant == 5:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id == user_id)
            .values(five_pack=UserPacks.five_pack - 1)
        )
    elif quant == 10:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id == user_id)
            .values(ten_pack=UserPacks.ten_pack - 1)
        )
    else:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id == user_id)
            .values(twenty_pack=UserPacks.twenty_pack - 1)
        )

    await ssn.commit()

    logging.info(
        f"User {user_id} ({username}) created {quant} cards pack battle lobby {new_battle.id}"
    )
    battle_q = await ssn.execute(
        select(PackBattle).filter(PackBattle.id == new_battle.id)
    )
    battle = battle_q.fetchone()[0]
    return battle


async def owner_card_battle_cancel(ssn: AsyncSession, battle_id):
    battle_q = await ssn.execute(select(PackBattle).filter(PackBattle.id == battle_id))
    battle: PackBattle = battle_q.fetchone()[0]
    if battle.status != "active":
        return "not_active"

    await ssn.execute(
        update(PackBattle).filter(PackBattle.id == battle_id).values(status="canceled")
    )

    if battle.quant == 20:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id.in_([battle.owner, battle.target]))
            .values(twenty_pack=UserPacks.twenty_pack + 1)
        )
    elif battle.quant == 10:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id.in_([battle.owner, battle.target]))
            .values(ten_pack=UserPacks.ten_pack + 1)
        )
    else:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id.in_([battle.owner, battle.target]))
            .values(five_pack=UserPacks.five_pack + 1)
        )

    await ssn.commit()

    logging.info(f"User {battle.owner} canceled card battle {battle_id}")
    return battle


async def target_card_battle_cancel(ssn: AsyncSession, battle_id, user_id):
    battle_q = await ssn.execute(select(PackBattle).filter(PackBattle.id == battle_id))
    battle: PackBattle = battle_q.fetchone()[0]
    if battle.status != "active":
        return "not_active"

    await ssn.execute(
        update(PackBattle)
        .filter(PackBattle.id == battle_id)
        .values(target=0, target_username="nouser", target_msg_id=0, target_ts=0)
    )

    if battle.quant == 20:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id == battle.target)
            .values(twenty_pack=UserPacks.twenty_pack + 1)
        )
    elif battle.quant == 10:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id == battle.target)
            .values(ten_pack=UserPacks.ten_pack + 1)
        )
    else:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id == battle.target)
            .values(five_pack=UserPacks.five_pack + 1)
        )

    await ssn.commit()

    user_q = await ssn.execute(select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    logging.info(f"User {battle.target} leave card battle {battle_id}")
    return battle, user


async def join_pack_battle(ssn: AsyncSession, user_id, username, battle_id, msg_id):
    battles_q = await ssn.execute(
        select(PackBattle)
        .filter(or_(PackBattle.target == user_id, PackBattle.owner == user_id))
        .filter(PackBattle.status == "active")
    )
    battles_res = battles_q.fetchone()
    if battles_res is not None:
        return "already_battle_playing"

    battle_q = await ssn.execute(select(PackBattle).filter(PackBattle.id == battle_id))
    battle: PackBattle = battle_q.fetchone()[0]
    if (battle.status != "active") or (battle.target != 0):
        return "not_available"

    upacks: UserPacks = await get_or_add_userpacks(ssn, user_id)
    if (upacks.five_pack < 1) and (battle.quant == 5):
        return "no_packs"
    elif (upacks.ten_pack < 1) and (battle.quant == 10):
        return "no_packs"
    elif (upacks.twenty_pack < 1) and (battle.quant == 20):
        return "no_packs"

    date = datetime.datetime.now()
    date_ts = int(date.timestamp())
    await ssn.execute(
        update(PackBattle)
        .filter(PackBattle.id == battle_id)
        .values(
            target=user_id,
            target_username=username,
            target_points=0,
            target_ready=0,
            target_msg_id=msg_id,
            target_ts=date_ts + 60,
        )
    )

    if battle.quant == 20:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id == user_id)
            .values(twenty_pack=UserPacks.twenty_pack - 1)
        )
    elif battle.quant == 10:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id == user_id)
            .values(ten_pack=UserPacks.ten_pack - 1)
        )
    else:
        await ssn.execute(
            update(UserPacks)
            .filter(UserPacks.id == user_id)
            .values(five_pack=UserPacks.five_pack - 1)
        )

    await ssn.commit()

    return battle


async def update_owner_battle_msg_id(ssn: AsyncSession, battle_id, msg_id):
    await ssn.execute(
        update(PackBattle)
        .filter(PackBattle.id == battle_id)
        .values(owner_msg_id=msg_id)
    )
    await ssn.commit()


async def update_target_battle_msg_id(ssn: AsyncSession, battle_id, msg_id):
    await ssn.execute(
        update(PackBattle)
        .filter(PackBattle.id == battle_id)
        .values(target_msg_id=msg_id)
    )
    await ssn.commit()


async def update_owner_battle_msg_id_db(db, battle_id, msg_id):
    ssn: AsyncSession
    async with db() as ssn:
        await ssn.execute(
            update(PackBattle)
            .filter(PackBattle.id == battle_id)
            .values(owner_msg_id=msg_id)
        )
        await ssn.commit()


async def check_pack_battle(db, battle_id, kind, user_id, date_ts):
    ssn: AsyncSession
    async with db() as ssn:
        battle_q = await ssn.execute(
            select(PackBattle).filter(PackBattle.id == battle_id)
        )
        battle: PackBattle = battle_q.fetchone()[0]
        if battle.status == "active":
            if kind == "owner":
                if date_ts == battle.owner_ts:
                    await ssn.execute(
                        update(PackBattle)
                        .filter(PackBattle.id == battle_id)
                        .values(status="timedout")
                    )

                    if battle.quant == 20:
                        await ssn.execute(
                            update(UserPacks)
                            .filter(UserPacks.id.in_([battle.owner, battle.target]))
                            .values(twenty_pack=UserPacks.twenty_pack + 1)
                        )
                    elif battle.quant == 10:
                        await ssn.execute(
                            update(UserPacks)
                            .filter(UserPacks.id.in_([battle.owner, battle.target]))
                            .values(ten_pack=UserPacks.ten_pack + 1)
                        )
                    else:
                        await ssn.execute(
                            update(UserPacks)
                            .filter(UserPacks.id.in_([battle.owner, battle.target]))
                            .values(five_pack=UserPacks.five_pack + 1)
                        )

                    await ssn.commit()
                    logging.info(f"Pack battle {battle_id} owner timed out")
                    return battle, "owner_timeout"
                else:
                    return battle, "continued"
            else:
                if (user_id == battle.target) and (date_ts == battle.target_ts):
                    old_user_id = battle.target
                    old_msg_id = battle.target_msg_id
                    old_username = battle.target_username

                    await ssn.execute(
                        update(PackBattle)
                        .filter(PackBattle.id == battle_id)
                        .values(
                            target=0,
                            target_username="nouser",
                            target_msg_id=0,
                            target_ts=0,
                        )
                    )
                    if battle.quant == 20:
                        await ssn.execute(
                            update(UserPacks)
                            .filter(UserPacks.id == old_user_id)
                            .values(twenty_pack=UserPacks.twenty_pack + 1)
                        )
                    elif battle.quant == 10:
                        await ssn.execute(
                            update(UserPacks)
                            .filter(UserPacks.id == old_user_id)
                            .values(ten_pack=UserPacks.ten_pack + 1)
                        )
                    else:
                        await ssn.execute(
                            update(UserPacks)
                            .filter(UserPacks.id == old_user_id)
                            .values(five_pack=UserPacks.five_pack + 1)
                        )

                    await ssn.commit()
                    logging.info(f"Pack battle {battle_id} target timed out")
                    return (
                        battle,
                        "target_timeout",
                        old_user_id,
                        old_msg_id,
                        old_username,
                    )
                else:
                    return battle, "continued"

        return "finished"


async def battle_user_ready(ssn: AsyncSession, user_id, battle_id):
    battle_q = await ssn.execute(select(PackBattle).filter(PackBattle.id == battle_id))
    battle: PackBattle = battle_q.fetchone()[0]
    if (battle.status != "active") or (user_id not in (battle.owner, battle.target)):
        return "not_available"

    if user_id == battle.owner:
        if battle.owner_ready == 1:
            return "already_ready"
    else:
        if battle.target_ready == 1:
            return "already_ready"

    if battle.owner == user_id:
        if battle.target_ready == 0:
            await ssn.execute(
                update(PackBattle)
                .filter(PackBattle.id == battle_id)
                .values(owner_ready=1)
            )
            await ssn.commit()
            return battle, "not_ready"
        else:
            if battle.quant == 0:
                owner_result = await calc_leg_pack(ssn, battle.owner)
                target_result = await calc_leg_pack(ssn, battle.target)
            else:
                owner_result = await calc_default_pack(ssn, battle.owner, battle.quant)
                target_result = await calc_default_pack(
                    ssn, battle.target, battle.quant
                )

            if owner_result[0] == target_result[0]:
                winner = 0

                owner_points = 0
                ownr_u_cards = []
                for card_id in owner_result[1]:
                    card_q = await ssn.execute(
                        select(CardItem).filter(CardItem.id == card_id)
                    )
                    card: CardItem = card_q.fetchone()[0]
                    usercard_q = await ssn.execute(
                        select(UserCard)
                        .filter(UserCard.user_id == battle.owner)
                        .filter(UserCard.card_id == card.id)
                    )
                    user_card_res = usercard_q.fetchone()
                    if user_card_res is None:
                        duplicate = 0
                    else:
                        duplicate = 1

                    user_card = await ssn.merge(
                        UserCard(
                            user_id=battle.owner,
                            card_id=card.id,
                            points=card.points,
                            card_rarity=card.rarity,
                            duplicate=duplicate,
                        )
                    )
                    await ssn.commit()
                    ownr_u_cards.append(user_card.id)
                    owner_points += card.points

                new_pack_one = await ssn.merge(CardPack(user_id=battle.owner))
                await ssn.execute(
                    update(Player)
                    .filter(Player.id == battle.owner)
                    .values(
                        rating=Player.rating + owner_points,
                        card_quants=Player.card_quants + len(ownr_u_cards),
                        season_rating=Player.season_rating + owner_points,
                    )
                )
                await ssn.commit()
                pack_one_id = new_pack_one.id

                for u_id in ownr_u_cards:
                    await ssn.merge(CardXPack(pack_id=pack_one_id, user_card_id=u_id))
                await ssn.commit()

                target_points = 0
                trgt_u_cards = []
                for card_id in target_result[1]:
                    card_q = await ssn.execute(
                        select(CardItem).filter(CardItem.id == card_id)
                    )
                    card: CardItem = card_q.fetchone()[0]
                    usercard_q = await ssn.execute(
                        select(UserCard)
                        .filter(UserCard.user_id == battle.target)
                        .filter(UserCard.card_id == card.id)
                    )
                    user_card_res = usercard_q.fetchone()
                    if user_card_res is None:
                        duplicate = 0
                    else:
                        duplicate = 1

                    user_card = await ssn.merge(
                        UserCard(
                            user_id=battle.target,
                            card_id=card.id,
                            points=card.points,
                            card_rarity=card.rarity,
                            duplicate=duplicate,
                        )
                    )
                    await ssn.commit()
                    trgt_u_cards.append(user_card.id)
                    target_points += card.points

                new_pack_two = await ssn.merge(CardPack(user_id=battle.target))
                await ssn.execute(
                    update(Player)
                    .filter(Player.id == battle.target)
                    .values(
                        rating=Player.rating + target_points,
                        card_quants=Player.card_quants + len(trgt_u_cards),
                        season_rating=Player.season_rating + target_points,
                    )
                )
                await ssn.commit()
                pack_two_id = new_pack_two.id

                for u_id in trgt_u_cards:
                    await ssn.merge(CardXPack(pack_id=pack_two_id, user_card_id=u_id))
                await ssn.commit()

            else:
                if owner_result[0] > target_result[0]:
                    winner = battle.owner
                else:
                    winner = battle.target

                points = 0

                ownr_u_cards = []
                for card_id in owner_result[1]:
                    card_q = await ssn.execute(
                        select(CardItem).filter(CardItem.id == card_id)
                    )
                    card: CardItem = card_q.fetchone()[0]
                    usercard_q = await ssn.execute(
                        select(UserCard)
                        .filter(UserCard.user_id == winner)
                        .filter(UserCard.card_id == card.id)
                    )
                    user_card_res = usercard_q.fetchone()
                    if user_card_res is None:
                        duplicate = 0
                    else:
                        duplicate = 1

                    user_card = await ssn.merge(
                        UserCard(
                            user_id=winner,
                            card_id=card.id,
                            points=card.points,
                            card_rarity=card.rarity,
                            duplicate=duplicate,
                        )
                    )
                    await ssn.commit()
                    ownr_u_cards.append(user_card.id)
                    points += card.points
                new_pack_one = await ssn.merge(CardPack(user_id=winner))
                await ssn.commit()
                pack_one_id = new_pack_one.id

                for u_id in ownr_u_cards:
                    await ssn.merge(CardXPack(pack_id=pack_one_id, user_card_id=u_id))
                await ssn.commit()

                trgt_u_cards = []
                for card_id in target_result[1]:
                    card_q = await ssn.execute(
                        select(CardItem).filter(CardItem.id == card_id)
                    )
                    card: CardItem = card_q.fetchone()[0]
                    usercard_q = await ssn.execute(
                        select(UserCard)
                        .filter(UserCard.user_id == user_id)
                        .filter(UserCard.card_id == card.id)
                    )
                    user_card_res = usercard_q.fetchone()
                    if user_card_res is None:
                        duplicate = 0
                    else:
                        duplicate = 1

                    user_card = await ssn.merge(
                        UserCard(
                            user_id=winner,
                            card_id=card.id,
                            points=card.points,
                            card_rarity=card.rarity,
                            duplicate=duplicate,
                        )
                    )
                    await ssn.commit()
                    trgt_u_cards.append(user_card.id)
                    points += card.points

                new_pack_two = await ssn.merge(CardPack(user_id=winner))
                await ssn.commit()
                pack_two_id = new_pack_two.id

                for u_id in trgt_u_cards:
                    await ssn.merge(CardXPack(pack_id=pack_two_id, user_card_id=u_id))
                await ssn.commit()

                cards_quant = len(ownr_u_cards) + len(trgt_u_cards)
                await ssn.execute(
                    update(Player)
                    .filter(Player.id == winner)
                    .values(
                        rating=Player.rating + points,
                        card_quants=Player.card_quants + cards_quant,
                        season_rating=Player.season_rating + points,
                    )
                )
                await ssn.commit()

            await ssn.execute(
                update(PackBattle)
                .filter(PackBattle.id == battle_id)
                .values(
                    owner_points=owner_result[0],
                    owner_ts=0,
                    target_points=target_result[0],
                    target_ts=0,
                    winner=winner,
                    status="closed",
                )
            )
            await ssn.commit()
            logging.info(
                f"Card Battle {battle_id} | p1 {battle.owner} vs p2 {battle.target} | winner {winner}"
            )
            return battle, winner, pack_one_id, pack_two_id
    else:
        if battle.owner_ready == 0:
            date = datetime.datetime.now()
            date_ts = int(date.timestamp())

            await ssn.execute(
                update(PackBattle)
                .filter(PackBattle.id == battle_id)
                .values(owner_ts=date_ts + 60, target_ts=0, target_ready=1)
            )
            await ssn.commit()
            return battle, "not_ready"
        else:
            if battle.quant == 0:
                owner_result = await calc_leg_pack(ssn, battle.owner)
                target_result = await calc_leg_pack(ssn, battle.target)
            else:
                owner_result = await calc_default_pack(ssn, battle.owner, battle.quant)
                target_result = await calc_default_pack(
                    ssn, battle.target, battle.quant
                )

            if owner_result[0] == target_result[0]:
                winner = 0

                owner_points = 0
                ownr_u_cards = []
                for card_id in owner_result[1]:
                    card_q = await ssn.execute(
                        select(CardItem).filter(CardItem.id == card_id)
                    )
                    card: CardItem = card_q.fetchone()[0]
                    usercard_q = await ssn.execute(
                        select(UserCard)
                        .filter(UserCard.user_id == battle.owner)
                        .filter(UserCard.card_id == card.id)
                    )
                    user_card_res = usercard_q.fetchone()
                    if user_card_res is None:
                        duplicate = 0
                    else:
                        duplicate = 1

                    user_card = await ssn.merge(
                        UserCard(
                            user_id=battle.owner,
                            card_id=card.id,
                            points=card.points,
                            card_rarity=card.rarity,
                            duplicate=duplicate,
                        )
                    )
                    await ssn.commit()
                    ownr_u_cards.append(user_card.id)
                    owner_points += card.points

                new_pack_one = await ssn.merge(CardPack(user_id=battle.owner))
                await ssn.execute(
                    update(Player)
                    .filter(Player.id == battle.owner)
                    .values(
                        rating=Player.rating + owner_points,
                        card_quants=Player.card_quants + len(ownr_u_cards),
                        season_rating=Player.season_rating + owner_points,
                    )
                )
                await ssn.commit()
                pack_one_id = new_pack_one.id

                for u_id in ownr_u_cards:
                    await ssn.merge(CardXPack(pack_id=pack_one_id, user_card_id=u_id))
                await ssn.commit()

                target_points = 0
                trgt_u_cards = []
                for card_id in target_result[1]:
                    card_q = await ssn.execute(
                        select(CardItem).filter(CardItem.id == card_id)
                    )
                    card: CardItem = card_q.fetchone()[0]
                    usercard_q = await ssn.execute(
                        select(UserCard)
                        .filter(UserCard.user_id == battle.target)
                        .filter(UserCard.card_id == card.id)
                    )
                    user_card_res = usercard_q.fetchone()
                    if user_card_res is None:
                        duplicate = 0
                    else:
                        duplicate = 1

                    user_card = await ssn.merge(
                        UserCard(
                            user_id=battle.target,
                            card_id=card.id,
                            points=card.points,
                            card_rarity=card.rarity,
                            duplicate=duplicate,
                        )
                    )
                    await ssn.commit()
                    trgt_u_cards.append(user_card.id)
                    target_points += card.points

                new_pack_two = await ssn.merge(CardPack(user_id=battle.target))
                await ssn.execute(
                    update(Player)
                    .filter(Player.id == battle.target)
                    .values(
                        rating=Player.rating + target_points,
                        card_quants=Player.card_quants + len(trgt_u_cards),
                        season_rating=Player.season_rating + target_points,
                    )
                )
                await ssn.commit()
                pack_two_id = new_pack_two.id

                for u_id in trgt_u_cards:
                    await ssn.merge(CardXPack(pack_id=pack_two_id, user_card_id=u_id))
                await ssn.commit()

            else:
                if owner_result[0] > target_result[0]:
                    winner = battle.owner
                else:
                    winner = battle.target

                points = 0
                ownr_u_cards = []
                for card_id in owner_result[1]:
                    card_q = await ssn.execute(
                        select(CardItem).filter(CardItem.id == card_id)
                    )
                    card: CardItem = card_q.fetchone()[0]
                    usercard_q = await ssn.execute(
                        select(UserCard)
                        .filter(UserCard.user_id == winner)
                        .filter(UserCard.card_id == card.id)
                    )
                    user_card_res = usercard_q.fetchone()
                    if user_card_res is None:
                        duplicate = 0
                    else:
                        duplicate = 1

                    user_card = await ssn.merge(
                        UserCard(
                            user_id=winner,
                            card_id=card.id,
                            points=card.points,
                            card_rarity=card.rarity,
                            duplicate=duplicate,
                        )
                    )
                    await ssn.commit()
                    ownr_u_cards.append(user_card.id)
                    points += card.points
                new_pack_one = await ssn.merge(CardPack(user_id=winner))
                await ssn.commit()
                pack_one_id = new_pack_one.id

                for u_id in ownr_u_cards:
                    await ssn.merge(CardXPack(pack_id=pack_one_id, user_card_id=u_id))
                await ssn.commit()

                trgt_u_cards = []
                for card_id in target_result[1]:
                    card_q = await ssn.execute(
                        select(CardItem).filter(CardItem.id == card_id)
                    )
                    card: CardItem = card_q.fetchone()[0]
                    usercard_q = await ssn.execute(
                        select(UserCard)
                        .filter(UserCard.user_id == winner)
                        .filter(UserCard.card_id == card.id)
                    )
                    user_card_res = usercard_q.fetchone()
                    if user_card_res is None:
                        duplicate = 0
                    else:
                        duplicate = 1

                    user_card = await ssn.merge(
                        UserCard(
                            user_id=winner,
                            card_id=card.id,
                            points=card.points,
                            card_rarity=card.rarity,
                            duplicate=duplicate,
                        )
                    )
                    await ssn.commit()
                    trgt_u_cards.append(user_card.id)
                    points += card.points

                new_pack_two = await ssn.merge(CardPack(user_id=winner))
                await ssn.commit()
                pack_two_id = new_pack_two.id

                for u_id in trgt_u_cards:
                    await ssn.merge(CardXPack(pack_id=pack_two_id, user_card_id=u_id))
                await ssn.commit()

                cards_quant = len(ownr_u_cards) + len(trgt_u_cards)
                await ssn.execute(
                    update(Player)
                    .filter(Player.id == winner)
                    .values(
                        rating=Player.rating + points,
                        card_quants=Player.card_quants + cards_quant,
                        season_rating=Player.season_rating + points,
                    )
                )
                await ssn.commit()

            await ssn.execute(
                update(PackBattle)
                .filter(PackBattle.id == battle_id)
                .values(
                    owner_points=owner_result[0],
                    owner_ts=0,
                    target_points=target_result[0],
                    target_ts=0,
                    winner=winner,
                    status="closed",
                )
            )
            await ssn.commit()
            logging.info(
                f"Card Battle {battle_id} | p1 {battle.owner} vs p2 {battle.target} | winner {winner}"
            )
            return battle, winner, pack_one_id, pack_two_id


async def calc_leg_pack(ssn: AsyncSession, user_id):
    leg_cards_q = await ssn.execute(
        select(CardItem)
        .filter(CardItem.rarity == "ЛЕГЕНДАРНАЯ")
        .filter(CardItem.status == "on")
    )
    leg_cards = leg_cards_q.scalars().all()
    leg_card: CardItem = random.choice(leg_cards)

    points = leg_card.points
    card_ids = []

    for _ in range(9):
        rarity = await card_rarity_randomize("card")
        cards_q = await ssn.execute(
            select(CardItem)
            .filter(CardItem.rarity == rarity)
            .filter(CardItem.status == "on")
        )
        cards = cards_q.scalars().all()
        card: CardItem = random.choice(cards)
        points += card.points
        card_ids.append(card.id)

    return points, card_ids


async def calc_default_pack(ssn: AsyncSession, user_id, quant):
    points = 0
    card_ids = []

    kind = "card"

    for _ in range(quant):
        rarity = await card_rarity_randomize(kind)
        cards_q = await ssn.execute(
            select(CardItem)
            .filter(CardItem.rarity == rarity)
            .filter(CardItem.status == "on")
        )
        cards = cards_q.scalars().all()
        card: CardItem = random.choice(cards)
        points += card.points
        card_ids.append(card.id)

    return points, card_ids


async def get_active_battles(db):
    ssn: AsyncSession
    async with db() as ssn:
        battles_q = await ssn.execute(
            select(PackBattle).filter(PackBattle.status == "active")
        )
        battles = battles_q.scalars().all()

        return battles
