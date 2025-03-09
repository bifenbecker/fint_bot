import bisect
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from db.base import Base
from enum_types import (
    CardBattleGameStatus,
    CardBattlePlayerStatus,
    CardBattleTurnType,
    CardPositionType,
)

boundaries = [0, 200, 400, 600, 800, 1000, 1300, 1600, 1900, 2500, float("inf")]
division_numbers = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]


class Player(Base):
    __tablename__ = "player"

    id = Column(BigInteger, primary_key=True)
    username = Column(String(255))
    access_minigame = Column(String(20), default="yes")
    game_pass = Column(String(10), default="no")
    pass_ts = Column(BigInteger, default=0)
    pass_until = Column(String(50), default="nopass")

    card_quants = Column(BigInteger, default=0)
    rating = Column(BigInteger, default=0)
    season_rating = Column(BigInteger, default=0)
    prev_season_rating = Column(BigInteger, default=0)

    season_penalty = Column(BigInteger, default=0)
    prev_season_penalty = Column(BigInteger, default=0)
    penalty_queue = Column(Integer, default=0)
    pen_wins = Column(Integer, default=0)
    pen_loses = Column(Integer, default=0)

    last_open = Column(BigInteger, default=0)
    open_count = Column(Integer, default=0)

    transactions = Column(BigInteger, default=0)

    lucky_quants = Column(Integer, default=0)
    last_lucky = Column(BigInteger, default=0)
    lucky_shots_plus = Column(Integer, default=0)

    joined_at_ts = Column(BigInteger, default=0)
    joined_at_txt = Column(String(50))

    role = Column(String(25), default="player")

    ban_status = Column(String(20), default="not_banned")

    trade_count = Column(BigInteger, default=0)

    card_battle_rating = Column(Integer, default=0, server_default="0", nullable=False)
    card_battle_status = Column(
        Enum(CardBattlePlayerStatus), default=CardBattlePlayerStatus.READY
    )
    win_card_battles = relationship(
        "CardBattle", back_populates="winner", foreign_keys="CardBattle.winner_id"
    )

    usercards = relationship("UserCard", back_populates="player")

    @hybrid_property
    def division(self) -> int:
        index = bisect.bisect_right(boundaries, self.card_battle_rating) - 1
        if index > len(division_numbers) or index < 0:
            raise Exception(f"Invalid rating: {self.card_battle_rating}")
        return division_numbers[index]

    @hybrid_property
    def max_rating(self) -> int:
        index = bisect.bisect_right(boundaries, self.card_battle_rating) + 1
        index = len(boundaries) if index > len(boundaries) else index
        return boundaries[index]

    @hybrid_property
    def min_rating(self) -> int:
        index = bisect.bisect_right(boundaries, self.card_battle_rating) - 3
        index = 0 if index < 0 else index
        return boundaries[index]


class CardItem(Base):
    __tablename__ = "carditem"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(255))
    card_name = Column(String(255))
    team = Column(String(255))
    league = Column(String(255))
    image = Column(String(255))
    rarity = Column(String(20))
    points = Column(Integer)

    status = Column(String(5), default="on")
    position = Column(Enum(CardPositionType), nullable=True, default=None)
    attack_rate = Column(Integer, default=0)
    defense_rate = Column(Integer, default=0)
    general_rate = Column(Integer, default=0)


class UserCard(Base):
    __tablename__ = "usercard"

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("player.id"))
    card_id = Column(Integer, ForeignKey("carditem.id", ondelete="CASCADE"))
    card_rarity = Column(String(20))
    points = Column(Integer)
    duplicate = Column(Integer, default=0)
    tradeble = Column(String(15), default="yes")

    card = relationship("CardItem", lazy="selectin")
    player = relationship("Player", back_populates="usercards")


class Trade(Base):
    __tablename__ = "trade"

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    status = Column(String(50), default="target_wait")
    quant = Column(Integer, default=1)

    owner = Column(BigInteger)
    owner_username = Column(String(255))
    owner_card_id = Column(Integer)

    target = Column(BigInteger)
    target_username = Column(String(255))
    target_card_id = Column(Integer)


class TradeCard(Base):
    __tablename__ = "tradecard"

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    trade_id = Column(BigInteger)
    card_id = Column(Integer)
    user_card_id = Column(BigInteger)
    kind = Column(String(25))


class UserTrade(Base):
    __tablename__ = "usertrade"

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    user_x_user = Column(String(50))


class Penalty(Base):
    __tablename__ = "penalty"

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    status = Column(String(50), default="active")
    kind = Column(String(25), default="target")

    owner = Column(BigInteger)
    owner_msg_id = Column(BigInteger)
    owner_username = Column(String(255))
    owner_score = Column(Integer, default=0)
    owner_txt = Column(String(15), default="")
    owner_card_id = Column(Integer, default=0)

    target = Column(BigInteger)
    target_msg_id = Column(BigInteger)
    target_username = Column(String(255))
    target_score = Column(Integer, default=0)
    target_txt = Column(String(15), default="")
    target_card_id = Column(Integer, default=0)

    round = Column(Integer, default=1)

    turn_user_id = Column(BigInteger, default=0)
    kicker = Column(BigInteger, default=0)
    kicker_pick = Column(Integer, default=0)
    keeper = Column(BigInteger, default=0)
    last_action = Column(BigInteger, default=0)

    winner = Column(BigInteger, default=0)


