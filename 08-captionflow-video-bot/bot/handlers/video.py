"""Video/havola -> rejim -> til -> subtitr oqimi (arxitektura 3.1, 4.2, 5.7).

Celery worker'ga topshirish: bot videoni yuklab oladi, keyin
process_video_task ni Celery'ga yuboradi. Worker alohida jarayonda
ishlab, natijani Telegram orqali yuboradi.
"""
from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import time
import uuid

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)

from config import settings
from bot.keyboards import (
    ALL_MODES,
    language_keyboard,
    mode_card_keyboard,
    mode_caption,
    mode_photo_path,
    target_lang_keyboard,
    transcript_lang_keyboard,
)
from worker.pipeline import (
    cleanup_all,
    job_paths,
)
from worker.download import detect_source, download_video, extract_url, probe_url
from web.server import publish_file, publish_input
from db.crud import (
    count_active_videos,
    create_payment,
    create_video,
    effective_plan,
    finish_video,
    get_effective_settings,
    get_effective_tariff,
    get_or_create_user,
    get_user_by_id,
)
from access import check_can_process

logger = logging.getLogger(__name__)
router = Router()

# Tarjima talab qiladigan rejimlar (maqsad tilini so'raydi)
_TRANSLATE_MODES = ("translate", "dual", "dual_vocab", "vocabulary")

# "Shu videoga boshqa rejim" — video havolasini qisqa token bilan xotirada
# saqlaymiz (state tozalangach ham qayta ishlatish uchun). Eng so'nggi ~500 ta.
_REUSE: dict[str, dict] = {}


def _store_reuse(info: dict) -> str:
    token = uuid.uuid4().hex[:10]
    _REUSE[token] = info
    if len(_REUSE) > 500:
        for k in list(_REUSE)[:100]:
            _REUSE.pop(k, None)
    return token


def _mode_head(is_long: bool, duration: int) -> str:
    """Rejim tanlash xabari boshi — uzun video bo'lsa to'lov haqida ogohlantirish."""
    if not is_long:
        return "✅ <b>Video qabul qilindi!</b>\n\n"
    minutes = duration // 60
    price_str = f"{settings.price_long_video:,}".replace(",", " ")
    return (
        "✅ <b>Video qabul qilindi!</b>\n\n"
        f"⏱ Bu video <b>{minutes} daqiqa</b> — {settings.long_video_minutes} "
        "daqiqadan katta.\n"
        f"💳 Bunday uzun videolar <b>bitta video uchun bir martalik "
        f"{price_str} so'm</b> to'lov bilan ishlanadi.\n\n"
        "Avval rejimni tanlang — keyin to'lov havolasi beriladi 👇\n\n"
    )


def _long_badge(is_long: bool) -> str:
    """Navigatsiya paytida (keyingi/oldingi rejim) qisqa eslatma."""
    if not is_long:
        return ""
    return "💳 <i>Uzun video — bir martalik to'lov talab qilinadi</i>\n\n"


def _est_time(duration: float, mode: str) -> str:
    """Taxminiy ishlov vaqti (ultrafast preset asosida)."""
    if mode == "audio":
        # Faqat ffmpeg MP3 ajratish — AI/transkripsiya yo'q, eng tez
        secs = int(duration * 0.05 + 8)
    elif mode in ("transcript", "vocabulary"):
        # Video kuydirilmaydi — faqat transkripsiya (+ lug'atда tarjima)
        secs = int(duration * 0.15 + 15 + (10 if mode == "vocabulary" else 0))
    else:
        secs = int(duration * 0.5 + 20 + (8 if mode in _TRANSLATE_MODES else 0))
    if secs < 60:
        return f"~{secs} soniya"
    return f"~{secs // 60} daqiqa {secs % 60} soniya"


