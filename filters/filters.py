from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from db.queries.admin_queries import get_user_role


class IsAdmin(BaseFilter):
    async def __call__(self, target: Union[Message, CallbackQuery], ssn):
        role = await get_user_role(ssn, target.from_user.id)
        return role == "admin"
