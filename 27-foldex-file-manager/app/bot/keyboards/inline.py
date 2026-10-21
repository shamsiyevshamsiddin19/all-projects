# -*- coding: utf-8 -*-
"""
Foldex Inline Keyboard moduli.
Veb-admin panelga ochiluvchi tugmalar va fayl amallari
uchun Inline klaviaturalarni shakllantiradi.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.core.config import settings


def get_admin_panel_inline_keyboard() -> InlineKeyboardMarkup:
    """
    /admin komandasi yuborilganda foydalanuvchiga taqdim etiladigan inline klaviatura.
    Talab bo'yicha: '🌐 Fayllarni boshqarish' tugmasi https://foldex.shamsiyev.uz manziliga olib boradi.
    Telegram Mini App (WebApp) sifatida to'g'ridan-to'g'ri ochiladi.
    """
    builder = InlineKeyboardBuilder()

    # 1. Asosiy veb-panel tugmasi (Telegram WebApp sifatida bot ichida ochiladi)
    builder.row(
        InlineKeyboardButton(
            text="🌐 Fayllarni boshqarish",
            web_app=WebAppInfo(url=settings.DOMAIN)
        )
    )

    # 2. Tashqi brauzerda ochish va bir martalik kirish havolasi
    builder.row(
        InlineKeyboardButton(
            text="🔗 Brauzerda ochish",
            url=settings.DOMAIN
        ),
        InlineKeyboardButton(
            text="🔑 1-bosishda kirish havolasi",
            callback_data="generate_login_link"
        )
    )

    return builder.as_markup()


def get_file_action_inline_keyboard(file_id: int) -> InlineKeyboardMarkup:
    """Alohida fayl yuborilganda uning ostidagi amallar tugmalari."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📥 Brauzer orqali yuklab olish",
            url=f"{settings.DOMAIN}/api/files/{file_id}/download"
        )
    )
    return builder.as_markup()
