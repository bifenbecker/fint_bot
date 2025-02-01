from textwrap import dedent

from aiogram import F, Router
from aiogram.types import CallbackQuery as CQ

from keyboards.cards_kbs import buy_cards_kb

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "cardsstore", flags=flags)
async def buy_cards_cmd(c: CQ):
    txt = """
    🛍 Ты находишься в магазине карт, у нас есть интересное предложение специально для тебя:

    💰5 рандомных карточек - 220 руб
    💰10 рандомных карточек - 400 руб 
    💰20 рандомных карточек - 700 руб 
    💰30 рандомных карточек - 990 руб 
    💰 Выбор игрока 1 из 3 - 100 руб

    Если у вас не получается оплатить, то оплату можно провести через нашего администратора - @fintsupport
    """
    await c.message.edit_text(dedent(txt), reply_markup=buy_cards_kb)
