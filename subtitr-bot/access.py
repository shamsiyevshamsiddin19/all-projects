"""Tarif/limit tekshiruvi (arxitektura 4.2 — obuna middleware mantig'i)."""
from __future__ import annotations
from db.crud import (
    effective_plan,
    get_effective_tariff,
    videos_done_this_month,
    videos_done_today,
    videos_in_month_by_mode,
)
from db.models import User

# Rejim nomlari (limit xabarlari uchun)
_MODE_TITLES = {
    "original": "Original subtitr", "translate": "Tarjima", "dual": "Ikki qatlam",
    "dual_vocab": "Ikki qatlam + lug'at",
    "srt": ".SRT fayl", "transcript": "Matn", "vocabulary": "Lug'at",
    "audio": "Audio (MP3)",
}


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


async def check_can_process(
    user: User, duration_seconds: int, mode: str
) -> tuple[bool, str]:
    """(ruxsat, sabab). ruxsat=False bo'lsa sabab foydalanuvchiga ko'rsatiladi."""
    if user.is_blocked:
        return False, "⛔ Hisobingiz bloklangan. Muammo bo'lsa admin bilan bog'laning."

    plan = effective_plan(user)
    tariff = await get_effective_tariff(plan)

    # Rejim chekivi
    if mode and mode not in tariff.modes:
        return False, (
            "🔒 <b>Bu rejim faqat obunachilarda mavjud.</b>\n\n"
            "💎 BASIC obuna bilan:\n"
            "✅ Tarjima (o'zbek · rus · ingliz)\n"
            "✅ Ikki qatlam subtitr\n"
            "✅ .SRT fayl\n\n"
            "👉 /subscribe — obuna olish"
        )

    # Davomiylik chekivi
    if duration_seconds > tariff.max_minutes * 60:
        minutes = duration_seconds // 60
        if plan == "free":
            return False, (
                f"⏱ Videongiz <b>{minutes} daqiqa</b> — bepul tarifda {tariff.max_minutes} daqiqagacha.\n\n"
                "💎 <b>BASIC obuna</b> bilan 45 daqiqalik video ham bo'ladi!\n\n"
                "👉 /subscribe — yoki qisqaroq video yuboring"
            )
        return False, (
            f"⏱ Videongiz <b>{minutes} daqiqa</b> — tarif limiti {tariff.max_minutes} daqiqa.\n"
            "Qisqaroq video yuboring."
        )

    # Har rejimga oylik limit (bepul tarif: har rejimga oyiga 3 ta)
    if mode and tariff.per_mode_monthly > 0:
        used_mode = await videos_in_month_by_mode(user.id, mode)
        if used_mode >= tariff.per_mode_monthly:
            mode_name = _MODE_TITLES.get(mode, mode)
            return False, (
                f"📊 <b>{mode_name}</b> rejimida bu oyги {tariff.per_mode_monthly} ta "
                "videongiz ishlatildi.\n\n"
                "🗓 Keyingi oy yangilanadi — YOKI boshqa rejimni sinab ko'ring.\n\n"
                "💎 <b>BASIC obuna</b> bilan kuniga 10 tagacha, har rejim cheksiz:\n"
                "👉 /subscribe"
            )

    # Oylik jami limit (bepul tarif: oyiga 10 ta + referal bonusi)
    if tariff.monthly_videos > 0:
        month_limit = tariff.monthly_videos + (user.bonus_videos or 0)
        used_month = await videos_done_this_month(user.id)
        if used_month >= month_limit:
            bonus_line = (
                f" (+{user.bonus_videos} referal bonusi)"
                if user.bonus_videos else ""
            )
            return False, (
                f"📊 Bu oygi bepul {month_limit} ta{bonus_line} videongiz tugadi.\n\n"
                "🎁 <b>Do'st taklif qiling</b> — har taklif uchun ikkovingizga "
                "+5 video/oy! 👉 /invite\n\n"
                "🗓 Yoki keyingi oy avtomatik yangilanadi — YOKI\n\n"
                "💎 <b>BASIC obuna</b> bilan cheksiz: /subscribe"
            )

    # Kunlik limit (basic uchun)
    if tariff.daily_videos != -1:
        used = await videos_done_today(user.id)
        if used >= tariff.daily_videos:
            if plan == "free":
                return False, (
                    f"📊 Bugungi bepul videongiz ({tariff.daily_videos} ta) ishlatildi.\n\n"
                    "⏳ Ertaga yana bepul — YOKI\n\n"
                    "💎 <b>BASIC obuna</b> bilan hoziroq davom eting:\n"
                    "✅ Kuniga 10 ta video\n"
                    "✅ Tarjima + ikki qatlam + .SRT\n\n"
                    "👉 /subscribe"
                )
            return False, (
                f"📊 Bugungi {tariff.daily_videos} ta videongiz tugadi.\n"
                "Ertaga qayta urinib ko'ring yoki /subscribe da yangilang."
            )

    return True, ""
