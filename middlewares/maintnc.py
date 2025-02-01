from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

ids = [
    746461090,
    340945828,
    604330006,
    904403939,
    159701726,
    1457788934,
    937966659,
    5131674802,
]


class MntcMessageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ):
        if event.from_user.id in ids:
            return await handler(event, data)
        # else:
        #     await event.answer("⚽ В данный момент проводятся технические работы!")


class MntcCallbackQueryMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ):
        if event.from_user.id in ids:
            return await handler(event, data)
        # else:
        #     await event.answer("⚽ В данный момент проводятся технические работы!")
