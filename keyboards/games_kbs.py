from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.cb_data import PageCB

games_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⚽ Пенальти", callback_data="penalty"),
        ],
        [
            InlineKeyboardButton(text="☘️ Удачный удар", callback_data="luckystrike"),
        ],
        [
            InlineKeyboardButton(text="⚖️ Битва паков", callback_data="packbattle"),
        ],
        [
            InlineKeyboardButton(text="🎯 Дартс", callback_data="darts"),
        ],
        [
            InlineKeyboardButton(text="🎰 Казино", callback_data="casino"),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")],
    ]
)

to_games_btn = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="⏪ Назад", callback_data="games")]]
)

cancel_penalty_queue_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⏪ Назад", callback_data="penqueuecancel")]
    ]
)


lucky_shot_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⚽ Сделать удар", callback_data="hitls"),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)

no_free_ls_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💵 Купить 3 удара", callback_data="buyls3"),
        ],
        [
            InlineKeyboardButton(text="💵 Купить 6 ударов", callback_data="buyls6"),
        ],
        [
            InlineKeyboardButton(text="💵 Купить 9 ударов", callback_data="buyls9"),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)

penalty_kind_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🃏 Игра на карту", callback_data="pengame_card"),
        ],
        [
            InlineKeyboardButton(
                text="🏆 Игра на рейтинг", callback_data="pengame_rating"
            ),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)

penalty_opp_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎲 Случайный соперник", callback_data="penopp_random"
            ),
        ],
        [
            InlineKeyboardButton(
                text="✉️ Определенный соперник", callback_data="penopp_target"
            ),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)


def penalty_offer_kb(pen_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Начать игру", callback_data=f"penstart_{pen_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"pencancel_{pen_id}"
                )
            ],
        ]
    )
    return keyboard


def card_penalty_offer_kb(pen_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🃏 Выбрать карту для пенальти",
                    callback_data=f"penawscard_{pen_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"pencancel_{pen_id}"
                )
            ],
        ]
    )
    return keyboard


def card_penalty_answer_kb(pen_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Начать игру", callback_data=f"pencardstart_{pen_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"pencancel_{pen_id}"
                )
            ],
        ]
    )
    return keyboard


after_penalty_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚽ Рейтинг игроков в Пенальти", callback_data="top_penalty"
            ),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)


draw_penalty_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⚽ Переигровка", callback_data="penalty"),
        ],
        [InlineKeyboardButton(text="🏳 Ничья", callback_data="games")],
    ]
)


def penalty_action_kb(pen_id, kind):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↖️", callback_data=f"pnactn_{kind}_{pen_id}_1"
                ),
                InlineKeyboardButton(
                    text="⬆️", callback_data=f"pnactn_{kind}_{pen_id}_2"
                ),
                InlineKeyboardButton(
                    text="↗️", callback_data=f"pnactn_{kind}_{pen_id}_3"
                ),
            ]
        ]
    )
    return keyboard


card_pen_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🃏 Все карты", callback_data="penrar_all")],
        [InlineKeyboardButton(text="🀄 По редкости", callback_data="penrarities")],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)


def card_penalty_kb(page, last, sorting, card_id):
    btns = []

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    btns.append([InlineKeyboardButton(text=txt, callback_data=f"srtpen_{sorting}")])
    btns.append(
        [
            InlineKeyboardButton(
                text="Выбрать для пенальти", callback_data=f"chspencard_{card_id}"
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

    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_games")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


def pen_rarities_kb(rarities):
    btns = []
    for rarity in rarities:
        btns.append(
            [InlineKeyboardButton(text=rarity, callback_data=f"penrar_{rarity}")]
        )

    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")])
    return InlineKeyboardMarkup(inline_keyboard=btns)


def answ_card_pen_kb(pen_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🃏 Все карты", callback_data=f"answpenrar_all_{pen_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🀄 По редкости", callback_data=f"answpenrarities_{pen_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"pencancel_{pen_id}"
                )
            ],
        ]
    )
    return keyboard


def answ_pen_rarity_cards_kb(rarities, pen_id):
    btns = []
    for rarity in rarities:
        btns.append(
            [
                InlineKeyboardButton(
                    text=rarity, callback_data=f"answpenrar_{rarity}_{pen_id}"
                )
            ]
        )

    btns.append(
        [InlineKeyboardButton(text="⏪ Назад", callback_data=f"penawscard_{pen_id}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=btns)


def answ_card_penalty_kb(page, last, sorting, card_id, pen_id):
    btns = []

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    btns.append([InlineKeyboardButton(text=txt, callback_data=f"answsrtpen_{sorting}")])
    btns.append(
        [
            InlineKeyboardButton(
                text="Выбрать для пенальти", callback_data=f"answpencard_{card_id}"
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
        [InlineKeyboardButton(text="⏪ Назад", callback_data=f"penawscard_{pen_id}")]
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


dice_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🎲 Удачный бросок", callback_data="dice"),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)

darts_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Бросить дротик", callback_data="hitdarts"),
        ],
        [
            InlineKeyboardButton(text="💰 Купить броски", callback_data="buydarts"),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)

no_free_darts_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 3 броска - 150 руб", callback_data="buydts3"),
        ],
        [
            InlineKeyboardButton(
                text="💰 6 бросков - 300 руб", callback_data="buydts6"
            ),
        ],
        [
            InlineKeyboardButton(
                text="💰 9 бросков - 400 руб", callback_data="buydts9"
            ),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)

casino_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 Крутить казино", callback_data="hitcasino"),
        ],
        [
            InlineKeyboardButton(text="💰 Купить попытки", callback_data="buycasino"),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)

no_casino_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💰 3 попытки - 150 руб", callback_data="buycsn1"
            ),
        ],
        [
            InlineKeyboardButton(
                text="💰 6 попыток - 300 руб", callback_data="buycsn2"
            ),
        ],
        [
            InlineKeyboardButton(
                text="💰 9 попыток - 400 руб", callback_data="buycsn3"
            ),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)

buy_casino_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Купить попытки", callback_data="buycasino"),
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="games")],
    ]
)
