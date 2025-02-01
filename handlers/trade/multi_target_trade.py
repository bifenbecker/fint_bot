import logging
from textwrap import dedent

from aiogram import Bot, F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.models import Trade
from db.queries.multi_trade_qs import (change_mtrade_status,
                                       get_mtrade_card_rarities,
                                       get_target_selected_cards,
                                       get_user_rarity_cards_m_target)
from keyboards.cb_data import PageCB
from keyboards.main_kbs import to_main_btn
from keyboards.trade_kbs import (accept_m_trade_kb, m_target_trade_rarities_kb,
                                 send_mtrade_answer_kb, target_card_mtrade_kb)
from utils.format_texts import (format_m_trade_answer_text,
                                format_target_trade_cards_text,
                                format_view_my_cards_text)
from utils.states import MultiTrade

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(
    F.data.startswith("answermtrade_"), flags={"throttling_key": "pages"}
)
async def answer_trade_multi_cmd(c: CQ, ssn, state: FSM):
    trade_id = int(c.data.split("_")[-1])

    res = await get_user_rarity_cards_m_target(
        ssn, c.from_user.id, "all", "nosort", trade_id)
    cards = res[0]
    page = 1
    last = len(cards)

    await c.message.delete()

    txt = await format_view_my_cards_text(cards[0].card)
    await c.message.answer_photo(
        cards[0].card.image, txt,
        reply_markup=target_card_mtrade_kb(
            page, last, "nosort", "not_in", "all"))

    await state.set_state(MultiTrade.target_cards)
    await state.update_data(
        cards=cards, sorting="nosort", quant=res[1],
        selected=[], rarity="all", trade_id=trade_id)


@router.callback_query(
    StateFilter(MultiTrade.target_cards),
    F.data == "ansmtrdrarities", flags=flags
)
async def target_mtrade_rarities_cmd(c: CQ, ssn, state: FSM):
    data = await state.get_data()
    trade_id = data.get("trade_id")
    rarities = await get_mtrade_card_rarities(ssn, c.from_user.id, trade_id)
    await c.message.delete()
    await c.message.answer(
        "Выбери редкость карт", reply_markup=m_target_trade_rarities_kb(rarities))


@router.callback_query(
    StateFilter(MultiTrade.target_cards),
    F.data.startswith("trgtmtrdrar_"), flags={"throttling_key": "pages"}
)
async def view_target_mtrade_rarity_cards_cmd(c: CQ, ssn, state: FSM):
    c_data = c.data.split("_")
    rarity = c_data[1]

    data = await state.get_data()
    trade_id = data.get("trade_id")

    res = await get_user_rarity_cards_m_target(
        ssn, c.from_user.id, rarity, "nosort", trade_id)
    cards = res[0]
    if len(cards) == 0:
        if rarity == "all":
            await c.answer("ℹ️ У тебя еще нет карт")
        else:
            await c.answer("ℹ️ У тебя нет карт этой редкости")
    else:
        page = 1
        last = len(cards)

        selected = data.get("selected")
        if cards[0].id in selected:
            status = "in"
        else:
            status = "not_in"

        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image, txt,
            reply_markup=target_card_mtrade_kb(
                page, last, "nosort", status, rarity))

        await state.update_data(
            cards=cards, sorting="nosort", rarity=rarity, quant=res[1])


@router.callback_query(
    StateFilter(MultiTrade.target_cards),
    F.data.startswith("anssortmtrd_"), flags={"throttling_key": "pages"}
)
async def view_target_mtrade_sorted_cards_cmd(c: CQ, ssn, state: FSM):
    c_data = c.data.split("_")[-1]
    if c_data == "nosort":
        sorting = "down"
    elif c_data == "down":
        sorting = "up"
    else:
        sorting = "nosort"

    data = await state.get_data()
    trade_id = data.get("trade_id")

    res = await get_user_rarity_cards_m_target(
        ssn, c.from_user.id, "all", sorting, trade_id)
    cards = res[0]

    page = 1
    last = len(cards)

    selected = data.get("selected")
    if cards[0].id in selected:
        status = "in"
    else:
        status = "not_in"

    await c.message.delete()

    txt = await format_view_my_cards_text(cards[0].card)
    await c.message.answer_photo(
        cards[0].card.image, txt,
        reply_markup=target_card_mtrade_kb(page, last, sorting, status, "all"))

    await state.update_data(cards=cards, sorting=sorting, rarity="all")


