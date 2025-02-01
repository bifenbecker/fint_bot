import datetime as dt
import logging
import random

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CardItem, CardPack, CardXPack, Games, Player, UserCard
from utils.misc import card_rarity_randomize, send_action_emoji


async def lucky_shot(ssn: AsyncSession, user_id, bot):
    user_q = await ssn.execute(select(Player).filter(Player.id == user_id))
    user: Player = user_q.fetchone()[0]

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    if user.last_lucky < date_ts:
        if user.game_pass == "yes":
            delay = 14400
        else:
            delay = 21600
        value = await send_action_emoji(bot, user_id, "⚽")
        if value < 3:
            card = "lose"

            await ssn.execute(
                update(Player)
                .filter(Player.id == user_id)
                .values(last_lucky=date_ts + delay)
            )
            logging.info(f"User {user_id} lost in lucky shot")
        else:
            rarity = await card_rarity_randomize("ls")

            cards_q = await ssn.execute(
                select(CardItem)
                .filter(CardItem.rarity == rarity)
                .filter(CardItem.status == "on")
            )
            cards = cards_q.scalars().all()

            if len(cards) == 0:
                return "no_cards"

            card: CardItem = random.choice(cards)

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

            await ssn.merge(
                UserCard(
                    user_id=user_id,
                    card_id=card.id,
                    points=card.points,
                    card_rarity=card.rarity,
                    duplicate=duplicate,
                )
            )

            if user.game_pass == "yes":
                delay = 14400
            else:
                delay = 21600

            await ssn.execute(
                update(Player)
                .filter(Player.id == user_id)
                .values(
                    last_lucky=date_ts + delay,
                    rating=Player.rating + card.points,
                    card_quants=Player.card_quants + 1,
                    season_rating=Player.season_rating + card.points,
                )
            )
            logging.info(f"User {user_id} won card {card.id} in lucky shot")

        await ssn.commit()
        return card, user, "attempts"

    elif user.lucky_quants > 0:
        value = await send_action_emoji(bot, user_id, "⚽")
        if value < 3:
            card = "lose"
            await ssn.execute(
                update(Player)
                .filter(Player.id == user_id)
                .values(lucky_quants=Player.lucky_quants - 1)
            )

            logging.info(f"User {user_id} lost in lucky shot")

        else:
            if user.lucky_shots_plus > 0:
                rarity = await card_rarity_randomize("lsplus")
            else:
                rarity = await card_rarity_randomize("ls")

            cards_q = await ssn.execute(
                select(CardItem)
                .filter(CardItem.rarity == rarity)
                .filter(CardItem.status == "on")
            )
            cards = cards_q.scalars().all()

            if len(cards) == 0:
                return "no_cards"

            card: CardItem = random.choice(cards)

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

            await ssn.merge(
                UserCard(
                    user_id=user_id,
                    card_id=card.id,
                    points=card.points,
                    card_rarity=card.rarity,
                    duplicate=duplicate,
                )
            )

            if user.lucky_shots_plus > 0:
                await ssn.execute(
                    update(Player)
                    .filter(Player.id == user_id)
                    .values(
                        lucky_quants=Player.lucky_quants - 1,
                        rating=Player.rating + card.points,
                        card_quants=Player.card_quants + 1,
                        lucky_shots_plus=Player.lucky_shots_plus - 1,
                        season_rating=Player.season_rating + card.points,
                    )
                )
            else:
                await ssn.execute(
                    update(Player)
                    .filter(Player.id == user_id)
                    .values(
                        lucky_quants=Player.lucky_quants - 1,
                        rating=Player.rating + card.points,
                        card_quants=Player.card_quants + 1,
                        season_rating=Player.season_rating + card.points,
                    )
                )

            logging.info(f"User {user_id} won card {card.id} in lucky shot")

        await ssn.commit()
        return card, user, "free"

    else:
        return user.last_lucky - date_ts


async def get_game(ssn: AsyncSession, user_id, kind):
    game_q = await ssn.execute(
        select(Games).filter(Games.user_id == user_id).filter(Games.kind == kind)
    )
    game_res = game_q.fetchone()
    if game_res is None:
        await ssn.merge(Games(user_id=user_id, kind=kind))
        await ssn.commit()
        game_q = await ssn.execute(
            select(Games).filter(Games.user_id == user_id).filter(Games.kind == kind)
        )
        game = game_q.fetchone()[0]
    else:
        game = game_res[0]
    return game


