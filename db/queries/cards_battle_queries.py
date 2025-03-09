from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence

from sqlalchemy import DateTime, and_, cast, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from db.models import CardBattle, CardBattleTurn, Player, UserCard, UserCardsToBattle
from enum_types import CardBattleGameStatus, CardBattlePlayerStatus, CardBattleTurnType


@dataclass(frozen=True)
class LastTurnResult:
    win_turn: CardBattleTurn | None = None
    lose_turn: CardBattleTurn | None = None


async def change_player_card_battle_status(
    ssn: AsyncSession, player_id: int, status: CardBattlePlayerStatus
) -> None:
    query = (
        update(Player)
        .filter(Player.id == player_id)
        .values(card_battle_status=status)
        .returning(Player)
    )
    await ssn.execute(query)
    await ssn.commit()


async def player_start_search_card_battle(ssn: AsyncSession, player_id: int) -> None:
    await change_player_card_battle_status(
        ssn, player_id, CardBattlePlayerStatus.SEARCHING
    )


async def player_end_search_card_battle(ssn: AsyncSession, player_id: int) -> None:
    await change_player_card_battle_status(ssn, player_id, CardBattlePlayerStatus.READY)


async def player_add_cards_pick_for_card_battle(
    ssn: AsyncSession, battle_id: int, user_card_ids: list[int]
) -> Sequence[UserCardsToBattle]:
    query = (
        insert(UserCardsToBattle)
        .values(battle_id=battle_id)
        .returning(UserCardsToBattle)
    )
    res = await ssn.scalars(
        query, [dict(user_card_id=user_card_id) for user_card_id in user_card_ids]
    )
    await ssn.commit()
    return res.all()


async def create_card_battle(
    ssn: AsyncSession, player_blue_id: int, player_red_id: int
) -> CardBattle:
    query = (
        insert(CardBattle)
        .values(
            status=CardBattleGameStatus.WAITING_FOR_BLUE,
            player_blue_id=player_blue_id,
            player_red_id=player_red_id,
            winner_id=None,
        )
        .returning(CardBattle)
    )
    res = await ssn.scalar(query)
    await ssn.commit()
    await ssn.refresh(res)
    return res


async def get_searching_players(ssn: AsyncSession, player_id: int) -> Sequence[Player]:
    # me = await ssn.scalar(select(Player).filter(Player.id == player_id))
    # return [me]
    search_player = await ssn.scalar(select(Player).filter(Player.id == player_id))
    query = select(Player).filter(
        and_(
            Player.card_battle_status == CardBattlePlayerStatus.SEARCHING,
            Player.id != search_player.id,
            Player.card_battle_rating <= search_player.max_rating,
            Player.card_battle_rating >= search_player.min_rating,
        )
    )
    res = await ssn.scalars(query)
    players = res.all()
    result = []
    for player in players:
        query = select(CardBattle).filter(
            or_(
                CardBattle.player_blue_id == player.id,
                CardBattle.player_red_id == player.id,
            ),
            or_(
                CardBattle.player_blue_id == search_player.id,
                CardBattle.player_red_id == search_player.id,
            ),
            cast(CardBattle.date_play, DateTime)
            >= (datetime.now() - timedelta(days=1)),
        )
        try:
            res = await ssn.scalars(query)
        except Exception as e:
            print(e)
        battles = res.all()
        if len(battles) < 5:
            result.append(player)

    return result


async def get_player_cards(
    ssn: AsyncSession, player_id: int, battle_id: int
) -> Sequence[UserCardsToBattle]:
    query = (
        select(UserCardsToBattle)
        .join(UserCardsToBattle.user_card)
        .filter(
            and_(
                UserCard.user_id == player_id,
                UserCardsToBattle.battle_id == battle_id,
            )
        )
    )
    res = await ssn.scalars(query)
    return res.all()


async def get_remaining_cards(
    ssn: AsyncSession, player_id: int, battle_id: int
) -> Sequence[UserCardsToBattle]:
    all_user_cards = await get_player_cards(ssn, player_id, battle_id)

    query = select(CardBattleTurn.card_id).filter(
        and_(
            CardBattleTurn.player_id == player_id,
            CardBattleTurn.battle_id == battle_id,
        )
    )
    used_cards = await ssn.scalars(query)
    used_cards = used_cards.all()
    return [card for card in all_user_cards if card.id not in used_cards]


