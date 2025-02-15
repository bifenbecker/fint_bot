# type: ignore
import logging
from typing import Sequence

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CardBattleTurn, UserCard, UserCardsToBattle
from db.queries.cards_battle_queries import (
    LastTurnResult,
    add_turn,
    battle_score,
    finish_players_cards_battle,
    get_battle,
    get_battle_result,
    get_last_turn_result,
    get_remaining_cards,
    opposite_player_has_turn,
    player_add_cards_pick_for_card_battle,
    update_ratings_after_battle,
)
from db.queries.global_queries import get_user_info
from enum_types import CardBattleTurnType
from keyboards.cards_battle_kbs import (
    SelectCardOnPageCB,
    finish_cards_battle_kb,
    select_cards_for_cards_battle_kb,
)
from keyboards.cb_data import PageCB, TurnTypeCB
from middlewares.actions import ActionMiddleware
from utils.format_texts import format_view_cards_battle_text
from utils.states import CardsBattleStates

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(
    StateFilter(CardsBattleStates.playing_cards_battle),
    F.data.startswith("ready_cards_battle_"),
    flags=flags,
)
async def handler_ready_cards_battle(
    c: CQ, action_queue, ssn: AsyncSession, state: FSM
):
    battle_id, red_player_id, blue_player_id, turn_type = c.data.split("_")[-1].split(
        ":"
    )
    await state.update_data(
        battle_id=battle_id,
        red_player_id=int(red_player_id),
        blue_player_id=int(blue_player_id),
        turn_type=CardBattleTurnType(turn_type),
    )
    data = await state.get_data()
    selected: tuple[UserCard] = tuple(data.get("selected"))
    user_cards_to_battle = await player_add_cards_pick_for_card_battle(
        ssn, int(battle_id), [card.id for card in selected]
    )
    await state.update_data(battle_cards=user_cards_to_battle)
    page = 1
    last = len(user_cards_to_battle)

    txt = await format_view_cards_battle_text(selected[0].card)
    await c.message.delete()
    await c.message.answer_photo(
        selected[0].card.image,
        txt,
        reply_markup=select_cards_for_cards_battle_kb(
            page, last, "nosort", card_id=user_cards_to_battle[0].id
        ),
    )

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(CardsBattleStates.playing_cards_battle),
    TurnTypeCB.filter(),
    flags=flags,
)
async def select_card_for_turn(
    c: CQ, bot: Bot, action_queue, ssn, state: FSM, callback_data: TurnTypeCB
):
    await state.update_data(turn_type=CardBattleTurnType(callback_data.type))
    data = await state.get_data()
    battle_id = callback_data.battle_id
    blue_player_id = callback_data.blue_player_id
    red_player_id = callback_data.red_player_id
    await state.update_data(
        battle_id=battle_id, blue_player_id=blue_player_id, red_player_id=red_player_id
    )
    await bot.send_message(
        chat_id=blue_player_id,
        text=f"ИГРОК {'АТАКУЕТ' if callback_data.type == CardBattleTurnType.ATTACK.value else 'ЗАЩИЩАЕТСЯ'}, ТЫ {'ЗАЩИЩАЕШЬСЯ' if callback_data.type == CardBattleTurnType.ATTACK.value else 'АТАКУЕШЬ'}\nГотов?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Готов",
                        callback_data=f"ready_cards_battle_{battle_id}:{c.from_user.id}:{blue_player_id}:{CardBattleTurnType.DEFENSE.value if callback_data.type == CardBattleTurnType.ATTACK.value else CardBattleTurnType.ATTACK.value}",
                    )
                ]
            ]
        ),
    )

    selected: tuple[UserCard] = tuple(data.get("selected"))

    user_cards_to_battle = await player_add_cards_pick_for_card_battle(
        ssn, battle_id, [card.id for card in selected]
    )
    await state.update_data(battle_cards=user_cards_to_battle)

    page = 1
    last = len(user_cards_to_battle)

    txt = await format_view_cards_battle_text(selected[0].card)
    await c.message.delete()
    await c.message.answer_photo(
        selected[0].card.image,
        txt,
        reply_markup=select_cards_for_cards_battle_kb(
            page, last, "nosort", card_id=user_cards_to_battle[0].id
        ),
    )
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(CardsBattleStates.playing_cards_battle),
    PageCB.filter(),
    flags=flags,
)
async def paginate_cards_cmd(c: CQ, action_queue, state: FSM, callback_data: PageCB):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    battle_cards: Sequence[UserCardsToBattle] = data.get("battle_cards")
    sorting = data.get("sorting")
    battle_card: UserCardsToBattle = battle_cards[page - 1]
    txt = await format_view_cards_battle_text(battle_card.user_card.card)

    media = InputMediaPhoto(caption=txt, media=battle_card.user_card.card.image)

    try:
        await c.message.edit_media(
            media=media,
            reply_markup=select_cards_for_cards_battle_kb(
                page, last, sorting, card_id=battle_card.id
            ),
        )
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


