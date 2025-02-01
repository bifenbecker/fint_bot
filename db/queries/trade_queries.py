import datetime as dt
import logging

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Penalty, Player, Trade, UserCard, UserTrade
from utils.const import rarities


async def check_target_trade(ssn: AsyncSession, user_id, card_id):
    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.card_id == card_id).filter(
        UserCard.user_id == user_id).options(
        selectinload(UserCard.card)))
    cards = cards_q.scalars().all()
    if len(cards) == 0:
        return "no_card"

    trade_q = await ssn.execute(select(Trade).filter(
        or_(Trade.target == user_id, Trade.owner == user_id)).filter(
        Trade.status.in_(["target_wait", "owner_wait"])).filter(
        Trade.quant == 1))
    trade_res = trade_q.fetchone()
    if trade_res is None:
        return "username"
    else:
        trade: Trade = trade_res[0]
        if trade.owner == user_id:
            return "already_trading"
        else:
            if trade.status == "owner_wait":
                return "already_trading"
            else:
                await ssn.execute(update(Trade).filter(
                    Trade.id == trade.id).values(target_card_id=card_id))
                await ssn.commit()

                return trade, cards[0].card


async def create_new_trade(
        ssn: AsyncSession, user_id, username, card_id, target_username):
    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.card_id == card_id).filter(
        UserCard.user_id == user_id).filter(
        UserCard.tradeble == "yes").options(
        selectinload(UserCard.card)))
    cards = cards_q.scalars().all()
    if len(cards) == 0:
        return "no_card"
    
    access_q: Player = await ssn.execute(
        select(Player).filter(Player.username == target_username))
    access_q = access_q.scalars().first()
    access: str = access_q.access_minigame

    if access == "not":
        return "not_access"

    target_q = await ssn.execute(
        select(Player).filter(Player.username.ilike(target_username)))
    target_res = target_q.fetchone()
    if target_res is None:
        return "not_found"

    target: Player = target_res[0]
    if user_id == target.id:
        return "not_found"

    txts = [f"{user_id}_{target.id}", f"{target.id}_{user_id}"]
    u_trades_q = await ssn.execute(select(UserTrade).filter(
        UserTrade.user_x_user.in_(txts)))
    u_trades = u_trades_q.scalars().all()
    if len(u_trades) >= 5:
        return "user_limit"

    penalty_q = await ssn.execute(select(Penalty).filter(
        or_(Penalty.target.in_([user_id, target.id]), Penalty.owner.in_([user_id, target.id]))).filter(
        Penalty.status == "active"))
    penalty_res = penalty_q.fetchone()
    if penalty_res is not None:
        return "already_playing"

    trade = await ssn.merge(Trade(
        status="target_wait", owner=user_id,
        owner_username=username, owner_card_id=card_id,
        target=target.id, target_username=target.username))
    await ssn.commit()

    trade_id = trade.id

    return trade_id, target.id, cards[0].card


async def update_trade_status(ssn: AsyncSession, user_id, card_id, trade_id):
    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.card_id == card_id).filter(
        UserCard.user_id == user_id).filter(
        UserCard.tradeble == "yes").options(
        selectinload(UserCard.card)))
    cards = cards_q.scalars().all()
    if len(cards) == 0:
        return "no_card"

    trade_q = await ssn.execute(select(Trade).filter(Trade.id == trade_id))
    trade: Trade = trade_q.fetchone()[0]
    if trade.status == "target_wait":
        await ssn.execute(update(Trade).filter(
            Trade.id == trade.id).values(
            target_card_id=card_id, status="owner_wait"))
        await ssn.commit()
        return trade, cards[0].card

    return "trade_not_available"


async def decline_trade(ssn: AsyncSession, trade_id):
    trade_q = await ssn.execute(
        select(Trade).filter(Trade.id == trade_id))
    trade: Trade = trade_q.fetchone()[0]
    if trade.status not in ("target_wait", "owner_wait"):
        return "not_active"

    await ssn.execute(update(Trade).filter(
        Trade.id == trade_id).values(status="declined"))
    await ssn.commit()

    return trade


async def decline_last_trade(ssn: AsyncSession, user_id):
    trade_q = await ssn.execute(select(Trade).filter(
        or_(Trade.target == user_id, Trade.owner == user_id)).filter(
        Trade.status.in_(["target_wait", "owner_wait"])))
    trade_res = trade_q.fetchone()
    if trade_res is None:
        return "not_found"

    await ssn.execute(update(Trade).filter(
        Trade.id == trade_res[0].id).values(status="canceled"))
    await ssn.commit()

    return trade_res[0]


async def decline_all_trades(ssn: AsyncSession, user_id):
    await ssn.execute(update(Trade).filter(
        or_(Trade.target == user_id, Trade.owner == user_id)).filter(
        Trade.status.in_(["target_wait", "owner_wait"])).values(status="canceled"))

    await ssn.commit()


