import os
import uuid
import asyncio
import collections
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.exceptions import TelegramBadRequest

from core.database import db
from core.config import BOT_USERNAME
from services.converter import create_pdf_from_images, create_zip_from_files, text_to_docx, pdf_to_docx, merge_pdfs, split_pdf, add_watermark, office_to_pdf, image_to_text_docx
from services.lang import get_text

router = Router()
UPLOAD_DIR = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

HEAVY_TASK_SEMAPHORE = asyncio.Semaphore(2)
CHAT_LOCKS = collections.defaultdict(asyncio.Lock)

# Fayllar oqimi tugagach bitta "Qabul qilindi" xabari chiqarish uchun debounce
UPLOAD_DEBOUNCE = {}          # chat_id -> asyncio.Task
DEBOUNCE_DELAY = 1.5          # soniya: shu vaqt ichida yangi fayl kelmasa xabar chiqadi

def get_user_dir(chat_id: int):
    d = os.path.join(UPLOAD_DIR, str(chat_id))
    os.makedirs(d, exist_ok=True)
    return d

def count_files(user_dir: str):
    return len([name for name in os.listdir(user_dir) if "___" in name])

def clear_user_dir(user_dir: str, keep: str = None):
    for filename in os.listdir(user_dir):
        file_path = os.path.join(user_dir, filename)
        if os.path.isfile(file_path) and file_path != keep:
            os.unlink(file_path)

def clear_outputs(user_dir: str):
    # Yig'ilayotgan ("___") fayllarga tegmasdan eski natijalarni tozalash
    for filename in os.listdir(user_dir):
        if "___" in filename:
            continue
        file_path = os.path.join(user_dir, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)

def uid():
    return uuid.uuid4().hex

def safe_name(name: str):
    cleaned = "".join(c for c in (name or "") if c.isalnum() or c in '._- ').strip()
    return cleaned or f"hujjat_{uid()[:8]}"

def orig_name(path: str):
    # "uid___AsliyNom.pdf" -> "AsliyNom" (kengaytmasiz)
    base = os.path.basename(path)
    base = base.split("___", 1)[-1] if "___" in base else base
    return os.path.splitext(base)[0] or "hujjat"

def main_menu_kb(lang: str):
    # Konvertatsiya tugagach to'liq menyuni tiklash uchun (lazy import - sikl bo'lmasin)
    from handlers.user_handlers import get_main_keyboard
    return get_main_keyboard(lang)

def done_caption(prefix: str = "Tayyor!"):
    # Har bir natija ostidagi yagona izoh: reply orqali tahrirlash + bot username
    return (
        f"{prefix}\n\n"
        f"✏️ Fayl nomini o'zgartirish uchun shu xabarga Reply qilib yangi nom yozing.\n\n"
        f"🤖 @{BOT_USERNAME}"
    )

async def send_result(message: Message, physical_path: str, display_name: str, lang: str):
    """Natijani yuborish + rename uchun uni saqlab qo'yish (reply orqali tahrirlash)."""
    await message.answer_document(
        FSInputFile(physical_path, filename=display_name),
        caption=done_caption(),
        reply_markup=main_menu_kb(lang),
    )
    # Faqat natijani qoldirib, kirish/oraliq fayllarni tozalaymiz
    clear_user_dir(get_user_dir(message.chat.id), keep=physical_path)
    await db.update_user(message.chat.id, mode=None, temp_data=physical_path)

async def _show_count_message(bot, chat_id: int):
    """Fayllar oqimi tinchigach (DEBOUNCE_DELAY) yakuniy son bilan bitta xabar chiqaradi."""
    try:
        await asyncio.sleep(DEBOUNCE_DELAY)
    except asyncio.CancelledError:
        return  # yangi fayl keldi -> bu urinish bekor qilindi, keyingisi chiqaradi

    user_dir = get_user_dir(chat_id)
    count = count_files(user_dir)
    if count == 0:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"YAKUNLASH ({count})", callback_data="finish_upload")]])
    text = f"Qabul qilindi: {count} ta fayl. Davom etishingiz mumkin yoki YAKUNLASH ni bosing."

    async with CHAT_LOCKS[chat_id]:
        user = await db.get_user(chat_id)
        last_msg_id = user.get('last_msg_id') if user else None
        if last_msg_id:
            try:
                await bot.edit_message_text(chat_id=chat_id, message_id=last_msg_id, text=text, reply_markup=kb)
                return
            except TelegramBadRequest as e:
                if "not modified" in str(e).lower():
                    return
            except Exception:
                pass
        sent_msg = await bot.send_message(chat_id, text, reply_markup=kb)
        await db.update_user(chat_id, last_msg_id=sent_msg.message_id)

