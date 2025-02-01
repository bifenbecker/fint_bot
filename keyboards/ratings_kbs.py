from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

ratings_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🃏 Рейтинг коллекционеров карточек",
                callback_data="alltimetop_rating",
            )
        ],
        [
            InlineKeyboardButton(
                text="🃏 Сезонный рейтинг коллекционеров карточек",
                callback_data="top_rating",
            )
        ],
        [
            InlineKeyboardButton(
                text="⚽ Сезонный рейтинг игроков в Пенальти",
                callback_data="top_penalty",
            )
        ],
        [InlineKeyboardButton(text="⏪ Назад", callback_data="backtostart")],
    ]
)

back_to_ratings_btn = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="⏪ Назад", callback_data="rating")]]
)
