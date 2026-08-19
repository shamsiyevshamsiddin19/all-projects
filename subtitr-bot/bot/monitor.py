"""Avtomatik holat kuzatuvi — adminга ogohlantirish + kunlik hisobot.

Bot jarayonida fon vazifa sifatida ishlaydi (main.py ishga tushiradi):
  • Servis o'chsa/qaytsa — darrov xabar
  • Disk to'lsa (>=90%) — ogohlantirish
  • Ish tiqilib qolsa (>70 daq processing) — ogohlantirish
  • Har kuni 09:00 (Toshkent) — to'liq holat hisoboti
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging

from config import settings

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 120          # har 2 daqiqada tekshiramiz
DAILY_HOUR = 9                # 09:00 (Toshkent) — kunlik hisobot
STUCK_MINUTES = 70            # 70 daqiqadan ortiq "processing" = tiqilgan
_TASHKENT = dt.timedelta(hours=5)

# Eng muhim servislar (o'chsa darrov xabar)
_CRITICAL = ["subtitr-bot", "subtitr-celery", "redis", "postgresql"]


async def _send_admins(bot, text: str) -> None:
    for aid in settings.admin_id_set:
        try:
            await bot.send_message(aid, text, parse_mode="HTML")
        except Exception:
            logger.warning("Adminга (%s) xabar yuborilmadi", aid)


async def _tick(bot, state: dict) -> None:
    from bot.handlers.admin import _gather_system
    from db.crud import get_queue

    svcs, res, _workers = await asyncio.to_thread(_gather_system)

    # 1) Servis o'chdi / qaytdi (faqat o'zgarishда xabar)
    now_down = {n for n in _CRITICAL if not svcs.get(n, True)}
    for n in now_down - state["down"]:
        await _send_admins(bot, f"🔴 <b>OGOHLANTIRISH:</b> <code>{n}</code> servisi <b>O'CHDI</b>!")
    for n in state["down"] - now_down:
        await _send_admins(bot, f"🟢 <code>{n}</code> servisi qayta ishga tushdi.")
    state["down"] = now_down

    # 2) Disk to'ldi
    disk = res.get("disk_pct", 0)
    if disk >= 90 and not state["disk_alert"]:
        await _send_admins(bot, f"🟠 <b>OGOHLANTIRISH:</b> Disk <b>{disk}%</b> to'ldi — tozalash kerak!")
        state["disk_alert"] = True
    elif disk < 85:
        state["disk_alert"] = False

    # 3) Tiqilib qolgan ish (uzoq "processing")
    try:
        queue = await get_queue()
        now = dt.datetime.utcnow()
        stuck = [
            a for a in queue.get("active", [])
            if a.get("status") == "processing" and a.get("created_at")
            and (now - a["created_at"]).total_seconds() > STUCK_MINUTES * 60
        ]
        if stuck and not state["stuck_alert"]:
            await _send_admins(
                bot, f"🟠 <b>OGOHLANTIRISH:</b> {len(stuck)} ta video <b>{STUCK_MINUTES}+ daqiqa</b> "
                "ishlanyapti — tiqilib qolgan bo'lishi mumkin."
            )
            state["stuck_alert"] = True
        elif not stuck:
            state["stuck_alert"] = False
    except Exception:
        logger.exception("Navbat tekshiruvида xato")

    # 4) Kunlik hisobot (09:00 Toshkent)
    now_tash = dt.datetime.utcnow() + _TASHKENT
    if now_tash.hour >= DAILY_HOUR and state["last_daily"] != now_tash.date():
        state["last_daily"] = now_tash.date()
        try:
            from bot.handlers.admin import build_holat_text
            text = await build_holat_text()
            await _send_admins(bot, "🌅 <b>Kunlik hisobot</b>\n\n" + text)
        except Exception:
            logger.exception("Kunlik hisobot xatosi")


async def monitor_loop(bot) -> None:
    """Asosiy kuzatuv sikli (main.py asyncio.create_task bilan ishga tushiradi)."""
    now_tash = dt.datetime.utcnow() + _TASHKENT
    state = {
        "down": set(),
        "disk_alert": False,
        "stuck_alert": False,
        # bugun 09:00 o'tib ketgan bo'lsa, bugungi hisobotni qayta yubormaymiz
        "last_daily": now_tash.date() if now_tash.hour >= DAILY_HOUR else None,
    }
    await asyncio.sleep(40)  # bot to'liq ishga tushsin
    logger.info("Holat kuzatuvi boshlandi (har %ss, kunlik %02d:00)", CHECK_INTERVAL, DAILY_HOUR)
    while True:
        try:
            await _tick(bot, state)
        except Exception:
            logger.exception("Monitor tick xatosi")
        await asyncio.sleep(CHECK_INTERVAL)
