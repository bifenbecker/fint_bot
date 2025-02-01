import datetime as dt
import logging

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Penalty, Player, Trade, TradeCard, UserCard, UserTrade
from utils.const import rarities


async def get_user_rarity_cards_m(ssn: AsyncSession, user_id, rarity, sorting):
    if rarity == "all":
        if sorting == "up":
            cards_q = await ssn.execute(select(UserCard).filter(
                UserCard.user_id == user_id).filter(
                    UserCard.tradeble == "yes").order_by(
                        UserCard.points).options(
                            selectinload(UserCard.card)))
        elif sorting == "down":
            cards_q = await ssn.execute(select(UserCard).filter(
                UserCard.user_id == user_id).filter(
                    UserCard.tradeble == "yes").order_by(
                        UserCard.points.desc()).options(
                            selectinload(UserCard.card)))
        else:
            cards_q = await ssn.execute(select(UserCard).filter(
                UserCard.user_id == user_id).filter(
                    UserCard.tradeble == "yes").options(
                        selectinload(UserCard.card)))
    else:
        cards_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.card_rarity == rarity).filter(
                    UserCard.tradeble == "yes").options(
                        selectinload(UserCard.card)))
    cards = cards_q.scalars().all()

    return cards


async def get_owner_selected_cards(ssn: AsyncSession, user_id, card_ids):
    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.id.in_(card_ids)).filter(
            UserCard.user_id == user_id).options(
                selectinload(UserCard.card)))
    cards = cards_q.scalars().all()
    return cards


async def create_new_mtrade(
        ssn: AsyncSession, user_id, username, card_ids, target_username, quant):
    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.id.in_(card_ids)).filter(
            UserCard.user_id == user_id).options(
                selectinload(UserCard.card)))
    cards = cards_q.scalars().all()
    if len(cards) < quant:
        return "error"
    
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
        status="target_wait", owner=user_id, owner_username=username,
        target=target.id, target_username=target.username, quant=quant))
    await ssn.commit()
    trade_id = trade.id

    for card in cards:
        await ssn.merge(TradeCard(
            trade_id=trade_id, card_id=card.card_id,
            user_card_id=card.id, kind="owner"))
    await ssn.commit()

    return trade_id, target.id, cards


async def get_user_rarity_cards_m_target(ssn: AsyncSession, user_id, rarity, sorting, trade_id):
    trade_q = await ssn.execute(
        select(Trade).filter(Trade.id == trade_id))
    trade: Trade = trade_q.fetchone()[0]

    if trade.status not in ("target_wait", "owner_wait"):
        return "not_active"

    owner_cards_q = await ssn.execute(select(TradeCard.card_id).filter(
        TradeCard.trade_id == trade_id).filter(
        TradeCard.kind == "owner"))
    owner_cards = owner_cards_q.scalars().all()

    if rarity == "all":
        if sorting == "up":
            cards_q = await ssn.execute(select(UserCard).filter(
                UserCard.user_id == user_id).filter(
                    UserCard.tradeble == "yes").filter(
                        UserCard.card_id.not_in(owner_cards)).order_by(
                            UserCard.points).options(
                                selectinload(UserCard.card)))
        elif sorting == "down":
            cards_q = await ssn.execute(select(UserCard).filter(
                UserCard.user_id == user_id).filter(
                    UserCard.tradeble == "yes").filter(
                        UserCard.card_id.not_in(owner_cards)).order_by(
                            UserCard.points.desc()).options(
                                selectinload(UserCard.card)))
        else:
            cards_q = await ssn.execute(select(UserCard).filter(
                UserCard.user_id == user_id).filter(
                    UserCard.tradeble == "yes").filter(
                        UserCard.card_id.not_in(owner_cards)).options(
                            selectinload(UserCard.card)))
    else:
        cards_q = await ssn.execute(select(UserCard).filter(
            UserCard.user_id == user_id).filter(
                UserCard.card_rarity == rarity).filter(
                    UserCard.tradeble == "yes").filter(
                        UserCard.card_id.not_in(owner_cards)).options(
                            selectinload(UserCard.card)))
    cards = cards_q.scalars().all()

    return cards, trade.quant


async def get_mtrade_card_rarities(ssn: AsyncSession, user_id, trade_id):
    trade_q = await ssn.execute(
        select(Trade).filter(Trade.id == trade_id))
    trade: Trade = trade_q.fetchone()[0]

    owner_cards_q = await ssn.execute(select(TradeCard.card_id).filter(
        TradeCard.trade_id == trade_id).filter(
        TradeCard.kind == "owner"))
    owner_cards = owner_cards_q.scalars().all()

    cards_q = await ssn.execute(select(UserCard.card_rarity).filter(
        UserCard.user_id == user_id).filter(
            UserCard.tradeble == "yes").filter(
                UserCard.card_id.not_in(owner_cards)))
    cards = cards_q.scalars().all()
    user_rarities = set(cards)
    result = []
    for rarity in rarities:
        if rarity in user_rarities:
            result.append(rarity)

    return result


