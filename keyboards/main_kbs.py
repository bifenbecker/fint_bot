from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import UserPacks
from utils.const import channel_link

start_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Начать игру", callback_data="startplay")]
    ]
)

close_window_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✖️ Закрыть окно", callback_data="closewindow")]
    ]
)

info_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🃏 О картах", callback_data="about_cards")],
        [InlineKeyboardButton(text="⚽ О пенальти", callback_data="about_penalty")],
        [
            InlineKeyboardButton(
                text="☘ Об удачном ударе", callback_data="about_luckystrike"
            )
        ],
        [InlineKeyboardButton(text="⚔️ О дуэли карт", callback_data="about_duels")],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="backtostart")],
    ]
)

back_to_info_btn = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="⏪ Назад", callback_data="info")]]
)


main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🃏 Получить карту", callback_data="getcard"),
            InlineKeyboardButton(text="🧳 Моя коллекция", callback_data="mycollection"),
        ],
        [
            InlineKeyboardButton(text="🎭 Обмен картами", callback_data="trade"),
            InlineKeyboardButton(text="🏆 Общий рейтинг", callback_data="rating"),
        ],
        [InlineKeyboardButton(text="🎲 Мини-игры", callback_data="games")],
        [
            InlineKeyboardButton(text="🎟 FINT Pass", callback_data="fintpass"),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="backtostart")],
    ]
)

sub_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Подписаться ✓", url=channel_link)],
        [InlineKeyboardButton(text="🎮 Начать игру", callback_data="startplay")],
    ]
)

to_main_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🧑💻 В личный кабинет", callback_data="startplay")]
    ]
)

back_to_main_btn = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")]]
)


cancel_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Отменить", callback_data="cancel_cb")]
    ]
)


def user_packs_kb(upacks: UserPacks):
    btns = []
    if upacks.five_pack > 0:
        btns.append(
            [
                InlineKeyboardButton(
                    text="🃏 Открыть пак на 5 карт", callback_data="openfivepack"
                )
            ]
        )
    if upacks.ten_pack > 0:
        btns.append(
            [
                InlineKeyboardButton(
                    text="🃏 Открыть пак на 10 карт", callback_data="opentenpack"
                )
            ]
        )
    if upacks.twenty_pack > 0:
        btns.append(
            [
                InlineKeyboardButton(
                    text="🃏 Открыть пак на 20 карт", callback_data="opentwentypack"
                )
            ]
        )
    if upacks.thirty_pack > 0:
        btns.append(
            [
                InlineKeyboardButton(
                    text="🃏 Открыть пак на 30 карт", callback_data="openthirtypack"
                )
            ]
        )
    if upacks.player_pick > 0:
        btns.append(
            [
                InlineKeyboardButton(
                    text="🃏 Открыть Выбор игрока", callback_data="openplayerpick"
                )
            ]
        )
    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")])

    return InlineKeyboardMarkup(inline_keyboard=btns)
