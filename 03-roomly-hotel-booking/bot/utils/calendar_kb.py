import calendar
from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CALLBACK_PREFIX = "cal"


def build_calendar(year: int, month: int, min_date: date | None = None, purpose: str = "checkin") -> InlineKeyboardMarkup:
    """Oddiy inline kalendar. purpose: 'checkin' | 'checkout' — callback_data ichida ishlatiladi."""
    min_date = min_date or date.today()
    rows = []

    rows.append(
        [
            InlineKeyboardButton(
                text=f"{calendar.month_name[month]} {year}", callback_data=f"{CALLBACK_PREFIX}:ignore"
            )
        ]
    )
    rows.append([InlineKeyboardButton(text=d, callback_data=f"{CALLBACK_PREFIX}:ignore") for d in ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]])

    month_days = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)
    for week in month_days:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data=f"{CALLBACK_PREFIX}:ignore"))
                continue
            current = date(year, month, day)
            if current < min_date:
                row.append(InlineKeyboardButton(text=" ", callback_data=f"{CALLBACK_PREFIX}:ignore"))
            else:
                row.append(
                    InlineKeyboardButton(
                        text=str(day),
                        callback_data=f"{CALLBACK_PREFIX}:{purpose}:pick:{current.isoformat()}",
                    )
                )
        rows.append(row)

    prev_month = month - 1 or 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️", callback_data=f"{CALLBACK_PREFIX}:{purpose}:nav:{prev_year}-{prev_month}"
            ),
            InlineKeyboardButton(text="➡️", callback_data=f"{CALLBACK_PREFIX}:{purpose}:nav:{next_year}-{next_month}"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
