"""Marketing uchun optimallashtirilgan /start handler."""
from __future__ import annotations
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from db.crud import get_or_create_user, get_user_by_code
from db.models import User
from bot.keyboards.inline import main_menu, doc_types_kb
from bot.states.order import OrderStates
from config import settings, DOC_TYPES

router = Router()

_WELCOME = """🎓 <b>Xush kelibsiz, {name}!</b>

📚 Men talabalar uchun akademik hujjatlar tayyorlaydigan <b>AI yordamchiman</b>.

<b>Nima yozib bera olaman?</b>
📄 Referat · 📝 Mustaqil ish · 📊 Slayd (PPTX)
📋 Tezis · 📰 Maqola · 🎯 Krossvord
📚 Kurs ishi · 🎓 Diplom ishi

<b>Nega aynan bu bot?</b>
✅ <b>Jadval, grafik va formulalar</b> — o'qituvchi talab qiladigan darajada
✅ <b>Titul varag'i</b> va to'liq akademik tuzilma tayyor holda
✅ Fanga moslashadi: iqtisodga statistika, matematikaga formulalar
✅ Sahifa hajmi aniq — necha bet buyurtsangiz, shuncha chiqadi
✅ Yoqmasa — <b>bepul qayta ishlash</b>
✅ <b>DOCX, PDF, PPTX</b> · O'zbek / Rus / Ingliz{bonus_line}{stats_line}

⬇️ <b>Buyurtma berish uchun tugmani bosing!</b>"""

_WELCOME_REF = _WELCOME + "\n\n🎁 <b>{ref_name}</b> taklifi bilan kelgansiz!"


async def _stats_line() -> str:
    """Jonli ijtimoiy isbot — bazadagi haqiqiy raqamlar (kichik bo'lsa ko'rsatilmaydi)."""
    parts = []
    try:
        from db.crud import public_stats, avg_rating
        st = await public_stats()
        if st["done_orders"] >= 30:
            parts.append(f"📊 <b>{st['done_orders']:,} ta hujjat</b> tayyorlandi")
        avg, cnt = await avg_rating()
        if cnt >= 10 and avg >= 4.0:
            parts.append(f"⭐ <b>{avg}/5</b> ({cnt} baho)")
    except Exception:
        pass
    return ("\n\n" + " · ".join(parts)) if parts else ""


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    user = message.from_user
    referrer_id = None

    # Argumentlarni tekshirish (ref_ yoki order_)
    arg = command.args or ""
    order_doc_type = None
    if arg.startswith("ref_"):
        code = arg[4:]
        referrer = await get_user_by_code(code)
        if referrer and referrer.id != user.id:
            referrer_id = referrer.id
    elif arg.startswith("order_"):
        candidate = arg[6:]
        if candidate in DOC_TYPES:
            order_doc_type = candidate

    db_user = await get_or_create_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        referred_by=referrer_id,
    )

    # Yangi foydalanuvchiga xush kelibsiz bonusi (halol reciprocity)
    bonus_line = ""
    if getattr(db_user, "_is_new", False):
        bonus = settings.eff_welcome_bonus()
        if bonus > 0:
            from db.crud import update_balance
            await update_balance(user.id, bonus)
            bonus_line = (f"\n\n🎁 <b>Sovg'a:</b> hisobingizga <b>{bonus:,} so'm</b> "
                          f"boshlang'ich bonus qo'shildi!")

    # Inline rejimdan kelgan to'g'ridan buyurtma — darrov hujjat turini tanlab
    # mavzu so'raymiz (marketing: bir tegishda buyurtma).
    if order_doc_type:
        info = DOC_TYPES[order_doc_type]
        await state.update_data(doc_type=order_doc_type)
        await state.set_state(OrderStates.entering_topic)
        await message.answer(
            f"{info['emoji']} <b>{info['label']}</b>\n\n"
            f"{info['desc']}\n\n"
            f"💰 <b>Narx:</b> {settings.min_price(order_doc_type):,} so'm dan "
            f"(har {info['unit']} {settings.per_unit(order_doc_type):,} so'm)\n\n"
            "✏️ <b>Hujjat mavzusini kiriting:</b>\n"
            "<i>Masalan: Qishloq xo'jaligida raqamlashtirish</i>",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )
        return

    name = user.first_name or "Foydalanuvchi"
    stats = await _stats_line()
    if referrer_id:
        ref_user = await get_or_create_user(referrer_id)
        ref_name = ref_user.full_name or ref_user.username or "Do'stingiz"
        text = _WELCOME_REF.format(name=name, ref_name=ref_name,
                                   bonus_line=bonus_line, stats_line=stats)
    else:
        text = _WELCOME.format(name=name, bonus_line=bonus_line, stats_line=stats)

    await message.answer(text, parse_mode="HTML", reply_markup=main_menu())


