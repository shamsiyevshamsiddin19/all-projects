# -*- coding: utf-8 -*-
"""
Foldex Reply Keyboard moduli.
Papkalar ierarxiyasini Reply klaviatura tugmalari sifatida dinamik
yaratadi. Ota papkaga qaytish (⬅️ Orqaga), Bosh menyu (🏠),
barcha fayllarni bir bosishda yuborish (📤 Hammasini yuborish)
va veb-panelga o'tish tugmalarini shakllantiradi.
"""

from typing import List, Union
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.models.file_item import FileItem
from app.models.folder import Folder


def build_folder_reply_keyboard(
    subfolders: List[Folder],
    files: List[FileItem],
    has_parent: bool = False
) -> Union[ReplyKeyboardMarkup, ReplyKeyboardRemove]:
    """
    Joriy papka holatiga mos Reply Keyboard yaratadi.
    - Ichki papkalar: 2 tadan qatorda
    - Fayllar: 1 tadan qatorda
    - Amal tugmalari: Hammasini yuborish, Orqaga
    - Eslatma: Admin panel, Bosh sahifa va Qidiruv tugmalari reply keyboarddan
      olib tashlangan, ular komanda orqali (/admin, /home, /search) ishlaydi.
    """
    builder = ReplyKeyboardBuilder()
    has_any_button = False

    # 1. Ichki papkalar tugmalari (har bir qatorda 2 tadan)
    folder_buttons = [
        KeyboardButton(text=f"{f.icon} {f.name}")
        for f in subfolders
    ]
    if folder_buttons:
        builder.row(*folder_buttons, width=2)
        has_any_button = True

    # 2. Ushbu papkadagi fayllar tugmalari (har bir qatorda 1 tadan)
    file_buttons = [
        KeyboardButton(text=f"📄 {file.name}")
        for file in files
    ]
    if file_buttons:
        builder.row(*file_buttons, width=1)
        has_any_button = True

    # 3. Fayllar mavjud bo'lsa "Hammasini yuborish" tugmasi
    if files:
        builder.row(KeyboardButton(text="📤 Hammasini yuborish"), width=1)
        has_any_button = True

    # 4. Agar ichki papkada bo'lsa "⬅️ Orqaga" navigatsiya tugmasi
    if has_parent:
        builder.row(KeyboardButton(text="⬅️ Orqaga"), width=1)
        has_any_button = True

    # Agar birorta ham tugma bo'lmasa, reply keyboardni olib tashlash
    if not has_any_button:
        return ReplyKeyboardRemove()

    return builder.as_markup(resize_keyboard=True)
