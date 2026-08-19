"""tatulmsbot klaviaturalari."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from lms.models import Course, Task


def main_menu() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="📅 Bugungi jadval"), KeyboardButton(text="🗓 Haftalik")],
        [KeyboardButton(text="📚 Fanlarim"), KeyboardButton(text="⏰ Deadline'lar")],
        [KeyboardButton(text="📊 Baholar"), KeyboardButton(text="📈 Umumiy")],
        [KeyboardButton(text="🏅 Reyting"), KeyboardButton(text="📋 Davomat")],
        [KeyboardButton(text="🏆 Yakuniy"), KeyboardButton(text="📦 Resurslar")],
        [KeyboardButton(text="🧮 GPA kalkulyator"), KeyboardButton(text="👤 Profil")],
        [KeyboardButton(text="⚙️ Sozlamalar")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True,
                               input_field_placeholder="Menyudan tanlang…")


def start_kb(logged_in: bool) -> InlineKeyboardMarkup:
    """/start xabari ostidagi inline tugmalar."""
    b = InlineKeyboardBuilder()
    if logged_in:
        b.button(text="🏠 Asosiy menyu", callback_data="menu:home")
        b.button(text="📅 Bugungi jadval", callback_data="start:today")
    else:
        b.button(text="🔑 LMS'ga kirish", callback_data="start:login")
    # inline rejim — istalgan chatda ulashish
    b.button(text="🤝 Do'stlarga ulashish", switch_inline_query="")
    b.button(text="ℹ️ Yordam", callback_data="start:help")
    b.adjust(1)
    return b.as_markup()


def rating_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🎓 Universitet", callback_data="rank:university")
    b.button(text="🧭 Yo'nalish", callback_data="rank:speciality")
    b.button(text="📚 Kurs", callback_data="rank:level")
    b.button(text="👥 Potok", callback_data="rank:patok")
    b.button(text="🏠 Guruh", callback_data="rank:group")
    b.button(text="📖 Fanlar bo'yicha", callback_data="rank:subjects")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()


def gpa_subjects_kb(grades: list, kurs_of) -> InlineKeyboardMarkup:
    """GPA kalkulyatori — fanlar kurs bo'yicha guruhlangan (StudyGrade ro'yxati).
    kurs_of(semester) -> kurs raqami."""
    b = InlineKeyboardBuilder()
    last = None
    for i, g in enumerate(grades):
        k = kurs_of(g.semester)
        if k != last:
            b.button(text=f"──  {k}-kurs  ──", callback_data="gpa:noop")
            last = k
        cur = f" · {g.grade:g}" if g.grade is not None else " · —"
        b.button(text=f"{g.subject[:30]}{cur}", callback_data=f"gpasel:{i}")
    b.adjust(1)
    return b.as_markup()


def gpa_grades_kb(idx: int) -> InlineKeyboardMarkup:
    """GPA kalkulyatori — faraziy baho tanlash."""
    b = InlineKeyboardBuilder()
    for g in (5, 4, 3, 2):
        b.button(text=str(g), callback_data=f"gpacalc:{idx}:{g}")
    b.button(text="« Fanlar", callback_data="gpa:back")
    b.adjust(4, 1)
    return b.as_markup()


def courses_kb(courses: list[Course], action: str = "course") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for c in courses:
        b.button(text=f"📘 {c.subject}", callback_data=f"{action}:{c.id}")
    b.adjust(1)
    return b.as_markup()


def course_view_kb(course_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    # Ustoz yuklagan asosiy resurslar (kalendar reja — ma'ruza/amaliyot materiallari)
    b.button(text="📖 Ma'ruza resurslari", callback_data=f"cal:{course_id}:lecture")
    b.button(text="✍️ Amaliyot resurslari", callback_data=f"cal:{course_id}:practice")
    # Topshiriqlarga biriktirilgan fayllar (namuna + material)
    b.button(text="📎 Topshiriq fayllari", callback_data=f"resall:{course_id}")
    b.button(text="🔗 Foydali havolalar", callback_data=f"cal:{course_id}:links")
    b.button(text="📊 Baholar", callback_data=f"grades:{course_id}")
    b.button(text="« Fanlar", callback_data="menu:courses")
    b.adjust(2, 1, 1, 1, 1)
    return b.as_markup()


def settings_kb(u: dict) -> InlineKeyboardMarkup:
    def onoff(v):
        return "✅ Yoqilgan" if v else "❌ O'chirilgan"

    b = InlineKeyboardBuilder()
    b.button(text=f"🌅 Ertalabki jadval: {onoff(u.get('morning_on'))}",
             callback_data="set:morning")
    b.button(text=f"⏰ Deadline eslatma: {onoff(u.get('deadline_on'))}",
             callback_data="set:deadline")
    b.button(text=f"🔔 O'zgarish xabari (baho/NB/material): {onoff(u.get('changes_on'))}",
             callback_data="set:changes")
    b.button(text=f"🤖 Avto-topshirish: {onoff(u.get('autosub_on'))}",
             callback_data="set:autosub")
    b.button(text="🎓 Semestrni tanlash", callback_data="set:semester")
    b.button(text="🚪 Hisobdan chiqish", callback_data="set:logout")
    b.adjust(1)
    return b.as_markup()


def semesters_kb(semesters: list[tuple[int, str]], current: int | None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    auto_mark = "✅ " if not current else ""
    b.button(text=f"{auto_mark}🔄 Avto (joriy semestr)", callback_data="sem:0")
    for sid, name in semesters:
        mark = "✅ " if sid == current else ""
        b.button(text=f"{mark}{name}", callback_data=f"sem:{sid}")
    b.button(text="« Sozlamalar", callback_data="menu:settings")
    b.adjust(1)
    return b.as_markup()


def confirm_logout_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, chiqish", callback_data="set:logout_yes"),
        InlineKeyboardButton(text="« Yo'q", callback_data="menu:settings"),
    ]])


def back_home_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="menu:home")
    ]])
