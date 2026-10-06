from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline import topup_amounts_kb, main_menu
from bot.states.order import TopupStates
from db.models import User
from payment.click import make_click_url
from db.crud import create_payment
from config import settings

router = Router()


def _topup_url_kb(amount: int, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 {amount:,} so'm — Click orqali to'lash", url=url)],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="cancel")],
    ])


@router.message(F.text == "💳 Hisobni to'ldirish")
async def topup_menu(message: Message, db_user: User):
    await message.answer(
        f"💳 <b>Hisobni to'ldirish</b>\n\n"
        f"💰 Joriy balans: <b>{db_user.balance:,} so'm</b>\n\n"
        f"Quyidagi miqdorlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=topup_amounts_kb(),
    )


@router.callback_query(F.data.startswith("topup:"))
async def topup_amount(call: CallbackQuery, db_user: User):
    amount = int(call.data.split(":")[1])
    await _make_topup(call.message, call.from_user.id, amount)
    await call.answer()


@router.callback_query(F.data == "topup_custom")
async def topup_custom(call: CallbackQuery, state: FSMContext):
    await state.set_state(TopupStates.entering_amount)
    await call.message.edit_text(
        f"✏️ <b>To'ldirmoqchi bo'lgan summani yozing</b>\n\n"
        f"Eng kami: <b>{settings.eff_min_topup():,} so'm</b>\n"
        f"<i>Masalan: 35000</i>",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(TopupStates.entering_amount)
async def topup_custom_amount(message: Message, state: FSMContext):
    digits = "".join(ch for ch in (message.text or "") if ch.isdigit())
    if not digits:
        await message.answer("⚠️ Iltimos, faqat son kiriting (masalan: 35000).")
        return
    amount = int(digits)
    mn = settings.eff_min_topup()
    if amount < mn:
        await message.answer(f"⚠️ Eng kami <b>{mn:,} so'm</b> bo'lsin.", parse_mode="HTML")
        return
    if amount > 10_000_000:
        await message.answer("⚠️ Juda katta summa. 10 mln so'mdan kam bo'lsin.")
        return
    await state.clear()
    await _make_topup(message, message.from_user.id, amount)


async def _make_topup(message: Message, user_id: int, amount: int) -> None:
    payment = await create_payment(
        user_id=user_id, amount=amount, order_id=None, payment_type="topup",
    )
    url = make_click_url(payment.merchant_trans_id, amount)
    await message.answer(
        f"💳 <b>{amount:,} so'm to'lash</b>\n\n"
        f"Quyidagi tugma orqali Click'ga o'ting va to'lovni amalga oshiring.\n"
        f"To'lov tasdiqlangach balans <b>avtomatik</b> yangilanadi.",
        parse_mode="HTML",
        reply_markup=_topup_url_kb(amount, url),
    )