async def add_turn(
    ssn: AsyncSession,
    player_id: int,
    card_id: int,
    battle_id: int,
    turn_type: CardBattleTurnType,
) -> CardBattleTurn:
    query = (
        insert(CardBattleTurn)
        .values(
            player_id=player_id,
            card_id=card_id,
            battle_id=battle_id,
            type=turn_type,
        )
        .returning(CardBattleTurn)
    )
    res = await ssn.scalar(query)
    await ssn.commit()
    return res


async def opposite_player_has_turn(
    ssn: AsyncSession, battle_id: int, turn_type: CardBattleTurnType
) -> bool:
    """Check if opposite player has a turn of given type in a battle.

    Args:
        ssn (AsyncSession): SQLAlchemy AsyncSession.
        player_id (int): Player ID.
        battle_id (int): Battle ID.
        turn_type (CardBattleTurnType): Type of turn to check.

    Returns:
        bool: True if opposite player has a turn, False otherwise.
    """
    query = select(CardBattleTurn).filter(
        CardBattleTurn.battle_id == battle_id,
    )
    turns = (await ssn.scalars(query)).all()
    my_turns = list(filter(lambda turn: turn.type == turn_type, turns))
    opposite_turn_type = (
        CardBattleTurnType.ATTACK
        if turn_type == CardBattleTurnType.DEFENSE
        else CardBattleTurnType.DEFENSE
    )
    opposite_turns = list(
        filter(
            lambda turn: turn.type == opposite_turn_type,
            turns,
        )
    )
    result = len(list(my_turns)) == len(list(opposite_turns))
    return result


async def get_result_turns(
    ssn: AsyncSession, turn1: CardBattleTurn, turn2: CardBattleTurn
) -> CardBattleTurn | None:
    query = (
        select(UserCard)
        .join(UserCardsToBattle, UserCardsToBattle.user_card_id == UserCard.id)
        .join(CardBattleTurn, CardBattleTurn.card_id == UserCardsToBattle.id)
        .filter(CardBattleTurn.id == turn1.id)
    )
    card1: UserCard = await ssn.scalar(query)
    query = (
        select(UserCard)
        .join(UserCardsToBattle, UserCardsToBattle.user_card_id == UserCard.id)
        .join(CardBattleTurn, CardBattleTurn.card_id == UserCardsToBattle.id)
        .filter(CardBattleTurn.id == turn2.id)
    )
    card2: UserCard = await ssn.scalar(query)
    if (
        turn1.type == CardBattleTurnType.ATTACK
        and turn2.type == CardBattleTurnType.DEFENSE
    ):
        if card1.card.attack_rate > card2.card.defense_rate:
            return turn1
        elif card1.card.attack_rate == card2.card.defense_rate:
            return None
        else:
            return turn2
    elif (
        turn1.type == CardBattleTurnType.DEFENSE
        and turn2.type == CardBattleTurnType.ATTACK
    ):
        if card1.card.defense_rate > card2.card.attack_rate:
            return turn1
        elif card1.card.defense_rate == card2.card.attack_rate:
            return None
        else:
            return turn2
    else:
        return None


async def get_last_win_turn(ssn: AsyncSession, battle_id: int) -> CardBattleTurn | None:
    query = (
        select(CardBattleTurn)
        .options(selectinload(CardBattleTurn.card))
        .filter(
            CardBattleTurn.battle_id == battle_id,
        )
    )
    turns = (await ssn.scalars(query)).all()
    turn1, turn2 = turns[len(turns) - 2 :]
    return await get_result_turns(ssn, turn1, turn2)


async def get_last_turn_result(ssn: AsyncSession, battle_id: int) -> LastTurnResult:
    query = (
        select(CardBattleTurn)
        .options(selectinload(CardBattleTurn.card))
        .filter(
            CardBattleTurn.battle_id == battle_id,
        )
    )
    turns = (await ssn.scalars(query)).all()
    turn1, turn2 = turns[len(turns) - 2 :]
    win_turn = await get_result_turns(ssn, turn1, turn2)
    return LastTurnResult(
        win_turn=win_turn, lose_turn=turn1 if win_turn.id == turn2.id else turn2
    )


async def get_battle_winner(ssn: AsyncSession, battle_id: int) -> Player | None:
    score = await battle_score(ssn, battle_id)
    winner_id = max(score, key=score.get)
    if len(set(score.values())) == 1:
        winner_id = None
        return None
    query = (
        update(CardBattle)
        .filter(CardBattle.id == battle_id)
        .values(winner_id=winner_id)
    )
    await ssn.execute(query)
    await ssn.commit()
    query = select(Player).filter(Player.id == winner_id)
    return await ssn.scalar(query)


