import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery as CQ

from db.queries.multi_trade_qs import close_multi_trade
from db.queries.trade_queries import close_trade
from keyboards.main_kbs import to_main_btn
from keyboards.trade_kbs import after_trade_kb
from middlewares.actions import ActionMiddleware

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data.startswith("accepttrade_"), flags=flags)
async def accept_trade_cmd(c: CQ, ssn, bot: Bot, action_queue):
    trade_id = int(c.data.split("_")[-1])

    res = await close_trade(ssn, trade_id)

    await c.message.delete()
    if res in ("already_closed", "error"):
        txt = "Это предложение обмена больше недоступно"
        await c.message.answer(txt, reply_markup=to_main_btn)
    else:
        txt = "✅ Cделка прошла успешно!\nВремя проверить коллекцию"
        await c.message.answer(txt, reply_markup=after_trade_kb)

        await bot.send_message(res[0].target, txt, reply_markup=after_trade_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data.startswith("confmtrade_"), flags=flags)
async def accept_m_trade_cmd(c: CQ, ssn, bot: Bot, action_queue):
    trade_id = int(c.data.split("_")[-1])

    trade = await close_multi_trade(ssn, trade_id)

    await c.message.delete_reply_markup()
    if trade in ("already_closed", "error"):
        txt = "Это предложение обмена больше недоступно"
        await c.message.answer(txt, reply_markup=to_main_btn)
    else:
        txt = "✅ Cделка прошла успешно!\nВремя проверить коллекцию"
        await c.message.answer(txt, reply_markup=after_trade_kb)

        await bot.send_message(trade.target, txt, reply_markup=after_trade_kb)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")
