# -*- coding: utf-8 -*-
"""
Foldex Reply Keyboard moduli.
Papkalar ierarxiyasini Reply klaviatura tugmalari sifatida dinamik
yaratadi. Ota papkaga qaytish (⬅️ Orqaga), Bosh menyu (🏠),
barcha fayllarni bir bosishda yuborish (📤 Hammasini yuborish)
va veb-panelga o'tish tugmalarini shakllantiradi.
"""

from typing import List
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.models.file_item import FileItem
from app.models.folder import Folder


def build_folder_reply_keyboard(
    subfolders: List[Folder],
    files: List[FileItem],
    has_parent: bool = False
) -> ReplyKeyboardMarkup:
    """
    Joriy papka holatiga mos Reply Keyboard yaratadi.
    - Ichki papkalar: 2 tadan qatorda
    - Fayllar: 1 tadan qatorda
    - Boshqaruv tugmalari: Orqaga, Bosh menyu, Hammasini yuborish
    """
    builder = ReplyKeyboardBuilder()

    # 1. Ichki papkalar tugmalari (har bir qatorda 2 tadan)
    folder_buttons = [
        KeyboardButton(text=f"{f.icon} {f.name}")
        for f in subfolders
    ]
    if folder_buttons:
        builder.row(*folder_buttons, width=2)

    # 2. Ushbu papkadagi fayllar tugmalari (har bir qatorda 1 tadan)
    file_buttons = [
        KeyboardButton(text=f"📄 {file.name}")
        for file in files
    ]
    if file_buttons:
        builder.row(*file_buttons, width=1)

    # 3. Fayllar mavjud bo'lsa "Hammasini yuborish" tugmasi
    action_buttons = []
    if files:
        action_buttons.append(KeyboardButton(text="📤 Hammasini yuborish"))

    if action_buttons:
        builder.row(*action_buttons, width=1)

    # 4. Navigatsiya tugmalari (Orqaga, Bosh menyu)
    nav_buttons = []
    if has_parent:
        nav_buttons.append(KeyboardButton(text="⬅️ Orqaga"))
    nav_buttons.append(KeyboardButton(text="🏠 Bosh menyu"))
    builder.row(*nav_buttons, width=len(nav_buttons))

    # 5. Tezkor boshqaruv va veb-panel tugmalari
    builder.row(
        KeyboardButton(text="🌐 Admin Panel"),
        KeyboardButton(text="🔍 Qidiruv"),
        width=2
    )

    return builder.as_markup(resize_keyboard=True)
