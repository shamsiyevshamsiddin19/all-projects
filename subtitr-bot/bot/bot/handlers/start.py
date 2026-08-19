"""/start, /help, /profile, /app, /id, /cancel buyruqlari."""
from __future__ import annotations
import html as html_mod
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from db.crud import effective_plan, get_or_create_user, videos_done_today
from tariffs import get_tariff

router = Router()


def _fmt(n: int) -> str:
    """30000 → '30 000'"""
    return f"{n:,}".replace(",", " ")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    from config import settings

    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    name = html_mod.escape(message.from_user.first_name or "do'stim")

    # Mini App'dan deep-link (?start=subscribe / ?start=donate)
    parts = (message.text or "").split(maxsplit=1)
    payload = parts[1].strip() if len(parts) > 1 else ""
    if payload == "subscribe":
        from bot.handlers.subscribe import cmd_subscribe
        await cmd_subscribe(message)
        return
    if payload == "donate":
        from bot.handlers.donate import cmd_donate
        await cmd_donate(message)
        return

    await message.answer(
        f"<b>Salom, {name}!</b>\n\n"
        f"Men — <b>Subtitr bot</b>. Istalgan videongizga bir necha "
        f"daqiqada <b>professional subtitr</b> yozib beraman.\n\n"
        f"<blockquote>🎬 Video yoki YouTube / Instagram havolasini yuboring\n"
        f"🌐 Tarjima · ikki qatlam · .SRT — o'zingiz tanlaysiz\n"
        f"⚡ Tez, aniq va oson — boshqa dastur kerak emas</blockquote>\n"
        f"💡 Video <b>≤{settings.max_upload_mb}MB</b> bo'lsa — to'g'ridan-to'g'ri yuboring.\n"
        f"Kattaroq video (500MB gacha) uchun → /app\n\n"
        f"🎁 <b>Birinchi video — mutlaqo bepul.</b> Hoziroq sinab ko'ring!",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    from config import settings

    await message.answer(
        "<b>📖 Qanday ishlataman?</b>\n\n"
        "1️⃣ Video yoki havola yuboring\n"
        "2️⃣ Rejim va tilni tanlang\n"
        "3️⃣ Tayyor subtitrli videoni oling ✅\n\n"
        "<b>Nima yuborish mumkin:</b>\n"
        f"• Video fayl (≤{settings.max_upload_mb}MB to'g'ridan-to'g'ri)\n"
        "• YouTube havolasi 📺\n"
        "• Instagram havolasi 📸\n"
        "• Katta video (500MB gacha) → /app\n\n"
        "<b>Rejimlar:</b>\n"
        "📝 <b>Original</b> — asl tilda subtitr\n"
        "🌐 <b>Tarjima</b> — o'zbek · rus · inglizga o'giradi\n"
        "📑 <b>Ikki qatlam</b> — asl + tarjima birga\n"
        "📄 <b>.SRT fayl</b> — o'zingiz tahrirlash uchun\n\n"
        "<b>Buyruqlar:</b>\n"
        "/profile — hisobim va limitlar\n"
        "/subscribe — obuna (tarjima + ko'proq video)\n"
        "/app — katta video (500MB gacha)\n"
        "/cancel — jarayonni bekor qilish\n\n"
        "❓ Muammo bo'lsa — shu yerga yozing!",
        parse_mode="HTML",
    )


@router.message(Command("app"))
async def cmd_app(message: Message) -> None:
    from web.miniapp import miniapp_open_button

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[miniapp_open_button("📱 Mini App'ni ochish")]]
    )
    await message.answer(
        "📱 <b>Subtitr Mini App</b>\n\n"
        "✅ 500MB gacha katta video\n"
        "✅ YouTube va Instagram havolasi\n"
        "✅ Subtitr uslubini sozlash\n"
        "✅ Yuklash tarixi\n\n"
        "Qulay va tez — Telegram ichida ishlaydi!",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.message(Command("web"))
async def cmd_web(message: Message) -> None:
    """Brauzer versiyasi — tokenли havola (kompyuter va telefon brauzeri uchun)."""
    from web.miniapp import make_web_token
    from web.server import base_url

    await get_or_create_user(message.from_user.id, message.from_user.username)
    token = make_web_token(message.from_user.id)
    url = f"{base_url()}/app?t={token}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🌐 Brauzerda ochish", url=url)]]
    )
    await message.answer(
        "🌐 <b>Brauzer versiyasi</b>\n\n"
        "Subtitr botni kompyuter yoki telefon brauzerida — to'liq ekranda oching.\n\n"
        "✅ Katta ekran, qulay ish maydoni\n"
        "✅ Barcha imkoniyatlar shu yerda\n\n"
        "ℹ️ Havola shaxsiy va 30 kun amal qiladi — boshqalarga bermang.",
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(
        f"Sizning Telegram ID: <code>{message.from_user.id}</code>",
        parse_mode="HTML",
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    plan = effective_plan(user)
    tariff = get_tariff(plan)
    used = await videos_done_today(user.id)

    daily = "cheksiz ♾️" if tariff.daily_videos == -1 else str(tariff.daily_videos)

    # Obuna muddati
    until_line = ""
    warning_line = ""
    if plan != "free" and user.plan_until:
        until_line = f"\nMuddati: <b>{user.plan_until.strftime('%d.%m.%Y')}</b> gacha"
        try:
            days_left = (user.plan_until.replace(tzinfo=None) - datetime.utcnow()).days
            if days_left <= 3:
                warning_line = f"\n⚠️ Obuna <b>{days_left}</b> kun ichida tugaydi — yangilang!"
            elif days_left <= 7:
                warning_line = f"\n💡 <b>{days_left}</b> kun qoldi."
        except Exception:
            pass

    text = (
        f"👤 <b>Mening hisobim</b>\n\n"
        f"Tarif: <b>{tariff.title}</b>{until_line}{warning_line}\n"
        f"Bugun: <b>{used}</b> / {daily} video\n"
        f"Maks. davomiylik: {tariff.max_minutes} daqiqa\n"
    )

    if plan == "free":
        text += (
            "\n<b>🔒 Bepul tarif cheklovi:</b>\n"
            f"• Kuniga {tariff.daily_videos} ta video (siz {used}/{tariff.daily_videos} ta ishlatdingiz)\n"
            f"• Faqat «Original» rejim — tarjima yo'q\n"
            f"• {tariff.max_minutes} daqiqagacha\n\n"
            "<b>💎 BASIC obuna bilan:</b>\n"
            "✅ Kuniga 10 ta video (30 daqiqagacha)\n"
            "✅ Tarjima + matn + lug'at + ikki qatlam + .SRT\n\n"
            "👉 /subscribe — obuna olish"
        )
    else:
        text += "\n👉 /subscribe — obunani yangilash yoki o'zgartirish"

    await message.answer(text, parse_mode="HTML")
