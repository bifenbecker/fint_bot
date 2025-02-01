import datetime
import logging
from textwrap import dedent

from aiogram import F, Router
from aiogram.types import CallbackQuery as CQ

from db.models import PayItem
from db.queries.payment_queries import (add_ls_after_pay, add_new_payment,
                                        cancel_payment, get_payment_info)
from keyboards.cb_data import PayCB
from keyboards.games_kbs import lucky_shot_btn
from keyboards.main_kbs import main_kb
from keyboards.pay_kbs import pay_kb
from utils.pay_actions import check_bill_for_pay, create_new_bill

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(PayCB.filter(F.act == "cncl"), flags=flags)
async def cancel_payment_cmd(c: CQ, callback_data: PayCB, ssn):
    pay_id = int(callback_data.pay_id)
    res = await cancel_payment(ssn, pay_id, c.from_user.id)

    try:
        await c.message.delete()
    except Exception as error:
        logging.error(f"Del error | chat {c.from_user.id}\n{error}")

    user = res[0]
    date = datetime.datetime.now()
    date_ts = int(date.timestamp())
    txt = f"""
    Твои достижения:

    👀 Дней в игре: {(date_ts - user.joined_at_ts) // 86400}

    🃏 Собранное количество карточек: {user.card_quants}
    🏆 Рейтинг собранных карточек: {user.rating}
    🧩 Сезонный рейтинг коллекционера: {user.season_rating}
    📊 Место в сезонном рейтинге: {res[1]}
    """
    await c.message.answer(dedent(txt), reply_markup=main_kb)


@router.callback_query(F.data.startswith("buyls"), flags=flags)
async def buy_ls_cmd(c: CQ, wallet, ssn):
    quant = int(c.data[-1])
    if quant == 3:
        price = 125
    elif quant == 6:
        price = 235
    else:
        price = 350

    pay_res = await create_new_bill(
        price, c.from_user.id, f"{quant} Lucky Shots", wallet)
    pay_id = await add_new_payment(
        ssn, c.from_user.id, pay_res[0], pay_res[1], f"{quant} Lucky Shots", price)
    logging.info(
        f"User {c.from_user.id} created new bill {pay_id} label {pay_res[0]} kind ls{quant}")

    txt = "Ваш заказ сформирован\nОплатите его по кнопке ниже"
    await c.message.edit_text(txt, reply_markup=pay_kb(pay_id, pay_res[1], f"ls{quant}"))


@router.callback_query(PayCB.filter((F.act == "paid") & (F.kind.startswith("ls"))), flags=flags)
async def paid_ls_cmd(c: CQ, callback_data: PayCB, ssn, yoo_token):
    pay_id = int(callback_data.pay_id)
    kind = callback_data.kind
    quant = int(kind[-1])

    pay: PayItem = await get_payment_info(ssn, pay_id)
    result = await check_bill_for_pay(pay.label, yoo_token)
    # result = "found"
    if result == "found":
        await add_ls_after_pay(ssn, c.from_user.id, pay_id, quant)
        logging.info(
            f"User {c.from_user.id} payd bill {pay_id} label {pay.label} kind {pay.kind}")
        txt = "Успешно ✅!\nКупленные удары уже начисленны вам, время проверить удачу!"
        await c.message.edit_text(txt, reply_markup=lucky_shot_btn)
    else:
        await c.answer("⚠️ Счет не оплачен", show_alert=True)