async def get_target_selected_cards(ssn: AsyncSession, trade_id, card_ids):
    trade_q = await ssn.execute(
        select(Trade).filter(Trade.id == trade_id))
    trade: Trade = trade_q.fetchone()[0]

    owner_trade_cards_q = await ssn.execute(select(TradeCard.user_card_id).filter(
        TradeCard.trade_id == trade_id).filter(
        TradeCard.kind == "owner"))
    owner_trade_cards = owner_trade_cards_q.scalars().all()

    owner_cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.id.in_(owner_trade_cards)).filter(
            UserCard.user_id == trade.owner).options(
                selectinload(UserCard.card)))
    owner_cards = owner_cards_q.scalars().all()

    target_cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.id.in_(card_ids)).filter(
            UserCard.user_id == trade.target).options(
                selectinload(UserCard.card)))
    target_cards = target_cards_q.scalars().all()

    return owner_cards, target_cards


async def change_mtrade_status(ssn: AsyncSession, trade_id, card_ids, user_id):
    trade_q = await ssn.execute(
        select(Trade).filter(Trade.id == trade_id))
    trade: Trade = trade_q.fetchone()[0]

    if trade.status not in ("target_wait", "owner_wait"):
        return "not_active"

    cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.id.in_(card_ids)).filter(
            UserCard.user_id == user_id).options(
                selectinload(UserCard.card)))
    cards = cards_q.scalars().all()
    if len(cards) < trade.quant:
        await ssn.execute(update(Trade).filter(
            Trade.id == trade_id).values(status="declined"))
        await ssn.commit()
        return "error"

    for card in cards:
        await ssn.merge(TradeCard(
            trade_id=trade_id, card_id=card.card_id,
            user_card_id=card.id, kind="target"))
    await ssn.execute(update(Trade).filter(
        Trade.id == trade_id).values(status="owner_wait"))
    await ssn.commit()

    return trade


async def close_multi_trade(ssn: AsyncSession, trade_id):
    trade_q = await ssn.execute(
        select(Trade).filter(Trade.id == trade_id))
    trade: Trade = trade_q.fetchone()[0]

    if trade.status != "owner_wait":
        return "already_closed"

    target_trade_cards_q = await ssn.execute(select(TradeCard.user_card_id).filter(
        TradeCard.trade_id == trade_id).filter(
        TradeCard.kind == "target"))
    target_trade_cards = target_trade_cards_q.scalars().all()

    target_cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.id.in_(target_trade_cards)).filter(
        UserCard.user_id == trade.target))
    target_cards = target_cards_q.scalars().all()

    owner_trade_cards_q = await ssn.execute(select(TradeCard.user_card_id).filter(
        TradeCard.trade_id == trade_id).filter(
        TradeCard.kind == "owner"))
    owner_trade_cards = owner_trade_cards_q.scalars().all()

    owner_cards_q = await ssn.execute(select(UserCard).filter(
        UserCard.id.in_(owner_trade_cards)).filter(
        UserCard.user_id == trade.owner))
    owner_cards = owner_cards_q.scalars().all()

    if len(owner_cards) != len(target_cards):
        await ssn.execute(update(Trade).filter(
            Trade.id == trade_id).values(status="declined"))
        await ssn.commit()
        return "error"

    # Добавляем карты второго игрока первому игроку
    new_owner_card_ids = []
    target_cards_rating = 0
    for t_o_card in target_cards:
        check_card_q = await ssn.execute(select(UserCard.id).filter(
            UserCard.card_id == t_o_card.card_id).filter(
                UserCard.user_id == trade.owner))
        check_card_res = check_card_q.scalars().all()
        if len(check_card_res) > 0:
            owner_duplicate = 1
        else:
            if t_o_card.card_id in new_owner_card_ids:
                owner_duplicate = 1
            else:
                owner_duplicate = 0
                new_owner_card_ids.append(t_o_card.card_id)
        target_cards_rating += t_o_card.points
        await ssn.execute(update(UserCard).filter(
            UserCard.id == t_o_card.id).values(
            user_id=trade.owner, duplicate=owner_duplicate))

    # Добавляем карту первого игрока второму игроку
    new_target_card_ids = []
    owner_cards_rating = 0
    for o_t_card in owner_cards:
        check_card_q = await ssn.execute(select(UserCard.id).filter(
            UserCard.card_id == o_t_card.card_id).filter(
            UserCard.user_id == trade.target))
        check_card_res = check_card_q.scalars().all()
        if len(check_card_res) > 0:
            target_duplicate = 1
        else:
            if o_t_card.card_id in new_target_card_ids:
                target_duplicate = 1
                new_target_card_ids.append(o_t_card.card_id)
            else:
                target_duplicate = 0

        owner_cards_rating += o_t_card.points
        await ssn.execute(update(UserCard).filter(
            UserCard.id == o_t_card.id).values(
            user_id=trade.target, duplicate=target_duplicate))

    if owner_cards_rating > target_cards_rating:
        diff = owner_cards_rating - target_cards_rating
        owner_rating = -diff
        target_rating = diff
    elif owner_cards_rating > target_cards_rating:
        diff = target_cards_rating - owner_cards_rating
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
        f"Traded {trade_id} | user1 {trade.owner} | user2 {trade.target}")

    return trade
