from enum import Enum


class CardBattleGameStatus(str, Enum):
    FINISHED = "FINISHED"
    WAITING_FOR_RED = "WAITING_FOR_RED"
    WAITING_FOR_BLUE = "WAITING_FOR_BLUE"