async def send_cards_battle_results(
    ssn: AsyncSession, bot: Bot, battle_id: int
) -> None:
    battle = await get_battle(ssn, battle_id)
    red_player = await get_user_info(ssn, battle.player_red_id)
    blue_player = await get_user_info(ssn, battle.player_blue_id)
    score: dict[int, int] = await battle_score(ssn, battle_id)
    red_player_score = score.get(battle.player_red_id, 0)
    blue_player_score = score.get(battle.player_blue_id, 0)
    txt = """
    🏵️Игра окончена
    ⚽️Счет: {red_player_score} - {blue_player_score}
    ✅{battle_result}

    🟦Синий: {blue_player_username}
    🟥Красный: {red_player_username}

    🏆Твой рейтинг: {player_rating}
    📊Твой дивизион: {player_division}
    """
    battle_result = "Ничья!"
    if red_player_score != blue_player_score:
        winner = await get_battle_result(ssn, battle_id)
        battle_result = f"Победил: {winner.username}"

    await bot.send_message(
        text=txt.format(
            battle_result=battle_result,
            red_player_score=red_player_score,
            blue_player_score=blue_player_score,
            blue_player_username=blue_player.username,
            red_player_username=red_player.username,
            player_rating=red_player.card_battle_rating,
            player_division=red_player.division,
        ),
        chat_id=battle.player_red_id,
        reply_markup=finish_cards_battle_kb,
    )
    await bot.send_message(
        text=txt.format(
            battle_result=battle_result,
            red_player_score=red_player_score,
            blue_player_score=blue_player_score,
            blue_player_username=blue_player.username,
            red_player_username=red_player.username,
            player_rating=blue_player.card_battle_rating,
            player_division=blue_player.division,
        ),
        chat_id=battle.player_blue_id,
        reply_markup=finish_cards_battle_kb,
    )


def get_media_group_for_player(
    last_turn_result: LastTurnResult,
    player_id: int,
    red_player_id: int,
    blue_player_id: int,
) -> MediaGroupBuilder:
    def get_turn_text_for_card(turn: CardBattleTurn, is_win: bool) -> str:
        card = turn.card.user_card.card

        return f"""
👤 {card.name} ({card.card_name})
🗡️ Атака: {card.attack_rate} {("✅" if is_win else "❌") if turn.type == CardBattleTurnType.ATTACK else ""}
🛡️ Защита: {card.defense_rate} {("✅" if is_win else "❌") if turn.type == CardBattleTurnType.DEFENSE else ""}
💎 Рейтинг: {card.general_rate} 
        """

    winner_title_txt = "⚽️ ТЫ ЗАБИЛ ГОЛ"
    looser_title_txt = "❌ ТЫ ПРОПУСТИЛ ГОЛ"

    txt = """
{title}

🟥Игрок красного: 
{red_player_card_text}

🟦Игрок синего:
{blue_player_card_text}
    """

    media_group = MediaGroupBuilder(
        caption=txt.format(
            title=winner_title_txt
            if last_turn_result.win_turn.player_id == player_id
            else looser_title_txt,
            red_player_card_text=get_turn_text_for_card(
                last_turn_result.win_turn
                if last_turn_result.win_turn.player_id == red_player_id
                else last_turn_result.lose_turn,
                True if last_turn_result.win_turn.player_id == red_player_id else False,
            ),
            blue_player_card_text=get_turn_text_for_card(
                last_turn_result.win_turn
                if last_turn_result.win_turn.player_id == blue_player_id
                else last_turn_result.lose_turn,
                True
                if last_turn_result.win_turn.player_id == blue_player_id
                else False,
            ),
        )
    )
    media_group.add_photo(last_turn_result.win_turn.card.user_card.card.image)
    media_group.add_photo(last_turn_result.lose_turn.card.user_card.card.image)
    return media_group


