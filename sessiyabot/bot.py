"""Sessiya tayyorgarlik bot — handlerlar (baza_bot.php'dan toza Python'ga).

DB-asoslangan step/temp FSM (PHP bilan 1:1, referal ballari saqlanadi).
"""
from __future__ import annotations

import logging
import os

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import db
import keyboards as kb
from config import settings
from services import (
    activation_key,
    click_payment_url,
    normalize_hwid,
    normalize_input,
    telegram_bot_url,
)

logger = logging.getLogger(__name__)
router = Router()


async def _capture_user_mw(handler, event, data):
    """Har bir xabar/tugmada foydalanuvchi profilini (username, ism) saqlab boradi."""
    u = getattr(event, "from_user", None)
    if u and not u.is_bot:
        try:
            await db.touch_user(u.id, u.username, u.first_name, u.last_name)
        except Exception:
            logger.debug("touch_user xato", exc_info=True)
    return await handler(event, data)


router.message.outer_middleware(_capture_user_mw)
router.callback_query.outer_middleware(_capture_user_mw)

_ASSETS = os.path.join(os.path.dirname(__file__), "assets")


def _photo(name: str) -> FSInputFile | None:
    path = os.path.join(_ASSETS, name)
    return FSInputFile(path) if os.path.isfile(path) else None


def is_admin(chat_id: int) -> bool:
    return chat_id in settings.admin_ids


# ----------------------------------------------------------- yordamchilar

async def check_subscription(bot: Bot, user_id: int):
    """True = obuna bo'lgan; aks holda — obuna klaviaturasi (InlineKeyboardMarkup)."""
    s = await db.get_settings()
    if not s.get("force_sub") or not s.get("channels"):
        return True
    need = []
    for ch in s["channels"]:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status in ("left", "kicked"):
                need.append(ch)
        except Exception:
            need.append(ch)
    if not need:
        return True
    return kb.subscription_kb(need)


async def ref_points(chat_id: int) -> int:
    total = await db.referral_count(chat_id)
    used = await db.get_temp(chat_id, "used_ref_points") or 0
    return total - int(used)


async def send_referral_section(bot: Bot, chat_id: int) -> None:
    count = await ref_points(chat_id)
    text = (
        "🎉 <b>DO'STLARNI TAKLIF QILING VA MUKOFOT OLING!</b>\n\n"
        "Har 5 ta taklif uchun 1 ta kod beriladi.\n\n"
        "🔗 <b>Sizning havolangiz:</b>\n"
        f"{telegram_bot_url('ref_' + str(chat_id))}\n\n"
        f"📊 <b>Takliflaringiz (Ball):</b> {count} ta"
    )
    await bot.send_message(chat_id, text, reply_markup=kb.referral_kb(count >= 5))


async def add_referral(bot: Bot, referrer_id: int, invited_id: int) -> None:
    """Faqat YANGI foydalanuvchi (60s ichida qo'shilgan) referal sifatida hisoblanadi."""
    if referrer_id == invited_id:
        return
    diff = await db.referral_seconds_since_join(invited_id)
    if diff is not None and diff > 60:
        return
    if await db.add_referral(referrer_id, invited_id):
        count = await ref_points(referrer_id)
        try:
            await bot.send_message(
                referrer_id,
                "🎉 <b>Yangi referal!</b>\nSizning havolangiz orqali yangi foydalanuvchi "
                f"qo'shildi.\n\nJami aktiv ballaringiz: <b>{count}</b> ta",
            )
        except Exception:
            pass


async def start_click_payment(bot: Bot, chat_id: int, hwid: str, base_num: str,
                              is_retry: bool = False) -> None:
    hwid = normalize_hwid(hwid)
    base_num = normalize_input(base_num)
    if not hwid or not base_num:
        return
    price = await db.get_base_price()
    payment_id = await db.create_baza_payment(chat_id, hwid, base_num, price)
    await db.set_temp(chat_id, "last_hwid", hwid)
    await db.set_temp(chat_id, "last_base", base_num)
    await db.set_temp(chat_id, "last_payment_id", payment_id)
    await db.set_step(chat_id, "none")

    url = click_payment_url(payment_id, price)
    title = "💠 <b>CLICK TO'LOV HAVOLASI YANGILANDI</b>" if is_retry else "💠 <b>CLICK TO'LOV HAVOLASI</b>"
    text = (
        f"{title}\n\n"
        f"📥 <b>Baza:</b> {base_num}\n"
        f"💰 <b>Summa:</b> <code>{price}</code> so'm\n\n"
        "Quyidagi tugma orqali Click ichida to'lov qiling.\n"
        "To'lov tasdiqlangach, aktivlashtirish kodingiz shu chatga avtomatik yuboriladi."
    )
    await bot.send_message(chat_id, text, reply_markup=kb.click_invoice_kb(url))


