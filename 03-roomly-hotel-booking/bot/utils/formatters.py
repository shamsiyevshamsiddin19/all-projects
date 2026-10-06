STATUS_EMOJI = {
    "PENDING": "🟡",
    "CONFIRMED": "🟢",
    "CHECKED_IN": "🔵",
    "CHECKED_OUT": "⚪️",
    "CANCELLED": "🔴",
    "EXPIRED": "🔴",
}


def format_room_type_card(room_type) -> str:
    amenities = ", ".join(a.name for a in room_type.amenities.all()) or "-"
    return (
        f"<b>{room_type.name}</b>\n"
        f"{room_type.description}\n\n"
        f"👥 Sig'im: {room_type.capacity} kishi\n"
        f"🛏 Karavotlar: {room_type.bed_count}\n"
        f"💵 Narx: {room_type.base_price} {room_type.currency} / kecha\n"
        f"✨ Qulayliklar: {amenities}"
    )


def format_booking_summary(room_type, check_in, check_out, adults, children, nights, total_price, currency) -> str:
    return (
        f"<b>Bron xulosasi</b>\n\n"
        f"🏨 Xona turi: {room_type.name}\n"
        f"📅 {check_in} — {check_out} ({nights} kecha)\n"
        f"👥 Mehmonlar: {adults} kattalar, {children} bolalar\n"
        f"💵 Jami narx: {total_price} {currency}"
    )


def format_booking_line(booking) -> str:
    emoji = STATUS_EMOJI.get(booking.status, "⚪️")
    return (
        f"{emoji} <b>{booking.booking_code}</b> — {booking.room_type.name}\n"
        f"   {booking.check_in_date} — {booking.check_out_date}, {booking.get_status_display()}"
    )