@router.callback_query(
    StateFilter(MultiTrade.target_cards),
    PageCB.filter(), flags={"throttling_key": "pages"}
)
async def paginate_target_mtrade_cards_cmd(c: CQ, state: FSM, callback_data: PageCB):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")
    sorting = data.get("sorting")
    selected = data.get("selected")
    rarity = data.get("rarity")

    card = cards[page-1]

    if card.id in selected:
        status = "in"
    else:
        status = "not_in"

    txt = await format_view_my_cards_text(card.card)

    media = types.InputMediaPhoto(caption=txt, media=card.card.image)

    try:
        await c.message.edit_media(
            media=media, reply_markup=target_card_mtrade_kb(
                page, last, sorting, status, rarity))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()


@router.callback_query(
    StateFilter(MultiTrade.target_cards),
    F.data.startswith("anstrdselecexcard_"), flags={"throttling_key": "pages"}
)
async def select_target_mtrade_card_cmd(c: CQ, state: FSM):
    page = int(c.data.split("_")[-1])

    data = await state.get_data()
    cards = data.get("cards")
    selected = data.get("selected")
    quant = data.get("quant")
    rarity = data.get("rarity")
    sorting = data.get("sorting")

    card = cards[page-1]
    if card.id not in selected:
        if len(selected) >= quant:
            await c.answer(f"Нельзя выбрать больше {quant} карт")
        else:
            selected.append(card.id)
    else:
        await c.answer()

    await state.update_data(selected=selected)

    if card.id in selected:
        status = "in"
    else:
        status = "not_in"
    try:
        await c.message.edit_reply_markup(
            reply_markup=target_card_mtrade_kb(
                page, len(cards), sorting, status, rarity))
    except Exception as error:
        logging.error(f"{error}")


@router.callback_query(
    StateFilter(MultiTrade.target_cards),
    F.data.startswith("anstrdunselecexcard_"), flags={"throttling_key": "pages"}
)
async def unselect_target_mtrade_card_cmd(c: CQ, state: FSM):
    page = int(c.data.split("_")[-1])

    data = await state.get_data()
    cards = data.get("cards")
    selected = data.get("selected")
    rarity = data.get("rarity")
    sorting = data.get("sorting")

    card = cards[page-1]
    if card.id in selected:
        selected.remove(card.id)
    else:
        await c.answer()

    await state.update_data(selected=selected)

    if card.id in selected:
        status = "in"
    else:
        status = "not_in"
    try:
        await c.message.edit_reply_markup(
            reply_markup=target_card_mtrade_kb(
                page, len(cards), sorting, status, rarity))
    except Exception as error:
        logging.error(f"{error}")


@router.callback_query(
    StateFilter(MultiTrade.target_cards),
    F.data == "sendansmtradeoffer", flags=flags
)
async def target_mtrade_cards_selected_cmd(c: CQ, state: FSM, ssn):
    data = await state.get_data()
    selected = data.get("selected")
    trade_id = data.get("trade_id")
    quant = data.get("quant")
    if len(selected) < quant:
        await c.answer(f"Обмен {quant} на {quant}. Выберите еще карты")
    else:
        res = await get_target_selected_cards(ssn, trade_id, selected)

        await c.message.delete()
        txt = await format_target_trade_cards_text(res)
        await c.message.answer(txt, reply_markup=send_mtrade_answer_kb)
        await state.update_data(owner_cards=res[0], target_cards=res[1])


@router.callback_query(
    StateFilter(MultiTrade.target_cards),
    F.data == "confsendansmtradeoffer", flags=flags
)
async def send_mtrade_answer_cmd(c: CQ, state: FSM, ssn, bot: Bot):
    data = await state.get_data()
    trade_id = data.get("trade_id")
    selected = data.get("selected")

    trade: Trade = await change_mtrade_status(ssn, trade_id, selected, c.from_user.id)
    if trade == "not_active":
        await state.clear()
        txt = "Это предложение обмена больше недоступно"
        await c.message.answer(txt, reply_markup=to_main_btn)
    elif trade == "error":
        await state.clear()
        txt = "⚠️ Возникла ошибка!"
        await c.message.answer(txt, reply_markup=to_main_btn)
    else:
        await c.message.delete()
        await c.message.answer(
            "✅ Предложение обмена успешно отправлено, ожидайте")

        logging.info(
            f"User {c.from_user.id} answered on trade {trade_id}")

        owner_cards = data.get("owner_cards")
        target_cards = data.get("target_cards")

        txt = await format_m_trade_answer_text(trade, owner_cards, target_cards)
        await bot.send_message(
            trade.owner, text=txt,
            reply_markup=accept_m_trade_kb(trade.id))
