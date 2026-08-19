from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

MAIN_MENU_ROOMS = "🏨 Xonalar"
MAIN_MENU_MY_BOOKINGS = "📅 Mening bronlarim"
MAIN_MENU_HELP = "ℹ️ Yordam"
MAIN_MENU_SETTINGS = "⚙️ Sozlamalar"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MAIN_MENU_ROOMS)],
            [KeyboardButton(text=MAIN_MENU_MY_BOOKINGS)],
            [KeyboardButton(text=MAIN_MENU_HELP), KeyboardButton(text=MAIN_MENU_SETTINGS)],
        ],
        resize_keyboard=True,
    )


def language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbek"), KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇬🇧 English")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def contact_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