def schedule_count_message(bot, chat_id: int):
    task = UPLOAD_DEBOUNCE.get(chat_id)
    if task and not task.done():
        task.cancel()
    UPLOAD_DEBOUNCE[chat_id] = asyncio.create_task(_show_count_message(bot, chat_id))

@router.message(F.document | F.photo | F.video | F.audio)
async def handle_files(message: Message):
    user = await db.get_user(message.chat.id)
    if not user: return
    lang = user.get('lang') if user.get('lang') else 'uz'
    mode = user.get('mode')
    user_dir = get_user_dir(message.chat.id)

    if user.get('finished'):
        clear_user_dir(user_dir)
        await db.update_user(message.chat.id, finished=False)

    lock = CHAT_LOCKS[message.chat.id]

    if mode == 'pdf_to_docx' and message.document:
        if lock.locked():
            await message.answer("Oldingi jarayoningiz hali tugamadi, kuting...")
            return
        if not (message.document.file_name or '').lower().endswith('.pdf'):
            await message.answer("PDF yuboring!")
            return
        msg = await message.answer("Navbat kutilmoqda...")
        if HEAVY_TASK_SEMAPHORE.locked():
            await msg.edit_text("Server hozir band. Navbatingizni kuting...")

        async with lock, HEAVY_TASK_SEMAPHORE:
            await msg.edit_text("Kuting, konvertatsiya qilinmoqda...")
            clear_outputs(user_dir)
            base = safe_name(os.path.splitext(message.document.file_name)[0])
            in_path = os.path.join(user_dir, f"in_{uid()}.pdf")
            out_path = os.path.join(user_dir, f"out_{uid()}.docx")
            await message.bot.download(message.document.file_id, destination=in_path)
            ok = await asyncio.to_thread(pdf_to_docx, in_path, out_path)
            if ok:
                await send_result(message, out_path, f"{base}.docx", lang)
            else:
                await msg.edit_text("Xatolik yuz berdi.")
                clear_user_dir(user_dir)
                await db.update_user(message.chat.id, mode=None, temp_data=None)
        return

    if mode == 'office_to_pdf' and message.document:
        if lock.locked():
            await message.answer("Oldingi jarayoningiz hali tugamadi, kuting...")
            return
        ext = (message.document.file_name or '').lower().split('.')[-1]
        if ext not in ['docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt']:
            await message.answer("Faqat Word, Excel yoki PowerPoint fayl yuboring!")
            return
        msg = await message.answer("Navbat kutilmoqda...")
        if HEAVY_TASK_SEMAPHORE.locked():
            await msg.edit_text("Server hozir band. Navbatingizni kuting...")

        async with lock, HEAVY_TASK_SEMAPHORE:
            await msg.edit_text("Konvertatsiya qilinmoqda, kutib turing...")
            clear_outputs(user_dir)
            base = safe_name(os.path.splitext(message.document.file_name)[0])
            in_path = os.path.join(user_dir, f"in_{uid()}.{ext}")
            await message.bot.download(message.document.file_id, destination=in_path)
            out_pdf = await asyncio.to_thread(office_to_pdf, in_path, user_dir)
            if out_pdf:
                await send_result(message, out_pdf, f"{base}.pdf", lang)
            else:
                await msg.edit_text("Xatolik yuz berdi.")
                clear_user_dir(user_dir)
                await db.update_user(message.chat.id, mode=None, temp_data=None)
        return

    if mode == 'ocr' and message.photo:
        if lock.locked():
            await message.answer("Oldingi jarayoningiz hali tugamadi, kuting...")
            return
        msg = await message.answer("Navbat kutilmoqda...")
        if HEAVY_TASK_SEMAPHORE.locked():
            await msg.edit_text("Server hozir band. Navbatingizni kuting...")

        async with lock, HEAVY_TASK_SEMAPHORE:
            await msg.edit_text("Skaner qilinmoqda (OCR), kuting...")
            clear_outputs(user_dir)
            in_path = os.path.join(user_dir, f"img_{uid()}.jpg")
            out_path = os.path.join(user_dir, f"ocr_{uid()}.docx")
            await message.bot.download(message.photo[-1].file_id, destination=in_path)

            lang_map = {'uz': 'uzb', 'ru': 'rus', 'en': 'eng'}
            ocr_lang = lang_map.get(lang, 'uzb')

            ok = await asyncio.to_thread(image_to_text_docx, in_path, out_path, ocr_lang)
            if ok:
                await send_result(message, out_path, f"skan_{uid()[:6]}.docx", lang)
            else:
                await msg.edit_text("Rasmdan matn o'qib bo'lmadi.")
                clear_user_dir(user_dir)
                await db.update_user(message.chat.id, mode=None, temp_data=None)
        return

    if mode == 'split_pdf' and message.document:
        if not (message.document.file_name or '').lower().endswith('.pdf'):
            await message.answer("PDF yuboring!")
            return
        clear_outputs(user_dir)
        in_path = os.path.join(user_dir, f"{uid()}___{safe_name(message.document.file_name)}")
        await message.bot.download(message.document.file_id, destination=in_path)
        await db.update_user(message.chat.id, temp_data=in_path)
        await message.answer("Endi menga qirqib olinadigan sahifalar oralig'ini yuboring.\nMasalan: 1-5")
        return

    if mode == 'watermark_pdf' and message.document:
        if not (message.document.file_name or '').lower().endswith('.pdf'):
            await message.answer("PDF yuboring!")
            return
        clear_outputs(user_dir)
        in_path = os.path.join(user_dir, f"{uid()}___{safe_name(message.document.file_name)}")
        await message.bot.download(message.document.file_id, destination=in_path)
        await db.update_user(message.chat.id, temp_data=in_path)
        await message.answer("Endi PDF orqasiga bosiladigan matnni yuboring (Watermark):")
        return

    if mode is None:
        mode = 'pdf' if message.photo else 'zip'
        await db.update_user(message.chat.id, mode=mode)
    elif mode == 'pdf' and not message.photo:
        mode = 'zip'
        await db.update_user(message.chat.id, mode=mode)

    # Collect rejimi: oldingi bitta-konvertatsiya natijasi qolgan bo'lsa tozalaymiz
    # (reply-rename eski faylga noto'g'ri ishlamasligi uchun)
    if user.get('temp_data'):
        clear_outputs(user_dir)
        await db.update_user(message.chat.id, temp_data=None)

    file_id = None
    file_name = f"file_{uid()}"
    if message.photo:
        file_id = message.photo[-1].file_id; file_name += ".jpg"
    elif message.document:
        file_id = message.document.file_id; file_name = message.document.file_name or f"file_{uid()}"
    elif message.video:
        file_id = message.video.file_id; file_name = message.video.file_name or f"video_{uid()}.mp4"
    elif message.audio:
        file_id = message.audio.file_id; file_name = message.audio.file_name or f"audio_{uid()}.mp3"

    if file_id:
        save_path = os.path.join(user_dir, f"{uid()}___{safe_name(file_name)}")
        await message.bot.download(file_id, destination=save_path)

    # Har fayl uchun alohida xabar chiqarmaymiz: oqim tinchigach (debounce) bitta
    # xabar yakuniy son bilan chiqadi.
    schedule_count_message(message.bot, message.chat.id)

