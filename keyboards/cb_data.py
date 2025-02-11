from aiogram.filters.callback_data import CallbackData


class PageCB(CallbackData, prefix="page"):
    num: int
    last: int


class PayCB(CallbackData, prefix="pay"):
    pay_id: int
    act: str
    kind: str


class TurnTypeCB(CallbackData, prefix="turn"):
    type: str
    battle_id: int
    red_player_id: int
    blue_player_id: int


class CardsBattleCancelCB(CallbackData, prefix="cancel_cards_battle"):
    battle_id: int
    red_player_id: int
    blue_player_id: int