async def close_trade(ssn: AsyncSession, trade_id):
    trade_q = await ssn.execute(
        select(Trade).filter(Trade.id == trade_id))
    trade: Trade = trade_q.fetchone()[0]

    if trade.status != "owner_wait":
        return "already_closed"

    owner_cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.card_id == trade.owner_card_id).filter(
        UserCard.user_id == trade.owner).filter(
        UserCard.tradeble == "yes").options(
        selectinload(UserCard.card)).order_by(
        UserCard.duplicate.desc()))
    owner_cards = owner_cards_q.scalars().all()

    target_cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.card_id == trade.target_card_id).filter(
        UserCard.user_id == trade.target).filter(
        UserCard.tradeble == "yes").options(
        selectinload(UserCard.card)).order_by(
        UserCard.duplicate.desc()))
    target_cards = target_cards_q.scalars().all()

    if (len(owner_cards) == 0) or (len(target_cards) == 0):
        await ssn.execute(update(Trade).filter(
            Trade.id == trade_id).values(status="error"))
        await ssn.commit()
        return "error"

    owner_card: UserCard = owner_cards[0]
    target_card: UserCard = target_cards[0]

    # Добавляем карту второго игрока первому игроку
    target_card_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == trade.owner).filter(
        UserCard.card_id == target_card.card_id))
    target_card_res = target_card_q.fetchone()
    if target_card_res is None:
        owner_duplicate = 0
    else:
        owner_duplicate = 1

    await ssn.execute(update(UserCard).filter(
        UserCard.id == target_card.id).values(
        user_id=trade.owner, duplicate=owner_duplicate))

    # Добавляем карту первого игрока второму игроку
    owner_card_q = await ssn.execute(select(UserCard).filter(
        UserCard.user_id == trade.target).filter(
        UserCard.card_id == owner_card.card_id))
    owner_card_res = owner_card_q.fetchone()
    if owner_card_res is None:
        target_duplicate = 0
    else:
        target_duplicate = 1

    await ssn.execute(update(UserCard).filter(
        UserCard.id == owner_card.id).values(
        user_id=trade.target, duplicate=target_duplicate))

    if owner_card.points > target_card.points:
        diff = owner_card.points - target_card.points
        owner_rating = -diff
        target_rating = diff
    elif target_card.points > owner_card.points:
        diff = target_card.points - owner_card.points
        owner_rating = diff
        target_rating = -diff
    else:
        owner_rating = 0
        target_rating = 0

    owner_user_q = await ssn.execute(
        select(Player).filter(Player.id == trade.owner))
    owner_user: Player = owner_user_q.fetchone()[0]

    if (owner_user.season_rating + owner_rating) < 0:
        new_owner_s_rating = 0
    else:
        new_owner_s_rating = owner_user.season_rating + owner_rating

    await ssn.execute(update(Player).filter(
        Player.id == trade.owner).values(
        rating=Player.rating + owner_rating,
        trade_count=Player.trade_count + 1
        # season_rating=new_owner_s_rating,
    ))

    target_user_q = await ssn.execute(
        select(Player).filter(Player.id == trade.target))
    target_user: Player = target_user_q.fetchone()[0]

    if (target_user.season_rating + target_rating) < 0:
        new_target_s_rating = 0
    else:
        new_target_s_rating = target_user.season_rating + target_rating

    await ssn.execute(update(Player).filter(
        Player.id == trade.target).values(
        rating=Player.rating + target_rating,
        # season_rating=new_target_s_rating,
    ))

    await ssn.execute(update(Trade).filter(
        Trade.id == trade_id).values(status="finished"))
    await ssn.merge(UserTrade(user_x_user=f"{trade.owner}_{trade.target}"))
    await ssn.commit()
    logging.info(
        f"Traded {trade_id} | user1 {trade.owner} card {trade.owner_card_id} | user2 {trade.target} card {trade.target_card_id}")

    return trade, owner_card.card, target_card.card


async def get_trade_card_rarities(ssn: AsyncSession, user_id):
    cards_q = await ssn.execute(select(UserCard.card_rarity).filter(
        UserCard.user_id == user_id).filter(
        UserCard.tradeble == "yes"))
    cards = cards_q.scalars().all()
    user_rarities = set(cards)
    result = []
    for rarity in rarities:
        if rarity in user_rarities:
            result.append(rarity)

    return result


async def get_trade_access_user(ssn: AsyncSession, user_id):
    """
    Возвращает значение из Player.access_minigame
    """
    access_q: Player = await ssn.execute(
        select(Player).filter(Player.id == user_id))

    access_q = access_q.scalars().first()

    access: str = access_q.access_minigame

    return access


async def get_trade_access_user_by_trade_count(ssn: AsyncSession, user_id):
    access_q: Player = await ssn.execute(
        select(Player).filter(Player.id == user_id))

    access_q = access_q.scalars().first()

    access: str = 'yes' if access_q.trade_count < 5 or access_q.trade_count is None else 'not'
    return access
