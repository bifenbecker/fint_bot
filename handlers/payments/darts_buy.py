import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery as CQ

from db.models import PayItem
from db.queries.payment_queries import (
    add_darts_after_pay,
    add_new_payment,
    get_payment_info,
)
from keyboards.cb_data import PayCB
from keyboards.games_kbs import darts_kb
from keyboards.pay_kbs import pay_kb
from utils.pay_actions import check_bill_for_pay, create_new_bill

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data.startswith("buydts"), flags=flags)
async def buy_darts_cmd(c: CQ, wallet, ssn):
    quant = int(c.data[-1])
    if quant == 3:
        price = 150
    elif quant == 6:
        price = 300
    else:
        price = 400

    pay_res = await create_new_bill(price, c.from_user.id, f"{quant} Darts", wallet)
    pay_id = await add_new_payment(
        ssn, c.from_user.id, pay_res[0], pay_res[1], f"{quant} Darts", price
    )
    logging.info(
        f"User {c.from_user.id} created new bill {pay_id} label {pay_res[0]} kind ls{quant}"
    )

    txt = "Ваш заказ сформирован\nОплатите его по кнопке ниже"
    await c.message.edit_text(
        txt, reply_markup=pay_kb(pay_id, pay_res[1], f"dts{quant}")
    )


@router.callback_query(
    PayCB.filter((F.act == "paid") & (F.kind.startswith("dts"))), flags=flags
)
async def paid_darts_cmd(c: CQ, callback_data: PayCB, ssn, yoo_token):
    pay_id = int(callback_data.pay_id)
    kind = callback_data.kind
    quant = int(kind[-1])

    pay: PayItem = await get_payment_info(ssn, pay_id)
    result = await check_bill_for_pay(pay.label, yoo_token)
    # result = "found"
    if result == "found":
        await add_darts_after_pay(ssn, c.from_user.id, pay_id, quant)
        logging.info(
            f"User {c.from_user.id} payd bill {pay_id} label {pay.label} kind {pay.kind}"
        )
        txt = "Успешно ✅!\nБроски дротика уже начисленны вам, время проверить удачу!"
        await c.message.edit_text(txt, reply_markup=darts_kb)
    else:
        await c.answer("⚠️ Счет не оплачен", show_alert=True)
