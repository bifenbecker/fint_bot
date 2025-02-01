import logging
from textwrap import dedent

from aiogram import Bot, F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ

from db.models import CardItem, Trade
from db.queries.card_queries import get_user_card_rarities
from db.queries.collection_queries import get_user_rarity_cards
from db.queries.trade_queries import (decline_all_trades, decline_last_trade,
                                      decline_trade, get_trade_card_rarities,
                                      update_trade_status)
from keyboards.cb_data import PageCB
from keyboards.main_kbs import to_main_btn
from keyboards.trade_kbs import (after_trade_kb, offer_to_owner_kb,
                                 target_card_trade_kb, target_cards_kb,
                                 target_rarity_cards_kb)
from utils.format_texts import format_view_my_cards_text
from utils.states import UserStates

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data.startswith("answertrade_"), flags=flags)
async def answer_trade_cmd(c: CQ):
    trade_id = int(c.data.split("_")[-1])
    await c.message.delete()
    await c.message.answer(
        "🧳 Выберите формат отображения коллекции",
        reply_markup=target_cards_kb(trade_id))


@router.callback_query(
    F.data.startswith("answsorttrd_"), flags={"throttling_key": "pages"}
)
async def view_target_trade_sorted_cards_cmd(c: CQ, ssn, state: FSM):
    c_data = c.data.split("_")[-1]
    if c_data == "nosort":
        sorting = "down"
    elif c_data == "down":
        sorting = "up"
    else:
        sorting = "nosort"

    cards = await get_user_rarity_cards(ssn, c.from_user.id, "all", sorting)
    if len(cards) == 0:
        await c.answer("ℹ️ У тебя еще нет карт")
        await c.message.delete()
    else:
        page = 1
        last = len(cards)

        data = await state.get_data()
        trade_id = data.get("trade_id")
        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image, txt,
            reply_markup=target_card_trade_kb(page, last, sorting, cards[0].card_id, trade_id))

        await state.set_state(UserStates.target_trade)
        await state.update_data(cards=cards, sorting=sorting)


@router.callback_query(
    F.data.startswith("answtrdrar_"), flags={"throttling_key": "pages"}
)
async def view_owner_trade_rarity_cards_cmd(c: CQ, ssn, state: FSM):
    c_data = c.data.split("_")
    rarity = c_data[1]
    trade_id = int(c_data[2])

    cards = await get_user_rarity_cards(ssn, c.from_user.id, rarity, "nosort")

    if len(cards) == 0:
        if rarity == "all":
            await c.answer("ℹ️ У тебя еще нет карт")
        else:
            await c.answer("ℹ️ У тебя нет карт этой редкости")
    else:
        page = 1
        last = len(cards)

        await state.clear()
        await c.message.delete()

        txt = await format_view_my_cards_text(cards[0].card)
        await c.message.answer_photo(
            cards[0].card.image, txt,
            reply_markup=target_card_trade_kb(
                page, last, "nosort", cards[0].card_id, trade_id))

        await state.set_state(UserStates.target_trade)
        await state.update_data(
            cards=cards, sorting="nosort", trade_id=trade_id)


@router.callback_query(
    StateFilter(UserStates.target_trade),
    PageCB.filter(), flags={"throttling_key": "pages"}
)
async def paginate_target_trade_cards_cmd(c: CQ, state: FSM, callback_data: PageCB):
    page = int(callback_data.num)
    last = int(callback_data.last)

    data = await state.get_data()
    cards = data.get("cards")
    sorting = data.get("sorting")
    trade_id = data.get("trade_id")

    card = cards[page-1]
    txt = await format_view_my_cards_text(card.card)

    media = types.InputMediaPhoto(caption=txt, media=card.card.image)

    try:
        await c.message.edit_media(
            media=media, reply_markup=target_card_trade_kb(
                page, last, sorting, card.card_id, trade_id))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()


@router.callback_query(F.data.startswith("answtrdcard_"), flags=flags)
async def answer_trade_cmd(c: CQ, state: FSM, ssn, bot: Bot):
    card_id = int(c.data.split("_")[-1])
    data = await state.get_data()
    trade_id = data.get("trade_id")

    res = await update_trade_status(ssn, c.from_user.id, card_id, trade_id)
    if res == "no_card":
        await c.message.delete()
        await state.clear()
    elif res == "trade_not_available":
        await c.message.delete()
        await state.clear()
        txt = "Это предложение обмена больше недоступно"
        await c.message.answer(txt, reply_markup=to_main_btn)
    else:
        trade: Trade = res[0]
        card: CardItem = res[1]
        logging.info(
            f"User {c.from_user.id} answered on trade {trade.id} with card {card_id}")

        await c.message.delete()
        await c.message.answer(
            "✅ Предложение обмена успешно отправлено, ожидайте")

        txt = f"""
        ✅ Пользователь ответил на ваше предложение обмена!
        Вы получите эту карточку за вашу:
        {card.name}
        С редкостью - {card.rarity}
        """
        await bot.send_photo(
            trade.owner, card.image, caption=dedent(txt),
            reply_markup=offer_to_owner_kb(trade.id))


@router.callback_query(F.data.startswith("targetdeclinetrade_"), flags=flags)
async def decline_target_trade_cmd(c: CQ, ssn, state: FSM, bot: Bot):
    trade_id = int(c.data.split("_")[-1])
    res: Trade = await decline_trade(ssn, trade_id)

    await c.message.delete()
    if res == "not_active":
        await state.clear()
        txt = "Это предложение обмена больше недоступно"
        await c.message.answer(txt, reply_markup=to_main_btn)
    else:
        logging.info(f"User {c.from_user.id} canceled trade {trade_id}")

        await c.message.answer("❌ Вы отменили обмен!", reply_markup=after_trade_kb)

        await bot.send_message(
            res.owner, "❌ Увы, сделка сорвалась.", reply_markup=after_trade_kb)


@router.callback_query(F.data == "cancel_trade", flags=flags)
async def cancel_last_trade_cmd(c: CQ, ssn, state: FSM, bot: Bot):
    res: Trade = await decline_last_trade(ssn, c.from_user.id)

    await state.clear()
    await c.message.delete()
    await c.message.answer("❌ Вы отменили обмен!", reply_markup=after_trade_kb)
    if res != "not_found":
        logging.info(f"User {c.from_user.id} canceled trade {res.id}")
        if res.owner == c.from_user.id:
            user_id = res.target
        else:
            user_id = res.owner
        await bot.send_message(
            user_id, "❌ Увы, сделка сорвалась.", reply_markup=after_trade_kb)


@router.callback_query(F.data.startswith("answtraderarities_"), flags=flags)
async def rarities_target_trade_cmd(c: CQ, ssn):
    trade_id = int(c.data.split("_")[-1])
    txt = "Выберите редкость карт"
    rarities = await get_trade_card_rarities(ssn, c.from_user.id)
    await c.message.edit_text(
        txt, reply_markup=target_rarity_cards_kb(rarities, trade_id))


@router.callback_query(F.data == "cancel_all_trades", flags=flags)
async def cancel_all_trades_cmd(c: CQ, ssn):
    await decline_all_trades(ssn, c.from_user.id)

    await c.message.edit_text(
        "Вы успешно завершили все активные обмены",
        reply_markup=after_trade_kb)
