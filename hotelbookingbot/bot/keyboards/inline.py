from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

PAGE_SIZE = 5


def room_types_keyboard(room_types, page: int = 0, total: int = 0) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{rt.name} — {rt.base_price} {rt.currency}",
                callback_data=f"room_type:{rt.id}",
            )
        ]
        for rt in room_types
    ]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"rooms_page:{page - 1}"))
    if (page + 1) * PAGE_SIZE < total:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"rooms_page:{page + 1}"))
    if nav:
        rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def room_details_keyboard(room_type_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Band qilish", callback_data=f"book:{room_type_id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_rooms")],
        ]
    )


def guests_count_keyboard(adults: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➖", callback_data="guests:dec"),
                InlineKeyboardButton(text=str(adults), callback_data="guests:noop"),
                InlineKeyboardButton(text="➕", callback_data="guests:inc"),
            ],
            [InlineKeyboardButton(text="✅ Davom etish", callback_data="guests:confirm")],
        ]
    )


def confirm_booking_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="booking:confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="booking:cancel"),
            ]
        ]
    )


def my_bookings_keyboard(bookings) -> InlineKeyboardMarkup:
    rows = []
    for booking in bookings:
        row = [InlineKeyboardButton(text=f"🔎 {booking.booking_code}", callback_data=f"booking_detail:{booking.id}")]
        if booking.status in ("PENDING", "CONFIRMED"):
            row.append(InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cancel_booking:{booking.id}"))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pay_click_keyboard(pay_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="💳 Click orqali to'lash", url=pay_url)]]
    )


def cancel_confirm_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, bekor qilaman", callback_data=f"cancel_confirm:{booking_id}"),
                InlineKeyboardButton(text="⬅️ Yo'q", callback_data="cancel_abort"),
            ]
        ]
    )


def staff_pending_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"staff_confirm:{booking_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"staff_reject:{booking_id}"),
            ]
        ]
    )
