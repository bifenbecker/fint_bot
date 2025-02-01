from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.cb_data import PageCB

trade_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 1 на 1 карту", callback_data="trdqnt_1")],
        # [
        #     InlineKeyboardButton(
        #         text="🔄 3 на 3 карты", callback_data=f"trdqnt_3")
        # ],
        # [
        #     InlineKeyboardButton(
        #         text="🔄 5 на 5 карт", callback_data=f"trdqnt_5")
        # ],
        [
            InlineKeyboardButton(
                text="❌ Отменить активные обмены", callback_data="cancel_all_trades"
            )
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")],
    ]
)


trade_one_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🃏 Все карты", callback_data="trdrar_all")],
        [InlineKeyboardButton(text="🀄 По редкости", callback_data="traderarities")],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")],
    ]
)


def card_trade_kb(page, last, sorting, card_id):
    btns = []

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    btns.append([InlineKeyboardButton(text=txt, callback_data=f"sorttrd_{sorting}")])
    btns.append(
        [
            InlineKeyboardButton(
                text="Выбрать для обмена", callback_data=f"chstrdcard_{card_id}"
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
        [InlineKeyboardButton(text="❌Отклонить обмен", callback_data="cancel_trade")]
    )
    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="trade")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


def offer_to_owner_kb(trade_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять", callback_data=f"accepttrade_{trade_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить обмен",
                    callback_data=f"ownerdeclinetrade_{trade_id}",
                )
            ],
        ]
    )
    return keyboard


def offer_to_target_kb(trade_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🃏 Выбрать карту для обмена",
                    callback_data=f"answertrade_{trade_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить обмен",
                    callback_data=f"targetdeclinetrade_{trade_id}",
                )
            ],
        ]
    )
    return keyboard


def target_cards_kb(trade_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🃏 Все карты", callback_data=f"answtrdrar_all_{trade_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🀄 По редкости", callback_data=f"answtraderarities_{trade_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить активные обмены",
                    callback_data="cancel_all_trades",
                )
            ],
            [InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")],
        ]
    )
    return keyboard


def target_card_trade_kb(page, last, sorting, card_id, trade_id):
    btns = []

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    btns.append(
        [InlineKeyboardButton(text=txt, callback_data=f"answsorttrd_{sorting}")]
    )
    btns.append(
        [
            InlineKeyboardButton(
                text="Выбрать для обмена", callback_data=f"answtrdcard_{card_id}"
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
        [
            InlineKeyboardButton(
                text="❌Отклонить обмен", callback_data=f"targetdeclinetrade_{trade_id}"
            )
        ]
    )
    btns.append(
        [InlineKeyboardButton(text="⏪ Назад", callback_data=f"answertrade_{trade_id}")]
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


after_trade_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🎭 Обмен картами", callback_data="trade")],
        [InlineKeyboardButton(text="🧑💻 В личный кабинет", callback_data="startplay")],
    ]
)


def trade_rarities_kb(rarities):
    btns = []
    for rarity in rarities:
        btns.append(
            [InlineKeyboardButton(text=rarity, callback_data=f"trdrar_{rarity}")]
        )

    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")])
    return InlineKeyboardMarkup(inline_keyboard=btns)


def target_rarity_cards_kb(rarities, trade_id):
    btns = []
    for rarity in rarities:
        btns.append(
            [
                InlineKeyboardButton(
                    text=rarity, callback_data=f"answtrdrar_{rarity}_{trade_id}"
                )
            ]
        )

    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")])
    return InlineKeyboardMarkup(inline_keyboard=btns)


def trade_multi_kb(quant):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🃏 Все карты", callback_data=f"mtrdrarall_{quant}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🀄 По редкости", callback_data=f"mtraderarities_{quant}"
                )
            ],
            [InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")],
        ]
    )
    return keyboard


