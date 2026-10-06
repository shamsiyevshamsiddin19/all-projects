from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from apps.accounts.models import LanguageChoices

from ..keyboards.reply import (
    MAIN_MENU_HELP,
    MAIN_MENU_SETTINGS,
    contact_request_keyboard,
    language_keyboard,
    main_menu_keyboard,
)
from ..states import ProfileStates

router = Router(name="start")

LANGUAGE_LABELS = {
    "🇺🇿 O'zbek": LanguageChoices.UZ,
    "🇷🇺 Русский": LanguageChoices.RU,
    "🇬🇧 English": LanguageChoices.EN,
}


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user):
    await state.clear()
    if not user.phone_number:
        await state.set_state(ProfileStates.choosing_language)
        await message.answer(
            "Assalomu alaykum! HotelBookingBot ga xush kelibsiz.\n\nIltimos, tilni tanlang:",
            reply_markup=language_keyboard(),
        )
        return

    await message.answer(
        f"Xush kelibsiz, {user.full_name}! 🏨",
        reply_markup=main_menu_keyboard(),
    )


@router.message(ProfileStates.choosing_language, F.text.in_(LANGUAGE_LABELS.keys()))
async def choose_language(message: Message, state: FSMContext, user):
    user.language = LANGUAGE_LABELS[message.text]
    await user.asave(update_fields=["language"])

    if user.phone_number:
        await state.clear()
        await message.answer("Til saqlandi ✅", reply_markup=main_menu_keyboard())
        return

    await state.set_state(ProfileStates.waiting_for_phone)
    await message.answer(
        "Rahmat! Endi telefon raqamingizni yuboring:", reply_markup=contact_request_keyboard()
    )


@router.message(ProfileStates.waiting_for_phone, F.contact)
async def receive_phone(message: Message, state: FSMContext, user):
    user.phone_number = message.contact.phone_number
    await user.asave(update_fields=["phone_number"])
    await state.clear()
    await message.answer("Ro'yxatdan o'tish yakunlandi! ✅", reply_markup=main_menu_keyboard())


@router.message(F.text == MAIN_MENU_HELP)
async def help_handler(message: Message):
    await message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "🏨 Xonalar — mavjud xona turlarini ko'rish va bron qilish.\n"
        "📅 Mening bronlarim — bronlaringizni kuzatish va bekor qilish.\n\n"
        "Savollar bo'lsa mehmonxona administratoriga murojaat qiling."
    )


@router.message(F.text == MAIN_MENU_SETTINGS)
async def settings_handler(message: Message, state: FSMContext):
    await state.set_state(ProfileStates.choosing_language)
    await message.answer("Tilni tanlang:", reply_markup=language_keyboard())
