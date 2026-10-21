# -*- coding: utf-8 -*-
"""
Foldex Qat'iy Avtorizatsiya Middleware (AdminAuthMiddleware).
Loyiha talabiga binoan, ushbu bot faqat bitta Telegram foydalanuvchisiga (7883409434) xizmat qiladi.
Barcha xabarlar, komandalar, inline so'rovlar va callback querylar
ushbu middleware orqali filtrlanadi. Ruxsatsiz shaxslar uchun bot butunlay yopiq.
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
    TelegramObject
)

from app.core.config import settings


class AdminAuthMiddleware(BaseMiddleware):
    """
    Faqat settings.TELEGRAM_ADMIN_ID (7883409434) ga ruxsat beruvchi middleware.
    Boshqa foydalanuvchilar murojaat qilganda so'rov handlerlarga o'tmasdan to'xtatiladi.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # 1. Foydalanuvchini aniqlash
        user = data.get("event_from_user")
        if not user:
            # Agar foydalanuvchi noma'lum bo'lsa (masalan kanal postlari)
            return None

        # 2. Qat'iy tekshiruv: ID faqat 7883409434 bo'lishi shart!
        if user.id != settings.TELEGRAM_ADMIN_ID:
            # a) Xabar yuborilgan bo'lsa:
            if isinstance(event, Message):
                await event.answer(
                    "⛔ <b>Kirish taqiqlangan!</b>\n\n"
                    "Ushbu bot shaxsiy fayl menejeri bo'lib, "
                    "faqat administrator uchun mo'ljallangan.",
                    parse_mode="HTML"
                )
                return None

            # b) Tugma bosilgan bo'lsa (CallbackQuery):
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "⛔ Ruxsat berilmagan! Siz administrator emassiz.",
                    show_alert=True
                )
                return None

            # c) Inline rejimda chaqirilgan bo'lsa (InlineQuery):
            elif isinstance(event, InlineQuery):
                unauthorized_article = InlineQueryResultArticle(
                    id="unauthorized",
                    title="⛔ Kirish huquqi mavjud emas",
                    description="Ushbu bot faqat administrator uchun shaxsiy fayl menejeri.",
                    input_message_content=InputTextMessageContent(
                        message_text="⛔ Ushbu bot shaxsiy fayl menejeri bo'lib, unga faqat administrator ruxsatiga ega."
                    )
                )
                await event.answer(
                    results=[unauthorized_article],
                    cache_time=1,
                    is_personal=True
                )
                return None

            return None

        # Agar admin bo'lsa, handlarga yo'l berish
        return await handler(event, data)