async def _deliver_result(message: Message, kind: str, out_path: str, elapsed_str: str) -> None:
    """Bitta natijani turiga qarab foydalanuvchiga yuboradi (ko'p rejim uchun ham)."""
    if kind == "srt":
        await message.reply_document(
            FSInputFile(out_path, filename="subtitle.srt"),
            caption=f"✅ .SRT fayl tayyor! ⏱ {elapsed_str}\n"
                    "📋 Istalgan subtitr muharririda oching.\n\n@subtitle_srtbot",
        )
        return

    if kind in ("text", "vocab"):
        base = out_path[:-4]  # ...txt -> ...
        try:
            with open(out_path, encoding="utf-8-sig") as f:
                content = f.read()
        except OSError:
            content = ""
        try:
            with open(base + ".title", encoding="utf-8-sig") as f:
                slug = f.read().strip()
        except OSError:
            slug = ""
        slug = slug or ("matn" if kind == "text" else "lugat")
        pdf_path = base + ".pdf"
        if kind == "text":
            head = f"📜 <b>Videodagi matn tayyor!</b> · ⏱ {elapsed_str}"
        else:
            n_words = len([ln for ln in content.splitlines() if ln.strip()])
            head = f"📚 <b>Lug'at tayyor!</b> · {n_words} ta so'z · ⏱ {elapsed_str}"
        preview = html.escape(content[:2500]) or "(bo'sh)"
        more = "\n\n… <i>to'liqi quyidagi fayllarda</i> 👇" if len(content) > 2500 else ""
        await message.answer(
            f"{head}\n\n<blockquote expandable>{preview}</blockquote>{more}",
            parse_mode="HTML",
        )
        await message.reply_document(FSInputFile(out_path, filename=f"{slug}.txt"))
        await message.reply_document(
            FSInputFile(pdf_path, filename=f"{slug}.pdf"),
            caption="⬇️ PDF yoki txt — qulayini oling\n\n@subtitle_srtbot",
        )
        return

    # Video — hajmga qarab Telegram yoki web havola
    out_mb = os.path.getsize(out_path) / (1024 * 1024)
    if out_mb > settings.max_send_mb:
        dl_url = publish_file(out_path)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬇️ Yuklab olish", url=dl_url)]]
        )
        await message.answer(
            f"🎬 Subtitr video tayyor! ⏱ {elapsed_str}\n\n"
            f"Video katta ({out_mb:.0f}MB) — havola orqali yuklab oling:\n{dl_url}",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
        return

    await message.reply_video(
        FSInputFile(out_path, filename="subtitled.mp4"),
        caption=f"🎉 Subtitr video tayyor! ✅ ⏱ {elapsed_str}\n\n@subtitle_srtbot",
    )


class VideoFlow(StatesGroup):
    waiting_mode = State()
    waiting_lang = State()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """FSM holatini bekor qilish (/cancel)."""
    current = await state.get_state()
    if current in (VideoFlow.waiting_mode, VideoFlow.waiting_lang):
        await state.clear()
        await message.answer("🚫 Bekor qilindi.\nYangi video yoki havola yuboring.")
        return
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    from db.base import async_session
    from sqlalchemy import select, func
    from db.models import Video
    
    async with async_session() as session:
        active = await session.scalar(
            select(func.count(Video.id)).where(
                Video.user_id == user.id, 
                Video.status.in_(("processing", "pending"))
            )
        )
        
    if active:
        await message.answer(
            "⏳ Sizning videongiz hali qayta ishlanmoqda.\n"
            "Jarayon tugaguncha kutish kerak — avtomatik to'xtaydi."
        )
        return
    await message.answer("Hozir bekor qilish uchun aktiv jarayon yo'q.")


@router.message(F.video)
async def on_video(message: Message, state: FSMContext) -> None:
    """Video keldi — limit tekshirib, rejim so'raymiz."""
    video = message.video
    duration = video.duration or 0

    user = await get_or_create_user(message.from_user.id, message.from_user.username)

    # 45+ daqiqalik video — oylik/kunlik limitga kirmaydi, bitta martalik
    # to'lov bilan ishlanadi (tarifdan qat'i nazar). Bloklangan user baribir rad etiladi.
    is_long = duration > settings.long_video_minutes * 60
    if is_long:
        if user.is_blocked:
            await message.reply("⛔ Hisobingiz bloklangan. Muammo bo'lsa admin bilan bog'laning.")
            return
    else:
        # Davomiylik + kunlik limit (rejimsiz)
        ok, reason = await check_can_process(user, duration, mode="")
        if not ok:
            await message.reply(reason)
            return

    size_mb = (video.file_size or 0) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        from web.miniapp import miniapp_open_button

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[miniapp_open_button()]])
        await message.reply(
            f"⚠️ Bu video {size_mb:.1f}MB — Bot API limiti {settings.max_upload_mb}MB.\n"
            "Katta videolarni Mini App orqali yuklang 👇",
            reply_markup=keyboard,
        )
        return

    tariff = await get_effective_tariff(effective_plan(user))
    await state.update_data(
        source_type="upload",
        file_id=video.file_id,
        duration=duration,
        user_db_id=user.id,
        is_long=is_long,
    )
    await state.set_state(VideoFlow.waiting_mode)
    allowed = [m for m in ALL_MODES if m in tariff.modes]
    await message.reply_photo(
        FSInputFile(mode_photo_path(allowed[0])),
        caption=_mode_head(is_long, duration) + mode_caption(allowed[0], 0, len(allowed)),
        reply_markup=mode_card_keyboard(allowed, 0),
        parse_mode="HTML",
    )


