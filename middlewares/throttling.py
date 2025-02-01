from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import CallbackQuery, Message
from cachetools import TTLCache


class ThrottlingMessageMiddleware(BaseMiddleware):
    caches = {
        "default": TTLCache(maxsize=10_000, ttl=0.25),
        "five": TTLCache(maxsize=10_000, ttl=5),
        "zero": TTLCache(maxsize=10_000, ttl=0),
        "half": TTLCache(maxsize=10_000, ttl=0.5),
        "pages": TTLCache(maxsize=10_000, ttl=0.1)
    }

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ):
        throttling_key = get_flag(data, "throttling_key")
        if throttling_key is not None and throttling_key in self.caches:
            if event.chat.id in self.caches[throttling_key]:
                return
            else:
                self.caches[throttling_key][event.chat.id] = None
        return await handler(event, data)


class ThrottlingCallbackQueryMiddleware(BaseMiddleware):
    caches = {
        "default": TTLCache(maxsize=10_000, ttl=0.25),
        "five": TTLCache(maxsize=10_000, ttl=5),
        "zero": TTLCache(maxsize=10_000, ttl=0),
        "half": TTLCache(maxsize=10_000, ttl=0.5),
        "pages": TTLCache(maxsize=10_000, ttl=0.1)
    }

    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any],
    ):
        throttling_key = get_flag(data, "throttling_key")
        if throttling_key is not None and throttling_key in self.caches:
            if event.message.chat.id in self.caches[throttling_key]:
                return
            else:
                self.caches[throttling_key][event.message.chat.id] = None
        return await handler(event, data)