class PayItem(Base):
    __tablename__ = "payitem"

    id = Column(Integer, autoincrement=True, primary_key=True)
    status = Column(String(25), default="not_paid")
    label = Column(String(50))
    url = Column(Text)

    user_id = Column(BigInteger)
    amount = Column(Integer)
    kind = Column(String(50))


class CardPack(Base):
    __tablename__ = "cardpack"

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(BigInteger)


class CardXPack(Base):
    __tablename__ = "cardxpack"

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    pack_id = Column(Integer)
    user_card_id = Column(BigInteger)


class PromoCode(Base):
    __tablename__ = "promocode"
    id = Column(Integer, autoincrement=True, primary_key=True)
    promo = Column(Text)
    card_id = Column(Integer, nullable=True)
    kind = Column(String(50), default="card")
    quant = Column(Integer, default=2000000)
    users = Column(String(15), default="all")


class PromoUser(Base):
    __tablename__ = "promouser"
    id = Column(BigInteger, autoincrement=True, primary_key=True)
    promo_id = Column(Integer)
    user_id = Column(BigInteger)


class Season(Base):
    __tablename__ = "season"

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    user_id = Column(BigInteger)
    username = Column(String(255))
    kind = Column(String(25))
    rating = Column(BigInteger)
    date_str = Column(String(50))


class UserPacks(Base):
    __tablename__ = "userpacks"

    id = Column(BigInteger, primary_key=True)

    five_pack = Column(Integer, default=0)
    ten_pack = Column(Integer, default=0)
    twenty_pack = Column(Integer, default=0)
    thirty_pack = Column(Integer, default=0)
    player_pick = Column(Integer, default=0)


class PackBattle(Base):
    __tablename__ = "packbattle"

    id = Column(Integer, autoincrement=True, primary_key=True)
    status = Column(String(50), default="active")
    quant = Column(Integer)

    owner = Column(BigInteger)
    owner_msg_id = Column(BigInteger)
    owner_username = Column(String(255))
    owner_points = Column(Integer, default=0)
    owner_ts = Column(BigInteger, default=0)
    owner_ready = Column(Integer, default=0)

    target = Column(BigInteger, default=0)
    target_msg_id = Column(BigInteger, default=0)
    target_username = Column(String(255))
    target_points = Column(Integer, default=0)
    target_ts = Column(BigInteger, default=0)
    target_ready = Column(Integer, default=0)

    winner = Column(BigInteger, default=0)


class PlayerPick(Base):
    __tablename__ = "playerpick"

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(BigInteger)

    card_one = Column(Integer, default=0)
    card_two = Column(Integer, default=0)
    card_three = Column(Integer, default=0)

    card_pick = Column(Integer, default=0)


class Games(Base):
    __tablename__ = "games"

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(BigInteger)
    kind = Column(String(25))

    last_free = Column(BigInteger, default=0)
    free_quant = Column(Integer, default=0)

    attempts = Column(Integer, default=0)

    curr_casino = Column(Integer, default=0)


class UserCardsToBattle(Base):
    __tablename__ = "usercardstobattle"

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_card_id = Column(ForeignKey("usercard.id"), nullable=False)
    battle_id = Column(ForeignKey("cardbattle.id"), nullable=False)

    user_card = relationship("UserCard", lazy="selectin")
    battle = relationship("CardBattle", back_populates="cards", lazy="selectin")


class CardBattle(Base):
    __tablename__ = "cardbattle"

    id = Column(Integer, autoincrement=True, primary_key=True)
    status = Column(Enum(CardBattleGameStatus), nullable=True, default=None)

    player_blue_id = Column(ForeignKey("player.id"), nullable=False)
    player_red_id = Column(ForeignKey("player.id"), nullable=False)
    winner_id = Column(ForeignKey("player.id"), nullable=True, default=None)
    date_play = Column(DateTime, server_default=func.now(), default=datetime.now)

    player_blue = relationship(
        "Player",
        foreign_keys="CardBattle.player_blue_id",
    )
    player_red = relationship("Player", foreign_keys="CardBattle.player_red_id")
    winner = relationship(
        "Player",
        lazy="selectin",
        back_populates="win_card_battles",
        foreign_keys="CardBattle.winner_id",
    )

    turns = relationship("CardBattleTurn", back_populates="battle")
    cards = relationship("UserCardsToBattle", back_populates="battle")


class CardBattleTurn(Base):
    __tablename__ = "cardbattleturn"

    id = Column(Integer, autoincrement=True, primary_key=True)
    player_id = Column(ForeignKey("player.id"), nullable=False)
    card_id = Column(ForeignKey("usercardstobattle.id"), nullable=False)
    battle_id = Column(ForeignKey("cardbattle.id"), nullable=False)
    type = Column(Enum(CardBattleTurnType), nullable=False)

    battle = relationship("CardBattle", back_populates="turns")
    player = relationship("Player")
    card = relationship("UserCardsToBattle")
