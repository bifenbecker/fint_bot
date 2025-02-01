from aiogram import F, Router
from aiogram.types import CallbackQuery as CQ

from db.queries.global_queries import (
    get_all_time_penalty,
    get_all_time_rating,
    get_top_penalty,
    get_top_rating,
)
from keyboards.ratings_kbs import back_to_ratings_btn, ratings_kb
from utils.format_texts import (
    format_all_time_penalty_text,
    format_all_time_rating_text,
    format_top_penalty_text,
    format_top_rating_text,
)

flags = {"throttling_key": "default"}
router = Router()


@router.callback_query(F.data == "rating", flags=flags)
async def ratings_cmd(c: CQ):
    txt = "В этом разделе ты можешь посмотреть 🏆 Топ 10 игроков по категориям!"
    await c.message.edit_text(txt, reply_markup=ratings_kb)


@router.callback_query(F.data == "top_rating", flags=flags)
async def top_rating_cmd(c: CQ, ssn):
    res = await get_top_rating(ssn, c.from_user.id)
    txt = await format_top_rating_text(*res)
    await c.message.edit_text(txt, reply_markup=back_to_ratings_btn)


@router.callback_query(F.data == "top_penalty", flags=flags)
async def top_penalty_cmd(c: CQ, ssn):
    res = await get_top_penalty(ssn, c.from_user.id)
    txt = await format_top_penalty_text(*res)
    await c.message.edit_text(txt, reply_markup=back_to_ratings_btn)


@router.callback_query(F.data == "alltimetop_rating", flags=flags)
async def top_rating_cmd(c: CQ, ssn):
    res = await get_all_time_rating(ssn, c.from_user.id)
    txt = await format_all_time_rating_text(*res)
    await c.message.edit_text(txt, reply_markup=back_to_ratings_btn)


@router.callback_query(F.data == "alltimetop_penalty", flags=flags)
async def top_penalty_cmd(c: CQ, ssn):
    res = await get_all_time_penalty(ssn, c.from_user.id)
    txt = await format_all_time_penalty_text(*res)
    await c.message.edit_text(txt, reply_markup=back_to_ratings_btn)
