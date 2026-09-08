"""Boostday bot bilan bog'lanish — saytdan rejalarni boshqarish.

Bot API'sining o'zi (`/boost/api`) qayta ishlatiladi: tekshiruv, `next_run_at` hisobi va
vazifa formatlash mantig'i faqat bitta joyda (botda) turadi, ikki nusxaga bo'linmaydi.
Sayt maxfiy kalit bilan tasdiqlanadi — kalit brauzerga hech qachon berilmaydi.
"""

from __future__ import annotations

import httpx
from fastapi import Request

from ..config import settings
from ..errors import ApiError, success

# Mini app'dagi kabi action'lar. Faqat shu ro'yxatdagilar uzatiladi.
# MUHIM: bot_py'ga (webapp.py::handle_action) yangi action qo'shilganda BU YERGA
# HAM qo'shish shart — aks holda "Noma'lum boost amali" xatosi chiqadi (bir marta
# shu sabab bilan toggle_task ishlamay qolgan edi, saboq uchun qarang: memory).
ALLOWED_ACTIONS = {
    "list", "get", "save", "delete", "stats",
    "channels", "add_channel", "delete_channel", "toggle_task", "set_channel_topics",
    # Kunlik odatlar (habits) — bot bazasida turadi, chunki eslatmalarni
    # va kunlik xabarni ham bot yuboradi.
    "habits_list", "habits_save", "habits_delete", "habits_toggle",
    # Telefon bildirishnomasi (Web Push) obunasi
    "push_key", "push_subscribe", "push_unsubscribe", "push_test",
}
# Yozuv amallari — saytda tizimga kirgan bo'lish shart (main.py tekshiradi)
WRITE_ACTIONS = {"save", "delete", "add_channel", "delete_channel", "toggle_task", "set_channel_topics",
                 "habits_save", "habits_delete", "habits_toggle",
                 "push_subscribe", "push_unsubscribe", "push_test"}


async def proxy(request: Request, body: dict, action: str):
    if action not in ALLOWED_ACTIONS:
        raise ApiError("Noma'lum boost amali.", 400)
    if not settings.BOOST_SITE_SECRET:
        raise ApiError("Boost ulanishi sozlanmagan (SITE_SECRET yo'q).", 503)

    # Bot API form-data kutadi; qiymatlarni matnga aylantiramiz.
    form: dict[str, str] = {"action": action}
    for key, value in (body or {}).items():
        if key in ("action", "init_data", "site_secret", "owner_id"):
            continue  # owner_id'ni bot o'zi aniqlaydi — mijozdan qabul qilinmaydi
        if value is None:
            continue
        form[key] = value if isinstance(value, str) else str(value)

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                settings.BOOST_API_URL,
                data=form,
                headers={"X-Site-Secret": settings.BOOST_SITE_SECRET},
            )
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        raise ApiError(f"Botga ulanib bo'lmadi: {exc}", 502)

    if not isinstance(data, dict):
        raise ApiError("Botdan noto'g'ri javob keldi.", 502)
    if not data.get("ok"):
        raise ApiError(str(data.get("message") or "Bot xatosi"), 400)

    payload = {k: v for k, v in data.items() if k != "ok"}
    return success(payload)
