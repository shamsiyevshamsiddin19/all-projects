"""Buyurtma berish — to'liq FSM.

Oqim: tur → mavzu → detallar → OTM (titul uchun) → til → hajm → format →
tarif (Standart/Premium) → to'lov → jonli progress bilan generatsiya →
fayl + cashback + baho → (ixtiyoriy) bepul revizyon.
"""
from __future__ import annotations
import asyncio
import logging
import os
import time
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from bot.states.order import OrderStates, ReviseStates, RateStates
from bot.keyboards.inline import (
    doc_types_kb, language_kb, format_kb, payment_kb, main_menu,
    tier_kb, otm_kb, rating_kb, share_kb, retry_kb, order_done_kb,
)
from db.crud import (
    create_order, set_order_status, get_order, update_balance,
    get_balance, create_payment, get_user, save_user_otm,
    add_rating, set_rating_comment, increment_revisions,
)
from db.models import User
from payment.click import make_click_url
from config import settings, DOC_TYPES

logger = logging.getLogger(__name__)
router = Router()

# Titul varag'i so'raladigan (OTM kerak) turlar
_OTM_TYPES = ("referat", "mustaqil", "kurs", "diplom")
# Premium tarif taklif qilinadigan turlar
_TIER_TYPES = ("referat", "mustaqil", "kurs", "diplom", "maqola", "tezis")
# Revizyon mumkin bo'lgan eng katta hajm (butun matn qayta ishlanadi)
_REVISE_MAX_PAGES = 30
_REVISE_LIMIT = 2


def _nice_filename(topic: str, doc_type: str, ext: str) -> str:
    """Fayl nomi: mavzu + hujjat turi (Telegram'da chiroyli ko'rinadi)."""
    import re as _re
    name = _re.sub(r'[<>:"/\\|?*\n\r]+', " ", topic or "Hujjat")
    name = _re.sub(r"\s+", " ", name).strip()[:60].strip(" .")
    label = DOC_TYPES.get(doc_type, {}).get("label", "")
    return f"{name} ({label}).{ext}" if label else f"{name}.{ext}"


def _eta(doc_type: str, pages: int) -> str:
    if doc_type in ("slayd", "krasword"):
        return "1-2 daqiqa"
    if pages >= 20:
        return "7-15 daqiqa"
    if pages >= 10:
        return "5-10 daqiqa"
    return "2-4 daqiqa"


@router.message(F.text == "📝 Buyurtma berish")
async def start_order(message: Message, state: FSMContext):
    if settings.maintenance():
        await message.answer(
            "🛠 <b>Texnik tanaffus</b>\n\n"
            "Hozircha yangi buyurtmalar vaqtincha to'xtatilgan. "
            "Iltimos, birozdan keyin urinib ko'ring.",
            parse_mode="HTML",
        )
        return
    await state.clear()
    await message.answer(
        "📋 <b>Qanday hujjat kerak?</b>\n\n"
        "Hujjat turini tanlang 👇",
        parse_mode="HTML",
        reply_markup=doc_types_kb(),
    )


