import logging
from textwrap import dedent

from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.queries.admin_queries import add_new_promo, delete_promo, get_promos
from db.queries.collection_queries import get_promo_rarity_cards, get_rarity_cards
from filters.filters import IsAdmin
from keyboards.admin_kbs import (
    admin_kb,
    back_to_admin_btn,
    promo_cards_kb,
    promo_kind_kb,
    promo_rarities_kb,
    promo_users_kb,
    view_promos_kb,
)
from keyboards.cb_data import PageCB
from utils.format_texts import format_view_my_cards_text
from utils.states import AdminStates

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "addpromo", IsAdmin(), flags=flags)
async def add_promo_cmd(c: CQ, state: FSM):
    await state.clear()

    txt = "Этот промокод для новых пользователей?"
    await c.message.edit_text(txt, reply_markup=promo_users_kb)
    await state.set_state(AdminStates.promo_users)


@router.callback_query(F.data.startswith("prmusers_"), IsAdmin(), flags=flags)
async def choose_promo_pack_cmd(c: CQ, state: FSM):
    users = c.data.split("_")[-1]

    txt = "Выберите награду за промокод"
    await c.message.edit_text(txt, reply_markup=promo_kind_kb)
    await state.set_state(AdminStates.promo_kind)
    await state.update_data(users=users)


@router.callback_query(F.data.startswith("prmkind_random_"), IsAdmin(), flags=flags)
async def choose_promo_pack_cmd(c: CQ, state: FSM):
    quant = int(c.data.split("_")[-1])
    if quant == 1:
        kind = "card"
        card_id = 0
    else:
        kind = f"pack{quant}"
        card_id = 0

    txt = """
    Напишите промокод, который хотите добавить
    Чтобы указать количество использований напишите это число через пробел от промокода
    """
    await c.message.edit_text(dedent(txt), reply_markup=back_to_admin_btn)
    await state.set_state(AdminStates.promo_text)
    await state.update_data(card_id=card_id, kind=kind)


@router.callback_query(F.data == "promokind_finpass", IsAdmin(), flags=flags)
async def choose_promo_pack_cmd(c: CQ, state: FSM):
    kind = "pass"

    txt = """
    Напишите промокод, который хотите добавить
    Чтобы указать количество использований напишите это число через пробел от промокода
    """
    await c.message.edit_text(dedent(txt), reply_markup=back_to_admin_btn)
    await state.set_state(AdminStates.promo_text)
    await state.update_data(kind=kind)


@router.callback_query(F.data == "prmkind_pick", IsAdmin(), flags=flags)
async def choose_promo_player_pick_cmd(c: CQ, state: FSM):
    card_id = 0
    kind = "pick"

    txt = """
    Напишите промокод, который хотите добавить
    Чтобы указать количество использований напишите это число через пробел от промокода
    """
    await c.message.edit_text(dedent(txt), reply_markup=back_to_admin_btn)
    await state.set_state(AdminStates.promo_text)
    await state.update_data(card_id=card_id, kind=kind)


@router.message(StateFilter(AdminStates.promo_text), F.text, flags=flags)
async def save_promo_text_cmd(m: Mes, state: FSM, ssn):
    m_data = m.text.split()
    if len(m_data) == 2:
        uses = int(m_data[1])
    else:
        uses = 2000000

    data = await state.get_data()
    card_id = data.get("card_id")
    kind = data.get("kind")
    users = data.get("users")

    await state.clear()
    text = m_data[0]

    await add_new_promo(ssn, card_id, text, kind, uses, users)
    txt = "Промокод был успешно добавлен! Время его проверить"
    await m.answer(txt, reply_markup=admin_kb)


@router.callback_query(
    F.data.startswith("promorarity_"), IsAdmin(), flags={"throttling_key": "pages"}
)
async def choose_promo_card_cmd(c: CQ, state: FSM, ssn):
    rarity = c.data.split("_")[-1]
    cards = await get_rarity_cards(ssn, rarity)

    page = 1
    last = len(cards)

    await c.message.delete()

    txt = await format_view_my_cards_text(cards[0])
    await c.message.answer_photo(
        cards[0].image,
        txt,
        reply_markup=promo_cards_kb(page, last, cards[0].id, "nosort", rarity),
    )

    await state.set_state(AdminStates.promo_cards)
    await state.update_data(cards=cards, sorting="nosort", rarity=rarity)


@router.callback_query(
    F.data.startswith("sortprmcards_"), flags={"throttling_key": "pages"}
)
async def view_sorted_promo_cards_cmd(c: CQ, ssn, state: FSM):
    c_data = c.data.split("_")[-1]
    if c_data == "nosort":
        sorting = "down"
    elif c_data == "down":
        sorting = "up"
    else:
        sorting = "nosort"

    rarity = "all"
    cards = await get_promo_rarity_cards(ssn, rarity, sorting)

    page = 1
    last = len(cards)

    await c.message.delete()

    txt = await format_view_my_cards_text(cards[0])
    await c.message.answer_photo(
        cards[0].image,
        txt,
        reply_markup=promo_cards_kb(page, last, cards[0].id, sorting, rarity),
    )

    await state.set_state(AdminStates.promo_cards)
    await state.update_data(cards=cards, sorting=sorting, rarity=rarity)


@router.callback_query(
    StateFilter(AdminStates.promo_cards),
    PageCB.filter(),
    flags={"throttling_key": "pages"},
)
async def paginate_promo_cards_cmd(c: CQ, state: FSM, callback_data: PageCB):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")
    sorting = data.get("sorting")
    rarity = data.get("rarity")

    card = cards[page - 1]
    txt = await format_view_my_cards_text(card)

    media = types.InputMediaPhoto(caption=txt, media=card.image)

    try:
        await c.message.edit_media(
            media=media,
            reply_markup=promo_cards_kb(page, last, card.id, sorting, rarity),
        )
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()


@router.callback_query(
    StateFilter(AdminStates.promo_cards),
    F.data == "changepromorarity",
    IsAdmin(),
    flags=flags,
)
async def change_promo_rarity_cmd(c: CQ):
    await c.message.delete()
    txt = "🎭 Выберите формат отображения"
    await c.message.answer(txt, reply_markup=promo_rarities_kb)


@router.callback_query(
    StateFilter(AdminStates.promo_cards),
    F.data.startswith("prmcard_"),
    IsAdmin(),
    flags=flags,
)
async def save_new_promo_cmd(c: CQ, state: FSM, ssn):
    card_id = int(c.data.split("_")[-1])
    kind = "card"

    txt = """
    Напишите промокод, который хотите добавить
    Чтобы указать количество использований напишите это число через пробел от промокода
    """
    await c.message.delete()
    await c.message.answer(dedent(txt), reply_markup=back_to_admin_btn)
    await state.set_state(AdminStates.promo_text)
    await state.update_data(card_id=card_id, kind=kind)


@router.callback_query(F.data == "delpromos", IsAdmin(), flags=flags)
async def view_promos_cmd(c: CQ, ssn):
    promos = await get_promos(ssn)

    txt = """
    Выберете промокод для удаления
    Все промокоды указаны в формате промокод - карточка
    """
    await c.message.edit_text(dedent(txt), reply_markup=view_promos_kb(promos))


@router.callback_query(F.data.startswith("delpromo_"), IsAdmin(), flags=flags)
async def delete_promo_cmd(c: CQ, ssn):
    promo_id = int(c.data.split("_")[-1])

    promos = await delete_promo(ssn, promo_id)

    await c.answer("Промокод удален", show_alert=True)
    await c.message.edit_reply_markup(reply_markup=view_promos_kb(promos))
