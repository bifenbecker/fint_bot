import logging
from textwrap import dedent

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext as FSM
from aiogram.types import CallbackQuery as CQ
from aiogram.types import Message as Mes

from db.models import CardItem
from db.queries.card_queries import get_free_card, use_promo
from keyboards.cards_kbs import (accept_new_card_btn, back_to_cards_kb,
                                 card_kb, no_free_card_kb, fintpass_back_kb)
from keyboards.main_kbs import back_to_main_btn
from keyboards.pay_kbs import cards_pack_btn, to_packs_kb, player_pick_kb
from middlewares.actions import ActionMiddleware
from utils.format_texts import format_new_free_card_text, format_view_my_cards_text
from utils.misc import format_delay_text
from utils.states import UserStates

flags = {"throttling_key": "default"}
router = Router()
router.callback_query.middleware(ActionMiddleware())


@router.callback_query(F.data == "getcard", flags=flags)
async def get_card_cmd(c: CQ, action_queue):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    txt = """
    🃏 Если ты хочешь получить карту, то ты попал куда надо!

    Раз в 24 часа ты можешь получать 1 карту бесплатно, но если ты не хочешь ждать, то рекомендуем тебе посетить магазин карт 🛍
    Стань владельцем FINT PASS и ты сможешь получать 2 карты в день ✌️
    """
    await c.message.edit_text(dedent(txt), reply_markup=card_kb)


@router.callback_query(F.data == "getfreecard", flags=flags)
async def get_free_card_cmd(c: CQ, ssn, action_queue):
    card: CardItem = await get_free_card(ssn, c.from_user.id)
    if isinstance(card, int):
        timer = await format_delay_text(card)
        txt = f"Ты недавно получал свою бесплатную карточку! Следующую ты можешь получить через {timer} ⏱️. Если не хочешь ждать - приобретай дополнительные карточки"
        try:
            await c.message.edit_text(txt, reply_markup=no_free_card_kb)
        except Exception as error:
            await c.answer()
            logging.error(f"Edit error | chat {c.from_user.id}\n{error}")

    elif card == "no_cards":
        await c.answer("⚠️ Возникла ошибка! Попробуй позже")
    else:
        txt = await format_new_free_card_text(card)
        try:
            await c.message.delete()
        except Exception as error:
            logging.error(f"Del error | chat {c.from_user.id}\n{error}")

        await c.message.answer_photo(
            card.image, txt, reply_markup=accept_new_card_btn)

    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")


@router.callback_query(F.data == "promo", flags=flags)
async def user_promo_cmd(c: CQ, ssn, action_queue, state: FSM):
    try:
        del action_queue[str(c.from_user.id)]
    except Exception as error:
        logging.info(f"Action delete error\n{error}")

    txt = "Введите промокод ниже"
    await c.message.edit_text(txt, reply_markup=back_to_main_btn)
    await state.set_state(UserStates.promo_text)


@router.message(StateFilter(UserStates.promo_text), flags=flags)
async def use_promo_cmd(m: Mes, state: FSM, ssn):
    await state.clear()

    text = m.text

    res = await use_promo(ssn, m.from_user.id, text)
    if res:
        if res == "not_found":
            txt = "Увы, но такого промокода не существует, либо он больше недействительный 😔"
            await m.answer(txt, reply_markup=back_to_cards_kb)
        elif res == "already_used":
            txt = "Вы уже использовали этот промокод 😔"
            await m.answer(txt, reply_markup=back_to_cards_kb)
        elif res == "only_newbee_promo":
            txt = "Этот промокод могут использовать только новые игроки"
            await m.answer(txt, reply_markup=back_to_cards_kb)
        else:
            if res[0] == "card":
                card = res[1]
                txt = await format_new_free_card_text(card)
                await m.answer_photo(
                    card.image, txt, reply_markup=accept_new_card_btn)
            elif res[0] == "added":
                txt = "✅ Промокод успешно активирован!!\nПак начислен на твой баланс!"
                await m.answer(txt, reply_markup=to_packs_kb)
            elif res[0] == 'fintpass':
                # logging.info(
                # f"User {m.from_user.id}  label {pay.label} kind {pay.kind}")

                card: CardItem = res[1]
                txt = await format_new_free_card_text(card)
                await m.answer_photo(card.image, txt)

                page = 1
                last = 3

                try:
                    await m.delete()
                except:
                    pass
                pick_card: CardItem = res[3][0]
                txt = await format_view_my_cards_text(pick_card)

                await m.answer_photo(
                    pick_card.image,
                    txt, reply_markup=player_pick_kb(page, last, res[2], pick_card.id))
                await state.set_state(UserStates.player_pick)
                await state.update_data(pick_id=res[2], cards=res[3])
                await m.answer(text='FINT PASS успешно активирован ✅', reply_markup=fintpass_back_kb)
            else:
                txt = "Успешно ✅!\nВот карты, которые ты получил!"
                await m.answer(txt, reply_markup=cards_pack_btn(res[1]))
