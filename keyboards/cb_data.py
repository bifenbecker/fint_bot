from aiogram.filters.callback_data import CallbackData


class PageCB(CallbackData, prefix="page"):
    num: int
    last: int


class PayCB(CallbackData, prefix="pay"):
    pay_id: int
    act: str
    kind: str
