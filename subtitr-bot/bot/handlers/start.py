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
from db.crud import get_effective_tariff, videos_done_this_month

router = Router()


def _fmt(n: int) -> str:
    """30000 → '30 000'"""
    return f"{n:,}".replace(",", " ")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    from config import settings

    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    name = html_mod.escape(message.from_user.first_name or "do'stim")

    # Mini App'dan deep-link (?start=subscribe / ?start=donate / ?start=ref_ID)
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
    # Referal havolasi: ?start=ref_<taklif_qilgan_telegram_id>
    if payload.startswith("ref_") and payload[4:].isdigit():
        referrer_tg_id = int(payload[4:])
        if referrer_tg_id != message.from_user.id:
            from db.crud import REFERRAL_BONUS, apply_referral
            applied, ref_tg = await apply_referral(
                message.from_user.id, referrer_tg_id
            )
            if applied:
                await message.answer(
                    f"🎁 <b>Tabriklaymiz!</b> Do'stingiz taklifi bilan keldingiz — "
                    f"sizga <b>+{REFERRAL_BONUS} bepul video/oy</b> qo'shildi!",
                    parse_mode="HTML",
                )
                # Taklif qilganga xabar (jim, xato bo'lsa e'tiborsiz)
                try:
                    inviter_name = message.from_user.first_name or "Do'stingiz"
                    await message.bot.send_message(
                        ref_tg,
                        f"🎉 <b>{html_mod.escape(inviter_name)}</b> sizning havolangiz "
                        f"orqali qo'shildi — sizga <b>+{REFERRAL_BONUS} video/oy</b> "
                        "bonus berildi! Rahmat! 🙌",
                        parse_mode="HTML",
                    )
                except Exception:
                    pass

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
        "📄 <b>.SRT fayl</b> — o'zingiz tahrirlash uchun\n"
        "📜 <b>Matn</b> · 📚 <b>Lug'at</b> — video matni va so'zlar (PDF/txt)\n\n"
        "<b>Buyruqlar:</b>\n"
        "/profile — hisobim va limitlar\n"
        "🎁 /invite — do'st taklif qilib bepul video ol\n"
        "/subscribe — obuna (tarjima + ko'proq video)\n"
        "/app — katta video (500MB gacha)\n"
        "🔊 /tts — matnni ovozga aylantirish (rus · ingliz)\n"
        "💬 /feedback — fikr yoki taklif yuborish\n"
        "🏆 /donors — homiylar ro'yxati\n"
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


@router.message(Command("invite"))
async def cmd_invite(message: Message) -> None:
    """Shaxsiy referal havolasi + statistika."""
    from db.crud import REFERRAL_BONUS, get_or_create_user, referral_stats

    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    invited, bonus = await referral_stats(user.id)

    me = await message.bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{message.from_user.id}"

    share_text = (
        "🎬 Subtitr bot — videoga AI subtitr, tarjima, matn va ovoz! "
        "Havolam orqali qo'shil, ikkovimizga bepul video 🎁"
    )
    from urllib.parse import quote
    share_url = f"https://t.me/share/url?url={quote(link)}&text={quote(share_text)}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="📤 Do'stlarga ulashish", url=share_url)
        ]]
    )
    await message.answer(
        "🎁 <b>Do'st taklif qiling — bepul video oling!</b>\n\n"
        f"Har bir do'stingiz havolangiz orqali qo'shilsa — <b>ikkovingizga "
        f"+{REFERRAL_BONUS} bepul video/oy</b> (doimiy) qo'shiladi.\n\n"
        f"👥 Siz taklif qilganlar: <b>{invited}</b> ta\n"
        f"🎬 Referal bonusingiz: <b>+{bonus} video/oy</b>\n\n"
        f"🔗 Shaxsiy havolangiz:\n<code>{link}</code>\n\n"
        "Quyidagi tugma bilan darrov ulashing 👇",
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
    tariff = await get_effective_tariff(plan)

    # Foydalanish satri — tarif turiga qarab (oylik / kunlik / cheksiz)
    if tariff.monthly_videos > 0:
        used_m = await videos_done_this_month(user.id)
        usage_line = f"Bu oy: <b>{used_m}</b> / {tariff.monthly_videos} video"
    elif tariff.daily_videos == -1:
        usage_line = "Limit: <b>cheksiz</b> ♾️"
    else:
        used_d = await videos_done_today(user.id)
        usage_line = f"Bugun: <b>{used_d}</b> / {tariff.daily_videos} video"

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
        f"{usage_line}\n"
        f"Maks. davomiylik: {tariff.max_minutes} daqiqa\n"
    )

    if plan == "free":
        bonus_line = (
            f"• 🎁 Referal bonusingiz: +{user.bonus_videos} video/oy\n"
            if user.bonus_videos else ""
        )
        text += (
            "\n<b>🎁 Bepul tarif:</b>\n"
            f"• Oyiga {tariff.monthly_videos} ta video — har rejimga {tariff.per_mode_monthly} tadan\n"
            + bonus_line +
            "• Barcha rejimlar ochiq (oz-ozdan sinab ko'ring)\n"
            f"• {tariff.max_minutes} daqiqagacha\n"
            "🗓 Limit har oy avtomatik yangilanadi\n\n"
            "🎁 <b>Do'st taklif qilib bepul video oling</b> → /invite\n\n"
            "<b>💎 BASIC obuna bilan:</b>\n"
            "✅ Kuniga 10 ta video (45 daqiqagacha)\n"
            "✅ Barcha rejimlar cheksiz\n\n"
            "👉 /subscribe — obuna olish"
        )
    else:
        text += "\n👉 /subscribe — obunani yangilash yoki o'zgartirish"

    await message.answer(text, parse_mode="HTML")
