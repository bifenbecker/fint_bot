from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.queries.admin_queries import get_adm_user_info
from filters.filters import IsAdmin
from keyboards.admin_kbs import (admin_card_kb, admin_kb, admin_promos_kb,
                                 back_to_admin_btn)
from utils.format_texts import format_user_info_text
from utils.states import AdminStates

flags = {"throttling_key": "default"}
router = Router()


@router.message(Command("admin"), IsAdmin(), flags=flags)
async def admin_cmd(m: Mes, state: FSM):
    await state.clear()
    txt = "Добро пожаловать в админскую панель\nВыберете раздел с которым вы хотите работать"
    await m.answer(txt, reply_markup=admin_kb)


@router.callback_query(F.data == "back_to_admin", IsAdmin(), flags=flags)
async def back_to_admin_cmd(c: CQ, state: FSM):
    await state.clear()
    txt = "Добро пожаловать в админскую панель\nВыберете раздел с которым вы хотите работать"
    await c.message.delete()
    await c.message.answer(txt, reply_markup=admin_kb)


@router.callback_query(F.data == "admincards", IsAdmin(), flags=flags)
async def admin_cards_cmd(c: CQ, state: FSM):
    await state.clear()
    txt = "Вы находитесь в разделе управления карточками!\nВыберете действие, которое хотите выполнить"
    await c.message.edit_text(txt, reply_markup=admin_card_kb)


@router.callback_query(F.data == "adminpromos", IsAdmin(), flags=flags)
async def admin_promos_cmd(c: CQ, state: FSM):
    await state.clear()
    txt = "Вы находитесь в разделе управления промокодами!\nВыберете действие, которое хотите выполнить"
    await c.message.edit_text(txt, reply_markup=admin_promos_kb)


@router.message(Command("ph"), flags=flags)
async def image_id_cmd(m: Mes, state: FSM):
    await m.answer("Need Image")
    await state.set_state(AdminStates.image_id)


@router.message(StateFilter(AdminStates.image_id), F.photo, flags=flags)
async def send_image_id_cmd(m: Mes, state: FSM):
    await state.clear()

    image = m.photo[-1].file_id
    await m.answer(f"<code>{image}</code>")


@router.message(Command("st"), flags=flags)
async def image_id_cmd(m: Mes, state: FSM):
    await m.answer("Need Sticker")
    await state.set_state(AdminStates.sticker_id)


@router.message(StateFilter(AdminStates.sticker_id), F.sticker, flags=flags)
async def send_sticker_id_cmd(m: Mes, state: FSM):
    await state.clear()

    image = m.sticker.file_id
    await m.answer(f"<code>{image}</code>")


@router.callback_query(F.data == "adminusers", IsAdmin(), flags=flags)
async def admin_users_cmd(c: CQ, state: FSM):
    await state.clear()
    txt = "Напишите @username или USER_ID пользователя, о котором хотите получить информацию"
    await c.message.edit_text(txt, reply_markup=back_to_admin_btn)
    await state.set_state(AdminStates.user_info)


@router.message(StateFilter(AdminStates.user_info), flags=flags)
async def view_user_info_cmd(m: Mes, state: FSM, ssn):
    await state.clear()

    res = await get_adm_user_info(ssn, m.text)
    if res == "not_found":
        await m.answer("Такой пользователь не найден", reply_markup=admin_kb)
    else:
        txt = await format_user_info_text(res)
        await m.answer(txt, reply_markup=admin_kb)


@router.message(Command("online"), IsAdmin(), flags=flags)
async def online_cmd(m: Mes, online):
    await m.answer(f"Online: {len(online)}")