@router.callback_query(F.data.startswith("doctype:"))
async def choose_doc_type(call: CallbackQuery, state: FSMContext):
    doc_type = call.data.split(":")[1]
    if doc_type not in DOC_TYPES:
        await call.answer("Noma'lum hujjat turi")
        return
    info = DOC_TYPES[doc_type]
    await state.update_data(doc_type=doc_type)
    await state.set_state(OrderStates.entering_topic)
    per = settings.per_unit(doc_type)
    await call.message.edit_text(
        f"{info['emoji']} <b>{info['label']}</b>\n\n"
        f"{info['desc']}\n\n"
        f"💰 <b>Narx:</b> {settings.min_price(doc_type):,} so'm dan "
        f"(har {info['unit']} {per:,} so'm)\n"
        f"📑 <b>Tavsiya:</b> {info['cmin']}-{info['cmax']} {info['unit']}\n\n"
        "✏️ <b>Hujjat mavzusini kiriting:</b>\n"
        "<i>Masalan: Qishloq xo'jaligida raqamlashtirish</i>",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(OrderStates.entering_topic)
async def enter_topic(message: Message, state: FSMContext):
    topic = message.text.strip()
    if len(topic) < 5:
        await message.answer("⚠️ Mavzu juda qisqa. Kamida 5 ta harf kiriting.")
        return
    if len(topic) > 300:
        await message.answer("⚠️ Mavzu juda uzun. 300 ta harfdan kam bo'lsin.")
        return
    await state.update_data(topic=topic)

    data = await state.get_data()
    doc_type = data["doc_type"]

    # Krossvord uchun qo'shimcha ma'lumot shart emas
    if doc_type == "krasword":
        await state.update_data(details={})
        await state.set_state(OrderStates.choosing_language)
        await message.answer(
            "👍 <b>Yaxshi mavzu!</b>\n\n🌐 <b>Tilni tanlang:</b>",
            parse_mode="HTML",
            reply_markup=language_kb(),
        )
        return

    await state.set_state(OrderStates.entering_details)
    prompt = _details_prompt(doc_type)
    await message.answer(prompt, parse_mode="HTML")


def _details_prompt(doc_type: str) -> str:
    if doc_type in ("referat", "mustaqil", "kurs", "diplom"):
        return (
            "📝 <b>Qo'shimcha ma'lumot kiriting</b> — titul varag'iga yoziladi:\n\n"
            "<code>Fan: Iqtisodiyot\n"
            "Talaba: Aliyev Sardor\n"
            "Guruh: IT-23\n"
            "Rahbar: Rahimov B.X.</code>\n\n"
            "<i>Agar ma'lumot yo'q bo'lsa, <b>o'tkazib yuborish</b> yozing</i>"
        )
    elif doc_type in ("tezis", "maqola"):
        return (
            "📝 <b>Muallif ma'lumotlarini kiriting:</b>\n\n"
            "<code>Fan: Informatika\n"
            "Muallif: Aliyev Sardor\n"
            "Tashkilot: Toshkent axborot texnologiyalari universiteti (TATU), IT-23</code>\n\n"
            "<i>Agar yo'q bo'lsa, <b>o'tkazib yuborish</b> yozing</i>"
        )
    return "📝 <b>Fan nomini kiriting</b> (yoki <b>o'tkazib yuborish</b>):"


@router.message(OrderStates.entering_details)
async def enter_details(message: Message, state: FSMContext):
    text = message.text.strip()
    details = {}
    if text.lower() not in ("o'tkazib yuborish", "otkazib yuborish", "-", "skip"):
        for line in text.split("\n"):
            if ":" in line:
                key, _, val = line.partition(":")
                details[key.strip().lower()] = val.strip()
    await state.update_data(details=details)

    data = await state.get_data()
    doc_type = data["doc_type"]

    # Titul varag'i uchun OTM so'raymiz (referat/mustaqil/kurs/diplom)
    if doc_type in _OTM_TYPES:
        user = await get_user(message.from_user.id)
        prev = getattr(user, "otm", None) if user else None
        await state.set_state(OrderStates.entering_otm)
        await message.answer(
            "🏛 <b>OTM (universitet) nomini kiriting</b> — titul varag'iga yoziladi:\n"
            "<i>Masalan: Toshkent davlat iqtisodiyot universiteti</i>",
            parse_mode="HTML",
            reply_markup=otm_kb(prev),
        )
        return

    await state.set_state(OrderStates.choosing_language)
    await message.answer(
        "🌐 <b>Hujjat tilini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=language_kb(),
    )


async def _otm_done(target, state: FSMContext, otm: str | None):
    data = await state.get_data()
    details = data.get("details", {})
    if otm:
        details["otm"] = otm
        await state.update_data(details=details)
    await state.set_state(OrderStates.choosing_language)
    await target.answer(
        "🌐 <b>Hujjat tilini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=language_kb(),
    )


@router.message(OrderStates.entering_otm)
async def enter_otm(message: Message, state: FSMContext):
    otm = (message.text or "").strip()
    if otm.lower() in ("o'tkazib yuborish", "otkazib yuborish", "-", "skip"):
        otm = ""
    if otm:
        await save_user_otm(message.from_user.id, otm)
    await _otm_done(message, state, otm or None)


@router.callback_query(OrderStates.entering_otm, F.data.startswith("otm:"))
async def otm_button(call: CallbackQuery, state: FSMContext):
    action = call.data.split(":")[1]
    otm = None
    if action == "prev":
        user = await get_user(call.from_user.id)
        otm = getattr(user, "otm", None) if user else None
    await call.message.delete()
    await _otm_done(call.message, state, otm)
    await call.answer()


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(call: CallbackQuery, state: FSMContext):
    lang = call.data.split(":")[1]
    await state.update_data(language=lang)
    data = await state.get_data()
    doc_type = data["doc_type"]
    info = DOC_TYPES[doc_type]
    per = settings.per_unit(doc_type)
    await state.set_state(OrderStates.entering_count)
    await call.message.edit_text(
        f"📏 <b>Nechta {info['unit']} kerak?</b>\n\n"
        f"{info['desc']}\n\n"
        f"✍️ <b>{info['cmin']} dan {info['cmax']} gacha</b> son kiriting "
        f"(masalan: <code>{info['cdef']}</code>)\n\n"
        f"💰 Narx: har {info['unit']} <b>{per:,} so'm</b> "
        f"(eng kami {settings.min_price(doc_type):,} so'm)",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(OrderStates.entering_count)
async def enter_count(message: Message, state: FSMContext):
    data = await state.get_data()
    doc_type = data["doc_type"]
    info = DOC_TYPES[doc_type]
    raw = (message.text or "").strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        await message.answer(
            f"⚠️ Iltimos, <b>son</b> kiriting ({info['cmin']}-{info['cmax']} {info['unit']}).",
            parse_mode="HTML")
        return
    count = int(digits)
    if count < info["cmin"] or count > info["cmax"]:
        await message.answer(
            f"⚠️ <b>{info['cmin']} dan {info['cmax']} gacha</b> bo'lsin "
            f"({info['unit']}). Siz <b>{count}</b> kiritdingiz.",
            parse_mode="HTML")
        return
    price = settings.price_for_user(message.from_user.id, doc_type, count)
    await state.update_data(page_count=count, price=price)
    await state.set_state(OrderStates.choosing_format)
    extras = ("jadval, grafik va formulalari bilan"
              if doc_type not in ("slayd", "krasword") else "professional dizaynda")
    await message.answer(
        f"✅ <b>{count} {info['unit']}</b> — {extras}\n"
        f"💰 Narx: <b>{price:,} so'm</b>\n\n"
        "📄 <b>Fayl formatini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=format_kb(doc_type),
    )


@router.callback_query(F.data.startswith("format:"))
async def choose_format(call: CallbackQuery, state: FSMContext, db_user: User):
    fmt = call.data.split(":")[1]
    await state.update_data(file_format=fmt)
    data = await state.get_data()
    doc_type = data["doc_type"]

    # Premium tarif taklifi (matnli hujjatlar uchun)
    if doc_type in _TIER_TYPES:
        price = data.get("price") or settings.price_for_user(
            call.from_user.id, doc_type,
            data.get("page_count", DOC_TYPES[doc_type]["cdef"]))
        premium_price = (settings.eff_vip_price() if settings.is_vip(call.from_user.id)
                         else int(round(price * settings.premium_mult(), -2)))
        await state.set_state(OrderStates.choosing_tier)
        await call.message.edit_text(
            "⚙️ <b>Sifat darajasini tanlang:</b>\n\n"
            f"⚡ <b>Standart</b> — {price:,} so'm\n"
            "Kuchli AI, to'liq tuzilma, jadval-grafiklar bilan.\n\n"
            f"👑 <b>Premium</b> — {premium_price:,} so'm\n"
            "Eng kuchli AI modeli: chuqurroq tahlil, boyroq til, "
            "murakkab mavzularda sezilarli ustunlik. Kurs ishi va diplom "
            "uchun tavsiya etiladi.",
            parse_mode="HTML",
            reply_markup=tier_kb(price, premium_price),
        )
        await call.answer()
        return

    await _create_order_flow(call, state, db_user)


@router.callback_query(OrderStates.choosing_tier, F.data.startswith("tier:"))
async def choose_tier(call: CallbackQuery, state: FSMContext, db_user: User):
    tier = call.data.split(":")[1]
    data = await state.get_data()
    details = data.get("details", {})
    if tier == "premium":
        details["tier"] = "premium"
        if settings.is_vip(call.from_user.id):
            price = settings.eff_vip_price()
        else:
            price = int(round((data.get("price") or 0) * settings.premium_mult(), -2))
        await state.update_data(details=details, price=price)
    else:
        details.pop("tier", None)
        await state.update_data(details=details)
    await _create_order_flow(call, state, db_user)


async def _create_order_flow(call: CallbackQuery, state: FSMContext, db_user: User):
    """Buyurtma + to'lov yozuvini yaratib, tasdiqlash xabarini chiqaradi."""
    data = await state.get_data()
    doc_type = data["doc_type"]
    count = data.get("page_count", DOC_TYPES[doc_type]["cdef"])
    price = data.get("price") or settings.price_for_user(
        call.from_user.id, doc_type, count)
    balance = db_user.balance

    order = await create_order(
        user_id=call.from_user.id,
        doc_type=doc_type,
        topic=data["topic"],
        details=data.get("details", {}),
        language=data.get("language", "uz"),
        page_count=count,
        price=price,
        paid_from="click",
    )
    await set_order_status(order.id, "pending", file_format=data.get("file_format", "docx"))

    payment = await create_payment(
        user_id=call.from_user.id, amount=price,
        order_id=order.id, payment_type="click",
    )
    click_url = make_click_url(payment.merchant_trans_id, price)

    await state.update_data(price=price, order_id=order.id)
    await state.set_state(OrderStates.confirming)
    summary = _order_summary(data, price, balance)
    await call.message.edit_text(
        summary, parse_mode="HTML",
        reply_markup=payment_kb(balance, price, order.id, click_url),
    )
    await call.answer()


def _order_summary(data: dict, price: int, balance: int) -> str:
    info = DOC_TYPES[data["doc_type"]]
    lang_map = {"uz": "O'zbek 🇺🇿", "ru": "Rus 🇷🇺", "en": "Ingliz 🇬🇧"}
    tier = data.get("details", {}).get("tier")
    lines = [
        f"📋 <b>Buyurtma tasdig'i</b>",
        f"",
        f"{info['emoji']} <b>Tur:</b> {info['label']}"
        + (" 👑 Premium" if tier == "premium" else ""),
        f"📌 <b>Mavzu:</b> {data.get('topic', '—')}",
        f"🌐 <b>Til:</b> {lang_map.get(data.get('language'), '—')}",
        f"📏 <b>Hajm:</b> {data.get('page_count', info['cdef'])} {info['unit']}",
        f"📄 <b>Format:</b> {data.get('file_format', 'docx').upper()}",
        f"💰 <b>Narx:</b> {price:,} so'm",
        f"",
        f"💳 <b>Balans:</b> {balance:,} so'm",
    ]
    if balance >= price:
        lines.append("✅ Balansingizdan to'lashingiz mumkin!")
    # Ishonch kafolati — to'lov oldidagi ikkilanishni kamaytiradi
    lines.append("")
    lines.append("🛡 <b>Kafolat:</b> yoqmasa — bepul qayta ishlaymiz. "
                 "Texnik xato bo'lsa — pul 100% qaytadi.")
    return "\n".join(lines)


@router.callback_query(F.data.startswith("pay:balance:"))
async def pay_from_balance(call: CallbackQuery, state: FSMContext, db_user: User):
    order_id = int(call.data.split(":")[2])
    order = await get_order(order_id)
    if not order or order.user_id != call.from_user.id:
        await call.answer("❌ Buyurtma topilmadi", show_alert=True)
        return
    price = order.price
    if db_user.balance < price:
        await call.answer("❌ Balans yetarli emas!", show_alert=True)
        return

    await update_balance(call.from_user.id, -price)
    await set_order_status(order_id, "generating", paid_from="balance")
    from db.crud import async_session
    from db.models import User as U
    async with async_session() as s:
        u = await s.get(U, call.from_user.id)
        if u:
            u.total_spent += price
            u.orders_count += 1
            await s.commit()
    await state.clear()

    await call.message.edit_text(
        f"✅ <b>To'lov qabul qilindi!</b>\n"
        f"💰 Balansingizdan {price:,} so'm yechildi.",
        parse_mode="HTML",
    )
    await call.answer("✅ To'lov qabul qilindi!")

    from services.notifications import notify_new_order
    await notify_new_order(call.bot, call.from_user, order.doc_type, order.topic,
                           order.page_count, price, "Balansdan")

    gen_data = _gen_data(order)
    asyncio.create_task(_generate_and_send(call.bot, call.from_user.id, order_id, gen_data))


def _gen_data(order) -> dict:
    return {
        "doc_type": order.doc_type, "topic": order.topic,
        "details": order.details or {}, "language": order.language,
        "page_count": order.page_count, "file_format": order.file_format or "docx",
    }


@router.callback_query(F.data.startswith("pay:cancel:"))
async def pay_cancel(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split(":")[2])
    await set_order_status(order_id, "refunded")
    await state.clear()
    await call.message.edit_text("❌ Buyurtma bekor qilindi.")
    await call.message.answer("🏠 Asosiy menyu", reply_markup=main_menu())
    await call.answer()


async def _notify_admins(bot, text: str):
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception:
            pass


_last_systemic_alert = 0.0


async def _alert_systemic(bot, detail: str):
    """AI kredit/kalit/kvota tugashi — SHOSHILINCH admin ogohlantirishi.
    10 daqiqada bir marta (ommaviy xatoda spam bo'lmasin)."""
    global _last_systemic_alert
    now = time.monotonic()
    if now - _last_systemic_alert < 600:
        return
    _last_systemic_alert = now
    await _notify_admins(
        bot,
        "🆘🆘 <b>SHOSHILINCH: AI provayder ishlamayapti!</b>\n"
        "Ehtimol Claude krediti/kaliti tugagan yoki kvota limiti.\n"
        "❗️ Har yangi buyurtma xato beryapti va pul qaytyapti.\n"
        "👉 <b>Tez orada .env dagi ANTHROPIC_API_KEY ni tekshiring/to'ldiring!</b>\n"
        f"<code>{detail}</code>",
    )


async def _generate_and_send(bot, user_id: int, order_id: int, data: dict):
    """AI hujjat yaratib Telegram'ga yuboradi (jonli progress bilan)."""
    from services import generator

    doc_type = data.get("doc_type", "referat")
    pages = data.get("page_count", 10)
    eta = _eta(doc_type, pages)
    qpos = generator.queue_size()
    queue_line = f"👥 Navbat: {qpos} ta buyurtma oldinda\n" if qpos else ""
    header = (f"⏳ <b>Hujjatingiz tayyorlanmoqda...</b>\n{queue_line}"
              f"🕒 Taxminan: <b>{eta}</b>\n"
              f"<i>Har bob alohida, jadval va grafiklari bilan sifatli yoziladi</i>")

    status_msg = None
    try:
        status_msg = await bot.send_message(user_id, header, parse_mode="HTML")
    except Exception:
        pass

    _last = {"t": 0.0, "text": ""}

    async def progress(text: str):
        if not status_msg:
            return
        now = time.monotonic()
        if now - _last["t"] < 3 or text == _last["text"]:
            return
        _last["t"], _last["text"] = now, text
        try:
            await status_msg.edit_text(header + f"\n\n{text}", parse_mode="HTML")
        except Exception:
            pass

    try:
        file_path, file_format, provider, source_text = await generator.generate_document(
            order_id, data, progress=progress)
        await set_order_status(order_id, "done",
                               file_path=file_path,
                               file_format=file_format,
                               ai_provider=provider,
                               source_text=source_text)

        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass

        order = await get_order(order_id)
        tier = (order.details or {}).get("tier") if order else None
        revisable = (doc_type not in ("slayd", "krasword")
                     and pages <= _REVISE_MAX_PAGES)
        caption = (
            f"✅ <b>Hujjatingiz tayyor!</b>\n"
            f"📄 Format: <b>{file_format.upper()}</b>"
            + (" · 👑 Premium" if tier == "premium" else "")
            + "\n<i>Yoqmagan joyi bo'lsa — «Qayta ishlash» bilan bepul tuzattiring</i>"
        )
        ext_map = {"docx": "document", "pdf": "document", "pptx": "document", "png": "photo"}
        send_type = ext_map.get(file_format, "document")
        topic = data.get("topic", "")
        input_file = FSInputFile(
            file_path, filename=_nice_filename(topic, doc_type, file_format))
        kb = order_done_kb(order_id, revisable=revisable)
        if send_type == "photo":
            msg = await bot.send_photo(user_id, input_file, caption=caption,
                                       parse_mode="HTML", reply_markup=kb)
            tg_id = msg.photo[-1].file_id
        else:
            msg = await bot.send_document(user_id, input_file, caption=caption,
                                          parse_mode="HTML", reply_markup=kb)
            tg_id = msg.document.file_id
        await set_order_status(order_id, "done", tg_file_id=tg_id)

        # Krossvord: rasmdan tashqari to'liq DOCX (katak + tariflar + javoblar)
        if doc_type == "krasword":
            docx_path = os.path.join(settings.tmp_dir, f"{order_id}.docx")
            if os.path.exists(docx_path):
                try:
                    await bot.send_document(
                        user_id,
                        FSInputFile(docx_path,
                                    filename=_nice_filename(topic, doc_type, "docx")),
                        caption="📄 Chop etish uchun: katakchalar, tariflar va javoblar")
                except Exception:
                    pass
                try:
                    os.remove(docx_path)
                except Exception:
                    pass

        try:
            os.remove(file_path)
        except Exception:
            pass

        # Cashback + baho so'rash
        cashback = 0
        pct = settings.eff_cashback_pct()
        if pct > 0 and order and order.price > 0:
            cashback = order.price * pct // 100
            if cashback > 0:
                await update_balance(user_id, cashback)
        cb_line = (f"💚 <b>+{cashback:,} so'm cashback</b> balansingizga qo'shildi "
                   f"(keyingi buyurtmaga chegirma)!\n\n" if cashback else "")
        try:
            await bot.send_message(
                user_id,
                f"{cb_line}⭐ <b>Hujjatni baholang</b> — sifatni yaxshilashga yordam beradi:",
                parse_mode="HTML",
                reply_markup=rating_kb(order_id),
            )
        except Exception:
            pass

        # Referal bonus tekshirish
        from services.referral import check_and_award
        await check_and_award(bot, user_id, doc_type)

    except Exception as e:
        logger.exception("Generatsiya xatosi order #%d: %s", order_id, e)
        order = await get_order(order_id)
        refunded = 0
        if order and order.status != "refunded" and order.price > 0:
            await update_balance(user_id, order.price)
            refunded = order.price
        await set_order_status(order_id, "refunded", error_msg=str(e)[:500])

        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
        refund_line = (f"💰 <b>{refunded:,} so'm</b> balansingizga qaytarildi.\n"
                       if refunded else "")
        await bot.send_message(
            user_id,
            "😔 <b>Kechirasiz, texnik xatolik yuz berdi.</b>\n"
            f"{refund_line}"
            "Pastdagi tugma bilan <b>bir bosishda</b> qayta urinib ko'ring — "
            "balansdagi mablag' yetarli bo'lsa, buyurtma darhol qayta boshlanadi.",
            parse_mode="HTML",
            reply_markup=retry_kb(order_id),
        )
        # Adminga ogohlantirish
        user_line = f"👤 <a href='tg://user?id={user_id}'>{user_id}</a>"
        err = str(e).lower()
        # Tizimli nosozlik (AI kredit/kalit/kvota tugashi) — SHOSHILINCH bildirish,
        # aks holda ommaviy refund boshlanadi
        systemic = any(k in err for k in (
            "credit", "billing", "quota", "insufficient", "balance is too low",
            "authentication", "invalid x-api-key", "401", "402", "429",
            "provayderlar sozlanmagan"))
        if systemic:
            await _alert_systemic(bot, str(e)[:200])
        await _notify_admins(
            bot,
            f"🚨 <b>Generatsiya xatosi</b> #{order_id}\n"
            f"{user_line} · {doc_type} · {pages} bet\n"
            f"❗️ <code>{str(e)[:300]}</code>",
        )


@router.callback_query(F.data.startswith("retry:"))
async def retry_order(call: CallbackQuery, db_user: User):
    """Xatodan keyin bir bosishda qayta urinish (balansdan qayta to'lab)."""
    order_id = int(call.data.split(":")[1])
    order = await get_order(order_id)
    if not order or order.user_id != call.from_user.id:
        await call.answer("❌ Buyurtma topilmadi", show_alert=True)
        return
    if order.status == "generating":
        await call.answer("⏳ Buyurtma allaqachon bajarilmoqda", show_alert=True)
        return
    if order.status != "refunded":
        await call.answer("Bu buyurtma qayta urinishga muhtoj emas", show_alert=True)
        return
    if db_user.balance < order.price:
        await call.answer("❌ Balans yetarli emas. Hisobni to'ldiring.", show_alert=True)
        return
    await update_balance(call.from_user.id, -order.price)
    await set_order_status(order_id, "generating", paid_from="balance", error_msg=None)
    await call.message.edit_text("🔄 <b>Qayta boshlandi!</b>", parse_mode="HTML")
    await call.answer("Boshladik!")
    asyncio.create_task(_generate_and_send(
        call.bot, call.from_user.id, order_id, _gen_data(order)))


# ─────────────────── BAHO (⭐) ───────────────────

@router.callback_query(F.data.startswith("rate:"))
async def rate_order(call: CallbackQuery, state: FSMContext):
    _, order_id, stars = call.data.split(":")
    order_id, stars = int(order_id), int(stars)
    order = await get_order(order_id)
    if not order or order.user_id != call.from_user.id:
        await call.answer("❌ Buyurtma topilmadi", show_alert=True)
        return
    await add_rating(order_id, call.from_user.id, stars)

    if stars >= 4:
        user = await get_user(call.from_user.id)
        ref_code = user.referral_code if user else ""
        await call.message.edit_text(
            f"{'⭐' * stars} <b>Rahmat!</b> 🎉\n\n"
            "Botdan mamnun bo'lsangiz, do'stlaringizga ulashing — "
            f"har bir do'stingizning birinchi buyurtmasidan "
            f"<b>bonus pul</b> olasiz! 👇",
            parse_mode="HTML",
            reply_markup=share_kb(settings.bot_username, ref_code),
        )
    else:
        await state.set_state(RateStates.waiting_comment)
        await state.update_data(rate_order_id=order_id)
        await call.message.edit_text(
            f"{'⭐' * stars} <b>Bahoyingiz uchun rahmat.</b>\n\n"
            "😔 Nima yoqmadi? Yozib qoldiring — keyingi safar yaxshiroq qilamiz.\n"
            "<i>(Yoki «Qayta ishlash» tugmasi bilan hujjatni bepul tuzattiring)</i>",
            parse_mode="HTML",
        )
    await call.answer()


@router.message(RateStates.waiting_comment)
async def rate_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("rate_order_id")
    await state.clear()
    if order_id:
        await set_rating_comment(order_id, message.text or "")
        await _notify_admins(
            message.bot,
            f"⚠️ <b>Past baho izohi</b> #{order_id}\n"
            f"👤 {message.from_user.full_name} (@{message.from_user.username})\n"
            f"💬 {(message.text or '')[:400]}",
        )
    await message.answer(
        "🙏 <b>Rahmat!</b> Fikringiz sifatni yaxshilashga ishlatiladi.",
        parse_mode="HTML", reply_markup=main_menu(),
    )


# ─────────────────── REVIZYON (bepul qayta ishlash) ───────────────────

@router.callback_query(F.data.startswith("revise:"))
async def revise_start(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split(":")[1])
    order = await get_order(order_id)
    if not order or order.user_id != call.from_user.id:
        await call.answer("❌ Buyurtma topilmadi", show_alert=True)
        return
    if order.status != "done" or not order.source_text:
        await call.answer("Bu buyurtmani qayta ishlab bo'lmaydi", show_alert=True)
        return
    if (order.revisions or 0) >= _REVISE_LIMIT:
        await call.answer(
            f"Bepul revizyon limiti tugagan ({_REVISE_LIMIT}/{_REVISE_LIMIT}). "
            "Yangi buyurtma bering.", show_alert=True)
        return
    if order.page_count > _REVISE_MAX_PAGES:
        await call.answer("Katta hajmli ishlar uchun revizyon hozircha mavjud emas",
                          show_alert=True)
        return
    await state.set_state(ReviseStates.waiting_feedback)
    await state.update_data(revise_order_id=order_id)
    left = _REVISE_LIMIT - (order.revisions or 0)
    await call.message.answer(
        f"✏️ <b>Nimani o'zgartirish kerak?</b> (bepul: {left}/{_REVISE_LIMIT})\n\n"
        "O'qituvchi izohini yoki o'z talabingizni yozib yuboring.\n"
        "<i>Masalan: «2-bobga statistika qo'shilsin», «Kirish qisqartirilib, "
        "xulosa kengaytirilsin», «Adabiyotlar GOST formatida bo'lsin»</i>",
        parse_mode="HTML",
    )
    await call.answer()


@router.message(ReviseStates.waiting_feedback)
async def revise_feedback(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("revise_order_id")
    await state.clear()
    feedback = (message.text or "").strip()
    if not order_id or len(feedback) < 5:
        await message.answer("⚠️ Izoh juda qisqa. Qaytadan urinib ko'ring.")
        return
    status = await message.answer(
        "♻️ <b>Hujjat qayta ishlanmoqda...</b>\n"
        "🕒 Taxminan 2-5 daqiqa.",
        parse_mode="HTML",
    )
    asyncio.create_task(_revise_and_send(
        message.bot, message.from_user.id, order_id, feedback, status))


async def _revise_and_send(bot, user_id: int, order_id: int, feedback: str, status_msg):
    from ai import provider as ai
    from ai import prompts
    from services import generator

    try:
        order = await get_order(order_id)
        if not order or not order.source_text:
            raise RuntimeError("Buyurtma matni topilmadi")
        label = DOC_TYPES.get(order.doc_type, {}).get("label", order.doc_type)
        sys_p, user_p = prompts.revise(label, order.topic, order.source_text,
                                       feedback, order.language)
        details = order.details or {}
        model = (settings.claude_model_premium
                 if details.get("tier") == "premium" else None)
        max_tok = max(6000, min(order.page_count * 1100 + 2000, 32000))
        new_text, prov = await ai.generate(sys_p, user_p, max_tokens=max_tok, model=model)
        if len(new_text.split()) < len(order.source_text.split()) * 0.5:
            raise RuntimeError("Revizyon natijasi juda qisqa chiqdi")

        path, fmt = await generator.rebuild_file(order_id, _gen_data(order), new_text)
        revs = await increment_revisions(order_id)
        await set_order_status(order_id, "done", source_text=new_text)

        try:
            await status_msg.delete()
        except Exception:
            pass
        left = max(0, _REVISE_LIMIT - revs)
        revisable = left > 0
        msg = await bot.send_document(
            user_id,
            FSInputFile(path, filename=_nice_filename(order.topic, order.doc_type, fmt)),
            caption=(f"♻️ <b>Qayta ishlangan hujjat tayyor!</b>\n"
                     f"📄 Format: <b>{fmt.upper()}</b> · "
                     f"Qolgan bepul revizyon: {left}/{_REVISE_LIMIT}"),
            parse_mode="HTML",
            reply_markup=order_done_kb(order_id, revisable=revisable),
        )
        await set_order_status(order_id, "done", tg_file_id=msg.document.file_id)
        try:
            os.remove(path)
        except Exception:
            pass
    except Exception as e:
        logger.exception("Revizyon xatosi #%s: %s", order_id, e)
        try:
            await status_msg.delete()
        except Exception:
            pass
        await bot.send_message(
            user_id,
            "😔 Qayta ishlashda xatolik. Revizyon limiti sarflanmadi — "
            "birozdan keyin yana urinib ko'ring.",
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("redownload:"))
async def redownload(call: CallbackQuery):
    order_id = int(call.data.split(":")[1])
    order = await get_order(order_id)
    if not order or order.user_id != call.from_user.id:
        await call.answer("❌ Buyurtma topilmadi", show_alert=True)
        return
    if order.tg_file_id:
        ext = order.file_format or "docx"
        if ext == "png":
            await call.message.answer_photo(order.tg_file_id,
                                            caption=f"📄 #{order.id} buyurtma — {order.topic[:50]}")
        else:
            await call.message.answer_document(order.tg_file_id,
                                               caption=f"📄 #{order.id} buyurtma — {order.topic[:50]}")
        await call.answer("✅ Yuborildi!")
    else:
        await call.answer("❌ Fayl saqlanmagan", show_alert=True)


@router.callback_query(F.data.startswith("back:"))
async def go_back(call: CallbackQuery, state: FSMContext):
    where = call.data.split(":")[1]
    data = await state.get_data()
    doc_type = data.get("doc_type", "referat")
    if where == "topic":
        await state.set_state(OrderStates.entering_topic)
        await call.message.edit_text("✏️ <b>Hujjat mavzusini kiriting:</b>", parse_mode="HTML")
    elif where == "lang":
        await state.set_state(OrderStates.choosing_language)
        await call.message.edit_text("🌐 <b>Tilni tanlang:</b>", parse_mode="HTML",
                                     reply_markup=language_kb())
    elif where in ("count", "pages"):
        info = DOC_TYPES[doc_type]
        await state.set_state(OrderStates.entering_count)
        await call.message.edit_text(
            f"📏 <b>Nechta {info['unit']} kerak?</b>\n"
            f"✍️ {info['cmin']} dan {info['cmax']} gacha son kiriting.",
            parse_mode="HTML")
    await call.answer()
