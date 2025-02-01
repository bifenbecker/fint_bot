from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from db.models import PromoCode
from keyboards.cb_data import PageCB

admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Карточки", callback_data="admincards"),
        ],
        [
            InlineKeyboardButton(
                text="Промокоды", callback_data="adminpromos"),
        ],
        [
            InlineKeyboardButton(
                text="Пользователи", callback_data="adminusers")
        ]
    ]
)

back_to_admin_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)

admin_card_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Добавить", callback_data="addcard"),
        ],
        [
            InlineKeyboardButton(
                text="Редактировать", callback_data="editcards"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)

admin_promos_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Добавить", callback_data="addpromo"),
            InlineKeyboardButton(
                text="Удалить", callback_data="delpromos"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)

admin_cards_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 Все карты", callback_data="admrarity_all"),
        ],
        [
            InlineKeyboardButton(
                text="🀄 По редкости", callback_data="admcardsrarities"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)

adm_card_rarities_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Common", callback_data="admrarity_Common"),
        ],
        [
            InlineKeyboardButton(
                text="Uncommon", callback_data="admrarity_Uncommon"),
        ],
        [
            InlineKeyboardButton(
                text="Rare", callback_data="admrarity_Rare"),
        ],
        [
            InlineKeyboardButton(
                text="Very rare", callback_data="admrarity_Very rare"),
        ],
        [
            InlineKeyboardButton(
                text="Coach", callback_data="admrarity_Coach"),
        ],
        [
            InlineKeyboardButton(
                text="Epic", callback_data="admrarity_Epic"),
        ],
        [
            InlineKeyboardButton(
                text="Unique", callback_data="admrarity_Unique"),
        ],
        [
            InlineKeyboardButton(
                text="Flashback", callback_data="admrarity_Flashback"),
        ],
        [
            InlineKeyboardButton(
                text="Legendary", callback_data="admrarity_Legendary"),
        ],
        [
            InlineKeyboardButton(
                text="Moments", callback_data="admrarity_Moments"),
        ],
        [
            InlineKeyboardButton(
                text="Heroes", callback_data="admrarity_Heroes"),
        ],
        [
            InlineKeyboardButton(
                text="Inform", callback_data="admrarity_Inform"),
        ],
        [
            InlineKeyboardButton(
                text="Event", callback_data="admrarity_Event"),
        ],
        [
            InlineKeyboardButton(
                text="Icons", callback_data="admrarity_Icons"),
        ],
        [
            InlineKeyboardButton(
                text="Limited", callback_data="admrarity_Limited"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)


def adm_view_cards_kb(page, last, card_id, kind, status):
    btns = []

    if kind == "edit":
        btns.append([
            InlineKeyboardButton(
                text="Изменить картинку",
                callback_data=f"imgedit_{card_id}")])
        btns.append([
            InlineKeyboardButton(
                text="Изменить характеристики",
                callback_data=f"txtedit_{card_id}")])
        if status == "on":
            btns.append([
                InlineKeyboardButton(
                    text="Убрать из пула",
                    callback_data=f"chngstatus_off_{page}")])
        else:
            btns.append([
                InlineKeyboardButton(
                    text="Добавить в пул",
                    callback_data=f"chngstatus_on_{page}")])
    else:
        btns.append([
            InlineKeyboardButton(text="Выбрать для промокода", callback_data=f"prmcard_{card_id}")])

    btns.append([InlineKeyboardButton(
        text=f"({page}/{last})", callback_data="useless")])

    page_btns = []
    if page > 1:
        page_btns.append(InlineKeyboardButton(
            text="<<", callback_data=PageCB(num=1, last=last).pack()))
        page_btns.append(InlineKeyboardButton(
            text="<", callback_data=PageCB(num=page-1, last=last).pack()))

    if page < last:
        page_btns.append(InlineKeyboardButton(
            text=">", callback_data=PageCB(num=page+1, last=last).pack()))
        page_btns.append(InlineKeyboardButton(
            text=">>", callback_data=PageCB(num=last, last=last).pack()))

    btns.append(page_btns)

    btns.append([
        InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_admin")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


promo_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Выбрать карточку",
                                 callback_data="promorarity_all")
        ],
        [
            InlineKeyboardButton(text="Рандомная карточка",
                                 callback_data="randompromocards")
        ],
        [
            InlineKeyboardButton(text="⏪ Назад",
                                 callback_data="back_to_admin")
        ]
    ]
)


