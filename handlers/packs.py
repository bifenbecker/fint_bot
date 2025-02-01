import datetime
import logging
from textwrap import dedent

from aiogram import Bot, F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.models import CardItem
from db.queries.global_queries import get_or_add_userpacks
from db.queries.packs_qs import (open_default_pack, open_player_pick,
                                 save_player_pick)
from keyboards.cards_kbs import accept_new_card_btn
from keyboards.cb_data import PageCB
from keyboards.main_kbs import user_packs_kb
from keyboards.pay_kbs import cards_pack_btn, player_pick_kb
from utils.format_texts import (format_view_my_cards_text,
                                format_view_my_packs_text)
from utils.states import UserStates

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "mypacks", flags=flags)
async def my_packs_cmd(c: CQ, ssn):
    upacks = await get_or_add_userpacks(ssn, c.from_user.id)
    txt = await format_view_my_packs_text(upacks)

    try:
        await c.message.delete()
    except:
        pass

    await c.message.answer(txt, reply_markup=user_packs_kb(upacks))


@router.callback_query(F.data == "openfivepack", flags=flags)
async def open_five_pack_cmd(c: CQ, ssn):
    res = await open_default_pack(ssn, c.from_user.id, 5)
    if res == "no_packs":
        await c.answer("У вас нет этого пака на балансе", show_alert=True)
    else:
        txt = "🗃 Пак открыт. Теперь ты можешь посмотреть полученные карты"
        await c.message.edit_text(txt, reply_markup=cards_pack_btn(res))


@router.callback_query(F.data == "opentenpack", flags=flags)
async def open_ten_pack_cmd(c: CQ, ssn):
    res = await open_default_pack(ssn, c.from_user.id, 10)
    if res == "no_packs":
        await c.answer("У вас нет этого пака на балансе", show_alert=True)
    else:
        txt = "🗃 Пак открыт. Теперь ты можешь посмотреть полученные карты"
        await c.message.edit_text(txt, reply_markup=cards_pack_btn(res))


@router.callback_query(F.data == "opentwentypack", flags=flags)
async def open_twenty_pack_cmd(c: CQ, ssn):
    res = await open_default_pack(ssn, c.from_user.id, 20)
    if res == "no_packs":
        await c.answer("У вас нет этого пака на балансе", show_alert=True)
    else:
        txt = "🗃 Пак открыт. Теперь ты можешь посмотреть полученные карты"
        await c.message.edit_text(txt, reply_markup=cards_pack_btn(res))


@router.callback_query(F.data == "openthirtypack", flags=flags)
async def open_thirty_pack_cmd(c: CQ, ssn):
    print("def open_thirty_pack_cmd")
    res = await open_default_pack(ssn, c.from_user.id, 30)
    if res == "no_packs":
        await c.answer("У вас нет этого пака на балансе", show_alert=True)
    else:
        txt = "🗃 Пак открыт. Теперь ты можешь посмотреть полученные карты"
        await c.message.edit_text(txt, reply_markup=cards_pack_btn(res))


@router.callback_query(F.data == "openplayerpick", flags=flags)
async def open_player_pick_cmd(c: CQ, ssn, state: FSM):
    res = await open_player_pick(ssn, c.from_user.id)
    if res == "no_packs":
        await c.answer("У вас нет этого пака на балансе", show_alert=True)
    else:
        page = 1
        last = 3

        try:
            await c.message.delete()
        except:
            pass
        card: CardItem = res[1][0]
        txt = await format_view_my_cards_text(card)

        await c.message.answer_photo(
            card.image,
            txt, reply_markup=player_pick_kb(page, last, res[0], card.id))
        await state.set_state(UserStates.player_pick)
        await state.update_data(pick_id=res[0], cards=res[1])


@router.callback_query(StateFilter(UserStates.player_pick), PageCB.filter())
async def paginate_player_pick(c: CQ, state: FSM, callback_data: PageCB):
    page = callback_data.num
    last = callback_data.last

    data = await state.get_data()
    pick_id = data.get("pick_id")
    cards = data.get("cards")
    card: CardItem = cards[page-1]

    txt = await format_view_my_cards_text(card)
    media = types.InputMediaPhoto(caption=txt, media=card.image)

    try:
        await c.message.edit_media(
            media=media,
            reply_markup=player_pick_kb(page, last, pick_id, card.id))
    except Exception as error:
        logging.error(f"Edit error\n{error}")
        await c.answer()


@router.callback_query(
    StateFilter(UserStates.player_pick), F.data.startswith("plrpick_")
)
async def player_pick_done(c: CQ, state: FSM, ssn):
    c_data = c.data.split("_")
    pick_id = int(c_data[1])
    card_id = int(c_data[2])
    await state.clear()

    res = await save_player_pick(ssn, c.from_user.id, pick_id, card_id)
    if res == "not_active":
        await c.answer(
            "Вы уже выбрали карту из этого выбора игрока", show_alert=True)
        try:
            await c.message.delete()
        except:
            pass
    else:
        await c.message.edit_reply_markup(reply_markup=accept_new_card_btn)
