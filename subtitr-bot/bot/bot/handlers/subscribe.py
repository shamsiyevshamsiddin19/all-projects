"""/subscribe — obuna tariflari va Click to'lov havolasi (arxitektura 7, 10)."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import settings
from db.crud import create_payment, get_effective_settings, get_or_create_user
from tariffs import TARIFFS

router = Router()


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _plans_keyboard(price_basic: int, price_premium: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💳 BASIC — {_fmt(price_basic)} so'm/oy",
                    callback_data="buy:basic",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"⭐ PREMIUM — {_fmt(price_premium)} so'm/oy",
                    callback_data="buy:premium",
                )
            ],
        ]
    )


def _click_url(payment_id: int, amount: int) -> str:
    return settings.click_pay_url(f"SUBT{payment_id}", amount)


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    basic = TARIFFS["basic"]
    eff = await get_effective_settings()
    pb = eff["price_basic"]
    pp = eff["price_premium"]

    await message.answer(
        "💎 <b>Obuna tariflari</b>\n\n"
        f"👤 <b>BASIC</b> — {_fmt(pb)} so'm/oy\n"
        f"✅ Kuniga {basic.daily_videos} ta video ({basic.max_minutes} daqiqagacha)\n"
        "✅ Tarjima (o'zbek · rus · ingliz)\n"
        "✅ Ikki qatlam subtitr\n"
        "✅ .SRT fayl — o'zingiz tahrirlang\n\n"
        f"⭐ <b>PREMIUM</b> — {_fmt(pp)} so'm/oy\n"
        "✅ Cheksiz video\n"
        "✅ Barcha rejimlar\n"
        "✅ Ustuvor navbat — tezroq ishlaydi\n\n"
        f"💡 <i>Bitta video uchun subtitr yozishga soatlar sarflashingiz mumkin —\n"
        f"biz buni bir daqiqada qilamiz.</i>\n\n"
        "Tarifni tanlang 👇",
        reply_markup=_plans_keyboard(pb, pp),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "show_plans")
async def on_show_plans(call: CallbackQuery) -> None:
    """«Boshqa tariflar» tugmasi — to'liq tarif menyusini ko'rsatadi."""
from __future__ import annotations

    await call.answer()
    await cmd_subscribe(call.message)


@router.callback_query(F.data.startswith("buy:"))
async def on_buy(call: CallbackQuery) -> None:
    plan = call.data.split(":", 1)[1]
    if plan not in ("basic", "premium"):
        await call.answer()
        return

    await call.answer()
    if not settings.click_configured:
        await call.message.answer(
            "⚠️ To'lov hali sozlanmagan.\n"
            "Sinov uchun admin /grant buyrug'idan foydalanishi mumkin."
        )
        return

    user = await get_or_create_user(call.from_user.id, call.from_user.username)
    eff = await get_effective_settings()
    amount = eff["price_premium"] if plan == "premium" else eff["price_basic"]
    payment_id = await create_payment(user.id, plan, amount)
    url = _click_url(payment_id, amount)

    plan_label = "PREMIUM ⭐" if plan == "premium" else "BASIC 👤"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Click orqali to'lash", url=url)],
        ]
    )
    await call.message.answer(
        f"📋 <b>To'lov: {plan_label}</b>\n\n"
        f"Summa: <b>{_fmt(amount)} so'm</b>\n\n"
        "Quyidagi tugmani bosing — Click ilovasi ochiladi.\n"
        "To'lov tugagach obuna <b>avtomatik</b> faollashadi ✅",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
