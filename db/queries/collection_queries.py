from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CardItem, CardXPack, UserCard


async def get_user_rarity_cards(ssn: AsyncSession, user_id, rarity, sorting):
    if rarity == "all":
        if sorting == "up":
            cards_q = await ssn.execute(
                select(UserCard)
                .filter(UserCard.user_id == user_id)
                .filter(UserCard.duplicate == 0)
                .filter(UserCard.tradeble == "yes")
                .order_by(UserCard.points)
                .options(selectinload(UserCard.card))
            )
        elif sorting == "down":
            cards_q = await ssn.execute(
                select(UserCard)
                .filter(UserCard.user_id == user_id)
                .filter(UserCard.duplicate == 0)
                .filter(UserCard.tradeble == "yes")
                .order_by(UserCard.points.desc())
                .options(selectinload(UserCard.card))
            )
        else:
            cards_q = await ssn.execute(
                select(UserCard)
                .filter(UserCard.user_id == user_id)
                .filter(UserCard.duplicate == 0)
                .filter(UserCard.tradeble == "yes")
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


async def get_user_collection_cards(ssn: AsyncSession, user_id, rarity, sorting):
    if rarity == "all":
        if sorting == "up":
            cards_q = await ssn.execute(
                select(UserCard)
                .filter(UserCard.user_id == user_id)
                .filter(UserCard.duplicate == 0)
                .order_by(UserCard.points)
                .options(selectinload(UserCard.card))
            )
        elif sorting == "down":
            cards_q = await ssn.execute(
                select(UserCard)
                .filter(UserCard.user_id == user_id)
                .filter(UserCard.duplicate == 0)
                .order_by(UserCard.points.desc())
                .options(selectinload(UserCard.card))
            )
        else:
            cards_q = await ssn.execute(
                select(UserCard)
                .filter(UserCard.user_id == user_id)
                .filter(UserCard.duplicate == 0)
                .options(selectinload(UserCard.card))
            )
    else:
        cards_q = await ssn.execute(
            select(UserCard)
            .filter(UserCard.user_id == user_id)
            .filter(UserCard.card_rarity == rarity)
            .filter(UserCard.duplicate == 0)
            .options(selectinload(UserCard.card))
        )
    cards = cards_q.scalars().all()

    return cards


async def get_user_list_cards(ssn: AsyncSession, user_id):
    cards_q = await ssn.execute(
        select(UserCard)
        .filter(UserCard.user_id == user_id)
        .order_by(UserCard.points)
        .options(selectinload(UserCard.card))
    )
    cards = cards_q.scalars().all()

    return cards


async def get_pack_cards(ssn: AsyncSession, pack_id, user_id):
    pack_ids_q = await ssn.execute(
        select(CardXPack.user_card_id).filter(CardXPack.pack_id == pack_id)
    )
    pack_ids = pack_ids_q.scalars().all()

    cards_q = await ssn.execute(
        select(UserCard)
        .filter(UserCard.id.in_(pack_ids))
        .order_by(UserCard.points)
        .options(selectinload(UserCard.card))
    )
    cards = cards_q.scalars().all()

    return cards


async def get_rarity_cards(ssn: AsyncSession, rarity):
    if rarity == "all":
        cards_q = await ssn.execute(select(CardItem).order_by(CardItem.id))
    else:
        cards_q = await ssn.execute(
            select(CardItem).filter(CardItem.rarity == rarity).order_by(CardItem.id)
        )
    cards = cards_q.scalars().all()

    return cards


async def get_promo_rarity_cards(ssn: AsyncSession, rarity, sorting):
    if rarity == "all":
        if sorting == "up":
            cards_q = await ssn.execute(select(CardItem).order_by(CardItem.points))
        elif sorting == "down":
            cards_q = await ssn.execute(
                select(CardItem).order_by(CardItem.points.desc())
            )
        else:
            cards_q = await ssn.execute(select(CardItem))
    else:
        cards_q = await ssn.execute(select(CardItem).filter(CardItem.rarity == rarity))
    cards = cards_q.scalars().all()

    return cards


async def re_count_duplicates(ssn: AsyncSession, user_id):
    await ssn.execute(
        update(UserCard).filter(UserCard.user_id == user_id).values(duplicate=0)
    )
    await ssn.commit()

    cards_q = await ssn.execute(
        select(UserCard).filter(UserCard.user_id == user_id).order_by(UserCard.card_id)
    )
    cards = cards_q.scalars().all()

    card: UserCard
    for card in cards:
        ucard_q = await ssn.execute(
            select(UserCard.id)
            .filter(UserCard.card_id == card.card_id)
            .filter(UserCard.user_id == user_id)
            .filter(UserCard.duplicate == 0)
            .filter(UserCard.id != card.id)
        )
        ucard_res = ucard_q.fetchone()
        if ucard_res is not None:
            if card.duplicate == 0:
                await ssn.execute(
                    update(UserCard).filter(UserCard.id == card.id).values(duplicate=1)
                )
                await ssn.commit()


async def get_user_card_teams(ssn: AsyncSession, user_id):
    cards_q = await ssn.execute(
        select(UserCard)
        .filter(UserCard.user_id == user_id)
        .options(selectinload(UserCard.card))
    )
    cards = cards_q.scalars().all()

    user_teams = []
    card: UserCard
    for card in cards:
        teams = card.card.team.split(" x ")
        for team in teams:
            if team not in user_teams:
                user_teams.append(team)
    user_teams.sort()

    return user_teams


async def get_user_team_cards(ssn: AsyncSession, user_id, team, sorting):
    card_ids_q = await ssn.execute(
        select(CardItem.id).filter(CardItem.team.ilike(f"%{team}%"))
    )
    card_ids = card_ids_q.scalars().all()

    if sorting == "up":
        cards_q = await ssn.execute(
            select(UserCard)
            .filter(UserCard.user_id == user_id)
            .filter(UserCard.card_id.in_(card_ids))
            .filter(UserCard.duplicate == 0)
            .order_by(UserCard.points)
            .options(selectinload(UserCard.card))
        )
    elif sorting == "down":
        cards_q = await ssn.execute(
            select(UserCard)
            .filter(UserCard.user_id == user_id)
            .filter(UserCard.card_id.in_(card_ids))
            .filter(UserCard.duplicate == 0)
            .order_by(UserCard.points.desc())
            .options(selectinload(UserCard.card))
        )
    else:
        cards_q = await ssn.execute(
            select(UserCard)
            .filter(UserCard.user_id == user_id)
            .filter(UserCard.card_id.in_(card_ids))
            .filter(UserCard.duplicate == 0)
            .options(selectinload(UserCard.card))
        )

    cards = cards_q.scalars().all()

    return cards
