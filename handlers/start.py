import datetime
from textwrap import dedent

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.queries.cards_battle_queries import cancel_card_battle_game
from db.queries.global_queries import check_and_add_user, update_user_info
from keyboards.main_kbs import main_kb, start_kb, sub_kb
from utils.const import channel_trade_info, channel_username

flags = {"throttling_key": "default"}
router = Router()


@router.message(Command("start"), flags=flags)
async def start_cmd(m: Mes, state: FSM, ssn, bot: Bot):
    winner_id = await cancel_card_battle_game(ssn, m.from_user.id)
    if winner_id:
        await bot.send_message(
            text="Ваш соперник покинул игру, Вы победили!", chat_id=winner_id
        )
        await m.answer("Вы покинули игру! Вы проиграли!")
    await state.clear()

    if m.from_user.username:
        username = f"@{m.from_user.username}"
    else:
        username = f"user{m.from_user.id}"

    await check_and_add_user(ssn, m.from_user.id, username)
    txt = """
    👋 <b>Добро пожаловать в мир FINT CARDS</b>

    ⚽️ Здесь ты сможешь собрать свою собственную команду любимых футболистов - от легенд прошлого до восходящих звезд современности. Коллекционируй, сражайся, побеждай и покоряй футбольный олимп вместе с нами.

    💭 <i>Ознакомься с гайдом (https://telegra.ph/Gajd-po-igre-Fint-Cards-09-07)</i> по нашей игре, который поможет тебе освоиться в нашей увлекательной игре.
    """

    await m.answer(dedent(txt), reply_markup=start_kb, disable_web_page_preview=True)


@router.callback_query(F.data == "backtostart", flags=flags)
async def back_to_start_cmd(c: CQ):
    txt = """
    👋 <b>Добро пожаловать в мир FINT CARDS</b>

    ⚽️ Здесь ты сможешь собрать свою собственную команду любимых футболистов - от легенд прошлого до восходящих звезд современности. Коллекционируй, сражайся, побеждай и покоряй футбольный олимп вместе с нами.

    💭 <i>Ознакомься с гайдом (https://telegra.ph/Gajd-po-igre-Fint-Cards-09-07)</i> по нашей игре, который поможет тебе освоиться в нашей увлекательной игре.
    """
    await c.message.edit_text(
        dedent(txt), reply_markup=start_kb, disable_web_page_preview=True
    )


@router.callback_query(F.data == "startplay", flags=flags)
async def start_play_cmd(c: CQ, ssn, bot: Bot):
    sub = await bot.get_chat_member(channel_trade_info, c.from_user.id)
    await c.message.delete()

    if sub.status == "left":
        txt = (
            f"Чтобы начать играть, необходимо 1️⃣ Подписаться на канал {channel_username}"
        )
        await c.message.answer(txt, reply_markup=sub_kb)

    else:
        res = await update_user_info(ssn, c.from_user.id)
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
        🎮 Рейтинг «Битвы составов»: {user.card_battle_rating} ({user.division} дивизион)
        """
        await c.message.answer(dedent(txt), reply_markup=main_kb)


@router.callback_query(F.data == "cancel_cb")
async def cancel_cb_cmd(c: CQ, state: FSM):
    await state.clear()
    await c.answer("✅ Действие отменено")
    await c.message.delete()


@router.callback_query(F.data == "closewindow")
async def close_window_cmd(c: CQ):
    await c.message.delete()
