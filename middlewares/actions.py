from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import CallbackQuery, Message
from cachetools import TTLCache


class ActionMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any],
    ):
        if str(event.from_user.id) not in data["action_queue"]:
            data["action_queue"][str(event.from_user.id)] = 1
            return await handler(event, data)
