import json
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message


class OnlineMessageMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ):
        if event.from_user.id in data["banned"]:
            return

        data["online"][str(event.from_user.id)] = 1
        return await handler(event, data)


class OnlineCallbackQueryMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any],
    ):
        if event.from_user.id in data["banned"]:
            return

        data["online"][str(event.from_user.id)] = 1
        return await handler(event, data)
