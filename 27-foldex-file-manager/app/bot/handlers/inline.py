# -*- coding: utf-8 -*-
"""
Foldex Telegram Inline Mode Handleri.
Foydalanuvchi istalgan chatda @bot_username orqali chaqirganda
papkalar bo'ylab interaktiv navigatsiya qilish, ichki papkalarni ochish,
fayllarni cached formatda tezkor yuborish va '📤 Hammasini yuborish' amallarini bajaradi.
"""

from typing import List, Union
from aiogram import Router
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResult,
    InlineQueryResultArticle,
    InlineQueryResultCachedAudio,
    InlineQueryResultCachedDocument,
    InlineQueryResultCachedPhoto,
    InlineQueryResultCachedVideo,
    InputTextMessageContent
)
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.file_item import FileItem
from app.models.folder import Folder
from app.schemas.file_item import format_bytes
from app.services.file_service import FileService
from app.services.folder_service import FolderService

router = Router(name="inline_router")


@router.inline_query()
async def handle_inline_explorer(inline_query: InlineQuery):
    """
    Inline qidiruv va papkalar navigatsiyasi.
    1. Bo'sh so'rov: Asosiy (ildiz) papkalar ro'yxati chiqadi.
    2. 'folder:<id>': O'sha papkaning ichidagi subfolderlar, fayllar va 'Hammasini yuborish' chiqadi.
    3. Matnli qidiruv: Fayl va papkalar bo'ylab qidiruv natijalari chiqadi.
    """
    # Xavfsizlik: Faqat settings.TELEGRAM_ADMIN_ID
    if inline_query.from_user.id != settings.TELEGRAM_ADMIN_ID:
        unauthorized = InlineQueryResultArticle(
            id="forbidden",
            title="⛔ Kirish huquqi mavjud emas",
            description="Ushbu bot shaxsiy fayl menejeri bo'lib, begona foydalanuvchilarga xizmat ko'rsatmaydi.",
            input_message_content=InputTextMessageContent(
                message_text="⛔ Ushbu bot faqat administrator uchun mo'ljallangan."
            )
        )
        return await inline_query.answer(results=[unauthorized], cache_time=1, is_personal=True)

    query = inline_query.query.strip()
    results: List[InlineQueryResult] = []

    async with async_session_maker() as db:
        # =====================================================================
        # 1-HOLAT: Muayyan papka ichiga kirilgan (folder:<id>)
        # =====================================================================
        if query.startswith("folder:") or query.startswith("f:"):
            try:
                folder_id_str = query.split(":")[1].strip()
                folder_id = int(folder_id_str)
            except (IndexError, ValueError):
                folder_id = None

            if folder_id is not None:
                current_folder = await FolderService.get_by_id(db, folder_id)
                if current_folder:
                    subfolders = await FolderService.get_subfolders(db, folder_id)
                    files = await FileService.get_files_by_folder(db, folder_id)
                    crumbs = await FolderService.get_breadcrumbs(db, folder_id)
                    path_str = " / ".join([c.name for c in crumbs])

                    # a) ⬅️ Orqaga qaytish tugmasi
                    parent_query = f"folder:{current_folder.parent_id}" if current_folder.parent_id else ""
                    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text="⬅️ Yuqoriga qaytish",
                            switch_inline_query_current_chat=parent_query
                        )
                    ]])
                    results.append(
                        InlineQueryResultArticle(
                            id=f"back_{folder_id}",
                            title=f"⬅️ Orqaga ({'Bosh sahifa' if not current_folder.parent_id else 'Ota papka'})",
                            description=f"Hozir: {path_str}",
                            reply_markup=back_keyboard,
                            input_message_content=InputTextMessageContent(
                                message_text=f"📂 <b>{current_folder.name}</b> papkasidan chiqildi.\n📍 <i>{path_str}</i>"
                            )
                        )
                    )

                    # b) 📤 Hammasini yuborish amali
                    if files:
                        file_links_text = [
                            f"📂 <b>{current_folder.name}</b> papkasidagi barcha fayllar ({len(files)} ta):\n",
                            f"📍 <i>{path_str}</i>\n"
                        ]
                        for idx, fl in enumerate(files, 1):
                            file_links_text.append(
                                f"{idx}. <b>{fl.name}</b> (<code>{format_bytes(fl.file_size)}</code>) — "
                                f"<a href=\"{settings.DOMAIN}/api/files/{fl.id}/download\">Yuklab olish</a>"
                            )

                        results.append(
                            InlineQueryResultArticle(
                                id=f"send_all_{folder_id}",
                                title=f"📤 Hammasini yuborish ({len(files)} ta fayl)",
                                description=f"Ushbu papkadagi barcha {len(files)} ta fayl ro'yxatini jo'natish",
                                input_message_content=InputTextMessageContent(
                                    message_text="\n".join(file_links_text),
                                    parse_mode="HTML",
                                    disable_web_page_preview=True
                                )
                            )
                        )

                    # c) Ichki papkalar (subfolders)
                    for sf in subfolders:
                        sf_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(
                                text=f"📂 {sf.name} ichiga kirish",
                                switch_inline_query_current_chat=f"folder:{sf.id}"
                            )
                        ]])
                        results.append(
                            InlineQueryResultArticle(
                                id=f"subfolder_{sf.id}",
                                title=f"{sf.icon} {sf.name}",
                                description="Ichki papkani ochish uchun bosing",
                                reply_markup=sf_keyboard,
                                input_message_content=InputTextMessageContent(
                                    message_text=f"📂 Tanlangan papka: <b>{sf.name}</b>\n📍 Joylashuv: <i>{path_str} / {sf.name}</i>"
                                )
                            )
                        )

                    # d) Ushbu papkadagi fayllar
                    for fl in files:
                        caption = f"📁 <b>{fl.name}</b>\n💾 Hajmi: {format_bytes(fl.file_size)}"

                        if fl.telegram_file_id:
                            # Telegram keshidagi file_id mavjud bo'lsa
                            if fl.file_type == "photo":
                                results.append(InlineQueryResultCachedPhoto(
                                    id=f"file_photo_{fl.id}",
                                    photo_file_id=fl.telegram_file_id,
                                    title=fl.name,
                                    caption=caption,
                                    parse_mode="HTML"
                                ))
                            elif fl.file_type == "video":
                                results.append(InlineQueryResultCachedVideo(
                                    id=f"file_video_{fl.id}",
                                    video_file_id=fl.telegram_file_id,
                                    title=fl.name,
                                    caption=caption,
                                    parse_mode="HTML"
                                ))
                            elif fl.file_type == "audio":
                                results.append(InlineQueryResultCachedAudio(
                                    id=f"file_audio_{fl.id}",
                                    audio_file_id=fl.telegram_file_id,
                                    caption=caption,
                                    parse_mode="HTML"
                                ))
                            else:
                                results.append(InlineQueryResultCachedDocument(
                                    id=f"file_doc_{fl.id}",
                                    title=fl.name,
                                    document_file_id=fl.telegram_file_id,
                                    caption=caption,
                                    parse_mode="HTML"
                                ))
                        else:
                            # Telegram file_id bo'lmasa, havola orqali yuklab olish shaklida
                            dl_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                                InlineKeyboardButton(
                                    text="📥 Yuklab olish",
                                    url=f"{settings.DOMAIN}/api/files/{fl.id}/download"
                                )
                            ]])
                            results.append(InlineQueryResultArticle(
                                id=f"file_art_{fl.id}",
                                title=f"📄 {fl.name}",
                                description=f"Hajmi: {format_bytes(fl.file_size)}",
                                reply_markup=dl_keyboard,
                                input_message_content=InputTextMessageContent(
                                    message_text=(
                                        f"📁 <b>{fl.name}</b>\n"
                                        f"💾 Hajmi: {format_bytes(fl.file_size)}\n"
                                        f"🔗 <a href=\"{settings.DOMAIN}/api/files/{fl.id}/download\">Faylni yuklab olish</a>"
                                    ),
                                    parse_mode="HTML"
                                )
                            ))

        # =====================================================================
        # 2-HOLAT: So'rov bo'sh bo'lsa (Asosiy / Ildiz papkalar)
        # =====================================================================
        elif not query:
            root_folders = await FolderService.get_root_folders(db)
            root_files = await FileService.get_files_by_folder(db, None)

            # Asosiy papkalar
            for rf in root_folders:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=f"📂 {rf.name} papkasini ochish",
                        switch_inline_query_current_chat=f"folder:{rf.id}"
                    )
                ]])
                results.append(
                    InlineQueryResultArticle(
                        id=f"root_folder_{rf.id}",
                        title=f"{rf.icon} {rf.name}",
                        description=rf.description or "Papkani ko'rish uchun bosing",
                        reply_markup=keyboard,
                        input_message_content=InputTextMessageContent(
                            message_text=f"📂 Tanlangan papka: <b>{rf.name}</b>\n<i>Tarkibini ko'rish uchun pastdagi tugmani bosing.</i>",
                            parse_mode="HTML"
                        )
                    )
                )

            # Ildizdagi mavjud fayllar
            for rf_file in root_files[:10]:
                if rf_file.telegram_file_id:
                    results.append(InlineQueryResultCachedDocument(
                        id=f"root_file_{rf_file.id}",
                        title=rf_file.name,
                        document_file_id=rf_file.telegram_file_id,
                        caption=f"📁 <b>{rf_file.name}</b>\n💾 {format_bytes(rf_file.file_size)}",
                        parse_mode="HTML"
                    ))

        # =====================================================================
        # 3-HOLAT: Qidiruv matni kiritilgan bo'lsa
        # =====================================================================
        else:
            # Fayllar bo'yicha global qidiruv
            found_files = await FileService.search_all_files(db, query)
            for fl in found_files:
                caption = f"🔍 <b>{fl.name}</b>\n💾 Hajmi: {format_bytes(fl.file_size)}"

                if fl.telegram_file_id:
                    results.append(InlineQueryResultCachedDocument(
                        id=f"search_doc_{fl.id}",
                        title=fl.name,
                        document_file_id=fl.telegram_file_id,
                        caption=caption,
                        parse_mode="HTML"
                    ))
                else:
                    dl_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text="📥 Yuklab olish",
                            url=f"{settings.DOMAIN}/api/files/{fl.id}/download"
                        )
                    ]])
                    results.append(InlineQueryResultArticle(
                        id=f"search_art_{fl.id}",
                        title=f"📄 {fl.name}",
                        description=f"Hajmi: {format_bytes(fl.file_size)}",
                        reply_markup=dl_keyboard,
                        input_message_content=InputTextMessageContent(
                            message_text=f"📁 <b>{fl.name}</b>\n💾 {format_bytes(fl.file_size)}\n🔗 <a href=\"{settings.DOMAIN}/api/files/{fl.id}/download\">Yuklab olish</a>",
                            parse_mode="HTML"
                        )
                    ))

            if not results:
                results.append(InlineQueryResultArticle(
                    id="not_found",
                    title="🔍 Hech narsa topilmadi",
                    description=f"«{query}» so'rovi bo'yicha fayl yoki papka mavjud emas.",
                    input_message_content=InputTextMessageContent(
                        message_text=f"🔍 «{query}» bo'yicha hech qanday fayl topilmadi."
                    )
                ))

    # Telegram API cheklovi: maksimal 50 ta natija
    await inline_query.answer(results=results[:50], cache_time=1, is_personal=True)