async def battle_score(ssn: AsyncSession, battle_id: int) -> dict[int, int]:
    query = select(CardBattleTurn).filter(
        CardBattleTurn.battle_id == battle_id,
    )
    turns = (await ssn.scalars(query)).all()
    red_player_turns = turns[::2]
    blue_player_turns = turns[1::2]
    red_player_id = red_player_turns[0].player_id
    blue_player_id = blue_player_turns[0].player_id
    result = {
        red_player_id: 0,
        blue_player_id: 0,
    }
    for turn1, turn2 in zip(red_player_turns, blue_player_turns, strict=True):
        turn_winner = await get_result_turns(ssn, turn1, turn2)
        if turn_winner:
            player_id = turn_winner.player_id
            if player_id not in result:
                result[player_id] = 0
            result[player_id] += 1
        else:
            for key in result:
                result[key] += 1
    return result


async def finish_players_cards_battle(ssn: AsyncSession, battle_id: int) -> None:
    query = select(CardBattle).filter(CardBattle.id == battle_id)
    battle: CardBattle = await ssn.scalar(query)
    await change_player_card_battle_status(
        ssn, battle.player_blue_id, CardBattlePlayerStatus.READY
    )
    await change_player_card_battle_status(
        ssn, battle.player_red_id, CardBattlePlayerStatus.READY
    )
    winner = await get_battle_winner(ssn, battle_id)
    battle.winner = winner
    battle.date_play = datetime.now()
    await ssn.commit()
    await ssn.refresh(battle)


async def update_ratings_after_battle(ssn: AsyncSession, battle_id: int) -> None:
    query = select(CardBattle).filter(CardBattle.id == battle_id)
    battle = await ssn.scalar(query)
    if battle.winner_id:
        looser_id = (
            battle.player_blue_id
            if battle.winner_id == battle.player_red_id
            else battle.player_red_id
        )
        query = select(Player).filter(Player.id == looser_id)
        looser = await ssn.scalar(query)
        if looser.card_battle_rating - 25 < 0:
            update_query = (
                update(Player)
                .filter(Player.id == looser_id)
                .values(card_battle_rating=0)
            )
        else:
            update_query = (
                update(Player)
                .filter(Player.id == looser_id)
                .values(card_battle_rating=Player.card_battle_rating - 25)
            )
        await ssn.execute(update_query)
        await ssn.commit()

        query = (
            update(Player)
            .filter(Player.id == battle.winner_id)
            .values(card_battle_rating=Player.card_battle_rating + 25)
        )
        await ssn.execute(query)
        await ssn.commit()


async def get_battle(ssn: AsyncSession, battle_id: int) -> CardBattle:
    query = select(CardBattle).filter(CardBattle.id == battle_id)
    return await ssn.scalar(query)


async def cancel_card_battle_game(ssn: AsyncSession, player_id: int) -> int | None:
    query = select(Player.card_battle_status).filter(Player.id == player_id)
    status = await ssn.scalar(query)

    if status == CardBattlePlayerStatus.PLAYING:
        await change_player_card_battle_status(
            ssn, player_id, CardBattlePlayerStatus.READY
        )
        query = (
            select(CardBattle)
            .options(
                joinedload(CardBattle.player_red), joinedload(CardBattle.player_blue)
            )
            .filter(
                and_(
                    or_(
                        CardBattle.player_red_id == player_id,
                        CardBattle.player_blue_id == player_id,
                    ),
                    CardBattle.winner_id.is_(None),
                    CardBattle.status != CardBattleGameStatus.FINISHED,
                )
            )
            .order_by(CardBattle.id.desc())
        )
        battle = await ssn.scalar(query)
        if battle:
            battle.winner_id = (
                battle.player_red_id
                if player_id == battle.player_blue_id
                else battle.player_blue_id
            )
            await change_player_card_battle_status(
                ssn, battle.winner_id, CardBattlePlayerStatus.READY
            )
            battle.status = CardBattleGameStatus.FINISHED
            battle.date_play = datetime.now()
            await ssn.commit()
            await ssn.refresh(battle)
            await update_ratings_after_battle(ssn, battle.id)
            return battle.winner_id
