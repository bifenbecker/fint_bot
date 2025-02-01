from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import PackBattle, UserPacks

pack_battle_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎪 Создать своё лобби", callback_data="packbattlecreate"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏹 Войти в лобби", callback_data="packbattlelobbies"
            )
        ],
        [InlineKeyboardButton(text="🧑💻 В личный кабинет", callback_data="startplay")],
    ]
)


def pack_battle_lobbies_kb(battles):
    btns = []
    battle: PackBattle
    for battle in battles:
        name = f"🟣 {battle.owner_username} - {battle.quant} карт"
        btns.append(
            [InlineKeyboardButton(text=name, callback_data=f"joinpbttl_{battle.id}")]
        )

    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="packbattle")])

    return InlineKeyboardMarkup(inline_keyboard=btns)


def create_pack_battle_kb(upacks: UserPacks):
    btns = []
    if upacks.five_pack > 0:
        btns.append(
            [
                InlineKeyboardButton(
                    text="🃏 Сыграть на пак на 5 карт", callback_data="crtpbttl_5"
                )
            ]
        )
    if upacks.ten_pack > 0:
        btns.append(
            [
                InlineKeyboardButton(
                    text="🃏 Сыграть на пак на 10 карт", callback_data="crtpbttl_10"
                )
            ]
        )
    if upacks.twenty_pack > 0:
        btns.append(
            [
                InlineKeyboardButton(
                    text="🃏 Сыграть на пак на 20 карт", callback_data="crtpbttl_20"
                )
            ]
        )
    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="packbattle")])

    return InlineKeyboardMarkup(inline_keyboard=btns)


def no_opp_battle_kb(duel_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧑‍💻 В личный кабинет",
                    callback_data=f"ownrcancelpbttl_{duel_id}",
                )
            ],
        ]
    )
    return keyboard


def opp_battle_kb(duel_id, kind, ready):
    if kind == "owner":
        cb = f"ownrcancelpbttl_{duel_id}"
    else:
        cb = f"targetcancelpbttl_{duel_id}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⚔️ Начать битву ({ready}/2)",
                    callback_data=f"rdypbttl_{duel_id}",
                )
            ],
            [InlineKeyboardButton(text="🧑‍💻 В личный кабинет", callback_data=cb)],
        ]
    )
    return keyboard