_SAMPLE_FILES = {
    "referat": ("referat.docx", "📄 <b>Referat namunasi</b> — 12 bet, jadval va grafik bilan"),
    "mustaqil": ("mustaqil.docx", "📝 <b>Mustaqil ish namunasi</b> — to'liq tuzilma, titul varag'i bilan"),
    "slayd": ("slayd.pptx", "📊 <b>Slayd namunasi</b> — professional dizayn, diagrammalar bilan"),
}


@router.message(F.text == "🎁 Bepul namuna")
async def samples_menu(message: Message):
    from bot.keyboards.inline import samples_kb
    await message.answer(
        "🎁 <b>Bepul namuna</b>\n\n"
        "To'lovsiz, tayyor namunani ko'rib chiqing — sifatimizga ishonch hosil qiling. "
        "Namunalar aynan bot yaratgan haqiqiy hujjatlar.\n\n"
        "Qaysi turini ko'rmoqchisiz? 👇",
        parse_mode="HTML",
        reply_markup=samples_kb(),
    )


@router.callback_query(F.data.startswith("sample:"))
async def send_sample(call: CallbackQuery):
    import os
    from aiogram.types import FSInputFile
    from db.crud import get_setting, set_setting
    stype = call.data.split(":")[1]
    if stype not in _SAMPLE_FILES:
        await call.answer("Namuna topilmadi")
        return
    fname, caption = _SAMPLE_FILES[stype]
    await call.answer("📤 Yuborilmoqda...")
    caption += "\n\n<i>Yoqdimi? «📝 Buyurtma berish» bilan o'zingizniki yarating!</i>"

    # Kesh: avval yuborilgan bo'lsa tg_file_id bilan darhol (qayta yuklashsiz)
    fid = await get_setting(f"sample_fid_{stype}")
    if fid:
        try:
            await call.message.answer_document(fid, caption=caption, parse_mode="HTML")
            return
        except Exception:
            pass  # file_id eskirgan bo'lsa fayldan qayta yuboramiz

    path = os.path.join(settings.tmp_dir, "..", "samples", fname)
    path = os.path.abspath(path)
    if not os.path.exists(path):
        # Server yo'li: /opt/mustaqilbot/samples/
        alt = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                           "samples", fname)
        path = alt if os.path.exists(alt) else path
    if not os.path.exists(path):
        await call.message.answer(
            "😔 Namuna hozircha tayyorlanmoqda. «📝 Buyurtma berish» orqali "
            "o'z hujjatingizni yaratishingiz mumkin.", parse_mode="HTML")
        return
    msg = await call.message.answer_document(
        FSInputFile(path, filename=fname), caption=caption, parse_mode="HTML")
    try:
        await set_setting(f"sample_fid_{stype}", msg.document.file_id)
    except Exception:
        pass


@router.message(F.text == "ℹ️ Yordam")
async def help_cmd(message: Message):
    prices = "\n".join(
        f"{i['emoji']} {i['label']} — {settings.min_price(k):,} so'm dan "
        f"({i['cmin']}-{i['cmax']} {i['unit']})"
        for k, i in DOC_TYPES.items()
    )
    contact = (f"\n\n<b>🆘 Yordam kerakmi?</b> {settings.admin_contact} ga yozing"
               if settings.admin_contact else "")
    txt = f"""<b>📖 Yordam</b>

<b>Buyurtma berish:</b>
1️⃣ «📝 Buyurtma berish» tugmasini bosing
2️⃣ Hujjat turini tanlang (qoidalari ko'rsatiladi)
3️⃣ Mavzu va kerakli ma'lumotni yozing
4️⃣ <b>Nechta bet/slayd/so'z</b> kerakligini kiriting
5️⃣ To'lang (Click yoki balans) → fayl avtomatik keladi!

<b>💰 Narxlar</b> (sahifa soniga qarab):
{prices}

<b>📄 Formatlar:</b> Word (DOCX), PDF, PowerPoint (PPTX)
<b>🌐 Tillar:</b> O'zbek, Rus, Ingliz

<b>💳 To'lov:</b> Click (UzCard/Humo) yoki hisob balansi

<b>🤝 Referal:</b> Do'stingizni taklif qiling — ular to'lov qilganda sizga bonus tushadi!{contact}"""
    await message.answer(txt, parse_mode="HTML", reply_markup=main_menu())


@router.callback_query(F.data == "main_menu")
async def to_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_reply_markup()
    await call.message.answer(
        "🏠 Asosiy menyu", reply_markup=main_menu()
    )
    await call.answer()


@router.callback_query(F.data == "new_order")
async def new_order_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(
        "📝 <b>Hujjat turini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=doc_types_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "cancel")
async def cancel_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_reply_markup()
    await call.message.answer("❌ Bekor qilindi.", reply_markup=main_menu())
    await call.answer()
