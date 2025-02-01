import logging
from textwrap import dedent

from aiogram import F, Router
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ

from db.models import CardItem, PayItem, Player
from db.queries.global_queries import get_user_info
from db.queries.payment_queries import (
    add_new_payment,
    get_payment_info,
    update_fint_pass,
)
from keyboards.cb_data import PayCB
from keyboards.main_kbs import to_main_btn
from keyboards.pay_kbs import buy_pass_kb, pay_kb, player_pick_kb
from utils.const import FINT_PASS_COST
from utils.format_texts import format_new_free_card_text, format_view_my_cards_text
from utils.pay_actions import check_bill_for_pay, create_new_bill
from utils.states import UserStates

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "fintpass", flags=flags)
async def fint_pass_cmd(c: CQ, ssn):
    user: Player = await get_user_info(ssn, c.from_user.id)

    txt = """
    🀄️Выдача одной лимитированной карты, недоступной в основной игре (Limited: 5000) 
    🎯 Дартс  - 1 раз в 2 дня бесплатно 3 попытки
    🔓 Закрытый розыгрыш 
    🛍  Скидка 10% на покупку (Обращаться к администрации)
    ⏳ Сокращение новой попытки удачного Удара до 4 часов
    🕕 Бесплатная карта раз в 12 часов, вместо 24
    🔮 Разовая попытка выбора игрока при оплате FINT PASS

    Если у вас не получается оплатить, то оплату можно провести через нашего администратора - @fintsupport

    💰 Стоимость FINT Pass - 599 Рублей
    Дата окончания текущего FINT Pass 19.10.2024 18:20
    """
    if user.pass_until == "nopass":
        footer_txt = "<i>FINT Pass не активирован</i>"
        keyboard = buy_pass_kb
    else:
        footer_txt = f"<i>Дата окончания текущего FINT Pass {user.pass_until}</i>"
        keyboard = to_main_btn

    await c.message.edit_text(dedent(txt) + footer_txt, reply_markup=keyboard)


@router.callback_query(F.data == "buyfintpass", flags=flags)
async def buy_fint_pass(c: CQ, ssn, wallet):
    user: Player = await get_user_info(ssn, c.from_user.id)
    if user.game_pass == "yes":
        await c.answer("У вас уже есть активированный FINT PASS")
    else:
        # price = 9
        pay_res = await create_new_bill(
            FINT_PASS_COST, c.from_user.id, "FINT PASS", wallet
        )
        pay_id = await add_new_payment(
            ssn, c.from_user.id, pay_res[0], pay_res[1], "FINT PASS", FINT_PASS_COST
        )
        logging.info(
            f"User {c.from_user.id} created new bill {pay_id} label {pay_res[0]} kind fint pass"
        )

        txt = "Ваш заказ сформирован\nОплатите его по кнопке ниже"
        await c.message.edit_text(txt, reply_markup=pay_kb(pay_id, pay_res[1], "pass"))


@router.callback_query(
    PayCB.filter((F.act == "paid") & (F.kind == "pass")), flags=flags
)
async def paid_fint_pass_cmd(c: CQ, callback_data: PayCB, ssn, yoo_token, state: FSM):
    pay_id = int(callback_data.pay_id)

    pay: PayItem = await get_payment_info(ssn, pay_id)
    result = await check_bill_for_pay(pay.label, yoo_token)
    # result = "found"
    if result == "found":
        res = await update_fint_pass(ssn, c.from_user.id, pay_id)
        logging.info(
            f"User {c.from_user.id} payd bill {pay_id} label {pay.label} kind {pay.kind}"
        )
        txt = "Успешно ✅!\nКупленные удары уже начисленны вам, время проверить удачу!"
        await c.message.edit_text(txt)

        card: CardItem = res[0]
        txt = await format_new_free_card_text(card)
        await c.message.answer_photo(card.image, txt)

        page = 1
        last = 3

        try:
            await c.message.delete()
        except:
            pass
        pick_card: CardItem = res[2][0]
        txt = await format_view_my_cards_text(pick_card)

        await c.message.answer_photo(
            pick_card.image,
            txt,
            reply_markup=player_pick_kb(page, last, res[1], pick_card.id),
        )
        await state.set_state(UserStates.player_pick)
        await state.update_data(pick_id=res[1], cards=res[2])

    else:
        await c.answer("⚠️ Счет не оплачен", show_alert=True)
