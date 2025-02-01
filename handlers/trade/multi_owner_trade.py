import logging

from aiogram import Bot, F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.queries.multi_trade_qs import (
    create_new_mtrade,
    get_owner_selected_cards,
    get_user_rarity_cards_m,
)
from db.queries.trade_queries import get_trade_card_rarities
from keyboards.cb_data import PageCB
from keyboards.main_kbs import to_main_btn
from keyboards.trade_kbs import (
    card_mtrade_kb,
    m_offer_to_target_kb,
    m_trade_rarities_kb,
)
from utils.format_texts import (
    format_multi_trade_offer_text,
    format_owner_trade_cards_text,
    format_view_my_cards_text,
)
from utils.states import MultiTrade

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data.startswith("trdqnt_"), flags={"throttling_key": "pages"})
async def trade_multi_cmd(c: CQ, ssn, state: FSM):
    quant = int(c.data.split("_")[-1])

    cards = await get_user_rarity_cards_m(ssn, c.from_user.id, "all", "nosort")
    if len(cards) < quant:
        await c.answer("ℹ️ У тебя недостаточно карт для такого обмена")
    else:
        page = 1
        last = len(cards)

        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image,
            txt,
            reply_markup=card_mtrade_kb(page, last, "nosort", "not_in", "all"),
        )

        await state.set_state(MultiTrade.owner_cards)
        await state.update_data(
            cards=cards, sorting="nosort", quant=quant, selected=[], rarity="all"
        )


@router.callback_query(
    StateFilter(MultiTrade.owner_cards), F.data == "mtrdrarities", flags=flags
)
async def mtrade_rarities_cmd(c: CQ, ssn):
    rarities = await get_trade_card_rarities(ssn, c.from_user.id)
    await c.message.delete()
    await c.message.answer(
        "Выбери редкость карт", reply_markup=m_trade_rarities_kb(rarities)
    )


@router.callback_query(
    StateFilter(MultiTrade.owner_cards),
    F.data.startswith("mtrdrar_"),
    flags={"throttling_key": "pages"},
)
async def view_owner_mtrade_rarity_cards_cmd(c: CQ, ssn, state: FSM):
    c_data = c.data.split("_")
    rarity = c_data[1]

    cards = await get_user_rarity_cards_m(ssn, c.from_user.id, rarity, "nosort")
    if len(cards) == 0:
        if rarity == "all":
            await c.answer("ℹ️ У тебя еще нет карт")
        else:
            await c.answer("ℹ️ У тебя нет карт этой редкости")
    else:
        page = 1
        last = len(cards)

        data = await state.get_data()
        selected = data.get("selected")
        if cards[0].id in selected:
            status = "in"
        else:
            status = "not_in"

        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image,
            txt,
            reply_markup=card_mtrade_kb(page, last, "nosort", status, rarity),
        )

        await state.set_state(MultiTrade.owner_cards)
        await state.update_data(cards=cards, sorting="nosort", rarity=rarity)


@router.callback_query(
    StateFilter(MultiTrade.owner_cards),
    F.data.startswith("sortmtrd_"),
    flags={"throttling_key": "pages"},
)
async def view_mtrade_sorted_cards_cmd(c: CQ, ssn, state: FSM):
    c_data = c.data.split("_")[-1]
    if c_data == "nosort":
        sorting = "down"
    elif c_data == "down":
        sorting = "up"
    else:
        sorting = "nosort"

    cards = await get_user_rarity_cards_m(ssn, c.from_user.id, "all", sorting)
    if len(cards) == 0:
        await c.answer("ℹ️ У тебя еще нет карт")
        await c.message.delete()
    else:
        page = 1
        last = len(cards)

        data = await state.get_data()
        selected = data.get("selected")
        if cards[0].id in selected:
            status = "in"
        else:
            status = "not_in"

        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image,
            txt,
            reply_markup=card_mtrade_kb(page, last, sorting, status, "all"),
        )

        await state.update_data(cards=cards, sorting=sorting, rarity="all")


@router.callback_query(
    StateFilter(MultiTrade.owner_cards),
    PageCB.filter(),
    flags={"throttling_key": "pages"},
)
async def paginate_owner_mtrade_cards_cmd(c: CQ, state: FSM, callback_data: PageCB):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")
    sorting = data.get("sorting")
    selected = data.get("selected")
    rarity = data.get("rarity")

    card = cards[page - 1]

    if card.id in selected:
        status = "in"
    else:
        status = "not_in"

    txt = await format_view_my_cards_text(card.card)

    media = types.InputMediaPhoto(caption=txt, media=card.card.image)

    try:
        await c.message.edit_media(
            media=media,
            reply_markup=card_mtrade_kb(page, last, sorting, status, rarity),
        )
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()


