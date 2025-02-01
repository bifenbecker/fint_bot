from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

scheduled_ls_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚽ Сделать удар", callback_data="hitls"),
        ]
    ]
)

scheduled_freecard_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 Получить карту", callback_data="getfreecard"),
        ]
    ]
)

scheduled_darts_btn = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎯 Бросить дротик", callback_data="hitdarts"),
        ]
    ]
)
