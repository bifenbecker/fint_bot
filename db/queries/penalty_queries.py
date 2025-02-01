import asyncio
import datetime as dt
import logging
import random

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Penalty, Player, Trade, UserCard
from utils.const import rarities
from utils.misc import (
    send_card_penalty_answer,
    send_card_penalty_offer,
    send_penalty_action,
    send_penalty_offer,
    send_random_penalty_offer,
)


async def get_user_penalty_info(ssn: AsyncSession, user_id):
    user_q = await ssn.execute(select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    place_q = await ssn.execute(
        select(Player.id)
        .filter(Player.id != user_id)
        .filter(Player.season_penalty > user.season_penalty)
    )
    place = place_q.scalars().all()

    return user, len(place) + 1


async def check_for_active_penalty(ssn: AsyncSession, user_id):
    penalty_q = await ssn.execute(
        select(Penalty)
        .filter(or_(Penalty.target == user_id, Penalty.owner == user_id))
        .filter(Penalty.status == "active")
    )
    penalty_res = penalty_q.fetchone()
    if penalty_res is None:
        return "available"

    return "already_playing"


async def check_for_active_penalty_card(ssn: AsyncSession, user_id):
    trade_q = await ssn.execute(
        select(Trade)
        .filter(or_(Trade.target == user_id, Trade.owner == user_id))
        .filter(Trade.status.in_(["target_wait", "owner_wait"]))
    )
    trade_res = trade_q.fetchone()
    if trade_res is not None:
        return "active_trade"

    penalty_q = await ssn.execute(
        select(Penalty)
        .filter(or_(Penalty.target == user_id, Penalty.owner == user_id))
        .filter(Penalty.status == "active")
    )
    penalty_res = penalty_q.fetchone()
    if penalty_res is None:
        return "available"

    return "already_playing"


async def find_penalty_opp(ssn: AsyncSession, user_id, bot):
    penalty_q = await ssn.execute(
        select(Penalty)
        .filter(or_(Penalty.target == user_id, Penalty.owner == user_id))
        .filter(Penalty.status == "active")
    )
    penalty_res = penalty_q.fetchone()
    if penalty_res is not None:
        return "already_playing"

    user_q = await ssn.execute(select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    low_rating = user.season_penalty - 400
    high_rating = user.season_penalty + 400
    targets_q = await ssn.execute(
        select(Player)
        .filter(Player.penalty_queue == 1)
        .filter(Player.season_penalty >= low_rating)
        .filter(Player.season_penalty <= high_rating)
        .filter(Player.id != user_id)
    )
    targets = targets_q.scalars().all()
    if len(targets) == 0:
        await ssn.execute(
            update(Player).filter(Player.id == user_id).values(penalty_queue=1)
        )
        await ssn.commit()
        return "queue_on"

    target: Player = random.choice(targets)
    if target.penalty_queue == 1:
        await ssn.execute(
            update(Player).filter(Player.id == target.id).values(penalty_queue=0)
        )
    if user.penalty_queue == 1:
        await ssn.execute(
            update(Player).filter(Player.id == user.id).values(penalty_queue=0)
        )

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    penalty = await ssn.merge(
        Penalty(
            owner=user_id,
            owner_username=user.username,
            target=target.id,
            target_username=target.username,
        )
    )
    await ssn.commit()
    penalty_id = penalty.id
    msg_id = await send_random_penalty_offer(bot, target.id, user.username, penalty_id)
    if msg_id == 0:
        await ssn.execute(
            update(Penalty).filter(Penalty.id == penalty_id).values(status="error")
        )
        await ssn.commit()
        return "error"
    else:
        await ssn.execute(
            update(Penalty)
            .filter(Penalty.id == penalty_id)
            .values(kind="random", target_msg_id=msg_id, last_action=date_ts + 60)
        )
        await ssn.commit()
        logging.info(
            f"User {user_id} created random penaly #{penalty_id} vs {target.id} ({target.username})"
        )
        return penalty_id, date_ts + 60, target.username


async def cancel_pen_queue(ssn: AsyncSession, user_id):
    await ssn.execute(
        update(Player).filter(Player.id == user_id).values(penalty_queue=0)
    )
    await ssn.commit()


async def create_new_penalty(
    ssn: AsyncSession, user_id, username, target_username, bot
):
    penalty_q = await ssn.execute(
        select(Penalty)
        .filter(or_(Penalty.target == user_id, Penalty.owner == user_id))
        .filter(Penalty.status == "active")
    )
    penalty_res = penalty_q.fetchone()
    if penalty_res is not None:
        return "already_playing"

    target_q = await ssn.execute(
        select(Player).filter(Player.username.ilike(target_username))
    )
    target_res = target_q.fetchone()
    if target_res is None:
        return "not_found"

    if user_id == target_res[0].id:
        return "self_error"

    user_q = await ssn.execute(select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]
    target: Player = target_res[0]

    rating_delta = abs(user.season_penalty - target.season_penalty)
    if rating_delta > 300:
        return "rating_diff"

    target_penalty_q = await ssn.execute(
        select(Penalty)
        .filter(or_(Penalty.target == target.id, Penalty.owner == target.id))
        .filter(Penalty.status == "active")
    )
    target_penalty_res = target_penalty_q.fetchone()
    if target_penalty_res is not None:
        return "target_already_playing"

    if target.penalty_queue == 1:
        await ssn.execute(
            update(Player).filter(Player.id == target.id).values(penalty_queue=0)
        )
    if user.penalty_queue == 1:
        await ssn.execute(
            update(Player).filter(Player.id == user.id).values(penalty_queue=0)
        )

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    penalty = await ssn.merge(
        Penalty(
            owner=user_id,
            owner_username=username,
            target=target.id,
            target_username=target.username,
        )
    )
    await ssn.commit()
    penalty_id = penalty.id
    msg_id = await send_penalty_offer(bot, target.id, username, penalty_id)
    if msg_id == 0:
        await ssn.execute(
            update(Penalty).filter(Penalty.id == penalty_id).values(status="error")
        )
        await ssn.commit()
        return "error"
    else:
        await ssn.execute(
            update(Penalty)
            .filter(Penalty.id == penalty_id)
            .values(target_msg_id=msg_id, last_action=date_ts + 60)
        )
        await ssn.commit()
        logging.info(
            f"User {user_id} created new penaly #{penalty_id} to {target.id} ({target.username})"
        )
        return penalty_id, date_ts + 60


async def create_new_card_penalty(
    ssn: AsyncSession, user_id, username, target_username, card_id, bot
):
    penalty_q = await ssn.execute(
        select(Penalty)
        .filter(or_(Penalty.target == user_id, Penalty.owner == user_id))
        .filter(Penalty.status == "active")
    )
    penalty_res = penalty_q.fetchone()
    if penalty_res is not None:
        return "already_playing"

    cards_q = await ssn.execute(
        select(UserCard)
        .filter(UserCard.card_id == card_id)
        .filter(UserCard.user_id == user_id)
        .options(selectinload(UserCard.card))
    )
    cards = cards_q.scalars().all()
    if len(cards) == 0:
        return "no_card"

    image = cards[0].card.image

    target_q = await ssn.execute(
        select(Player).filter(Player.username.ilike(target_username))
    )
    target_res = target_q.fetchone()
    if target_res is None:
        return "not_found"

    if user_id == target_res[0].id:
        return "self_error"

    user_q = await ssn.execute(select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]
    target: Player = target_res[0]

    target_penalty_q = await ssn.execute(
        select(Penalty)
        .filter(or_(Penalty.target == target.id, Penalty.owner == target.id))
        .filter(Penalty.status == "active")
    )
    target_penalty_res = target_penalty_q.fetchone()
    if target_penalty_res is not None:
        return "target_already_playing"

    access_q: Player = await ssn.execute(
        select(Player).filter(Player.username == target_username)
    )
    access_q = access_q.scalars().first()
    access: str = access_q.access_minigame

    if access == "not":
        return "not_access"

    if target.penalty_queue == 1:
        await ssn.execute(
            update(Player).filter(Player.id == target.id).values(penalty_queue=0)
        )
    if user.penalty_queue == 1:
        await ssn.execute(
            update(Player).filter(Player.id == user.id).values(penalty_queue=0)
        )

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    penalty = await ssn.merge(
        Penalty(
            owner=user_id,
            owner_username=username,
            owner_card_id=card_id,
            target=target.id,
            target_username=target.username,
        )
    )
    await ssn.commit()
    penalty_id = penalty.id
    msg_id = await send_card_penalty_offer(bot, target.id, username, penalty_id, image)
    if msg_id == 0:
        await ssn.execute(
            update(Penalty).filter(Penalty.id == penalty_id).values(status="error")
        )
        await ssn.commit()
        return "error"
    else:
        await ssn.execute(
            update(Penalty)
            .filter(Penalty.id == penalty_id)
            .values(target_msg_id=msg_id, last_action=date_ts + 60)
        )
        await ssn.commit()
        logging.info(
            f"User {user_id} created new card penaly #{penalty_id} to {target.id} ({target.username})"
        )
        return penalty_id, date_ts + 60


async def answer_card_penalty(ssn: AsyncSession, user_id, pen_id, card_id, bot):
    penalty_q = await ssn.execute(select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.status != "active":
        return "not_active"

    cards_q = await ssn.execute(
        select(UserCard)
        .filter(UserCard.card_id == card_id)
        .filter(UserCard.user_id == user_id)
        .options(selectinload(UserCard.card))
    )
    cards = cards_q.scalars().all()
    if len(cards) == 0:
        return "no_card"

    image = cards[0].card.image

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    msg_id = await send_card_penalty_answer(
        bot, penalty.owner, penalty.target_username, pen_id, image
    )
    if msg_id == 0:
        await ssn.execute(
            update(Penalty).filter(Penalty.id == pen_id).values(status="error")
        )
        await ssn.commit()
        return "error"
    else:
        await ssn.execute(
            update(Penalty)
            .filter(Penalty.id == pen_id)
            .values(
                target_card_id=card_id, owner_msg_id=msg_id, last_action=date_ts + 60
            )
        )
        await ssn.commit()
        logging.info(f"User {user_id} answered card penaly #{pen_id}")
        return date_ts + 60, penalty.owner_username


async def check_penalty(db, penalty_id, date_ts):
    ssn: AsyncSession
    async with db() as ssn:
        penalty_q = await ssn.execute(select(Penalty).filter(Penalty.id == penalty_id))
        penalty: Penalty = penalty_q.fetchone()[0]
        if penalty.last_action == date_ts:
            if penalty.kicker == penalty.keeper == 0:
                await ssn.execute(
                    update(Penalty)
                    .filter(Penalty.id == penalty_id)
                    .values(status="auto_canceled", last_action=0)
                )
                await ssn.commit()
                logging.info(f"Penalty {penalty_id} auto canceled")
            else:
                if penalty.owner_card_id != 0 and penalty.target_card_id != 0:
                    owner_cards_q = await ssn.execute(
                        select(UserCard)
                        .filter(UserCard.user_id == penalty.owner)
                        .filter(UserCard.card_id == penalty.owner_card_id)
                        .order_by(UserCard.duplicate.desc())
                    )
                    owner_cards = owner_cards_q.scalars().all()

                    target_cards_q = await ssn.execute(
                        select(UserCard)
                        .filter(UserCard.user_id == penalty.target)
                        .filter(UserCard.card_id == penalty.target_card_id)
                        .order_by(UserCard.duplicate.desc())
                    )
                    target_cards = target_cards_q.scalars().all()

                    if (len(owner_cards) == 0) or (len(target_cards) == 0):
                        await ssn.execute(
                            update(Penalty)
                            .filter(Penalty.id == penalty_id)
                            .values(last_action=0, winner=0, status="error")
                        )
                        await ssn.commit()
                        return False

                    if penalty.turn_user_id == penalty.target:
                        owner_dup_check_q = await ssn.execute(
                            select(UserCard)
                            .filter(UserCard.card_id == penalty.target_card_id)
                            .filter(UserCard.user_id == penalty.owner)
                        )
                        owner_dup_check_res = owner_dup_check_q.fetchone()
                        if owner_dup_check_res is None:
                            owner_duplicate = 0
                        else:
                            owner_duplicate = 1

                        owner_rating = target_cards[0].points
                        owner_quant = 1
                        target_rating = -target_cards[0].points
                        target_quant = -1
                        winner = penalty.owner

                        await ssn.execute(
                            update(UserCard)
                            .filter(UserCard.id == target_cards[0].id)
                            .values(user_id=penalty.owner, duplicate=owner_duplicate)
                        )
                        await ssn.execute(
                            update(Penalty)
                            .filter(Penalty.id == penalty_id)
                            .values(
                                last_action=0, winner=winner, status="owner_auto_win"
                            )
                        )
                        logging.info(f"Penalty {penalty_id} owner auto win")

                    else:
                        target_dup_check_q = await ssn.execute(
                            select(UserCard)
                            .filter(UserCard.card_id == penalty.owner_card_id)
                            .filter(UserCard.user_id == penalty.target)
                        )
                        target_dup_check_res = target_dup_check_q.fetchone()
                        if target_dup_check_res is None:
                            target_duplicate = 0
                        else:
                            target_duplicate = 1

                        owner_rating = -owner_cards[0].points
                        owner_quant = -1
                        target_rating = owner_cards[0].points
                        target_quant = 1
                        winner = penalty.target

                        await ssn.execute(
                            update(UserCard)
                            .filter(UserCard.id == owner_cards[0].id)
                            .values(user_id=penalty.target, duplicate=target_duplicate)
                        )
                        await ssn.execute(
                            update(Penalty)
                            .filter(Penalty.id == penalty_id)
                            .values(
                                last_action=0, winner=winner, status="target_auto_win"
                            )
                        )
                        logging.info(f"Penalty {penalty_id} target auto win")

                    owner_user_q = await ssn.execute(
                        select(Player).filter(Player.id == penalty.owner)
                    )
                    owner_user: Player = owner_user_q.fetchone()[0]

                    if (owner_user.season_rating + owner_rating) < 0:
                        new_owner_s_rating = 0
                    else:
                        new_owner_s_rating = owner_user.season_rating + owner_rating

                    await ssn.execute(
                        update(Player)
                        .filter(Player.id == penalty.owner)
                        .values(
                            rating=Player.rating + owner_rating,
                            card_quants=Player.card_quants + owner_quant,
                            # season_rating=new_owner_s_rating,
                        )
                    )

                    target_user_q = await ssn.execute(
                        select(Player).filter(Player.id == penalty.target)
                    )
                    target_user: Player = target_user_q.fetchone()[0]

                    if (target_user.season_rating + target_rating) < 0:
                        new_target_s_rating = 0
                    else:
                        new_target_s_rating = target_user.season_rating + target_rating

                    await ssn.execute(
                        update(Player)
                        .filter(Player.id == penalty.target)
                        .values(
                            rating=Player.rating + target_rating,
                            card_quants=Player.card_quants + target_quant,
                            # season_rating=new_target_s_rating,
                        )
                    )
                    await ssn.commit()
                else:
                    if penalty.turn_user_id == penalty.owner:
                        if penalty.kind == "random":
                            await ssn.execute(
                                update(Player)
                                .filter(Player.id == penalty.target)
                                .values(season_penalty=Player.season_penalty + 25)
                            )

                            owner_user_q = await ssn.execute(
                                select(Player).filter(Player.id == penalty.owner)
                            )
                            owner_user: Player = owner_user_q.fetchone()[0]

                            if (owner_user.season_penalty - 25) < 0:
                                new_owner_s_rating = 0
                            else:
                                new_owner_s_rating = owner_user.season_penalty - 25

                            await ssn.execute(
                                update(Player)
                                .filter(Player.id == penalty.owner)
                                .values(season_penalty=new_owner_s_rating)
                            )

                        await ssn.execute(
                            update(Penalty)
                            .filter(Penalty.id == penalty_id)
                            .values(
                                status="target_auto_win",
                                last_action=0,
                                winner=penalty.target,
                            )
                        )
                        logging.info(f"Penalty {penalty_id} target auto win")

                    else:
                        if penalty.kind == "random":
                            await ssn.execute(
                                update(Player)
                                .filter(Player.id == penalty.owner)
                                .values(season_penalty=Player.season_penalty + 25)
                            )

                            target_user_q = await ssn.execute(
                                select(Player).filter(Player.id == penalty.target)
                            )
                            target_user: Player = target_user_q.fetchone()[0]

                            if (target_user.season_penalty - 25) < 0:
                                new_target_s_rating = 0
                            else:
                                new_target_s_rating = target_user.season_penalty - 25

                            await ssn.execute(
                                update(Player)
                                .filter(Player.id == penalty.target)
                                .values(season_penalty=new_target_s_rating)
                            )

                        await ssn.execute(
                            update(Penalty)
                            .filter(Penalty.id == penalty_id)
                            .values(
                                status="owner_auto_win",
                                last_action=0,
                                winner=penalty.owner,
                            )
                        )
                        logging.info(f"Penalty {penalty_id} owner auto win")

                    await ssn.execute(
                        update(Player)
                        .filter(Player.season_penalty < 0)
                        .filter(Player.id.in_([penalty.owner, penalty.target]))
                        .values(season_penalty=0)
                    )

                    await ssn.commit()

            return penalty
        return False


async def cancel_penalty(ssn: AsyncSession, pen_id):
    penalty_q = await ssn.execute(select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.status == "active":
        await ssn.execute(
            update(Penalty)
            .filter(Penalty.id == pen_id)
            .values(status="canceled", last_action=0)
        )
        await ssn.commit()
        logging.info(f"User {penalty.target} canceled penalty {pen_id}")
        return penalty

    return "not_active"


async def start_penalty(ssn: AsyncSession, pen_id, bot):
    penalty_q = await ssn.execute(select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.status != "active":
        return "not_active"

    msg_owner_id = await send_penalty_action(bot, penalty.owner, pen_id, "kicker")
    await asyncio.sleep(0.01)
    msg_target_id = await send_penalty_action(bot, penalty.target, pen_id, "keeper")

    if (msg_owner_id == 0) or (msg_target_id == 0):
        await ssn.execute(
            update(Penalty)
            .filter(Penalty.id == pen_id)
            .values(status="canceled", last_action=0)
        )
        await ssn.commit()
        logging.info(f"Penalty {pen_id} canceled with error")
        return "error"

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    await ssn.execute(
        update(Penalty)
        .filter(Penalty.id == pen_id)
        .values(
            owner_msg_id=msg_owner_id,
            target_msg_id=msg_target_id,
            turn_user_id=penalty.owner,
            kicker=penalty.owner,
            keeper=penalty.target,
            last_action=date_ts + 60,
        )
    )
    await ssn.commit()
    logging.info(f"Penalty {pen_id} started")
    return date_ts + 60


async def start_card_penalty(ssn: AsyncSession, pen_id, bot):
    penalty_q = await ssn.execute(select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.status != "active":
        return "not_active"

    msg_owner_id = await send_penalty_action(bot, penalty.owner, pen_id, "kicker")
    await asyncio.sleep(0.01)
    msg_target_id = await send_penalty_action(bot, penalty.target, pen_id, "keeper")

    if (msg_owner_id == 0) or (msg_target_id == 0):
        await ssn.execute(
            update(Penalty)
            .filter(Penalty.id == pen_id)
            .values(status="canceled", last_action=0)
        )
        await ssn.commit()
        logging.info(f"Penalty {pen_id} canceled with error")
        return "error"

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    await ssn.execute(
        update(Penalty)
        .filter(Penalty.id == pen_id)
        .values(
            owner_msg_id=msg_owner_id,
            target_msg_id=msg_target_id,
            turn_user_id=penalty.owner,
            kicker=penalty.owner,
            keeper=penalty.target,
            last_action=date_ts + 180,
        )
    )
    await ssn.commit()
    logging.info(f"Card Penalty {pen_id} started")
    return date_ts + 180


async def kicker_action(ssn: AsyncSession, pen_id, user_id, kicker_pick):
    penalty_q = await ssn.execute(select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.status != "active":
        return "not_active"

    date = dt.datetime.now()
    date_ts = int(date.timestamp())
    if penalty.owner_card_id == 0:
        new_date_ts = date_ts + 60
        delay = 60
    else:
        new_date_ts = date_ts + 180
        delay = 180

    await ssn.execute(
        update(Penalty)
        .filter(Penalty.id == pen_id)
        .values(
            turn_user_id=penalty.keeper,
            kicker_pick=kicker_pick,
            last_action=new_date_ts,
        )
    )
    await ssn.commit()
    logging.info(f"Penalty {pen_id} | Kicker {user_id} kick to pos {kicker_pick}")
    return new_date_ts, delay


async def keeper_action(ssn: AsyncSession, pen_id, user_id, keeper_pick):
    penalty_q = await ssn.execute(select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.status != "active":
        return "not_active"

    if penalty.kicker_pick == 0:
        return "not_ready"

    result = penalty.kicker_pick == keeper_pick
    if penalty.round == 10:
        if penalty.kicker_pick == keeper_pick:
            if penalty.kicker == penalty.owner:
                owner_txt = penalty.owner_txt + "0"
                target_txt = penalty.target_txt
            else:
                owner_txt = penalty.owner_txt
                target_txt = penalty.target_txt + "0"
            owner_score = penalty.owner_score
            target_score = penalty.target_score
        else:
            if penalty.kicker == penalty.owner:
                owner_txt = penalty.owner_txt + "1"
                target_txt = penalty.target_txt
                owner_score = penalty.owner_score + 1
                target_score = penalty.target_score
            else:
                owner_txt = penalty.owner_txt
                target_txt = penalty.target_txt + "1"
                owner_score = penalty.owner_score
                target_score = penalty.target_score + 1

        if penalty.owner_card_id != 0 and penalty.target_card_id != 0:
            owner_cards_q = await ssn.execute(
                select(UserCard)
                .filter(UserCard.user_id == penalty.owner)
                .filter(UserCard.card_id == penalty.owner_card_id)
                .order_by(UserCard.duplicate.desc())
            )
            owner_cards = owner_cards_q.scalars().all()

            target_cards_q = await ssn.execute(
                select(UserCard)
                .filter(UserCard.user_id == penalty.target)
                .filter(UserCard.card_id == penalty.target_card_id)
                .order_by(UserCard.duplicate.desc())
            )
            target_cards = target_cards_q.scalars().all()

            if (len(owner_cards) == 0) or (len(target_cards) == 0):
                await ssn.execute(
                    update(Penalty)
                    .filter(Penalty.id == pen_id)
                    .values(last_action=0, winner=0, status="error")
                )
                await ssn.commit()
                return "error"

            if owner_score > target_score:
                owner_dup_check_q = await ssn.execute(
                    select(UserCard)
                    .filter(UserCard.card_id == penalty.target_card_id)
                    .filter(UserCard.user_id == penalty.owner)
                )
                owner_dup_check_res = owner_dup_check_q.fetchone()
                if owner_dup_check_res is None:
                    owner_duplicate = 0
                else:
                    owner_duplicate = 1

                owner_rating = target_cards[0].points
                owner_quant = 1
                target_rating = -target_cards[0].points
                target_quant = -1
                winner = penalty.owner
                owner_wins = 1
                owner_loses = 0
                target_wins = 0
                target_loses = 1

                await ssn.execute(
                    update(UserCard)
                    .filter(UserCard.id == target_cards[0].id)
                    .values(user_id=penalty.owner, duplicate=owner_duplicate)
                )

            elif owner_score < target_score:
                target_dup_check_q = await ssn.execute(
                    select(UserCard)
                    .filter(UserCard.card_id == penalty.owner_card_id)
                    .filter(UserCard.user_id == penalty.target)
                )
                target_dup_check_res = target_dup_check_q.fetchone()
                if target_dup_check_res is None:
                    target_duplicate = 0
                else:
                    target_duplicate = 1

                owner_rating = -owner_cards[0].points
                owner_quant = -1
                target_rating = owner_cards[0].points
                target_quant = 1
                winner = penalty.target
                owner_wins = 0
                owner_loses = 1
                target_wins = 1
                target_loses = 0

                await ssn.execute(
                    update(UserCard)
                    .filter(UserCard.id == owner_cards[0].id)
                    .values(user_id=penalty.target, duplicate=target_duplicate)
                )
            else:
                owner_rating = 0
                owner_quant = 0
                target_rating = 0
                target_quant = 0
                winner = 0
                owner_wins = 0
                owner_loses = 0
                target_wins = 0
                target_loses = 0

            if owner_rating != 0:
                owner_user_q = await ssn.execute(
                    select(Player).filter(Player.id == penalty.owner)
                )
                owner_user: Player = owner_user_q.fetchone()[0]

                if (owner_user.season_rating + owner_rating) < 0:
                    new_owner_s_rating = 0
                else:
                    new_owner_s_rating = owner_user.season_rating + owner_rating

                await ssn.execute(
                    update(Player)
                    .filter(Player.id == penalty.owner)
                    .values(
                        rating=Player.rating + owner_rating,
                        card_quants=Player.card_quants + owner_quant,
                        # season_rating=new_owner_s_rating,
                        pen_wins=Player.pen_wins + owner_wins,
                        pen_loses=Player.pen_loses + owner_loses,
                    )
                )

                target_user_q = await ssn.execute(
                    select(Player).filter(Player.id == penalty.target)
                )
                target_user: Player = target_user_q.fetchone()[0]

                if (target_user.season_rating + target_rating) < 0:
                    new_target_s_rating = 0
                else:
                    new_target_s_rating = target_user.season_rating + target_rating

                await ssn.execute(
                    update(Player)
                    .filter(Player.id == penalty.target)
                    .values(
                        rating=Player.rating + target_rating,
                        card_quants=Player.card_quants + target_quant,
                        # season_rating=new_target_s_rating,
                        pen_wins=Player.pen_wins + target_wins,
                        pen_loses=Player.pen_loses + target_loses,
                    )
                )

            await ssn.execute(
                update(Penalty)
                .filter(Penalty.id == pen_id)
                .values(
                    owner_txt=owner_txt,
                    target_txt=target_txt,
                    owner_score=owner_score,
                    target_score=target_score,
                    last_action=0,
                    winner=winner,
                    status="finished",
                )
            )
            await ssn.commit()
            logging.info(
                f"Card penalty {pen_id} | Keeper {user_id} saved pos {keeper_pick} | Winner {winner}"
            )
            return penalty, result

        else:
            if owner_score > target_score:
                owner_rating = 25
                target_rating = -25
                owner_wins = 1
                owner_loses = 0
                target_wins = 0
                target_loses = 1
                winner = penalty.owner
            elif owner_score < target_score:
                owner_rating = -25
                target_rating = 25
                owner_wins = 0
                owner_loses = 1
                target_wins = 1
                target_loses = 0
                winner = penalty.target
            else:
                owner_rating = 0
                target_rating = 0
                winner = 0
                owner_wins = 0
                target_wins = 0
                owner_loses = 0
                target_loses = 0

            if (owner_rating != 0) and (penalty.kind == "random"):
                owner_user_q = await ssn.execute(
                    select(Player).filter(Player.id == penalty.owner)
                )
                owner_user: Player = owner_user_q.fetchone()[0]

                if (owner_user.season_penalty + owner_rating) < 0:
                    new_owner_s_rating = 0
                else:
                    new_owner_s_rating = owner_user.season_penalty + owner_rating

                await ssn.execute(
                    update(Player)
                    .filter(Player.id == penalty.owner)
                    .values(
                        season_penalty=new_owner_s_rating,
                        pen_wins=Player.pen_wins + owner_wins,
                        pen_loses=Player.pen_loses + owner_loses,
                    )
                )

                target_user_q = await ssn.execute(
                    select(Player).filter(Player.id == penalty.target)
                )
                target_user: Player = target_user_q.fetchone()[0]

                if (target_user.season_penalty + target_rating) < 0:
                    new_target_s_rating = 0
                else:
                    new_target_s_rating = target_user.season_penalty + target_rating

                await ssn.execute(
                    update(Player)
                    .filter(Player.id == penalty.target)
                    .values(
                        season_penalty=new_target_s_rating,
                        pen_wins=Player.pen_wins + target_wins,
                        pen_loses=Player.pen_loses + target_loses,
                    )
                )

            else:
                await ssn.execute(
                    update(Player)
                    .filter(Player.id == penalty.owner)
                    .values(
                        pen_wins=Player.pen_wins + owner_wins,
                        pen_loses=Player.pen_loses + owner_loses,
                    )
                )
                await ssn.execute(
                    update(Player)
                    .filter(Player.id == penalty.target)
                    .values(
                        pen_wins=Player.pen_wins + target_wins,
                        pen_loses=Player.pen_loses + target_loses,
                    )
                )

            await ssn.execute(
                update(Penalty)
                .filter(Penalty.id == pen_id)
                .values(
                    owner_txt=owner_txt,
                    target_txt=target_txt,
                    owner_score=owner_score,
                    target_score=target_score,
                    last_action=0,
                    winner=winner,
                    status="finished",
                )
            )
            await ssn.commit()
            await ssn.execute(
                update(Player)
                .filter(Player.season_penalty < 0)
                .filter(Player.id.in_([penalty.owner, penalty.target]))
                .values(season_penalty=0)
            )
            await ssn.commit()

            logging.info(
                f"Penalty {pen_id} | Keeper {user_id} saved pos {keeper_pick} | Winner {winner}"
            )
            return penalty, result
    else:
        if penalty.kicker_pick == keeper_pick:
            if penalty.kicker == penalty.owner:
                owner_txt = penalty.owner_txt + "0"
                target_txt = penalty.target_txt
            else:
                owner_txt = penalty.owner_txt
                target_txt = penalty.target_txt + "0"
            owner_score = 0
            target_score = 0
        else:
            if penalty.kicker == penalty.owner:
                owner_txt = penalty.owner_txt + "1"
                target_txt = penalty.target_txt
                owner_score = 1
                target_score = 0
            else:
                owner_txt = penalty.owner_txt
                target_txt = penalty.target_txt + "1"
                owner_score = 0
                target_score = 1

        if penalty.turn_user_id == penalty.owner:
            kicker = penalty.owner
            keeper = penalty.target
        else:
            kicker = penalty.target
            keeper = penalty.owner

        date = dt.datetime.now()
        date_ts = int(date.timestamp())
        if penalty.owner_card_id == 0:
            new_date_ts = date_ts + 60
            delay = 60
        else:
            new_date_ts = date_ts + 180
            delay = 180

        await ssn.execute(
            update(Penalty)
            .filter(Penalty.id == pen_id)
            .values(
                owner_txt=owner_txt,
                target_txt=target_txt,
                owner_score=Penalty.owner_score + owner_score,
                target_score=Penalty.target_score + target_score,
                kicker=kicker,
                keeper=keeper,
                last_action=new_date_ts,
                kicker_pick=0,
                round=Penalty.round + 1,
            )
        )
        await ssn.commit()
        logging.info(f"Penalty {pen_id} | Keeper {user_id} saved  pos {keeper_pick}")

        return penalty, result, new_date_ts, delay


async def penalty_switch(ssn: AsyncSession, pen_id, new_ts, bot):
    penalty_q = await ssn.execute(select(Penalty).filter(Penalty.id == pen_id))
    penalty: Penalty = penalty_q.fetchone()[0]

    if penalty.turn_user_id == penalty.owner:
        owner_kind = "kicker"
        target_kind = "keeper"
    else:
        owner_kind = "keeper"
        target_kind = "kicker"

    msg_owner_id = await send_penalty_action(bot, penalty.owner, pen_id, owner_kind)
    await asyncio.sleep(0.01)
    msg_target_id = await send_penalty_action(bot, penalty.target, pen_id, target_kind)

    if (msg_owner_id == 0) or (msg_target_id == 0):
        await ssn.execute(
            update(Penalty)
            .filter(Penalty.id == pen_id)
            .values(status="canceled", last_action=0)
        )
        await ssn.commit()
        logging.info(f"Penalty {pen_id} canceled with error")
        return "error"

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    await ssn.execute(
        update(Penalty)
        .filter(Penalty.id == pen_id)
        .values(
            owner_msg_id=msg_owner_id, target_msg_id=msg_target_id, last_action=new_ts
        )
    )
    await ssn.commit()
    return None


async def get_active_penalties(db):
    ssn: AsyncSession
    async with db() as ssn:
        penalties_q = await ssn.execute(
            select(Penalty).filter(Penalty.status == "active")
        )
        penalties = penalties_q.scalars().all()

        return penalties


async def get_penalty_card_rarities(ssn: AsyncSession, user_id):
    cards_q = await ssn.execute(
        select(UserCard.card_rarity)
        .filter(UserCard.user_id == user_id)
        .filter(UserCard.tradeble == "yes")
        .filter(UserCard.card_rarity != "Heroes")
        .filter(UserCard.card_rarity != "Icons")
        .filter(UserCard.card_rarity != "Limited")
    )
    cards = cards_q.scalars().all()
    user_rarities = set(cards)
    result = []
    for rarity in rarities:
        if rarity in user_rarities:
            result.append(rarity)

    return result


async def get_penalty_user_rarity_cards(ssn: AsyncSession, user_id, rarity, sorting):
    if rarity == "all":
        if sorting == "up":
            cards_q = await ssn.execute(
                select(UserCard)
                .filter(UserCard.user_id == user_id)
                .filter(UserCard.duplicate == 0)
                .filter(UserCard.tradeble == "yes")
                .filter(UserCard.card_rarity != "Heroes")
                .filter(UserCard.card_rarity != "Icons")
                .filter(UserCard.card_rarity != "Limited")
                .order_by(UserCard.points)
                .options(selectinload(UserCard.card))
            )
        elif sorting == "down":
            cards_q = await ssn.execute(
                select(UserCard)
                .filter(UserCard.user_id == user_id)
                .filter(UserCard.duplicate == 0)
                .filter(UserCard.tradeble == "yes")
                .filter(UserCard.card_rarity != "Heroes")
                .filter(UserCard.card_rarity != "Icons")
                .filter(UserCard.card_rarity != "Limited")
                .order_by(UserCard.points.desc())
                .options(selectinload(UserCard.card))
            )
        else:
            cards_q = await ssn.execute(
                select(UserCard)
                .filter(UserCard.user_id == user_id)
                .filter(UserCard.duplicate == 0)
                .filter(UserCard.tradeble == "yes")
                .filter(UserCard.card_rarity != "Heroes")
                .filter(UserCard.card_rarity != "Icons")
                .filter(UserCard.card_rarity != "Limited")
                .options(selectinload(UserCard.card))
            )
    else:
        cards_q = await ssn.execute(
            select(UserCard)
            .filter(UserCard.user_id == user_id)
            .filter(UserCard.card_rarity == rarity)
            .filter(UserCard.duplicate == 0)
            .filter(UserCard.tradeble == "yes")
            .options(selectinload(UserCard.card))
        )
    cards = cards_q.scalars().all()

    return cards


async def get_penalty_access_user(ssn: AsyncSession, user_id):
    """
    Возвращает значение из Player.access_minigame
    """
    access_q: Player = await ssn.execute(select(Player).filter(Player.id == user_id))

    access_q = access_q.scalars().first()

    access: str = access_q.access_minigame

    return access
