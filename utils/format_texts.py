import datetime
from textwrap import dedent

from db.models import CardItem, Penalty, Player, Trade, UserCard, UserPacks


async def format_new_free_card_text(card: CardItem):
    txt = f"""
    {card.name} <b>{card.card_name}</b>
    Лига: <b>{card.league}</b>
    Команда: <b>{card.team}</b>
    Рейтинг: <b>{card.points}</b>
    Редкость: <b>{card.rarity}</b>
    """
    return dedent(txt)


async def format_view_my_cards_text(card: CardItem):
    txt = f"""
    {card.name} <b>{card.card_name}</b>
    Лига: <b>{card.league}</b>
    Команда: <b>{card.team}</b>
    Рейтинг: <b>{card.points}</b>
    Редкость: <b>{card.rarity}</b>
    Коллекционный номер: <b>{card.id}</b>
    """
    return dedent(txt)


async def format_list_my_cards_text(cards: dict):
    txts = []
    txt = "Список всех ваших карт:\n"
    num = 0
    for k, v in cards.items():
        txt += f"\n{v['card_name']} | Рейтинг: {v['rating']} | {v['quant']} шт."
        num += 1
        if num == 51:
            txts.append(txt)
            num = 0
            txt = ""

    if len(txt) > 0:
        txts.append(txt)

    return txts


async def format_top_rating_text(tops, user: Player, place):
    txt = "🏆 Сезонный рейтинг игроков по картам\n"

    top: Player
    for num, top in enumerate(tops):
        if num == 0:
            plc = "🥇"
        elif num == 1:
            plc = "🥈"
        elif num == 2:
            plc = "🥉"
        else:
            plc = f" {num + 1}."

        txt += f"\n{plc} {top.username} - {top.season_rating}"

    if place > len(tops):
        txt += f"\n\n{place}. {user.username} - {user.season_rating}"

    return txt


async def format_all_time_rating_text(tops, user: Player, place):
    txt = "🏆 Рейтинг игроков по картам\n"

    top: Player
    for num, top in enumerate(tops):
        if num == 0:
            plc = "🥇"
        elif num == 1:
            plc = "🥈"
        elif num == 2:
            plc = "🥉"
        else:
            plc = f" {num + 1}."

        txt += f"\n{plc} {top.username} - {top.rating}"

    if place > len(tops):
        txt += f"\n\n{place}. {user.username} - {user.rating}"

    return txt


async def format_top_penalty_text(tops, user: Player, place):
    txt = "🏆 Сезонный рейтинг игроков по пенальти\n"

    top: Player
    for num, top in enumerate(tops):
        if num == 0:
            plc = "🥇"
        elif num == 1:
            plc = "🥈"
        elif num == 2:
            plc = "🥉"
        else:
            plc = f" {num + 1}."

        txt += f"\n{plc} {top.username} - {top.season_penalty}"

    if place > len(tops):
        txt += f"\n\n{place}. {user.username} - {user.season_penalty}"

    return txt


async def format_all_time_penalty_text(tops, user: Player, place):
    txt = "🏆 Сезонный рейтинг игроков по пенальти\n"

    top: Player
    for num, top in enumerate(tops):
        if num == 0:
            plc = "🥇"
        elif num == 1:
            plc = "🥈"
        elif num == 2:
            plc = "🥉"
        else:
            plc = f" {num + 1}."

        txt += f"\n{plc} {top.username} - {top.penalty_rating}"

    if place > len(tops):
        txt += f"\n\n{place}. {user.username} - {user.penalty_rating}"

    return txt


async def format_penalty_round_result_text(penalty: Penalty, result):
    # Условие инвертировано, так как уже произошла смена сторон
    if penalty.keeper == penalty.owner:
        keeper_username = penalty.target_username
        kicker_username = penalty.owner_username
    else:
        keeper_username = penalty.owner_username
        kicker_username = penalty.target_username

    if result:
        keeper_res_txt = f"🏆 Ты отбил удар\n{kicker_username} бил в тот же угол\n"
        kicker_res_txt = f"❌ Увы ты не забил\n{keeper_username} угадал твой удар\n"
    else:
        keeper_res_txt = f"❌ Ты пропустил гол\n{kicker_username} бил в другой угол\n"
        kicker_res_txt = f"⚽️ ГОЛ!!!\n{keeper_username} прыгнул в другую сторону\n"

    owner_res_txt = penalty.owner_txt.replace("0", "❌").replace("1", "⚽️")
    target_res_txt = penalty.target_txt.replace("0", "❌").replace("1", "⚽️")

    if (penalty.round % 2) == 0:
        target_res_txt += "⌛️"
    else:
        owner_res_txt += "⌛️"

    # Условие инвертировано, так как уже произошла смена сторон
    if penalty.keeper == penalty.target:
        keeper_txt = keeper_res_txt + "Результаты твоих ударов:\n" + \
            owner_res_txt + "\nРезультаты ударов противника:\n" + target_res_txt
        kicker_txt = kicker_res_txt + "Результаты твоих ударов:\n" + \
            target_res_txt + "\nРезультаты ударов противника:\n" + owner_res_txt

    else:
        keeper_txt = keeper_res_txt + "Результаты твоих ударов:\n" + \
            target_res_txt + "\nРезультаты ударов противника:\n" + owner_res_txt
        kicker_txt = kicker_res_txt + "Результаты твоих ударов:\n" + \
            owner_res_txt + "\nРезультаты ударов противника:\n" + target_res_txt

    return keeper_txt, kicker_txt