@router.callback_query(F.data == "finish_upload")
async def finish_upload_callback(callback: CallbackQuery):
    await callback.answer()
    user = await db.get_user(callback.message.chat.id)
    if not user: return

    lock = CHAT_LOCKS[callback.message.chat.id]
    if lock.locked():
        await callback.message.edit_text("Jarayon allaqachon davom etmoqda, kuting...")
        return

    if HEAVY_TASK_SEMAPHORE.locked():
        await callback.message.edit_text("Server hozir band. Navbatingizni kuting...")
    else:
        await callback.message.edit_text("Jarayon ketmoqda...")

    async with lock, HEAVY_TASK_SEMAPHORE:
        await process_finish_with_bot(callback.bot, callback.message.chat.id)

    await db.update_user(callback.message.chat.id, finished=True, last_msg_id=None)
    try: await callback.message.delete()
    except: pass

async def process_finish_with_bot(bot, chat_id: int, custom_name: str = None):
    user_dir = get_user_dir(chat_id)
    files = sorted([os.path.join(user_dir, f) for f in os.listdir(user_dir) if "___" in f])
    if not files: return

    # Standart nom: birinchi yuborilgan faylning asl nomi
    if not custom_name:
        custom_name = safe_name(orig_name(files[0]))

    user = await db.get_user(chat_id)
    mode = user.get('mode')

    if mode == 'merge_pdf':
        out_pdf = os.path.join(user_dir, 'merged.pdf')
        ok = await asyncio.to_thread(merge_pdfs, files, out_pdf)
        if ok:
            await bot.send_document(chat_id, FSInputFile(out_pdf, filename=f"{custom_name}.pdf"), caption=done_caption())
        else:
            await bot.send_message(chat_id, "Xatolik yuz berdi.")
        clear_user_dir(user_dir)
        await db.update_user(chat_id, mode=None)
        return

    has_images = any(f.lower().endswith(('.jpg', '.jpeg', '.png')) for f in files)
    if has_images and (mode == 'pdf' or mode is None):
        out_pdf = os.path.join(user_dir, 'output.pdf')
        if await asyncio.to_thread(create_pdf_from_images, files, out_pdf):
            await bot.send_document(chat_id, FSInputFile(out_pdf, filename=f"{custom_name}.pdf"), caption=done_caption())
    else:
        out_zip = os.path.join(user_dir, 'output.zip')
        if await asyncio.to_thread(create_zip_from_files, files, out_zip):
            await bot.send_document(chat_id, FSInputFile(out_zip, filename=f"{custom_name}.zip"), caption=done_caption())

