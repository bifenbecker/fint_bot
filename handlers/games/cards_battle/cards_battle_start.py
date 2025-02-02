import logging
from collections import Counter
from textwrap import dedent
from typing import Sequence

from aiogram import Bot, F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ

from db.models import UserCard
from db.queries.collection_queries import (
    get_user_collection_cards,
)
from enum_types import CardPositionType
from keyboards.cards_battle_kbs import (
    SelectCardOnPageCB,
    search_cards_battle_kb,
    select_cards_for_cards_battle_kb,
)
from keyboards.cb_data import PageCB
from keyboards.main_kbs import to_main_btn
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
    if len(cards) == 0:
        await c.answer("ℹ️ У тебя еще нет карт")
    # TODO: Check if enough cards here
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
    async def show_cards(page, last, sorting, card: UserCard):
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

    state_data = await state.get_data()

    sorting = state_data.get("sorting")
    page = int(callback_data.num)
    last = int(callback_data.last)
    card_id = int(callback_data.card_id)

    cards: Sequence[UserCard] = state_data.get("cards")
    selected = state_data.get("selected")
    selected_card: UserCard = next(filter(lambda x: x.id == card_id, cards))
    if not selected:
        selected = set()
    counter = Counter([x.card.position for x in selected])
    add_counter = Counter([selected_card.card.position])
    check = counter + add_counter

    if counter.total() == 5:
        await c.message.delete()
        await state.set_state(CardsBattleStates.search_cards_battle)
        await c.message.answer("Твои карты готовы", reply_markup=search_cards_battle_kb)
    elif check[CardPositionType.GOALKEEPER] > 1:
        await c.answer("❌ Нельзя выбрать более одного вратаря")
        await show_cards(page, last, sorting, card=selected_card)
    elif any(
        filter(
            lambda item: item[1] > 2 and item[0] != CardPositionType.GOALKEEPER,
            check.items(),
        )
    ):
        await c.answer("❌ Нельзя выбрать более двух игроков одной позиции")
        await show_cards(page, last, sorting, card=selected_card)
    else:
        await c.answer("✅ Карта выбрана")
        selected.add(selected_card)

        await state.update_data(selected=selected)

        remaining_cards: Sequence[UserCard] = list(
            filter(lambda x: x.id != selected_card.id, cards)
        )
        await state.update_data(cards=remaining_cards)
        if len(remaining_cards) == 0:
            await c.message.delete()
            await state.clear()
            await c.message.answer(
                "У тебя не хватает карт. Необходимо 5 карт",
                reply_markup=to_main_btn,
            )
        else:
            last = len(remaining_cards)
            page = 1
            try:
                card = remaining_cards[page - 1]
            except Exception as error:
                logging.error(f"Card error\n{error}")
                card = remaining_cards[0]

            await show_cards(page, last, sorting, card=card)
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    StateFilter(CardsBattleStates.search_cards_battle),
    F.data == "searchcardsbattle",
    flags=flags,
)
async def search_cards_battle_cmd(c: CQ, action_queue, ssn, state: FSM):
    await c.answer("🔎 Поиск карт")
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