def view_promos_kb(promos):
    btns = []
    promo: PromoCode
    for promo in promos:
        if promo.card_id != 0:
            name = f"Card_ID {promo.card_id}"
        else:
            if promo.kind == "card":
                name = "Random card"
            elif promo.kind == "legpack":
                name = "Legendart pack"
            else:
                quant = promo.kind[4:]
                name = f"{quant} cards pack"
        btns.append(
            [InlineKeyboardButton(
                text=f"{promo.promo} - {name}",
                callback_data=f"delpromo_{promo.id}")]
        )

    btns.append([
        InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_admin")])

    return InlineKeyboardMarkup(inline_keyboard=btns)


def promo_cards_kb(page, last, card_id, sorting, rarity):
    btns = []

    if sorting == "up":
        txt = "Рейтинг⬆️"
    elif sorting == "down":
        txt = "Рейтинг⬇️"
    else:
        txt = "Рейтинг❌"

    if rarity == "all":
        btns.append([
            InlineKeyboardButton(text=txt, callback_data=f"sortprmcards_{sorting}")])
    btns.append([
        InlineKeyboardButton(text="Выбрать для промокода", callback_data=f"prmcard_{card_id}")])

    btns.append([InlineKeyboardButton(
        text=f"({page}/{last})", callback_data="useless")])

    page_btns = []
    if page > 1:
        page_btns.append(InlineKeyboardButton(
            text="<<", callback_data=PageCB(num=1, last=last).pack()))
        page_btns.append(InlineKeyboardButton(
            text="<", callback_data=PageCB(num=page-1, last=last).pack()))

    if page < last:
        page_btns.append(InlineKeyboardButton(
            text=">", callback_data=PageCB(num=page+1, last=last).pack()))
        page_btns.append(InlineKeyboardButton(
            text=">>", callback_data=PageCB(num=last, last=last).pack()))

    btns.append(page_btns)

    btns.append([
        InlineKeyboardButton(text="🀄 По редкости", callback_data="changepromorarity")])
    btns.append([
        InlineKeyboardButton(text="⏪ Назад", callback_data="back_to_admin")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    return keyboard


promo_rarities_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Все редкости", callback_data="promorarity_all"),
        ],
        [
            InlineKeyboardButton(
                text="Common", callback_data="promorarity_Common"),
        ],
        [
            InlineKeyboardButton(
                text="Uncommon", callback_data="promorarity_Uncommon"),
        ],
        [
            InlineKeyboardButton(
                text="Rare", callback_data="promorarity_Rare"),
        ],
        [
            InlineKeyboardButton(
                text="Very rare", callback_data="promorarity_Very rare"),
        ],
        [
            InlineKeyboardButton(
                text="Coach", callback_data="promorarity_Coach"),
        ],
        [
            InlineKeyboardButton(
                text="Epic", callback_data="promorarity_Epic"),
        ],
        [
            InlineKeyboardButton(
                text="Unique", callback_data="promorarity_Unique"),
        ],
        [
            InlineKeyboardButton(
                text="Flashback", callback_data="promorarity_Flashback"),
        ],
        [
            InlineKeyboardButton(
                text="Legendary", callback_data="promorarity_Legendary"),
        ],
        [
            InlineKeyboardButton(
                text="Moments", callback_data="promorarity_Moments"),
        ],
        [
            InlineKeyboardButton(
                text="Heroes", callback_data="promorarity_Heroes"),
        ],
        [
            InlineKeyboardButton(
                text="Inform", callback_data="promorarity_Inform"),
        ],
        [
            InlineKeyboardButton(
                text="Event", callback_data="promorarity_Event"),
        ],
        [
            InlineKeyboardButton(
                text="Icons", callback_data="promorarity_Icons"),
        ],
        [
            InlineKeyboardButton(
                text="Limited", callback_data="promorarity_Limited"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)

promo_kind_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="1 случайная карта", callback_data="prmkind_random_1"),
        ],
        [
            InlineKeyboardButton(
                text="5 случайных карт", callback_data="prmkind_random_5"),
        ],
        [
            InlineKeyboardButton(
                text="10 случайных карт", callback_data="prmkind_random_10"),
        ],
        [
            InlineKeyboardButton(
                text="20 случайных карт", callback_data="prmkind_random_20"),
        ],
        [
            InlineKeyboardButton(
                text="30 случайных карт", callback_data="prmkind_random_30"),
        ],
        [
            InlineKeyboardButton(
                text="Выбор игрока", callback_data="prmkind_pick"),
        ],
        [
            InlineKeyboardButton(
                text="Конкретная карта", callback_data="promorarity_all"),
        ],
        [
            InlineKeyboardButton(
                text="FINT PASS", callback_data="promokind_finpass")
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)

promo_users_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Да", callback_data="prmusers_new"),
            InlineKeyboardButton(
                text="Нет", callback_data="prmusers_all"),
        ],
        [
            InlineKeyboardButton(
                text="⏪ Назад", callback_data="back_to_admin")
        ]
    ]
)
