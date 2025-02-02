from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.cb_data import PageCB

card_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎁 Получить бесплатную карточку", callback_data="getfreecard"
            ),
        ],
        [
            InlineKeyboardButton(text="🛍 Магазин карточек", callback_data="cardsstore"),
        ],
        [
            InlineKeyboardButton(text="🎟 FINT Pass", callback_data="fintpass"),
        ],
        [
            InlineKeyboardButton(text="🧑‍💻 Ввести промокод", callback_data="promo"),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")],
    ]
)

no_free_card_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🛍 Магазин карточек", callback_data="cardsstore"),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")],
    ]
)

accept_new_card_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data="startplay")]
    ]
)

buy_cards_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💵 Купить 5 рандомных карточки", callback_data="cardbuy_5"
            ),
        ],
        [
            InlineKeyboardButton(
                text="💵 Купить 10 рандомных карточки", callback_data="cardbuy_10"
            ),
        ],
        [
            InlineKeyboardButton(
                text="💵 Купить 20 рандомных карточки", callback_data="cardbuy_20"
            ),
        ],
        [
            InlineKeyboardButton(
                text="💵 Купить 30 рандомных карточки", callback_data="cardbuy_30"
            ),
        ],
        [
            InlineKeyboardButton(
                text="💵 Купить выбор игрока", callback_data="cardbuy_pick"
            ),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")],
    ]
)

my_collection_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🃏 Просмотр карт", callback_data="mycards"),
        ],
        [
            InlineKeyboardButton(text="🗃 Просмотр паков", callback_data="mypacks"),
        ],
        [
            InlineKeyboardButton(
                text="🔄 Отсортировать дубликаты карт ",
                callback_data="recountduplicates",
            ),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")],
    ]
)

filter_my_cards_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🃏 Все карты", callback_data="rarity_all"),
        ],
        [
            InlineKeyboardButton(
                text="🀄 По редкости", callback_data="mycardsrarities"
            ),
        ],
        [
            InlineKeyboardButton(text="🎴 По команде", callback_data="mycardsteams"),
        ],
        [
            InlineKeyboardButton(text="📋 Список карт", callback_data="list_my_cards"),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")],
    ]
)


def my_cards_kb(page, last, sorting):
    btns = []

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    btns.append(
        [InlineKeyboardButton(text=txt, callback_data=f"sortmycards_{sorting}")]
    )

    btns.append(
        [InlineKeyboardButton(text=f"({page}/{last})", callback_data="useless")]
    )

    page_btns = []
    if page > 1:
        page_btns.append(
            InlineKeyboardButton(
                text="<<", callback_data=PageCB(num=1, last=last).pack()
            )
        )
        page_btns.append(
            InlineKeyboardButton(
                text="<", callback_data=PageCB(num=page - 1, last=last).pack()
            )
        )

    if page < last:
        page_btns.append(
            InlineKeyboardButton(
                text=">", callback_data=PageCB(num=page + 1, last=last).pack()
            )
        )
        page_btns.append(
            InlineKeyboardButton(
                text=">>", callback_data=PageCB(num=last, last=last).pack()
            )
        )

    btns.append(page_btns)
    btns.append(
        [InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_mycards")]
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


def my_card_rarities_kb(rarities):
    btns = []
    for rarity in rarities:
        btns.append(
            [InlineKeyboardButton(text=rarity, callback_data=f"rarity_{rarity}")]
        )

    btns.append(
        [InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_mycards")]
    )
    return InlineKeyboardMarkup(inline_keyboard=btns)


my_card_list_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🃏 Получить карту", callback_data="getcard"),
        ],
        [
            InlineKeyboardButton(
                text="📲 Начать просмотр по карточкам", callback_data="rarity_all"
            ),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_mycards")],
    ]
)


def pack_cards_kb(page, last):
    btns = []

    page_btns = []
    if page > 1:
        page_btns.append(
            InlineKeyboardButton(
                text="<<", callback_data=PageCB(num=1, last=last).pack()
            )
        )
        page_btns.append(
            InlineKeyboardButton(
                text="<", callback_data=PageCB(num=page - 1, last=last).pack()
            )
        )

    page_btns.append(
        InlineKeyboardButton(text=f"({page}/{last})", callback_data="useless")
    )

    if page < last:
        page_btns.append(
            InlineKeyboardButton(
                text=">", callback_data=PageCB(num=page + 1, last=last).pack()
            )
        )
        page_btns.append(
            InlineKeyboardButton(
                text=">>", callback_data=PageCB(num=last, last=last).pack()
            )
        )

    btns.append(page_btns)

    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


back_to_cards_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🧑💻 В личный кабинет", callback_data="startplay")],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="getcard")],
    ]
)


def my_card_teams_kb(teams):
    btns = []
    for item in teams:
        btns.append([InlineKeyboardButton(text=item, callback_data=f"cteam_{item}")])

    btns.append(
        [InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_mycards")]
    )
    return InlineKeyboardMarkup(inline_keyboard=btns)


def my_team_cards_kb(page, last, sorting, team):
    btns = []

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    btns.append(
        [
            InlineKeyboardButton(
                text=txt, callback_data=f"sortmyteamcards_{sorting}_{team}"
            )
        ]
    )

    btns.append(
        [InlineKeyboardButton(text=f"({page}/{last})", callback_data="useless")]
    )

    page_btns = []
    if page > 1:
        page_btns.append(
            InlineKeyboardButton(
                text="<<", callback_data=PageCB(num=1, last=last).pack()
            )
        )
        page_btns.append(
            InlineKeyboardButton(
                text="<", callback_data=PageCB(num=page - 1, last=last).pack()
            )
        )

    if page < last:
        page_btns.append(
            InlineKeyboardButton(
                text=">", callback_data=PageCB(num=page + 1, last=last).pack()
            )
        )
        page_btns.append(
            InlineKeyboardButton(
                text=">>", callback_data=PageCB(num=last, last=last).pack()
            )
        )

    btns.append(page_btns)

    btns.append(
        [InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_mycards")]
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


fintpass_back_kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")]]
)