def card_mtrade_kb(page, last, sorting, status, rarity):
    btns = []

    if status == "in":
        btns.append(
            [InlineKeyboardButton(text="➖", callback_data=f"trdunselecexcard_{page}")]
        )
    else:
        btns.append(
            [InlineKeyboardButton(text="➕", callback_data=f"trdselecexcard_{page}")]
        )

    btns.append(
        [
            InlineKeyboardButton(
                text="Отправить предложение обмена", callback_data="sendmtradeoffer"
            )
        ]
    )

    if rarity == "all":
        if sorting == "up":
            txt = "Рейтинг⬆️"
        elif sorting == "down":
            txt = "Рейтинг⬇️"
        else:
            txt = "Рейтинг❌"

        btns.append(
            [InlineKeyboardButton(text=txt, callback_data=f"sortmtrd_{sorting}")]
        )

    btns.append(
        [InlineKeyboardButton(text="🃏 Выбор редкости", callback_data="mtrdrarities")]
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
        [InlineKeyboardButton(text="❌Отклонить обмен", callback_data="cancel_trade")]
    )
    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="trade")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


def m_offer_to_target_kb(trade_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🃏 Выбрать карты для обмена",
                    callback_data=f"answermtrade_{trade_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить обмен",
                    callback_data=f"targetdeclinetrade_{trade_id}",
                )
            ],
        ]
    )
    return keyboard


def m_trade_rarities_kb(rarities):
    btns = [[InlineKeyboardButton(text="🃏 Все карты", callback_data="mtrdrar_all")]]
    for rarity in rarities:
        btns.append(
            [InlineKeyboardButton(text=rarity, callback_data=f"mtrdrar_{rarity}")]
        )

    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")])
    return InlineKeyboardMarkup(inline_keyboard=btns)


def target_card_mtrade_kb(page, last, sorting, status, rarity):
    btns = []

    if status == "in":
        btns.append(
            [
                InlineKeyboardButton(
                    text="➖", callback_data=f"anstrdunselecexcard_{page}"
                )
            ]
        )
    else:
        btns.append(
            [InlineKeyboardButton(text="➕", callback_data=f"anstrdselecexcard_{page}")]
        )

    btns.append(
        [
            InlineKeyboardButton(
                text="Отправить предложение обмена", callback_data="sendansmtradeoffer"
            )
        ]
    )

    if rarity == "all":
        if sorting == "up":
            txt = "Рейтинг⬆️"
        elif sorting == "down":
            txt = "Рейтинг⬇️"
        else:
            txt = "Рейтинг❌"

        btns.append(
            [InlineKeyboardButton(text=txt, callback_data=f"anssortmtrd_{sorting}")]
        )

    btns.append(
        [
            InlineKeyboardButton(
                text="🃏 Выбор редкости", callback_data="ansmtrdrarities"
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
        [InlineKeyboardButton(text="❌Отклонить обмен", callback_data="cancel_trade")]
    )
    btns.append([InlineKeyboardButton(text="⏪ Назад", callback_data="trade")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


def m_target_trade_rarities_kb(rarities):
    btns = [
        [InlineKeyboardButton(text="🃏 Все карты", callback_data="trgtmtrdrar_all")]
    ]
    for rarity in rarities:
        btns.append(
            [InlineKeyboardButton(text=rarity, callback_data=f"trgtmtrdrar_{rarity}")]
        )
    btns.append(
        [InlineKeyboardButton(text="❌Отклонить обмен", callback_data="cancel_trade")]
    )
    return InlineKeyboardMarkup(inline_keyboard=btns)


send_mtrade_answer_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Отправить предложение обмена",
                callback_data="confsendansmtradeoffer",
            )
        ],
        [InlineKeyboardButton(text="❌Отклонить обмен", callback_data="cancel_trade")],
    ]
)


def accept_m_trade_kb(trade_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить обмен", callback_data=f"confmtrade_{trade_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить обмен",
                    callback_data=f"ownerdeclinetrade_{trade_id}",
                )
            ],
        ]
    )
    return keyboard
