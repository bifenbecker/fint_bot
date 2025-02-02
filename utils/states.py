from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    mycards = State()
    myteamcards = State()

    owner_trade = State()
    target_trade = State()

    target_penalty = State()

    pack_cards = State()
    promo_text = State()

    pen_owner_card = State()
    pen_target_card = State()
    answ_pen_card = State()

    ex_craft = State()
    player_pick = State()


class CardsBattleStates(StatesGroup):
    select_cards_battle = State()
    search_cards_battle = State()


class MultiTrade(StatesGroup):
    owner_cards = State()
    target_username = State()
    target_cards = State()


class AdminStates(StatesGroup):
    add_card = State()
    card_image = State()

    image_id = State()
    sticker_id = State()

    view_cards = State()
    promo_cards = State()
    new_image = State()
    new_text = State()

    promo_users = State()
    promo_kind = State()
    promo_text = State()
    promo_card = State()

    user_info = State()
