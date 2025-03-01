import asyncio
import logging
import random
from collections import Counter
from typing import Sequence

from aiogram import Bot, F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import dice
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.models import Player, UserCard
from db.queries.cards_battle_queries import (
    change_player_card_battle_status,
    create_card_battle,
    get_searching_players,
    player_end_search_card_battle,
    player_start_search_card_battle,
)
from db.queries.collection_queries import get_user_collection_cards
from enum_types import CardBattlePlayerStatus, CardPositionType
from keyboards.cards_battle_kbs import (
    SelectCardOnPageCB,
    cancel_cards_battle_btn,
    get_choose_type_of_turn_kb,
    search_cards_battle_kb,
    select_cards_for_cards_battle_kb,
)
from keyboards.cb_data import PageCB
from middlewares.actions import ActionMiddleware
from utils.format_texts import format_view_cards_battle_text
from utils.states import CardsBattleStates

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "cardsbattle", flags=flags)
async def create_cards_battle_cmd(c: CQ, action_queue, ssn, state: FSM):
    txt = """
    ⚖️ Битва составов

    Собери составы и сыграй в битву.
    """
    rarity = "all"
    cards: Sequence[UserCard] = await get_user_collection_cards(
        ssn, c.from_user.id, rarity, "nosort"
    )
    if len(cards) < 5:
        await c.answer("ℹ️ У тебя не хватает карт. Необходимое количество: 5")
    else:
        page = 1
        last = len(cards)

        await state.clear()
        try:
            await c.message.delete()
        except Exception as error:
            logging.error(f"Del error | chat {c.from_user.id}\n{error}")

        txt = await format_view_cards_battle_text(cards[0].card)

        await state.set_state(CardsBattleStates.select_cards_battle)
        await state.update_data(cards=cards, sorting="nosort", selected=None)
        first_card: UserCard = cards[page - 1]
        await c.message.answer_photo(
            cards[0].card.image,
            txt,
            reply_markup=select_cards_for_cards_battle_kb(
                page, last, "nosort", card_id=first_card.id
            ),
        )
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("cards_battle_sortmycards_"), flags=flags)
async def view_sorted_cards_cmd(c: CQ, ssn, state: FSM, action_queue):
    c_data = c.data.split("_")[-1]
    if c_data == "nosort":
        sorting = "down"
    elif c_data == "down":
        sorting = "up"
    else:
        sorting = "nosort"

    data = await state.get_data()
    cards: Sequence[UserCard] = data.get("cards", [])
    if len(cards) == 0:
        await c.answer("ℹ️ У тебя еще нет карт")
        await c.message.delete()
    else:
        page = 1
        last = len(cards)
        await state.update_data(sorting=sorting)
        await c.message.delete()

        txt = await format_view_cards_battle_text(cards[0].card)
        first_card: UserCard = cards[page - 1]
        await c.message.answer_photo(
            cards[0].card.image,
            txt,
            reply_markup=select_cards_for_cards_battle_kb(
                page, last, sorting, card_id=first_card.id
            ),
        )
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(CardsBattleStates.select_cards_battle),
    PageCB.filter(),
    flags=flags,
)
async def paginate_cards_cmd(c: CQ, action_queue, state: FSM, callback_data: PageCB):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")
    sorting = data.get("sorting")
    card = cards[page - 1]
    txt = await format_view_cards_battle_text(card.card)

    media = types.InputMediaPhoto(caption=txt, media=card.card.image)

    try:
        await c.message.edit_media(
            media=media,
            reply_markup=select_cards_for_cards_battle_kb(
                page, last, sorting, card_id=card.id
            ),
        )
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(CardsBattleStates.select_cards_battle),
    SelectCardOnPageCB.filter(),
    flags=flags,
)
async def save_selected_cards(
    c: CQ, action_queue, state: FSM, callback_data: SelectCardOnPageCB
):
    async def show_cards(
        page_to_show: int,
        last_to_show: int,
        sorting_to_show: str,
        card_to_show: UserCard,
    ) -> None:
        txt = await format_view_cards_battle_text(card_to_show.card)
        media = types.InputMediaPhoto(caption=txt, media=card_to_show.card.image)
        try:
            await c.message.edit_media(
                media=media,
                reply_markup=select_cards_for_cards_battle_kb(
                    page_to_show, last_to_show, sorting_to_show, card_id=card_to_show.id
                ),
            )
        except Exception as error:
            logging.error(f"Edit error\n{error}")
            await c.answer()

    state_data = await state.get_data()

    sorting = state_data.get("sorting")
    page = int(callback_data.num)
    last = int(callback_data.last)
    card_id = int(callback_data.card_id)

    cards: Sequence[UserCard] = state_data.get("cards")
    selected: None | set = state_data.get("selected")
    selected_card: UserCard = next(filter(lambda x: x.id == card_id, cards))
    if not selected:
        selected = set()
    counter = Counter([x.card.position for x in selected])
    add_counter = Counter([selected_card.card.position])
    check = counter + add_counter

    if check.total() == 5:
        await c.answer("✅ Карта выбрана")
        selected.add(selected_card)
        await state.update_data(selected=selected)
        await c.message.delete()
        await state.set_state(CardsBattleStates.search_cards_battle)
        await c.message.answer("Твои карты готовы", reply_markup=search_cards_battle_kb)
    elif check[CardPositionType.GOALKEEPER] > 1:
        await c.answer("❌ Нельзя выбрать более одного вратаря")
        await show_cards(page, last, sorting, card_to_show=selected_card)
    elif any(
        filter(
            lambda item: item[1] > 2 and item[0] != CardPositionType.GOALKEEPER,
            check.items(),
        )
    ):
        await c.answer("❌ Нельзя выбрать более двух игроков одной позиции")
        await show_cards(page, last, sorting, card_to_show=selected_card)
    else:
        await c.answer("✅ Карта выбрана")
        selected.add(selected_card)
        await state.update_data(selected=selected)

        remaining_cards: Sequence[UserCard] = list(
            filter(lambda x: x.id != selected_card.id, cards)
        )
        await state.update_data(cards=remaining_cards)
        last = len(remaining_cards)
        page = 1
        try:
            card = remaining_cards[page - 1]
        except Exception as error:
            logging.error(f"Card error\n{error}")
            card = remaining_cards[0]

        await show_cards(page, last, sorting, card_to_show=card)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


