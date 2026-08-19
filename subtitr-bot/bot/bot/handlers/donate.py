"""/donate — loyihani qo'llab-quvvatlash + izoh (arxitektura 10.1).

Foydalanuvchi summa tanlaydi (yoki /donate <summa> <izoh> bilan yuboradi).
Click sozlangan bo'lsa to'lov havolasi beriladi (transaction_param=SUBTD{id}
— myxvest ko'prigi orqali yo'naltiriladi), to'lov tugagach web/click.py
donatni "paid" qiladi. Izohlar admin panelда moderatsiyadan o'tadi.
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import settings
from db.crud import create_donation, get_or_create_user

router = Router()

_PRESETS = (5000, 10000, 30000, 50000)
_MIN_AMOUNT = 1000


def _amounts_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{a:,} so'm".replace(",", " "), callback_data=f"donate:{a}"
            )
        ]
        for a in _PRESETS
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _click_url(donation_id: int, amount: int) -> str:
    # "SUBTD" prefiksi: myxvest ko'prigi donat callback'ini subtitr botga uzatadi.
    return settings.click_pay_url(f"SUBTD{donation_id}", amount)


async def _start_donation(tg_id: int, username: str | None, amount: int,
                          comment: str | None, answer) -> None:
    user = await get_or_create_user(tg_id, username)
    donation_id = await create_donation(user.id, amount, comment)
    if settings.click_configured:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="💳 To'lash (Click)", url=_click_url(donation_id, amount)
                )
            ]]
        )
        await answer(
            f"❤️ Rahmat! Donat: <b>{amount:,} so'm</b>\n".replace(",", " ")
            + "Quyidagi tugma orqali to'lang. To'lovdan so'ng tasdiqlanadi.",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    else:
        await answer(
            "❤️ Qo'llab-quvvatlash niyatingiz uchun rahmat!\n"
            "(To'lov hali sozlanmagan — Click kalitlari kiritilgach faollashadi.)",
            parse_mode="HTML",
        )


@router.message(Command("donate"))
async def cmd_donate(message: Message) -> None:
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) >= 2 and parts[1].isdigit():
        amount = int(parts[1])
        comment = parts[2] if len(parts) > 2 else None
        if amount < _MIN_AMOUNT:
            await message.reply(f"Minimal summa {_MIN_AMOUNT:,} so'm.".replace(",", " "))
            return
        await _start_donation(
            message.from_user.id, message.from_user.username, amount, comment,
            message.answer,
        )
        return
    await message.answer(
        "❤️ <b>Loyihani qo'llab-quvvatlash</b>\n\n"
        "Botni rivojlantirishga hissa qo'shishingiz mumkin. Summani tanlang "
        "yoki izoh bilan yuboring:\n"
        "<code>/donate 10000 Zo'r bot, rahmat!</code>\n\n"
        "ℹ️ Donat — obuna emas (limit/imkoniyat bermaydi), faqat ixtiyoriy "
        "qo'llab-quvvatlash.",
        reply_markup=_amounts_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("donate:"))
async def on_donate(call: CallbackQuery) -> None:
    try:
        amount = int(call.data.split(":", 1)[1])
    except ValueError:
        await call.answer()
        return
    await call.answer()
    await _start_donation(
        call.from_user.id, call.from_user.username, amount, None, call.message.answer
    )
