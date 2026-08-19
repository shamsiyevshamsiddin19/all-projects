"""Video/havola -> rejim -> til -> subtitr oqimi (arxitektura 3.1, 4.2, 5.7).

Celery worker'ga topshirish: bot videoni yuklab oladi, keyin
process_video_task ni Celery'ga yuboradi. Worker alohida jarayonda
ishlab, natijani Telegram orqali yuboradi.
"""
from __future__ import annotations

import asyncio
import html
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
    Message,
)

from config import settings
from bot.keyboards import language_keyboard, mode_keyboard, target_lang_keyboard
from worker.pipeline import (
    cleanup_all,
    job_paths,
)
from worker.download import detect_source, download_video, extract_url, probe_url
from web.server import publish_file
from db.crud import (
    create_payment,
    create_video,
    effective_plan,
    finish_video,
    get_effective_settings,
    get_or_create_user,
)
from access import check_can_process
from tariffs import get_tariff

logger = logging.getLogger(__name__)
router = Router()

# Tarjima talab qiladigan rejimlar (maqsad tilini so'raydi)
_TRANSLATE_MODES = ("translate", "dual", "vocabulary")


def _est_time(duration: float, mode: str) -> str:
    """Taxminiy ishlov vaqti (ultrafast preset asosida)."""
    if mode in ("transcript", "vocabulary"):
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
    if message.from_user.id in _ACTIVE_USERS:
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

    tariff = get_tariff(effective_plan(user))
    await state.update_data(
        source_type="upload",
        file_id=video.file_id,
        duration=duration,
        user_db_id=user.id,
    )
    await state.set_state(VideoFlow.waiting_mode)
    await message.reply(
        "✅ <b>Video qabul qilindi!</b>\n\n"
        "Kerakli rejim(lar)ni tanlang — <b>bir nechta</b> ham bo'ladi, "
        "so'ng <b>▶️ Boshlash</b> 👇",
        reply_markup=mode_keyboard(tariff.modes),
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
                    text="⬇️ Videoni yuklab olish", url="https://cobalt.tools",
                )
            ]]
        )
        await status.edit_text(
            f"😊 <b>{src_name} videosini to'g'ridan-to'g'ri ololmadim</b> — "
            "lekin hammasi joyida, bir necha soniyada hal qilamiz:\n\n"
            "1️⃣ Quyidagi tugmani bosing va videoni yuklab oling\n"
            "2️⃣ Yuklangan videoni <b>shu yerga yuboring</b>\n"
            "3️⃣ Men unga darrov subtitr yozaman ✅\n\n"
            "🔒 <b>cobalt.tools</b> — bepul, reklamasiz va ishonchli "
            "(YouTube, Instagram, TikTok…).",
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return

    duration = info["duration"]
    ok, reason = await check_can_process(user, duration, mode="")
    if not ok:
        await status.edit_text(reason)
        return

    tariff = get_tariff(effective_plan(user))
    await state.update_data(
        source_type=source, url=url, duration=duration, user_db_id=user.id
    )
    await state.set_state(VideoFlow.waiting_mode)

    title = info.get("title") or ""
    head = f"🎬 <b>{html.escape(title)}</b>\n\n" if title else ""
    await status.edit_text(
        head + "✅ <b>Video tayyor!</b>\n\n"
        "Kerakli rejim(lar)ni tanlang — <b>bir nechta</b> ham bo'ladi, "
        "so'ng <b>▶️ Boshlash</b> 👇",
        reply_markup=mode_keyboard(tariff.modes),
        parse_mode="HTML",
    )


_MODE_NAMES = {
    "original": "Original",
    "translate": "🌐 Tarjima",
    "dual": "📑 Ikki qatlam",
    "srt": "📄 .SRT fayl",
    "transcript": "📜 Matn",
    "vocabulary": "📚 Lug'at",
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


@router.callback_query(VideoFlow.waiting_mode, F.data.startswith("mode:"))
async def on_mode(call: CallbackQuery, state: FSMContext) -> None:
    """Rejim tanlandi — ruxsat tekshirib, til so'raymiz yoki obuna taklif qilamiz."""
    mode = call.data.split(":", 1)[1]

    user = await get_or_create_user(call.from_user.id, call.from_user.username)
    tariff = get_tariff(effective_plan(user))
    if mode not in tariff.modes:
        # Qulflangan rejim — klaviaturani qoldiramiz (boshqa rejim tanlasin)
        await call.answer("🔒 Bu rejim obunachilarda", show_alert=False)
        await _offer_subscription(call, mode)
        return

    await state.update_data(modes=[mode])
    await state.set_state(VideoFlow.waiting_lang)
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)

    if mode in _TRANSLATE_MODES:
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
    """Til tanlandi — videoni yuklab, Celery worker'ga topshiramiz."""
    user_tg_id = call.from_user.id

    lang = call.data.split(":", 1)[1]
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

    # Manba/tarjima tilini aniqlash (tarjima-turidagi rejim bo'lsa — maqsad til)
    if any(m in _TRANSLATE_MODES for m in modes):
        source_lang = "auto"
        target_lang = lang
    else:
        source_lang = lang
        target_lang = None

    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)

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
    status_msg = await call.message.answer(f"⏳ Qabul qilindi! Video yuklanmoqda... ({est})")
    try:
        os.makedirs(settings.work_dir, exist_ok=True)
        if source_type == "upload":
            tg_file = await bot.get_file(file_id)
            await bot.download_file(tg_file.file_path, paths["video"])
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
                    text="⬇️ Videoni yuklab olish", url="https://cobalt.tools",
                )
            ]])
            try:
                await status_msg.edit_text(
                    f"😔 <b>{src_name} videosini hozir to'g'ridan-to'g'ri ololmadim.</b>\n\n"
                    "1️⃣ Quyidagi tugma orqali videoni yuklab oling\n"
                    "2️⃣ Yuklangan videoni <b>shu yerga yuboring</b>\n"
                    "3️⃣ Men unga darrov subtitr yozaman ✅\n\n"
                    "🔒 cobalt.tools — bepul, reklamasiz va ishonchli.",
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
    user = await get_or_create_user(call.from_user.id, call.from_user.username)
    plan = effective_plan(user)
    queue = "high" if plan in ("premium", "basic") else "default"

    process_video_task.apply_async(
        args=[job_id, paths["video"], modes, source_lang, target_lang, user_tg_id, video_id],
        queue=queue,
    )

    try:
        await status_msg.edit_text(
            f"✅ Video qabul qilindi va navbatga qo'shildi! ({est})\n\n"
            "⏳ Tayyor bo'lganda sizga xabar yuboraman.\n"
            "Kutayotgan vaqtda boshqa video ham yuborishingiz mumkin!"
        )
    except Exception:
        pass

    # Shu videodan boshqa format olish imkoni
    tariff = get_tariff(plan)
    await state.set_state(VideoFlow.waiting_mode)
    await state.update_data(
        source_type=source_type, file_id=file_id, url=url,
        duration=duration, user_db_id=user_db_id,
    )
    await call.message.answer(
        "🔁 <b>Shu videodan boshqa format ham olishingiz mumkin.</b>\n"
        "Rejimni tanlang (yoki yangi video / havola yuboring):",
        reply_markup=mode_keyboard(tariff.modes),
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