async def roll_cards_battle(
    ssn: AsyncSession, bot: Bot, player_id: int, second_player: Player
) -> tuple[int, int]:
    dice1 = await bot.send_dice(player_id, emoji=dice.DiceEmoji.DICE)
    dice2 = await bot.send_dice(int(second_player.id), emoji=dice.DiceEmoji.DICE)
    await asyncio.sleep(5)
    red_player_id = (
        player_id if dice1.dice.value >= dice2.dice.value else second_player.id
    )
    blue_player_id = (
        player_id if dice1.dice.value < dice2.dice.value else second_player.id
    )
    return int(red_player_id), int(blue_player_id)


async def send_roll_result_messages(
    bot: Bot, ssn: AsyncSession, red_player_id: int, blue_player_id: int, state: FSM
) -> None:
    battle = await create_card_battle(ssn, blue_player_id, red_player_id)
    await change_player_card_battle_status(
        ssn, blue_player_id, CardBattlePlayerStatus.PLAYING
    )
    await change_player_card_battle_status(
        ssn, red_player_id, CardBattlePlayerStatus.PLAYING
    )
    await state.set_state(CardsBattleStates.playing_cards_battle)
    await state.update_data(
        battle_id=battle.id, red_player_id=red_player_id, blue_player_id=blue_player_id
    )
    await bot.send_message(
        chat_id=red_player_id,
        text="🔸<b>Соперник найден.</b>\nВы ходите первым, ваш цвет <b>красный</b> 🟥",
        reply_markup=get_choose_type_of_turn_kb(
            battle_id=battle.id,
            red_player_id=red_player_id,
            blue_player_id=blue_player_id,
        ),
    )
    await bot.send_message(
        chat_id=blue_player_id,
        text="🔸<b>Соперник найден.</b>\nВы ходите вторым, ваш цвет <b>синий</b> 🟦",
    )


@router.callback_query(
    StateFilter(CardsBattleStates.search_cards_battle),
    F.data == "searchcardsbattle",
    flags=flags,
)
async def search_cards_battle_cmd(
    c: CQ,
    bot: Bot,
    action_queue,
    ssn: AsyncSession,
    db: async_sessionmaker[AsyncSession],
    state: FSM,
):
    await c.answer("🔎 Поиск соперника")
    await c.message.delete()
    message = await c.message.answer(
        "🔎 Идет поиск...",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[[cancel_cards_battle_btn]]
        ),
    )
    searching_players = await get_searching_players(ssn, c.from_user.id)
    if len(searching_players) > 0:
        second_player: Player = random.choice(searching_players)
        await message.delete()
        red_player_id, blue_player_id = await roll_cards_battle(
            ssn, bot, c.from_user.id, second_player
        )
        await send_roll_result_messages(bot, ssn, red_player_id, blue_player_id, state)
    else:
        await player_start_search_card_battle(ssn=ssn, player_id=c.from_user.id)
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


# TODO: Add CardsBattleCancelCB from keyboards.cb_data
@router.callback_query(F.data == "cancel_cards_battle", flags=flags)
async def cancel_cards_battle_cmd(c: CQ, action_queue, ssn, state: FSM):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
    await c.answer("✅ Выход")
    await c.message.delete()
    await player_end_search_card_battle(ssn=ssn, player_id=c.from_user.id)
    await state.clear()
    await c.message.answer(
        "✅ Выход",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="🧑💻 В личный кабинет", callback_data="startplay"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="Собрать карты", callback_data="cardsbattle"
                    )
                ],
            ]
        ),
    )