async def deliver_activation_key(bot: Bot, chat_id: int, base_num: str, hwid: str) -> None:
    """Click complete (ko'prik) chaqiradi — kodni foydalanuvchiga yuboradi."""
    key = activation_key(hwid, base_num)
    await bot.send_message(
        chat_id,
        "✅ <b>Click to'lovi tasdiqlandi!</b>\n\n"
        f"📂 <b>Baza kodi:</b> {base_num}\n"
        f"🔑 <b>Aktivlashtirish kodi:</b>\n<code>{key}</code>\n\n"
        "Kod dasturdagi shu baza uchun ishlaydi.",
    )


# =================================================================== CALLBACK

@router.callback_query(F.data == "open_referral_section")
async def cb_referral(call: CallbackQuery) -> None:
    await call.answer()
    await send_referral_section(call.bot, call.message.chat.id)


@router.callback_query(F.data == "check_subs_btn")
async def cb_check_subs(call: CallbackQuery) -> None:
    chat_id = call.message.chat.id
    res = await check_subscription(call.bot, chat_id)
    if res is True:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.bot.send_message(chat_id, "✅ <b>Obuna tasdiqlandi!</b>", reply_markup=kb.user_menu())
        referrer = await db.get_temp(chat_id, "pending_referrer")
        if referrer:
            await add_referral(call.bot, int(referrer), chat_id)
            await db.set_temp(chat_id, "pending_referrer", None)
    else:
        await call.answer("Hali to'liq a'zo bo'lmadingiz!", show_alert=True)
        try:
            await call.message.edit_reply_markup(reply_markup=res)
        except Exception:
            pass


@router.callback_query(F.data == "get_free_code_auto")
async def cb_free_code(call: CallbackQuery) -> None:
    chat_id = call.message.chat.id
    if await ref_points(chat_id) >= 5:
        try:
            await call.message.delete()
        except Exception:
            pass
        await db.set_step(chat_id, "wait_free_hwid_auto")
        await call.bot.send_message(
            chat_id,
            "🚀 <b>Kod olish jarayoni boshlandi!</b>\n\nIltimos, dasturdan olgan "
            "<b>Kompyuter ID</b> (HWID) raqamini yuboring:",
            reply_markup=kb.reply_kb([], back=True),
        )
    else:
        await call.answer("Ball yetarli emas!", show_alert=True)


@router.callback_query()
async def cb_legacy(call: CallbackQuery) -> None:
    """Eski (chek) tugmalari — endi Click avtomatik."""
    await call.answer("Endi to'lovlar Click orqali avtomatik tasdiqlanadi.", show_alert=True)


# =================================================================== MESSAGE

def _text(msg: Message) -> str:
    return (msg.text or msg.caption or "").strip()


@router.message(F.chat.type != ChatType.PRIVATE)
async def on_group(msg: Message) -> None:
    if _text(msg).startswith("/"):
        await msg.answer(
            "⚠️ <b>Kechirasiz, men faqat shaxsiy chatda ishlayman!</b>\n\n"
            "Botdan to'liq foydalanish uchun tugmani bosing:",
            reply_markup=kb.back_to_bot_kb(),
        )


@router.message(F.contact)
async def on_contact(msg: Message) -> None:
    """Foydalanuvchi raqamini ulashganda saqlaymiz (faqat o'z raqami)."""
    chat_id = msg.chat.id
    c = msg.contact
    if c and (c.user_id == chat_id or c.user_id is None):
        await db.set_phone(chat_id, c.phone_number)
        await msg.answer("✅ Raqamingiz saqlandi, rahmat!",
                         reply_markup=kb.admin_menu() if is_admin(chat_id) else kb.user_menu())
    else:
        await msg.answer("⚠️ Iltimos, o'zingizning raqamingizni ulashing.")