async def format_penalty_final_result_text(penalty: Penalty):
    owner_res_txt = f"Результаты ударов {penalty.owner_username}\n"
    target_res_txt = f"Результаты ударов {penalty.target_username}\n"

    owner_res_txt += penalty.owner_txt.replace("0", "❌").replace("1", "⚽️")
    target_res_txt += penalty.target_txt.replace("0", "❌").replace("1", "⚽️")

    if penalty.owner_card_id == 0:
        if penalty.owner == penalty.winner:
            winner_txt = f"\nПобедитель - {penalty.owner_username}"
        elif penalty.target == penalty.winner:
            winner_txt = f"\nПобедитель - {penalty.target_username}"
        else:
            winner_txt = "\n🏆 Вы забили одинаковое количество голов! Предлагаем вам переигровку или же ничью, выбор за вами!"
    else:
        if penalty.owner == penalty.winner:
            winner_txt = f"\n{penalty.owner_username} победил и получил карту соперника"
        elif penalty.target == penalty.winner:
            winner_txt = f"\n{penalty.target_username} победил и получил карту соперника"
        else:
            winner_txt = "\n🏆 Вы забили одинаковое количество голов! Предлагаем вам переигровку или же ничью, выбор за вами!"

    return target_res_txt + "\n" + owner_res_txt + winner_txt


async def format_user_info_text(user: Player):
    last_date = datetime.datetime.fromtimestamp(user.last_open - 86400)
    date_str = last_date.strftime("%d.%m.%Y %H:%M")
    txt = f"""
    Данные по пользователю {user.username} (ID {user.id})

    Дата регистрации - {user.joined_at_txt}
    Собранное количество карточек - {user.card_quants}
    Рейтинг собранных карточек - {user.rating}
    Рейтинг в игре пенальти - {user.season_penalty}

    Забирал бесплатную карточку - {date_str}
    Количество транзакций - {user.transactions}
    """
    return dedent(txt)


async def format_view_my_packs_text(upacks: UserPacks):
    txt = f"""
    🗃 Твои паки:

    🃏 Пак на 5 карт: <b>{upacks.five_pack}</b>
    🃏 Пак на 10 карт: <b>{upacks.ten_pack}</b>
    🃏 Пак на 20 карт: <b>{upacks.twenty_pack}</b>
    🃏 Пак на 30 карт: <b>{upacks.thirty_pack}</b>
    🃏 Выбор игрока: <b>{upacks.player_pick}</b>
    """
    return dedent(txt)


async def format_owner_trade_cards_text(cards):
    txt = "Выбраны карты:\n"
    card: UserCard
    for card in cards:
        txt += f"\n• {card.card.name} <b>{card.card.card_name}</b> | Рейтинг: <b>{card.points}</b>"

    txt += "\n\nНапишите юзернейм пользователя (@username), с которым хотите обменяться"

    return txt


async def format_multi_trade_offer_text(username, cards, quant):
    txt = f"{username} Предлагает обмен {quant} на {quant} этими картами:\n"
    card: UserCard
    for card in cards:
        txt += f"\n• {card.card.name} <b>{card.card.card_name}</b> | Рейтинг: <b>{card.points}</b>"

    return txt


async def format_target_trade_cards_text(res):
    txt = "Вы отдаете карты:\n"
    for card in res[1]:
        txt += f"\n• {card.card.name} <b>{card.card.card_name}</b> | Рейтинг: <b>{card.points}</b>"

    txt += "\n\nВы получаете карты:"
    for card in res[0]:
        txt += f"\n• {card.card.name} <b>{card.card.card_name}</b> | Рейтинг: <b>{card.points}</b>"

    txt += "\n\nВы действительно хотите обменять эти карты?"

    return txt


async def format_m_trade_answer_text(trade: Trade, owner_cards, target_cards):
    txt = f"{trade.target_username} отправил вам встречное предложение обмена.\n\nВы получите карты:\n"
    for card in target_cards:
        txt += f"\n• {card.card.name} <b>{card.card.card_name}</b> | Рейтинг: <b>{card.points}</b>"

    txt += "\n\nВы отдадите карты:"
    for card in owner_cards:
        txt += f"\n• {card.card.name} <b>{card.card.card_name}</b> | Рейтинг: <b>{card.points}</b>"

    return txt