@router.callback_query(
    StateFilter(CardsBattleStates.playing_cards_battle),
    SelectCardOnPageCB.filter(),
    flags=flags,
)
async def pick_card_handler(
    c: CQ,
    bot: Bot,
    state: FSM,
    ssn: AsyncSession,
    action_queue,
    callback_data: SelectCardOnPageCB,
):
    data = await state.get_data()
    battle_id = int(data.get("battle_id"))
    card_id = int(callback_data.card_id)
    red_player_id = int(data.get("red_player_id"))
    blue_player_id = int(data.get("blue_player_id"))
    turn_type: CardBattleTurnType = data.get("turn_type")
    battle_cards: Sequence[UserCardsToBattle] = tuple(data.get("battle_cards"))
    await add_turn(ssn, c.from_user.id, card_id, battle_id, turn_type)
    opposite_player_id = (
        red_player_id if c.from_user.id == blue_player_id else blue_player_id
    )
    remaining_cards = tuple(filter(lambda card: card.id != card_id, battle_cards))
    await state.update_data(battle_cards=remaining_cards)

    is_opposite_player_turn = await opposite_player_has_turn(
        ssn,
        battle_id,
        turn_type,
    )
    await c.message.delete()

    if is_opposite_player_turn:
        page = 1
        last = len(remaining_cards)

        try:
            opposite_remaining_cards = await get_remaining_cards(
                ssn, opposite_player_id, battle_id
            )
            last_opposite = len(opposite_remaining_cards)
            score: dict[int, int] = await battle_score(ssn, battle_id)
            red_player_score = score.get(red_player_id, 0)
            blue_player_score = score.get(blue_player_id, 0)
            if (last == 0 and last_opposite == 0) or (
                (red_player_score == 3 and blue_player_score == 0)
                or (red_player_score == 0 and blue_player_score == 3)
            ):
                await finish_players_cards_battle(ssn, battle_id)
                await update_ratings_after_battle(ssn, battle_id)

                await send_cards_battle_results(ssn, bot, battle_id)
                await state.clear()
                try:
                    del action_queue[str(c.from_user.id)]
                except Exception as error:
                    logging.info(f"Action delete error\n{error}")

                return
            else:
                txt = await format_view_cards_battle_text(
                    remaining_cards[0].user_card.card
                )
                opposite_txt = await format_view_cards_battle_text(
                    opposite_remaining_cards[0].user_card.card
                )

                last_turn_result = await get_last_turn_result(ssn, battle_id)
                last_win_turn = last_turn_result.win_turn
                if last_win_turn:
                    red_player_media_group = get_media_group_for_player(
                        last_turn_result, red_player_id, red_player_id, blue_player_id
                    )
                    blue_player_media_group = get_media_group_for_player(
                        last_turn_result, blue_player_id, red_player_id, blue_player_id
                    )
                    await bot.send_media_group(
                        chat_id=red_player_id,
                        media=red_player_media_group.build(),
                    )
                    await bot.send_media_group(
                        chat_id=blue_player_id,
                        media=blue_player_media_group.build(),
                    )
                else:
                    await bot.send_message(
                        text=f"Ничья!\nСчет: \nКрасный: {red_player_score}\nСиний: {blue_player_score}",
                        chat_id=red_player_id,
                    )
                    await bot.send_message(
                        text=f"Ничья!\nСчет: \nКрасный: {red_player_score}\nСиний: {blue_player_score}",
                        chat_id=blue_player_id,
                    )

                await bot.send_photo(
                    photo=opposite_remaining_cards[0].user_card.card.image,
                    caption=opposite_txt,
                    chat_id=opposite_player_id,
                    reply_markup=select_cards_for_cards_battle_kb(
                        page,
                        last_opposite,
                        "nosort",
                        card_id=opposite_remaining_cards[0].id,
                    ),
                )

                await c.message.answer_photo(
                    remaining_cards[0].user_card.card.image,
                    txt,
                    reply_markup=select_cards_for_cards_battle_kb(
                        page, last, "nosort", card_id=remaining_cards[0].id
                    ),
                )
        except Exception as error:
            print(error)
            raise error
    else:
        await c.answer("Ожидайте хода соперника")

    await state.update_data(
        turn_type=CardBattleTurnType.ATTACK
        if turn_type == CardBattleTurnType.DEFENSE
        else CardBattleTurnType.DEFENSE
    )
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
