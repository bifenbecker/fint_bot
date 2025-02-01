from textwrap import dedent

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.queries.admin_queries import add_new_card
from enum_types import CardPositionType
from filters.filters import IsAdmin
from keyboards.admin_kbs import back_to_admin_btn
from utils.const import rarities
from utils.states import AdminStates

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "addcard", IsAdmin(), flags=flags)
async def add_card_cmd(c: CQ, state: FSM):
    await state.clear()

    txt = """
    Для начала укажите характеристики карточки в формате
    1.Имя игрока
    2.Название карты
    3.Команда игрока
    4.Лига
    5.Редкость карточки
    6.Рейтинг карточки
    7.Позиция
	8.Атака
	9.Защита
	10.Общий рейтинг

    цифры указывать не надо
    
    Позиции:
    <code>Вратарь</code>, <code>Защитник</code>, 
    <code>Полузащитник</code>, <code>Нападающий</code>

    Список редкостей:
    <code>Common</code>, <code>Uncommon</code>, <code>Rare</code>, 
    <code>Very rare</code>, <code>Coach</code>, <code>Epic</code>, 
    <code>Unique</code>, <code>Flashback</code>, 
    <code>Legendary</code>, <code>Moments</code>,
    <code>Heroes</code>, <code>Inform</code>,
    <code>Icons</code>, <code>Limited</code>,
    <code>Event</code>
    """

    await c.message.delete()
    await c.message.answer(dedent(txt), reply_markup=back_to_admin_btn)
    await state.set_state(AdminStates.add_card)


@router.message(StateFilter(AdminStates.add_card), F.text, flags=flags)
async def add_new_card_cmd(m: Mes, state: FSM):
    data = m.text.split("\n")
    if len(data) != 10:
        await state.clear()
        await m.answer(
            "Некорректный ввод данных, попробуйте снова", reply_markup=back_to_admin_btn
        )
    else:
        name = data[0]
        card_name = data[1]
        team = data[2]
        league = data[3]
        rarity = data[4]
        points = data[5]
        position = data[6]
        attack_rate = data[7]
        defense_rate = data[8]
        general_rate = data[9]
        print(rarity)

        if rarity not in rarities:
            await m.answer(
                "Такая редкость не найдена, попробуйте снова",
                reply_markup=back_to_admin_btn,
            )
        elif not points.isdigit():
            await m.answer(
                "Некорректный ввод данных, попробуйте снова",
                reply_markup=back_to_admin_btn,
            )
        elif position not in CardPositionType:
            await m.answer(
                "Такая позиция не найдена, попробуйте снова",
                reply_markup=back_to_admin_btn,
            )
        elif (
            not attack_rate.isdigit()
            or not defense_rate.isdigit()
            or not general_rate.isdigit()
        ):
            await m.answer(
                "Атака, защита и общий рейтинг должны быть числами, попробуйте снова",
                reply_markup=back_to_admin_btn,
            )
        elif int(attack_rate) < 0 or int(defense_rate) < 0 or int(general_rate) < 0:
            await m.answer(
                "Атака, защита и общий рейтинг не могут быть меньше нуля, попробуйте снова",
                reply_markup=back_to_admin_btn,
            )
        elif int(attack_rate) + int(defense_rate) != int(general_rate):
            await m.answer(
                "Сумма атаки и защиты должна быть равна общему рейтингу, попробуйте снова",
                reply_markup=back_to_admin_btn,
            )
        else:
            await m.answer(
                "Теперь отправьте фото карточки игрока", reply_markup=back_to_admin_btn
            )
            await state.set_state(AdminStates.card_image)
            await state.update_data(
                name=name,
                card_name=card_name,
                team=team,
                rarity=rarity,
                points=int(points),
                league=league,
                position=position,
                attack_rate=int(attack_rate),
                defense_rate=int(defense_rate),
                general_rate=int(general_rate),
            )


@router.message(StateFilter(AdminStates.card_image), F.photo, flags=flags)
async def save_new_card_cmd(m: Mes, state: FSM, ssn):
    image = m.photo[-1].file_id
    data = await state.get_data()
    await state.clear()
    await add_new_card(ssn, data, image)

    txt = f"""
    Новая карточка добавлена!

    {data["name"]}
    {data["card_name"]}
    Лига: <b>{data["league"]}</b>
    Рейтинг: <b>{data["points"]}</b>
    Редкость: <b>{data["rarity"]}</b>
    Команда: <b>{data["team"]}</b>
    Позиция: <b>{data["position"]}</b>
    Атака: <b>{data["attack_rate"]}</b>
    Защита: <b>{data["defense_rate"]}</b>
    Общий рейтинг: <b>{data["general_rate"]}</b>
    """
    await m.answer_photo(image, dedent(txt), reply_markup=back_to_admin_btn)
