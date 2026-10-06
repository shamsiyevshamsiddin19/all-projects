from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from core.database import db
from services.utils import check_user_subscription
from core.config import BOT_USERNAME
from services.lang import get_text, TEXTS

router = Router()

# Menyudagi funksiya tugmalari (barcha tillar bo'yicha). mode_selection faqat shu
# tugmalarga javob beradi, aks holda matn file_handlers'ga o'tib ketishi kerak
# (masalan PDF qirqish oralig'i, watermark matni, matn->docx va h.k.).
FEATURE_BUTTON_KEYS = [
    'btn_img_pdf', 'btn_zip', 'btn_text_docx', 'btn_pdf_docx', 'btn_merge_pdf',
    'btn_split_pdf', 'btn_watermark', 'btn_office_pdf', 'btn_ocr', 'btn_titul',
]
FEATURE_BUTTONS = {
    TEXTS[lang][key]
    for lang in TEXTS
    for key in FEATURE_BUTTON_KEYS
    if key in TEXTS[lang]
}

def get_main_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, 'btn_img_pdf')), KeyboardButton(text=get_text(lang, 'btn_zip'))],
            [KeyboardButton(text=get_text(lang, 'btn_text_docx')), KeyboardButton(text=get_text(lang, 'btn_pdf_docx'))],
            [KeyboardButton(text=get_text(lang, 'btn_office_pdf')), KeyboardButton(text=get_text(lang, 'btn_ocr'))],
            [KeyboardButton(text=get_text(lang, 'btn_merge_pdf')), KeyboardButton(text=get_text(lang, 'btn_split_pdf'))],
            [KeyboardButton(text=get_text(lang, 'btn_watermark')), KeyboardButton(text=get_text(lang, 'btn_titul'))],
            [KeyboardButton(text=get_text(lang, 'btn_settings'))]
        ],
        resize_keyboard=True
    )

def get_lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message):
    if message.chat.type != 'private':
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Botga o'tish", url=f"https://t.me/{BOT_USERNAME}")]
        ])
        await message.answer("<b>⚠️ Diqqat!</b>\nMen faqat shaxsiy yozishmalarda ishlayman.", reply_markup=kb)
        return

    await db.create_user(message.chat.id, message.from_user.full_name, message.from_user.username)
    await db.update_user(message.chat.id, mode=None, last_msg_id=None, finished=False)
    
    user = await db.get_user(message.chat.id)
    lang = user['lang'] if user and user['lang'] else 'uz'

    sub_check = await check_user_subscription(message.bot, message.chat.id)
    if not sub_check['status']:
        kb_buttons = [[InlineKeyboardButton(text="A'ZO BO'LISH", url=f"https://t.me/{ch[1:]}")] if ch.startswith('@') else [] for ch in sub_check['missing']]
        kb_buttons.append([InlineKeyboardButton(text="TEKSHIRISH", callback_data="check_sub")])
        await message.answer(
            "<b>Assalomu alaykum!</b>\nBotimizdan bepul foydalanish uchun homiy kanallarimizga a'zo bo'ling.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons)
        )
        return

    await message.answer(get_text(lang, 'welcome'), reply_markup=get_main_keyboard(lang))

@router.callback_query(F.data.startswith("lang_"))
async def process_lang_change(callback: CallbackQuery):
    lang_code = callback.data.split("_")[1]
    await db.update_user(callback.message.chat.id, lang=lang_code)
    await callback.answer(get_text(lang_code, 'lang_changed'))
    await callback.message.delete()
    await callback.message.answer(get_text(lang_code, 'welcome'), reply_markup=get_main_keyboard(lang_code))

@router.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery):
    sub_check = await check_user_subscription(callback.bot, callback.message.chat.id)
    user = await db.get_user(callback.message.chat.id)
    lang = user['lang'] if user and user['lang'] else 'uz'
    
    if sub_check['status']:
        await callback.answer("Rahmat! Botdan foydalanishingiz mumkin.")
        await callback.message.delete()
        await callback.message.answer(get_text(lang, 'welcome'), reply_markup=get_main_keyboard(lang))
    else:
        await callback.answer("Hali to'liq a'zo bo'lmadingiz!", show_alert=True)