@router.message()
async def on_message(msg: Message) -> None:
    chat_id = msg.chat.id
    text = _text(msg)
    bot = msg.bot
    name = (msg.from_user.first_name or "") if msg.from_user else ""
    await db.ensure_user(chat_id)

    # Obuna gate (adminlardan tashqari)
    if not is_admin(chat_id):
        sub = await check_subscription(bot, chat_id)
        if sub is not True:
            if text.startswith("/start") and "ref_" in text:
                ref = text.split("ref_", 1)[1].split()[0]
                if ref.isdigit():
                    await db.set_temp(chat_id, "pending_referrer", ref)
            await msg.answer("<b>⚠️ Botdan foydalanish uchun obuna bo'ling:</b>", reply_markup=sub)
            return

    step = await db.get_step(chat_id)

    # --- /start, ORQAGA, CHIQISH ---
    if text.startswith("/start") or text in ("🔙 ORQAGA", "CHIQISH"):
        await db.set_step(chat_id, "none")
        if "ref_" in text:
            ref = text.split("ref_", 1)[1].split()[0]
            if ref.isdigit():
                await add_referral(bot, int(ref), chat_id)
        if "code_" in text:
            await _handle_code_deeplink(bot, chat_id, text.split("code_", 1)[1].strip())
            return
        if is_admin(chat_id):
            await msg.answer("👑 <b>Admin Panel</b>", reply_markup=kb.admin_menu())
        else:
            await msg.answer(_start_text(), reply_markup=kb.user_menu())
        return

    # --- oddiy komandalar ---
    if text == "/admin":
        await msg.answer("👤 Admin: @tuiyordamadminbot")
        return
    if text == "/help":
        await msg.answer("ℹ️ <b>Yordam:</b> .EXE fayllarni ochish uchun to'lov qiling va kod oling.")
        return
    if text == "/about":
        await msg.answer("Bu bot baza fayllari va talaba xizmatlari buyurtmalarini boshqaradi.")
        return

    # --- step-asoslangan oqimlar ---
    if await _handle_steps(bot, msg, chat_id, text, step, name):
        return

    # --- admin tugmalari ---
    if is_admin(chat_id):
        if await _handle_admin(bot, msg, chat_id, text, step):
            return

    # --- user tugmalari ---
    if not is_admin(chat_id):
        if await _handle_user(bot, msg, chat_id, text):
            return


def _start_text() -> str:
    return (
        "<b>Exe Seller Bot</b>\n\n"
        "<b>Asosiy menyu:</b>\n"
        "/start - Botni ishga tushirish\n"
        "/courses - Fanlar bo'yicha qidirish\n"
        "/code - Aktivlashtirish kodini olish\n"
        "/order - Bazaga buyurtma berish\n"
        "/free - Tekin baza olish\n\n"
        "<b>Yordamchi bo'limlar:</b>\n"
        "/help - Qo'llanma\n/about - Loyiha haqida\n/admin - Admin bilan bog'lanish"
    )


async def _handle_code_deeplink(bot: Bot, chat_id: int, code: str) -> None:
    prod = await db.product_by_code(code)
    if not prod:
        await bot.send_message(chat_id, "❌ <b>Bunday kodli baza topilmadi.</b>")
        return
    await db.set_temp(chat_id, "base_num", code)
    await db.set_step(chat_id, "get_code_hwid_direct")
    caption = (
        f"📂 <b>Baza topildi:</b> {prod['name']}\n"
        f"ℹ️ <b>Tavsif:</b> {prod['description']}\n\n"
        "Fayl kalitini olish uchun dasturdan olgan <b>Kompyuter ID</b> (HWID) raqamini yuboring:"
    )
    photo = _photo("hwid_instruction.jpg")
    if photo:
        await bot.send_photo(chat_id, photo, caption=caption)
    else:
        await bot.send_message(chat_id, caption)


async def _ask_hwid(bot: Bot, chat_id: int, caption: str) -> None:
    photo = _photo("hwid_instruction.jpg")
    if photo:
        await bot.send_photo(chat_id, photo, caption=caption, reply_markup=kb.reply_kb([], back=True))
    else:
        await bot.send_message(chat_id, caption, reply_markup=kb.reply_kb([], back=True))


async def _ask_base(bot: Bot, chat_id: int, caption: str) -> None:
    photo = _photo("base_instruction.jpg")
    if photo:
        await bot.send_photo(chat_id, photo, caption=caption)
    else:
        await bot.send_message(chat_id, caption)


