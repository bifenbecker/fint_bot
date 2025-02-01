from textwrap import dedent

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.queries.admin_queries import add_new_card
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

    цифры указывать не надо

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
    if len(data) != 6:
        await state.clear()
        await m.answer(
            "Некорректный ввод данных, попробуйте снова",
            reply_markup=back_to_admin_btn)
    else:
        name = data[0]
        card_name = data[1]
        team = data[2]
        league = data[3]
        rarity = data[4]
        points = data[5]
        print(rarity)

        if rarity not in rarities:
            await m.answer(
                "Такая редкость не найдена, попробуйте снова",
                reply_markup=back_to_admin_btn)
        elif not points.isdigit():
            await m.answer(
                "Некорректный ввод данных, попробуйте снова",
                reply_markup=back_to_admin_btn)
        else:
            await m.answer(
                "Теперь отправьте фото карточки игрока",
                reply_markup=back_to_admin_btn)
            await state.set_state(AdminStates.card_image)
            await state.update_data(
                name=name, card_name=card_name, team=team,
                rarity=rarity, points=int(points), league=league)


@router.message(StateFilter(AdminStates.card_image), F.photo, flags=flags)
async def save_new_card_cmd(m: Mes, state: FSM, ssn):
    image = m.photo[-1].file_id
    data = await state.get_data()
    await state.clear()
    await add_new_card(ssn, data, image)

    txt = f"""
    Новая карточка добавлена!

    {data['name']}
    {data['card_name']}
    Лига: <b>{data['league']}</b>
    Рейтинг: <b>{data['points']}</b>
    Редкость: <b>{data['rarity']}</b>
    Команда: <b>{data['team']}</b>
    """
    await m.answer_photo(
        image, dedent(txt), reply_markup=back_to_admin_btn)