@router.message(F.text.in_(['BOSH MENYU', 'ORQAGA', 'НАЗАД', 'BACK', 'MAIN MENU', 'ГЛАВНОЕ МЕНЮ']))
async def back_to_main(message: Message):
    await db.update_user(message.chat.id, mode=None, last_msg_id=None, finished=False)
    user = await db.get_user(message.chat.id)
    lang = user['lang'] if user and user['lang'] else 'uz'
    await message.answer(get_text(lang, 'welcome'), reply_markup=get_main_keyboard(lang))

@router.message(F.text.in_(["⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings"]))
async def settings_menu(message: Message):
    user = await db.get_user(message.chat.id)
    lang = user['lang'] if user and user['lang'] else 'uz'
    await message.answer(get_text(lang, 'choose_lang'), reply_markup=get_lang_keyboard())

# Faqat menyu tugmalariga javob beradi; boshqa matn file_handlers'ga o'tadi.
@router.message(F.text.in_(FEATURE_BUTTONS))
async def mode_selection(message: Message):
    user = await db.get_user(message.chat.id)
    lang = user['lang'] if user and user['lang'] else 'uz'
    text = message.text
    
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='BOSH MENYU')]], resize_keyboard=True)
    
    if text == get_text(lang, 'btn_img_pdf'):
        await db.update_user(message.chat.id, mode='pdf')
        await message.answer("Rasmlarni yuboring, bitta PDF qilib beraman.", reply_markup=kb)
    elif text == get_text(lang, 'btn_zip'):
        await db.update_user(message.chat.id, mode='zip')
        await message.answer("Fayllarni yuboring, ZIP qilib beraman.", reply_markup=kb)
    elif text == get_text(lang, 'btn_text_docx'):
        await db.update_user(message.chat.id, mode='text_to_doc')
        await message.answer("Menga matn yuboring, uni Word (.docx) qilib beraman.", reply_markup=kb)
    elif text == get_text(lang, 'btn_pdf_docx'):
        await db.update_user(message.chat.id, mode='pdf_to_docx')
        await message.answer("PDF hujjat yuboring, uni Word formatiga o'zgartirib beraman.", reply_markup=kb)
    elif text == get_text(lang, 'btn_merge_pdf'):
        await db.update_user(message.chat.id, mode='merge_pdf')
        await message.answer("Birlashtirmoqchi bo'lgan PDF fayllaringizni ketma-ket yuboring.", reply_markup=kb)
    elif text == get_text(lang, 'btn_split_pdf'):
        await db.update_user(message.chat.id, mode='split_pdf')
        await message.answer("Qirqmoqchi bo'lgan PDF faylni yuboring.", reply_markup=kb)
    elif text == get_text(lang, 'btn_watermark'):
        await db.update_user(message.chat.id, mode='watermark_pdf')
        await message.answer("Watermark bosiladigan PDF faylni yuboring.", reply_markup=kb)
    elif text == get_text(lang, 'btn_office_pdf'):
        await db.update_user(message.chat.id, mode='office_to_pdf')
        await message.answer("Word (docx), Excel (xlsx) yoki PowerPoint (pptx) fayl yuboring.", reply_markup=kb)
    elif text == get_text(lang, 'btn_ocr'):
        await db.update_user(message.chat.id, mode='ocr')
        await message.answer("Matnli rasmni yuboring, uni o'qib matn/word qilib beraman.", reply_markup=kb)
    elif text == get_text(lang, 'btn_titul'):
        import os
        from aiogram.types import FSInputFile
        file_path = os.path.join("assets", "tuit_titul.docx")
        if os.path.exists(file_path):
            await message.answer_document(FSInputFile(file_path), caption="TUIT titul varaqasi.")
        else:
            await message.answer("Hozircha bu fayl bazada yo'q.")