# ---------------------------------------------------- pre-split step oqimlari

async def _handle_steps(bot: Bot, msg: Message, chat_id: int, text: str,
                        step: str, name: str) -> bool:
    # Tekin kod (avto): HWID
    if step == "wait_free_hwid_auto":
        hwid = normalize_hwid(text)
        if not hwid:
            await msg.answer("❌ <b>HWID noto'g'ri yuborildi.</b>\nFaqat dastur ko'rsatgan kodni yuboring.")
            return True
        await db.set_temp(chat_id, "pending_free_hwid", hwid)
        await db.set_step(chat_id, "wait_free_base_auto")
        await _ask_base(bot, chat_id, "📂 Endi <b>Baza Kodi</b> (ID) ni yozing (Masalan: 101):")
        return True

    # Tekin kod (avto): baza + generatsiya
    if step == "wait_free_base_auto":
        base_code = normalize_input(text)
        hwid = normalize_hwid(str(await db.get_temp(chat_id, "pending_free_hwid") or ""))
        if not hwid:
            await db.set_step(chat_id, "wait_free_hwid_auto")
            await msg.answer("⚠️ Avval HWID ni qayta yuboring.", reply_markup=kb.reply_kb([], back=True))
            return True
        prod = await db.product_by_code(base_code)
        if not prod:
            await msg.answer("❌ <b>Bunday kodli baza topilmadi!</b>\nQaytadan urinib ko'ring.")
            return True
        if await ref_points(chat_id) >= 5:
            used = int(await db.get_temp(chat_id, "used_ref_points") or 0)
            await db.set_temp(chat_id, "used_ref_points", used + 5)
            key = activation_key(hwid, base_code)
            await msg.answer(
                "✅ <b>Tabriklaymiz! Kod muvaffaqiyatli yaratildi.</b>\n(5 ball yechildi)\n\n"
                f"📂 Baza: <b>{prod['name']}</b>\n🔑 <b>KOD:</b> <code>{key}</code>",
                reply_markup=kb.user_menu(),
            )
            for aid in settings.admin_ids:
                try:
                    await bot.send_message(
                        aid, f"🎁 <b>REFERAL KOD BERILDI (AVTO)</b>\nUser: "
                        f"<a href='tg://user?id={chat_id}'>{name}</a>\nBaza: {base_code}\nKod: {key}",
                    )
                except Exception:
                    pass
        else:
            await msg.answer("❌ Ball yetarli emas!")
        await db.set_step(chat_id, "none")
        return True

    if step == "wait_payment_proof":
        await db.set_step(chat_id, "none")
        await msg.answer(
            "ℹ️ <b>Chek yuborish endi kerak emas.</b>\n\nTo'lovlar Click orqali avtomatik "
            "tasdiqlanadi. Yangi havola olish uchun kod olish jarayonini qaytadan boshlang.",
            reply_markup=kb.user_menu(),
        )
        return True

    return False


# ---------------------------------------------------------------- ADMIN

