from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.cb_data import PageCB


class SelectCardOnPageCB(PageCB, prefix="select_card_on_page"):
    card_id: int


def select_cards_for_cards_battle_kb(page, last, sorting, card_id: int):
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
                text="Выбрать",
                callback_data=SelectCardOnPageCB(
                    card_id=card_id, num=page, last=last
                ).pack(),
            )
        ]
    )

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
                text=">",
                callback_data=PageCB(num=page + 1, last=last).pack(),
            )
        )
        page_btns.append(
            InlineKeyboardButton(
                text=">>", callback_data=PageCB(num=last, last=last).pack()
            )
        )

    btns.append(page_btns)

    btns.append(
        [InlineKeyboardButton(text="🧑💻 В личный кабинет", callback_data="startplay")]
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


search_cards_battle_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Искать игру", callback_data="searchcardsbattle"),
        ],
        [InlineKeyboardButton(text="🧑💻 В личный кабинет", callback_data="startplay")],
    ]
)