@router.message(F.text, ~F.text.startswith('/'))
async def process_text_reply(message: Message):
    user = await db.get_user(message.chat.id)
    if not user: return
    mode = user.get('mode')
    lang = user.get('lang') if user.get('lang') else 'uz'

    if mode == 'text_to_doc':
        user_dir = get_user_dir(message.chat.id)
        clear_outputs(user_dir)
        out_path = os.path.join(user_dir, f"matn_{uid()}.docx")
        await asyncio.to_thread(text_to_docx, message.text, out_path)
        await send_result(message, out_path, "matn.docx", lang)
        return

    if mode == 'split_pdf':
        in_path = user.get('temp_data')
        if not in_path or not os.path.exists(in_path):
            await message.answer("Fayl topilmadi, boshqatdan yuboring.")
            return
        try:
            start, end = map(int, message.text.split('-'))
        except Exception:
            await message.answer("Noto'g'ri format! Iltimos '1-5' kabi yozing.")
            return
        user_dir = get_user_dir(message.chat.id)
        out_path = os.path.join(user_dir, f"split_{uid()}.pdf")
        if await asyncio.to_thread(split_pdf, in_path, out_path, start, end):
            await send_result(message, out_path, f"{safe_name(orig_name(in_path))}_{start}-{end}.pdf", lang)
        else:
            await message.answer("PDF ni qirqishda xato (sahifalar oralig'ini tekshiring).")
        return

    if mode == 'watermark_pdf':
        in_path = user.get('temp_data')
        if not in_path or not os.path.exists(in_path):
            return
        user_dir = get_user_dir(message.chat.id)
        out_path = os.path.join(user_dir, f"wm_{uid()}.pdf")
        if await asyncio.to_thread(add_watermark, in_path, out_path, message.text):
            await send_result(message, out_path, f"{safe_name(orig_name(in_path))}_wm.pdf", lang)
        else:
            await message.answer("Xatolik yuz berdi.")
        return

    if message.reply_to_message:
        # 1) Bitta konvertatsiya natijasini reply orqali qayta nomlash
        last = user.get('temp_data')
        if last and os.path.isfile(last) and "___" not in os.path.basename(last):
            ext = os.path.splitext(last)[1] or ".dat"
            await message.answer_document(
                FSInputFile(last, filename=f"{safe_name(message.text.strip())}{ext}"),
                caption=done_caption(),
                reply_markup=main_menu_kb(lang),
            )
            return
        # 2) Yig'ilgan fayllar natijasini qayta nomlash (rasm->PDF / ZIP / merge)
        user_dir = get_user_dir(message.chat.id)
        if count_files(user_dir) > 0:
            lock = CHAT_LOCKS[message.chat.id]
            if lock.locked():
                await message.answer("Jarayon allaqachon davom etmoqda, kuting...")
                return
            async with lock:
                await process_finish_with_bot(message.bot, message.chat.id, safe_name(message.text.strip()))
            return