async def _handle_admin(bot: Bot, msg: Message, chat_id: int, text: str, step: str) -> bool:
    # /bases — barcha bazalarni yuborish
    if text == "/bases":
        await _send_all_bases(bot, chat_id)
        return True

    if text == "BAZA QO'SHISH":
        await db.set_step(chat_id, "add_prod_course")
        await msg.answer("Kursni tanlang (1-4):", reply_markup=kb.courses_kb())
        return True
    if step == "add_prod_course":
        await db.set_temp(chat_id, "p_course", text)
        subjects = await db.product_subjects(text)
        await db.set_step(chat_id, "add_prod_subject")
        await msg.answer("Fan nomini yozing yoki ro'yxatdan tanlang:",
                         reply_markup=kb.reply_kb(subjects, back=True))
        return True
    if step == "add_prod_subject":
        await db.set_temp(chat_id, "p_subject", text)
        await db.set_step(chat_id, "add_prod_name")
        await msg.answer("Baza nomini yozing:", reply_markup=kb.reply_kb([], back=True))
        return True
    if step == "add_prod_name":
        await db.set_temp(chat_id, "p_name", text)
        await db.set_step(chat_id, "add_prod_code")
        await msg.answer("Kod (ID):")
        return True
    if step == "add_prod_code":
        await db.set_temp(chat_id, "p_code", text)
        await db.set_step(chat_id, "add_prod_desc")
        await msg.answer("Tavsif:")
        return True
    if step == "add_prod_desc":
        await db.set_temp(chat_id, "p_desc", text)
        await db.set_step(chat_id, "add_prod_file")
        await msg.answer("Fayl:")
        return True
    if step == "add_prod_file":
        if not msg.document:
            await msg.answer("Iltimos, fayl (document) yuboring.")
            return True
        try:
            await db.add_product(
                str(await db.get_temp(chat_id, "p_code")),
                str(await db.get_temp(chat_id, "p_name")),
                str(await db.get_temp(chat_id, "p_course")),
                str(await db.get_temp(chat_id, "p_subject")),
                str(await db.get_temp(chat_id, "p_desc")),
                msg.document.file_id,
            )
            await msg.answer("✅ Saqlandi!", reply_markup=kb.admin_menu())
        except Exception:
            await msg.answer("❌ Xatolik! Bu kodli (ID) baza allaqachon mavjud. Boshqa kod bilan urinib ko'ring.",
                             reply_markup=kb.admin_menu())
        await db.set_step(chat_id, "none")
        return True

    if text == "BAZA O'CHIRISH":
        names = await db.all_product_names()
        if not names:
            await msg.answer("Baza yo'q.")
        else:
            await db.set_step(chat_id, "del_prod")
            await msg.answer("O'chirish uchun tanlang:", reply_markup=kb.reply_kb(names, back=True))
        return True
    if step == "del_prod":
        await db.delete_product_by_name(text)
        await msg.answer("O'chirildi.", reply_markup=kb.admin_menu())
        await db.set_step(chat_id, "none")
        return True

    if text == "HAVOLALAR":
        await db.set_step(chat_id, "gen_link")
        await msg.answer("Baza kodi:", reply_markup=kb.reply_kb([], back=True))
        return True
    if step == "gen_link":
        await msg.answer(f"Link: {telegram_bot_url('code_' + text)}", reply_markup=kb.admin_menu())
        await db.set_step(chat_id, "none")
        return True

    if text == "TAG SOZLAMALARI":
        await db.set_step(chat_id, "set_global_tag")
        await msg.answer("Yangi tag yuboring:", reply_markup=kb.reply_kb([], back=True))
        return True
    if step == "set_global_tag":
        await db.set_global_tag(text)
        await msg.answer("✅ Saqlandi.", reply_markup=kb.admin_menu())
        await db.set_step(chat_id, "none")
        return True

    if text == "👥 REFERALLAR":
        await _show_referral_leaderboard(bot, chat_id)
        return True

    if text == "STATISTIKA":
        users = await db.count_users()
        prods = await db.count_products()
        stats = await db.get_stats()
        rev = f"{int(stats.get('revenue', 0)):,}".replace(",", " ")
        await msg.answer(
            f"📊 <b>STATISTIKA</b>\n\nUsers: <b>{users}</b>\nBazalar: <b>{prods}</b>\n"
            f"Sotuv: {stats.get('sales', 0)}\nDaromad: {rev}"
        )
        return True

    if text == "REKLAMA":
        await db.set_step(chat_id, "send_ad_wait")
        await msg.answer("📢 Reklama postini yuboring:", reply_markup=kb.reply_kb([], back=True))
        return True
    if step == "send_ad_wait" and text != "🔙 ORQAGA":
        await db.set_step(chat_id, "none")
        await msg.answer("🚀 Boshlandi...")
        count = 0
        for uid in await db.all_user_ids():
            try:
                await bot.copy_message(uid, chat_id, msg.message_id)
                count += 1
            except Exception:
                pass
        await msg.answer(f"✅ Tugadi! {count} ta user.", reply_markup=kb.admin_menu())
        return True

    # --- OBUNA SOZLAMALARI ---
    if text == "📢 OBUNA SOZLAMALARI":
        await db.set_step(chat_id, "sub_settings")
        s = await db.get_settings()
        status = "YONIQ" if s.get("force_sub") else "O'CHIQ"
        await msg.answer(f"Holat: {status}",
                         reply_markup=kb.reply_kb(["KANAL QO'SHISH", "KANAL O'CHIRISH", "MAJBURIY OBUNA: ON/OFF"], back=True))
        return True
    if step == "sub_settings":
        s = await db.get_settings()
        if text == "MAJBURIY OBUNA: ON/OFF":
            s["force_sub"] = not s.get("force_sub")
            await db.save_settings(s)
            await msg.answer("O'zgardi.", reply_markup=kb.admin_menu())
            await db.set_step(chat_id, "none")
            return True
        if text == "KANAL QO'SHISH":
            await db.set_step(chat_id, "add_channel_link")
            await msg.answer("Username yoki ID:", reply_markup=kb.reply_kb([], back=True))
            return True
        if text == "KANAL O'CHIRISH":
            channels = s.get("channels", [])
            if channels:
                await db.set_step(chat_id, "del_channel_select")
                await msg.answer("Tanlang:", reply_markup=kb.reply_kb([c["title"] for c in channels], back=True))
            else:
                await msg.answer("Bo'sh.")
            return True
        return True
    if step == "add_channel_link":
        try:
            chat = await bot.get_chat(text)
            link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else "")
            s = await db.get_settings()
            s.setdefault("channels", []).append({"id": chat.id, "title": chat.title, "link": link})
            await db.save_settings(s)
            await msg.answer("Qo'shildi!", reply_markup=kb.admin_menu())
            await db.set_step(chat_id, "none")
        except Exception:
            await msg.answer("Xato. Bot kanalда admin ekanini tekshiring.")
        return True
    if step == "del_channel_select":
        s = await db.get_settings()
        s["channels"] = [c for c in s.get("channels", []) if c["title"] != text]
        await db.save_settings(s)
        await msg.answer("O'chirildi.", reply_markup=kb.admin_menu())
        await db.set_step(chat_id, "none")
        return True

    return False