async def hit_darts(ssn: AsyncSession, user_id, bot):
    game: Games = await get_game(ssn, user_id, "darts")

    date = dt.datetime.now()
    date_ts = int(date.timestamp())

    if game.free_quant > 0:
        kind = "free"
        time = 0
    else:
        if game.last_free < date_ts:
            kind = "free"
            time = 1
        else:
            if game.attempts > 0:
                kind = "attempts"
                time = 0
            else:
                return game.last_free - date_ts

    value = await send_action_emoji(bot, user_id, "🎯")
    if value == 6:
        points = 0
        u_cards_ids = []

        for _ in range(3):
            rarity = await card_rarity_randomize("darts")
            cards_q = await ssn.execute(
                select(CardItem)
                .filter(CardItem.rarity == rarity)
                .filter(CardItem.status == "on")
            )
            cards = cards_q.scalars().all()
            card: CardItem = random.choice(cards)
            points += card.points
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
                    user_id=user_id,
                    card_id=card.id,
                    points=card.points,
                    card_rarity=card.rarity,
                    duplicate=duplicate,
                )
            )
            await ssn.commit()
            u_cards_ids.append(user_card.id)

        new_pack = await ssn.merge(CardPack(user_id=user_id))
        await ssn.execute(
            update(Player)
            .filter(Player.id == user_id)
            .values(
                rating=Player.rating + points,
                card_quants=Player.card_quants + 3,
                season_rating=Player.season_rating + points,
            )
        )

        await ssn.commit()
        pack_id = new_pack.id

        for u_id in u_cards_ids:
            await ssn.merge(CardXPack(pack_id=pack_id, user_card_id=u_id))
        await ssn.commit()

        logging.info(f"User {user_id} won in darts pick_id {pack_id}")
        res = "win", pack_id

    else:
        res = "lose", game
        logging.info(f"User {user_id} lose in darts")

    if kind == "free":
        if time == 1:
            user_q = await ssn.execute(select(Player).filter(Player.id == user_id))
            user: Player = user_q.fetchone()[0]
            if user.game_pass == "yes":
                new_ts = date_ts + 172800
            else:
                new_ts = date_ts + 345600
            await ssn.execute(
                update(Games)
                .filter(Games.id == game.id)
                .values(last_free=new_ts, free_quant=2)
            )
        else:
            await ssn.execute(
                update(Games)
                .filter(Games.id == game.id)
                .values(free_quant=Games.free_quant - 1)
            )
    else:
        await ssn.execute(
            update(Games)
            .filter(Games.id == game.id)
            .values(attempts=Games.attempts - 1)
        )
    await ssn.commit()
    return res


async def hit_casino(ssn: AsyncSession, user_id, bot):
    game: Games = await get_game(ssn, user_id, "casino")

    if game.curr_casino < 1:
        return "no_attempts"
    else:
        value = await send_action_emoji(bot, user_id, "🎰")
        if value in [1, 22, 43, 64]:
            rarity = await card_rarity_randomize("casino")
            cards_q = await ssn.execute(
                select(CardItem)
                .filter(CardItem.rarity == rarity)
                .filter(CardItem.status == "on")
            )
            cards = cards_q.scalars().all()

            if len(cards) == 0:
                return "no_cards"

            card: CardItem = random.choice(cards)

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

            await ssn.merge(
                UserCard(
                    user_id=user_id,
                    card_id=card.id,
                    points=card.points,
                    card_rarity=card.rarity,
                    duplicate=duplicate,
                )
            )

            await ssn.execute(
                update(Player)
                .filter(Player.id == user_id)
                .values(
                    rating=Player.rating + card.points,
                    card_quants=Player.card_quants + 1,
                    season_rating=Player.season_rating + card.points,
                )
            )
            await ssn.execute(
                update(Games)
                .filter(Games.id == game.id)
                .values(curr_casino=Games.curr_casino - 1)
            )
            await ssn.commit()

            logging.info(f"User {user_id} won in casino pick_id {card.id}")
            return "win", card

        else:
            await ssn.execute(
                update(Games)
                .filter(Games.id == game.id)
                .values(curr_casino=Games.curr_casino - 1)
            )
            await ssn.commit()
            logging.info(f"User {user_id} lose in casino")
            return "lose", game
    # else:
    #     value = await send_action_emoji(bot, user_id, "🎰")
    #     if value in [1, 22, 43, 64]:
    #         rarity = await card_rarity_randomize("casino")
    #         cards_q = await ssn.execute(select(CardItem).filter(
    #             CardItem.rarity == rarity).filter(
    #             CardItem.status == "on"))
    #         cards = cards_q.scalars().all()
    #
    #         if len(cards) == 0:
    #             return "no_cards"
    #
    #         card: CardItem = random.choice(cards)
    #
    #         usercard_q = await ssn.execute(select(UserCard).filter(
    #             UserCard.user_id == user_id).filter(
    #                 UserCard.card_id == card.id))
    #         user_card_res = usercard_q.fetchone()
    #         if user_card_res is None:
    #             duplicate = 0
    #         else:
    #             duplicate = 1
    #
    #         await ssn.merge(UserCard(
    #             user_id=user_id, card_id=card.id, points=card.points,
    #             card_rarity=card.rarity, duplicate=duplicate))
    #
    #         await ssn.execute(update(Player).filter(
    #             Player.id == user_id).values(
    #             rating=Player.rating + card.points,
    #             card_quants=Player.card_quants + 1,
    #             season_rating=Player.season_rating + card.points))
    #         await ssn.execute(update(Games).filter(
    #             Games.id == game.id).values(curr_casino=0))
    #         await ssn.commit()
    #
    #         logging.info(f"User {user_id} won in casino pick_id {card.id}")
    #         return "win", card
    #
    #     else:
    #         await ssn.execute(update(Games).filter(
    #             Games.id == game.id).values(
    #                 curr_casino=Games.curr_casino - 1))
    #         await ssn.commit()
    #         logging.info(f"User {user_id} lose in casino")
    #         return "lose", game