@router.message(F.text.func(detect_source))
async def on_url(message: Message, state: FSMContext) -> None:
    """YouTube/Instagram havolasi — metama'lumot olib, rejim so'raymiz."""
    url = extract_url(message.text)
    source = detect_source(message.text)
    if not url or not source:
        return

    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    if user.is_blocked:
        await message.reply("⛔ Hisobingiz bloklangan.")
        return

    status = await message.reply("🔎 Havola tekshirilmoqda...")
    try:
        info = await asyncio.to_thread(probe_url, url)
    except Exception as exc:
        logger.warning("Havolani tekshirib bo'lmadi: %s", url, exc_info=True)
        src_name = "Instagram" if source == "instagram" else "YouTube"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="⬇️ @taronabot'ni ochish",
                    url="https://t.me/taronabot",
                )
            ]]
        )
        await status.edit_text(
            f"😊 <b>{src_name} videosini to'g'ridan-to'g'ri ololmadim</b> — "
            "lekin hammasi joyida, bir necha soniyada hal qilamiz:\n\n"
            "1️⃣ <b>@taronabot</b>'ga o'sha havolani yuboring\n"
            "2️⃣ U yuklab bergan videoni <b>shu yerga qaytaring</b>\n"
            "3️⃣ Men unga darrov subtitr yozaman ✅",
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return

    duration = info["duration"]
    is_long = duration > settings.long_video_minutes * 60
    if not is_long:
        ok, reason = await check_can_process(user, duration, mode="")
        if not ok:
            await status.edit_text(reason)
            return

    tariff = await get_effective_tariff(effective_plan(user))
    await state.update_data(
        source_type=source, url=url, duration=duration, user_db_id=user.id,
        is_long=is_long,
    )
    await state.set_state(VideoFlow.waiting_mode)

    title = info.get("title") or ""
    head = f"🎬 <b>{html.escape(title)}</b>\n\n" if title else ""
    allowed = [m for m in ALL_MODES if m in tariff.modes]
    try:
        await status.delete()
    except Exception:
        pass
    await message.answer_photo(
        FSInputFile(mode_photo_path(allowed[0])),
        caption=head + _mode_head(is_long, duration) + mode_caption(allowed[0], 0, len(allowed)),
        reply_markup=mode_card_keyboard(allowed, 0),
        parse_mode="HTML",
    )


_MODE_NAMES = {
    "original": "Original",
    "translate": "🌐 Tarjima",
    "dual": "📑 Ikki qatlam",
    "dual_vocab": "🎓 Ikki qatlam + lug'at",
    "srt": "📄 .SRT fayl",
    "transcript": "📜 Matn",
    "vocabulary": "📚 Lug'at",
    "audio": "🎵 Audio",
}


async def _offer_subscription(call: CallbackQuery, mode: str) -> None:
    """Qulflangan rejim bosildi — obuna taklif qilamiz (Click tugmasi bilan)."""
    user = await get_or_create_user(call.from_user.id, call.from_user.username)
    eff = await get_effective_settings()
    amount = eff["price_basic"]
    mode_name = _MODE_NAMES.get(mode, mode)

    # To'lov sozlanmagan bo'lsa — oddiy taklif
    if not settings.click_configured:
        await call.message.answer(
            f"🔒 <b>{mode_name}</b> — bu rejim faqat obunachilarda.\n\n"
            "💎 Obuna bilan tarjima, ikki qatlam va .SRT ochiladi.\n"
            "👉 /subscribe",
            parse_mode="HTML",
        )
        return

    # BASIC to'lov yozuvi yaratib, to'g'ridan-to'g'ri Click havolasini beramiz
    payment_id = await create_payment(user.id, "basic", amount)
    url = settings.click_pay_url(f"SUBT{payment_id}", amount)
    amount_str = f"{amount:,}".replace(",", " ")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"💳 BASIC obuna — {amount_str} so'm", url=url,
            )],
            [InlineKeyboardButton(
                text="⭐ Boshqa tariflar", callback_data="show_plans",
            )],
        ]
    )
    await call.message.answer(
        f"🔒 <b>{mode_name}</b> — bu rejim faqat obunachilarda.\n\n"
        f"💎 <b>BASIC obuna</b> — {amount_str} so'm/oy bilan ochiladi:\n"
        "✅ Tarjima (o'zbek · rus · ingliz)\n"
        "✅ Ikki qatlam subtitr\n"
        "✅ .SRT fayl\n"
        "✅ Kuniga 10 ta video (30 daqiqagacha)\n\n"
        "Quyidagi tugmani bosing — Click ilovasida to'lang.\n"
        "To'lov tugagach obuna <b>avtomatik</b> faollashadi ✅",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(VideoFlow.waiting_mode, F.data.startswith("modenav:"))
async def on_mode_nav(call: CallbackQuery, state: FSMContext) -> None:
    """"Oldingi/Keyingi rejim" — kartani (rasm+tavsif) almashtiradi."""
    try:
        idx = int(call.data.split(":", 1)[1])
    except ValueError:
        await call.answer()
        return

    user = await get_or_create_user(call.from_user.id, call.from_user.username)
    tariff = await get_effective_tariff(effective_plan(user))
    allowed = [m for m in ALL_MODES if m in tariff.modes]
    idx = idx % len(allowed)
    mode = allowed[idx]

    data = await state.get_data()
    is_long = bool(data.get("is_long"))
    caption = _long_badge(is_long) + mode_caption(mode, idx, len(allowed))
    media = InputMediaPhoto(
        media=FSInputFile(mode_photo_path(mode)), caption=caption, parse_mode="HTML"
    )
    try:
        await call.message.edit_media(media=media, reply_markup=mode_card_keyboard(allowed, idx))
    except Exception:
        pass
    await call.answer()


@router.callback_query(VideoFlow.waiting_mode, F.data.startswith("mode:"))
async def on_mode(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Rejim tanlandi — ruxsat tekshirib, til so'raymiz yoki obuna taklif qilamiz."""
    mode = call.data.split(":", 1)[1]

    user = await get_or_create_user(call.from_user.id, call.from_user.username)
    tariff = await get_effective_tariff(effective_plan(user))
    if mode not in tariff.modes:
        # Qulflangan rejim — klaviaturani qoldiramiz (boshqa rejim tanlasin)
        await call.answer("🔒 Bu rejim obunachilarda", show_alert=False)
        await _offer_subscription(call, mode)
        return

    data0 = await state.get_data()
    is_long = bool(data0.get("is_long"))

    # Limit (bepul: har rejimga oyiga 3 ta, oyiga jami 10 ta) — uzun (to'lovli)
    # video oddiy limitlarga kirmaydi, shuning uchun bu tekshiruv o'tkaziladi.
    if not is_long:
        ok_lim, reason = await check_can_process(user, data0.get("duration", 0), mode=mode)
        if not ok_lim:
            await call.answer()
            await call.message.answer(reason, parse_mode="HTML", disable_web_page_preview=True)
            return

    await state.update_data(modes=[mode])
    await state.set_state(VideoFlow.waiting_lang)

    # AUDIO — til so'ralmaydi (faqat ovoz ajratiladi), darrov ishga tushiramiz
    if mode == "audio":
        await call.answer()
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        if is_long:
            await _offer_long_video_payment(call, state, "none")
        else:
            await _launch_job(call, state, bot, "none")
        return

    await call.answer()
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if mode == "transcript":
        await call.message.answer(
            "📜 Matnni <b>tarjima</b> qilaymi? Tilni tanlang yoki asl tilda qoldiring 👇",
            reply_markup=transcript_lang_keyboard(),
            parse_mode="HTML",
        )
    elif mode in _TRANSLATE_MODES:
        await call.message.answer(
            "🌐 Qaysi tilga tarjima qilinsin?",
            reply_markup=target_lang_keyboard(),
        )
    else:
        await call.message.answer(
            "🗣 Video qaysi tilda? (subtitr shu tilda bo'ladi)",
            reply_markup=language_keyboard(),
        )


@router.callback_query(VideoFlow.waiting_lang, F.data.startswith("lang:"))
async def on_language(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Til tanlandi — uzun (to'lovli) video bo'lsa to'lov havolasi, aks holda
    videoni yuklab Celery worker'ga topshiramiz."""
    lang = call.data.split(":", 1)[1]
    data = await state.get_data()
    if data.get("is_long"):
        await _offer_long_video_payment(call, state, lang)
    else:
        await _launch_job(call, state, bot, lang)


async def _launch_job(
    call: CallbackQuery, state: FSMContext, bot: Bot, lang: str
) -> None:
    """Videoni yuklab, Celery worker'ga topshiradi (til allaqachon aniq).

    Audio rejimida til so'ralmaydi — on_mode bu funksiyani lang="none" bilan
    to'g'ridan-to'g'ri chaqiradi."""
    user_tg_id = call.from_user.id

    data = await state.get_data()
    source_type = data.get("source_type", "upload")
    file_id = data.get("file_id")
    url = data.get("url")
    duration = data.get("duration", 0)
    user_db_id = data.get("user_db_id")
    modes = data.get("modes") or ["original"]
    await state.clear()

    if not user_db_id or not (file_id or url):
        await call.answer(
            "❌ Video topilmadi, iltimos videoni qaytadan yuboring.", show_alert=True
        )
        return

    await call.answer()
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await _submit_job(
        bot, chat_id=call.message.chat.id, user_tg_id=user_tg_id,
        source_type=source_type, file_id=file_id, url=url, duration=duration,
        user_db_id=user_db_id, modes=modes, lang=lang,
    )


async def _offer_long_video_payment(
    call: CallbackQuery, state: FSMContext, lang: str
) -> None:
    """45+ daqiqalik video — bitta martalik Click to'lov havolasini beradi.

    To'lov tasdiqlangach (web/click.py webhook) video avtomatik navbatga
    qo'yiladi — foydalanuvchi qayta hech narsa qilishi shart emas."""
    data = await state.get_data()
    source_type = data.get("source_type", "upload")
    file_id = data.get("file_id")
    url = data.get("url")
    duration = data.get("duration", 0)
    user_db_id = data.get("user_db_id")
    modes = data.get("modes") or ["original"]
    mode = modes[0]
    user_tg_id = call.from_user.id
    await state.clear()

    if not user_db_id or not (file_id or url):
        await call.answer(
            "❌ Video topilmadi, iltimos videoni qaytadan yuboring.", show_alert=True
        )
        return

    await call.answer()
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if not settings.click_configured:
        await call.message.answer(
            "💳 Uzun videolar uchun to'lov tizimi hozircha sozlanmagan.\n"
            "Admin bilan bog'laning: /help",
        )
        return

    amount = settings.price_long_video
    meta = json.dumps({
        "source_type": source_type, "file_id": file_id, "url": url,
        "duration": duration, "user_db_id": user_db_id, "mode": mode,
        "lang": lang, "telegram_id": user_tg_id,
    })
    payment_id = await create_payment(user_db_id, "longvideo", amount, meta=meta)
    pay_url = settings.click_pay_url(f"SUBT{payment_id}", amount)
    amount_str = f"{amount:,}".replace(",", " ")
    minutes = duration // 60

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"💳 To'lash — {amount_str} so'm", url=pay_url),
    ]])
    await call.message.answer(
        f"⏱ Bu video <b>{minutes} daqiqa</b> — {settings.long_video_minutes} "
        "daqiqadan katta.\n\n"
        f"💳 Bunday uzun videolar <b>bitta video uchun bir martalik "
        f"{amount_str} so'm</b> to'lov bilan ishlanadi.\n\n"
        "Quyidagi tugmani bosing — Click ilovasida to'lang.\n"
        "To'lov tugagach video <b>avtomatik</b> navbatga qo'yiladi va tayyor "
        "bo'lganda shu yerga yuboriladi ✅",
        reply_markup=kb, parse_mode="HTML",
    )