async def _send_all_bases(bot: Bot, chat_id: int) -> None:
    products = await db.all_products()
    if not products:
        await bot.send_message(chat_id, "Bazalar yo'q.")
        return
    await bot.send_message(chat_id, "📂 <b>Yuklanmoqda...</b>")
    tag = await db.get_global_tag()
    for p in products:
        caption = (f"<b>Nomi:</b> {p['name']}\n<b>Kodi:</b> {p['code']}\n"
                   f"<b>Tavsif:</b> {p['description']}\n<b>Kodni olish:</b> /code")
        if tag:
            caption += f"\n\n{tag}"
        try:
            await bot.send_document(chat_id, p["file_id"], caption=caption)
        except Exception:
            pass


async def _show_referral_leaderboard(bot: Bot, chat_id: int) -> None:
    rows = await db.referral_leaderboard()
    board = []
    for r in rows:
        used = int(await db.get_temp(r["referrer_id"], "used_ref_points") or 0)
        score = r["total"] - used
        if score > 0:
            board.append((r["referrer_id"], score))
    board.sort(key=lambda x: x[1], reverse=True)
    text = "🏆 <b>REFERALLAR REYTINGI (Top 50):</b>\n\n"
    for i, (uid, score) in enumerate(board[:50], 1):
        text += f"{i}. <a href='tg://user?id={uid}'>Foydalanuvchi {uid}</a> - <b>{score}</b> ta\n"
    if not board:
        text += "Hozircha faol referallar yo'q."
    await bot.send_message(chat_id, text)


# ---------------------------------------------------------------- USER

