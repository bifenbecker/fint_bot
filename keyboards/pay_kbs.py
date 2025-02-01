from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.cb_data import PageCB, PayCB


def pay_kb(pay_id, url, kind):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить", url=url)],
            [
                InlineKeyboardButton(
                    text="Проверить оплату",
                    callback_data=PayCB(pay_id=pay_id, act="paid", kind=kind).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏪ Назад",
                    callback_data=PayCB(pay_id=pay_id, act="cncl", kind=kind).pack(),
                )
            ],
        ]
    )
    return keyboard


def cards_pack_btn(pack_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👀 Посмотреть карты", callback_data=f"viewpack_{pack_id}"
                )
            ]
        ]
    )
    return keyboard


def player_pick_kb(page, last, pick_id, card_id):
    btns = [
        [
            InlineKeyboardButton(
                text="Выбрать игрока", callback_data=f"plrpick_{pick_id}_{card_id}"
            )
        ]
    ]

    page_btns = []
    if page > 1:
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

    btns.append(page_btns)
    return InlineKeyboardMarkup(inline_keyboard=btns)


to_packs_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🗃 Просмотр паков", callback_data="mypacks")],
        [InlineKeyboardButton(text="🧑‍💻 В личный кабинет", callback_data="startplay")],
    ]
)

buy_pass_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Купить FINT Pass", callback_data="buyfintpass")],
        [InlineKeyboardButton(text="Активировать промокод", callback_data="promo")],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="startplay")],
    ]
)
