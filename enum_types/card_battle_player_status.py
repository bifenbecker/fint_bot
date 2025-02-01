from enum import Enum


class CardBattlePlayerStatus(str, Enum):
    READY = "READY"
    PLAYING = "PLAYING"
    SEARCHING = "SEARCHING"