async def submit_long_video_job(bot: Bot, meta: dict) -> None:
    """To'lov tasdiqlangach (web/click.py webhook) uzun videoni navbatga qo'yadi.

    _offer_long_video_payment'da saqlangan meta (source_type/file_id yoki url,
    rejim, til, user) bilan to'g'ridan-to'g'ri _submit_job'ni chaqiradi —
    foydalanuvchi bilan qayta muloqot (FSM/callback) kerak emas."""
    telegram_id = meta["telegram_id"]
    try:
        await bot.send_message(
            telegram_id,
            "✅ To'lov qabul qilindi! Videongiz navbatga qo'shilmoqda...",
        )
    except Exception:
        logger.warning("Uzun video to'lov xabarini yuborib bo'lmadi: %s", telegram_id)
    await _submit_job(
        bot, chat_id=telegram_id, user_tg_id=telegram_id,
        source_type=meta["source_type"], file_id=meta.get("file_id"),
        url=meta.get("url"), duration=meta.get("duration", 0),
        user_db_id=meta["user_db_id"], modes=[meta["mode"]],
        lang=meta.get("lang") or "none",
    )


async def _submit_job(
    bot: Bot, *, chat_id: int, user_tg_id: int, source_type: str,
    file_id: str | None, url: str | None, duration: int, user_db_id: int,
    modes: list[str], lang: str,
) -> None:
    """Videoni yuklab, Celery worker'ga topshiradi (rejim+til allaqachon aniq).

    Oddiy callback oqimi (_launch_job) va to'lovdan keyingi uzun-video oqimi
    (submit_long_video_job, webhook orqali) ikkalasi ham shu funksiyani
    chaqiradi — CallbackQuery'ga bog'liq emas, faqat bot+chat_id kerak."""
    # Manba/tarjima tilini aniqlash
    if "transcript" in modes:
        # Matn: "asl tilda" (none) -> tarjimasiz; aks holda tanlangan tilga tarjima
        source_lang = "auto"
        target_lang = None if lang == "none" else lang
    elif any(m in _TRANSLATE_MODES for m in modes):
        source_lang = "auto"
        target_lang = lang
    else:
        source_lang = lang
        target_lang = None

    est = _est_time(duration or 0, modes[0])
    if len(modes) > 1:
        est += f", ×{len(modes)} rejim"

    job_id = uuid.uuid4().hex[:12]
    paths = job_paths(job_id)
    video_id = await create_video(
        user_db_id, ",".join(modes), duration,
        source_type=source_type, target_lang=target_lang,
    )

    # Video faylni yuklab olish (bot API yoki yt-dlp) — bot handler'da qilish shart
    # chunki file_id faqat bot API orqali ishlaydi
    status_msg = await bot.send_message(chat_id, f"⏳ Qabul qilindi! Video yuklanmoqda... ({est})")
    try:
        os.makedirs(settings.work_dir, exist_ok=True)
        if source_type == "upload":
            tg_file = await bot.get_file(file_id)
            if settings.local_bot_api:
                # Local server (--local): fayl allaqachon serverimiz diskida.
                # get_file KONTEYNER yo'lini beradi — host yo'liga o'girib, HTTP
                # yuklab olishsiz nusxalaymiz (tez), so'ng originalni o'chiramiz.
                import shutil

                from tg_session import local_to_host_path

                src = local_to_host_path(tg_file.file_path)
                await asyncio.to_thread(shutil.copy, src, paths["video"])
                try:
                    os.remove(src)
                except OSError:
                    pass
            else:
                await bot.download_file(tg_file.file_path, paths["video"])
        else:
            from worker import home_relay

            if source_type in ("youtube", "instagram") and home_relay.is_relay_user(user_tg_id):
                # Bu foydalanuvchi uchun YouTube/Instagram uy kompyuteri orqali
                # yuklanadi (datacenter IP blokini chetlab o'tish). Kompyuterdagi
                # skript ishlamasa (grace muddat o'tsa) — pastdagi except server-
                # tomon yuklashga QAYTA URINADI (foydalanuvchi tiqilib qolmasin).
                async def _relay_progress(text: str) -> None:
                    try:
                        await status_msg.edit_text(text)
                    except Exception:
                        pass

                try:
                    await home_relay.request_download(url, paths["video"], _relay_progress)
                except Exception as relay_exc:
                    # Kompyuter o'chiq yoki yuklay olmadi — server-tomon urinmaymiz
                    # (datacenter IP baribir bloklangan, behuda vaqt ketardi).
                    # "yuklab olinmadi" so'zi tashqi except'da @taronabot yo'riqnomasini
                    # ochadi (kompyuter yoniq bo'lsa bu yergacha yetib kelmaydi).
                    logger.info("Home relay ishlamadi (job %s): %s", job_id, relay_exc)
                    raise RuntimeError(
                        f"Video yuklab olinmadi (uy kompyuteri o'chiq): {relay_exc}"
                    )
            else:
                try:
                    await status_msg.edit_text("📥 Video havoladan yuklab olinmoqda...")
                except Exception:
                    pass
                await asyncio.to_thread(download_video, url, paths["video"])
    except Exception as exc:
        logger.exception("Video yuklab olishda xato (job %s)", job_id)
        await finish_video(video_id, "error", error_message=str(exc))
        err = str(exc)
        if "yuklab olinmadi" in err and source_type in ("youtube", "instagram"):
            src_name = "Instagram" if source_type == "instagram" else "YouTube"
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="⬇️ @taronabot'ni ochish",
                    url="https://t.me/taronabot",
                )
            ]])
            try:
                await status_msg.edit_text(
                    f"😔 <b>{src_name} videosini hozir to'g'ridan-to'g'ri ololmadim.</b>\n\n"
                    "1️⃣ <b>@taronabot</b>'ga o'sha havolani yuboring\n"
                    "2️⃣ U yuklab bergan videoni <b>shu yerga qaytaring</b>\n"
                    "3️⃣ Men unga darrov subtitr yozaman ✅",
                    reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True,
                )
            except Exception:
                pass
        else:
            try:
                await status_msg.edit_text(
                    "❌ Videoni yuklab olishda xatolik bo'ldi.\n"
                    "Qayta urinib ko'ring yoki /help."
                )
            except Exception:
                pass
        return

    # Celery worker'ga topshirish
    from worker.celery_app import process_video_task

    # Premium/Basic foydalanuvchilarga ustuvor navbat
    user = await get_user_by_id(user_db_id)
    plan = effective_plan(user) if user else "free"
    queue = "high" if plan in ("premium", "basic") else "default"

    # Kirish videoni masofaviy worker yuklab olishi uchun ulashamiz (master'ning
    # o'z worker'i lokal fayldan foydalanadi — havola faqat boshqa serverdagi
    # worker uchun).
    in_url = await asyncio.to_thread(publish_input, paths["video"])

    process_video_task.apply_async(
        args=[job_id, paths["video"], modes, source_lang, target_lang, user_tg_id, video_id],
        kwargs={"in_url": in_url},
        queue=queue,
    )

    # Holat tozalangan (yuqorida state.clear) — foydalanuvchi bloklanmaydi:
    # bemalol yangi video/havola yuboraversa bo'ladi. Takroriy "boshqa format"
    # so'rovi olib tashlandi (foydalanuvchilar tushunmasdan bosib, takroriy
    # ish boshlanardi). Faqat aniq taxminiy vaqtni ko'rsatamiz.
    # "Shu videoga boshqa rejim" tugmasi — videoni qayta yubormasdan boshqa
    # rejimda ham ishlatish uchun (havola/file_id saqlanadi).
    reuse_token = _store_reuse({
        "source_type": source_type, "file_id": file_id, "url": url,
        "duration": duration, "user_db_id": user_db_id,
    })
    reuse_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="➕ Shu videoga boshqa rejim", callback_data=f"reuse:{reuse_token}"
        )
    ]])
    # Navbat o'rni — o'zimizning videomiz ham hisobda, shuning uchun -1
    try:
        ahead = max(0, await count_active_videos() - 1)
    except Exception:
        ahead = 0
    queue_line = (
        f"📊 Navbatda sizdan oldin: <b>{ahead} ta video</b>\n" if ahead > 0 else ""
    )
    try:
        await status_msg.edit_text(
            "✅ <b>Qabul qilindi!</b> Navbatga qo'shildi.\n\n"
            + queue_line
            + f"⏱ Taxminiy vaqt: <b>{est}</b>\n"
            "🔔 Tayyor bo'lganda darrov yuboraman.\n\n"
            "💡 Shu videoni <b>boshqa rejimda</b> ham olmoqchimisiz? Quyidagi "
            "tugmani bosing — qaytadan yuborish shart emas 👇",
            parse_mode="HTML",
            reply_markup=reuse_kb,
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("reuse:"))
async def on_reuse(call: CallbackQuery, state: FSMContext) -> None:
    """"Shu videoga boshqa rejim" — saqlangan video havolasi bilan rejim so'raymiz."""
    token = call.data.split(":", 1)[1]
    info = _REUSE.get(token)
    if not info:
        await call.answer(
            "⏳ Bu video eskirgan — iltimos videoni qayta yuboring.", show_alert=True
        )
        return
    user = await get_or_create_user(call.from_user.id, call.from_user.username)
    tariff = await get_effective_tariff(effective_plan(user))
    duration = info.get("duration", 0)
    is_long = duration > settings.long_video_minutes * 60
    await state.update_data(
        source_type=info["source_type"], file_id=info.get("file_id"),
        url=info.get("url"), duration=duration,
        user_db_id=info["user_db_id"], is_long=is_long,
    )
    await state.set_state(VideoFlow.waiting_mode)
    await call.answer()
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    allowed = [m for m in ALL_MODES if m in tariff.modes]
    await call.message.answer_photo(
        FSInputFile(mode_photo_path(allowed[0])),
        caption=_mode_head(is_long, duration) + mode_caption(allowed[0], 0, len(allowed)),
        reply_markup=mode_card_keyboard(allowed, 0),
        parse_mode="HTML",
    )


@router.message(F.text & ~F.text.startswith("/"))
async def on_other_text(message: Message) -> None:
    """Video/havola emas — yo'naltirib qo'yamiz. Boshqa linkni rad etamiz."""
    if extract_url(message.text):
        await message.answer(
            "🔗 Hozircha faqat <b>YouTube</b> va <b>Instagram</b> havolalari qabul qilinadi.\n\n"
            "📤 Yoki videoni to'g'ridan-to'g'ri yuboring!\n"
            "/help — batafsil yo'riqnoma",
            parse_mode="HTML",
        )
        return
    await message.answer(
        "🎬 Video yoki <b>YouTube/Instagram havolasi</b> yuboring — men subtitr yozaman!\n\n"
        "/help — qo'llanma  |  /app — katta video",
        parse_mode="HTML",
    )