@router.callback_query(
    StateFilter(MultiTrade.owner_cards),
    F.data.startswith("trdselecexcard_"),
    flags={"throttling_key": "pages"},
)
async def select_mtrade_card_cmd(c: CQ, state: FSM):
    page = int(c.data.split("_")[-1])

    data = await state.get_data()
    cards = data.get("cards")
    selected = data.get("selected")
    quant = data.get("quant")
    rarity = data.get("rarity")
    sorting = data.get("sorting")

    card = cards[page - 1]
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
            reply_markup=card_mtrade_kb(page, len(cards), sorting, status, rarity)
        )
    except Exception as error:
        logging.error(f"{error}")


@router.callback_query(
    StateFilter(MultiTrade.owner_cards),
    F.data.startswith("trdunselecexcard_"),
    flags={"throttling_key": "pages"},
)
async def unselect_mtrade_card_cmd(c: CQ, state: FSM):
    page = int(c.data.split("_")[-1])

    data = await state.get_data()
    cards = data.get("cards")
    selected = data.get("selected")
    rarity = data.get("rarity")
    sorting = data.get("sorting")

    card = cards[page - 1]
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
            reply_markup=card_mtrade_kb(page, len(cards), sorting, status, rarity)
        )
    except Exception as error:
        logging.error(f"{error}")


@router.callback_query(
    StateFilter(MultiTrade.owner_cards),
    F.data == "sendmtradeoffer",
    flags={"throttling_key": "pages"},
)
async def mtrade_cards_selected_cmd(c: CQ, state: FSM, ssn):
    data = await state.get_data()
    selected = data.get("selected")
    quant = data.get("quant")
    if len(selected) < quant:
        await c.answer(f"Выбран обмен {quant} на {quant}. Выберите еще карты")
    else:
        cards = await get_owner_selected_cards(ssn, c.from_user.id, selected)

        if len(cards) < len(selected):
            await c.answer("Возникла ошибка!", show_alert=True)
            await c.message.delete()
            await state.clear()
        else:
            await c.message.delete()
            txt = await format_owner_trade_cards_text(cards)
            await c.message.answer(txt)
            await state.set_state(MultiTrade.target_username)


@router.message(StateFilter(MultiTrade.target_username), F.text, flags=flags)
async def save_target_mtrade_username_cmd(m: Mes, state: FSM, ssn, bot: Bot):
    data = await state.get_data()
    await state.clear()
    target = m.text
    quant = data.get("quant")

    if m.from_user.username:
        username = f"@{m.from_user.username}"
    else:
        username = m.from_user.mention_html()

    res = await create_new_mtrade(
        ssn, m.from_user.id, username, data["selected"], target, quant
    )
    if res == "no_card":
        await m.answer(
            "⚠️ Возникла ошибка при создании обмена", reply_markup=to_main_btn
        )
    elif res == "not_access":
        txt = "Этому пользователю запрещено проводить обмен"
        await m.answer(txt, reply_markup=to_main_btn)
    elif res == "not_found":
        txt = "Этому пользователю нельзя предложить обмен, попробуйте снова"
        await m.answer(txt, reply_markup=to_main_btn)
    elif res == "already_playing":
        txt = "Не удалось создать обмен, так как один из игроков находится в пенальти или дуэли"
        await m.answer(txt, reply_markup=to_main_btn)
    elif res == "user_limit":
        txt = "Сегодня вы больше не можете обмениваться с этим игроком"
        await m.answer(txt, reply_markup=to_main_btn)
    else:
        trade_id = res[0]
        target_id = res[1]

        logging.info(
            f"User {m.from_user.id} created new multi trade {quant}x{quant} #{trade_id} to {target_id} ({target})"
        )

        txt = f"✅ Предложение обмена успешно отправлено пользователю - {target}"
        await m.answer(txt)

        target_txt = await format_multi_trade_offer_text(username, res[2], quant)
        await bot.send_message(
            target_id, text=target_txt, reply_markup=m_offer_to_target_kb(trade_id)
        )