async def _handle_user(bot: Bot, msg: Message, chat_id: int, text: str) -> bool:
    if text in ("🎁 TEKIN BAZA (REFERAL)", "/free"):
        await send_referral_section(bot, chat_id)
        return True

    if text in ("🔑 AKTIVLASHTIRISH KODINI OLISH", "/code", "🔑 KOD OLISH"):
        await db.set_step(chat_id, "get_code_hwid")
        await _ask_hwid(bot, chat_id, "🖥 <b>Kompyuter ID</b> (HWID) raqamini yuboring:\n"
                                      "<i>(Dasturni ochganda chiqadigan kod)</i>")
        return True

    step = await db.get_step(chat_id)

    if step in ("get_code_hwid", "get_code_hwid_direct"):
        hwid = normalize_hwid(text)
        if not hwid:
            await msg.answer("❌ <b>HWID noto'g'ri yuborildi.</b>\nFaqat dastur ko'rsatgan kodni yuboring.")
            return True
        await db.set_temp(chat_id, "hwid", hwid)
        if step == "get_code_hwid_direct":
            base_num = normalize_input(str(await db.get_temp(chat_id, "base_num") or ""))
            if not base_num:
                await msg.answer("❌ Baza ma'lumoti topilmadi. Qaytadan boshlang.", reply_markup=kb.user_menu())
                await db.set_step(chat_id, "none")
                return True
            await start_click_payment(bot, chat_id, hwid, base_num)
        else:
            await db.set_step(chat_id, "get_code_base")
            await _ask_base(bot, chat_id, "📂 Qaysi baza uchun kod kerak? <b>Baza Kodi</b>ni yozing:")
        return True

    if step == "get_code_base":
        base_code = normalize_input(text)
        hwid = normalize_hwid(str(await db.get_temp(chat_id, "hwid") or ""))
        if not hwid:
            await db.set_step(chat_id, "get_code_hwid")
            await msg.answer("⚠️ Avval HWID ni qayta yuboring.", reply_markup=kb.reply_kb([], back=True))
            return True
        prod = await db.product_by_code(base_code)
        if not prod:
            await msg.answer("❌ <b>Bunday kodli baza topilmadi.</b>\nKodni to'g'ri kiriting (masalan: 101):")
            return True
        await start_click_payment(bot, chat_id, hwid, base_code)
        return True

    if text in ("📚 FAN BAZALAR", "/courses"):
        await db.set_step(chat_id, "select_course")
        await msg.answer("🎓 <b>Kursni tanlang:</b>", reply_markup=kb.courses_kb())
        return True
    if step == "select_course":
        await db.set_temp(chat_id, "filter_course", text)
        subjects = await db.product_subjects(text)
        if not subjects:
            await msg.answer("Ushbu kursda fanlar topilmadi.", reply_markup=kb.courses_kb())
        else:
            await db.set_step(chat_id, "select_subject")
            await msg.answer("📚 <b>Fanni tanlang:</b>", reply_markup=kb.reply_kb(subjects, back=True))
        return True
    if step == "select_subject":
        course = str(await db.get_temp(chat_id, "filter_course") or "")
        prods = await db.products_by(course, text)
        if not prods:
            await msg.answer("Kechirasiz, ushbu fandan fayllar topilmadi.")
        else:
            tag = await db.get_global_tag()
            await msg.answer("📂 <b>Quyidagi fayllar topildi:</b>")
            for p in prods:
                caption = (f"<b>Nomi:</b> {p['name']}\n<b>Kodi:</b> {p['code']}\n"
                           f"<b>Tavsif:</b> {p['description']}\n<b>Kodni olish:</b> /code")
                if tag:
                    caption += f"\n\n{tag}"
                try:
                    await bot.send_document(chat_id, p["file_id"], caption=caption)
                except Exception:
                    pass
        return True

    if text in ("📝 BUYURTMA BERISH", "/order"):
        await db.set_step(chat_id, "make_order_details")
        await msg.answer(
            "Siz bu yerdan bazaga buyurtma berishingiz yoki .docx/.pdf fayllarni .exe ga "
            "aylantirishingiz mumkin.\n\n👇 <b>Batafsil ma'lumot yozing:</b>",
            reply_markup=kb.reply_kb([], back=True),
        )
        return True
    if step == "make_order_details":
        await db.set_temp(chat_id, "order_text", text)
        await db.set_step(chat_id, "make_order_file")
        await msg.answer("📂 <b>Fayl yoki rasm bormi?</b>\n\nYuboring yoki <b>KERAK EMAS</b> tugmasini bosing:",
                         reply_markup=kb.reply_kb(["KERAK EMAS"], back=True))
        return True
    if step == "make_order_file":
        order_text = str(await db.get_temp(chat_id, "order_text") or "")
        name = (msg.from_user.first_name or "") if msg.from_user else ""
        admin_text = (f"🔔 <b>YANGI BUYURTMA!</b>\n\n👤 User: "
                      f"<a href='tg://user?id={chat_id}'>{name}</a>\n📝 Info: {order_text}")
        for aid in settings.admin_ids:
            try:
                if text == "KERAK EMAS":
                    await bot.send_message(aid, admin_text)
                else:
                    await bot.copy_message(aid, chat_id, msg.message_id, caption=admin_text)
            except Exception:
                pass
        await msg.answer("✅ <b>Buyurtmangiz qabul qilindi!</b>\nTez orada adminlar bog'lanishadi.",
                         reply_markup=kb.user_menu())
        await db.set_step(chat_id, "none")
        return True

    return False
