import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery as CQ

from db.models import PayItem
from db.queries.payment_queries import (add_cards_pack, add_new_payment,
                                        add_player_pick_pack, get_payment_info)
from keyboards.cb_data import PayCB
from keyboards.pay_kbs import cards_pack_btn, pay_kb, to_packs_kb
from middlewares.actions import ActionMiddleware
from utils.pay_actions import check_bill_for_pay, create_new_bill

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data.startswith("cardbuy_"), flags=flags)
async def buy_ls_cmd(c: CQ, wallet, ssn, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    quant = c.data.split("_")[-1]
    if quant == "10":
        kind = "10 Cards"
        k = "cards10"
        amount = 400
    elif quant == "5":
        kind = "5 Cards"
        k = "cards5"
        amount = 220
    elif quant == "20":
        kind = "20 Cards"
        k = "cards20"
        amount = 700
    elif quant == "30":
        kind = "30 Cards"
        k = "cards30"
        amount = 990
    else:
        kind = "Player Pick"
        k = "pick"
        amount = 100

    pay_res = await create_new_bill(
        amount, c.from_user.id, kind, wallet)
    pay_id = await add_new_payment(
        ssn, c.from_user.id, pay_res[0], pay_res[1], kind, amount)
    logging.info(
        f"User {c.from_user.id} created new bill {pay_id} label {pay_res[0]} kind {k}")

    txt = "Ваш заказ сформирован\nОплатите его по кнопке ниже"
    await c.message.edit_text(txt, reply_markup=pay_kb(pay_id, pay_res[1], k))


@router.callback_query(PayCB.filter((F.act == "paid") & (F.kind == "pick")), flags=flags)
async def paid_pick_cardpack_cmd(c: CQ, callback_data: PayCB, ssn, yoo_token, action_queue, bot: Bot):
    pay_id = int(callback_data.pay_id)
    pay: PayItem = await get_payment_info(ssn, pay_id)
    result = await check_bill_for_pay(pay.label, yoo_token)
    # result = "found"
    if result == "found":
        await bot.send_chat_action(c.from_user.id, "typing")
        await add_player_pick_pack(ssn, c.from_user.id, pay_id)
        logging.info(
            f"User {c.from_user.id} payd bill {pay_id} label {pay.label} kind {pay.kind}")
        txt = "✅ Оплата прошла успешно!!\nПак начислен на твой баланс!"
        await c.message.edit_text(txt, reply_markup=to_packs_kb)
    else:
        await c.answer("⚠️ Счет не оплачен", show_alert=True)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(
    PayCB.filter((F.act == "paid") & (F.kind.in_(
        {"cards5", "cards10", "cards20", "cards30"}))),
    flags=flags
)
async def paid_cardpack_cmd(c: CQ, callback_data: PayCB, ssn, yoo_token, action_queue, bot: Bot):
    pay_id = int(callback_data.pay_id)
    pay: PayItem = await get_payment_info(ssn, pay_id)
    result = await check_bill_for_pay(pay.label, yoo_token)
    # result = "found"
    if result == "found":
        kind = callback_data.kind
        quant = int(kind[5:])
        await bot.send_chat_action(c.from_user.id, "typing")
        # pack_id = await add_cards_pack(ssn, c.from_user.id, quant, pay_id)
        await add_cards_pack(ssn, c.from_user.id, quant, pay_id)

        logging.info(
            f"User {c.from_user.id} payd bill {pay_id} label {pay.label} kind {pay.kind}")
        txt = "✅ Оплата прошла успешно!!\nПак начислен на твой баланс!"
        await c.message.edit_text(txt, reply_markup=to_packs_kb)
    else:
        await c.answer("⚠️ Счет не оплачен", show_alert=True)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
