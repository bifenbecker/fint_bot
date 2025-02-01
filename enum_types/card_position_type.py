from enum import Enum

from .meta import EnumContainsMeta


class CardPositionType(str, Enum, metaclass=EnumContainsMeta):
    GOALKEEPER = "Вратарь"
    DEFENDER = "Защитник"
    MIDFIELDER = "Полузащитник"
    FORWARD = "Нападающий"
