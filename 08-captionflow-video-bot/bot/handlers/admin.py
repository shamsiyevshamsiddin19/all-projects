"""Admin buyruqlari (test uchun). To'liq boshqaruv keyin admin saytda bo'ladi.

/grant <tarif> [kun]            -> o'zingizga tarif beradi (test)
/grant <telegram_id> <tarif> [kun] -> boshqa foydalanuvchiga
  tarif: free | basic | premium ; kun: default 30
"""
from __future__ import annotations

import asyncio
import subprocess

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from db.crud import get_dashboard_stats, get_queue, set_plan
from tariffs import TARIFFS

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_id_set


# /holat uchun kuzatiladigan servislar
_HOLAT_SERVICES = [
    ("subtitr-bot", "Bot"),
    ("subtitr-celery", "Worker"),
    ("redis", "Redis"),
    ("postgresql", "Baza"),
    ("subtitr-tunnel", "Tunnel"),
    ("subtitr-arm-hunt-se", "ARM-hunt"),
]


def _svc_active(name: str) -> bool:
    try:
        r = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True, text=True, timeout=4,
        )
        return r.stdout.strip() == "active"
    except Exception:
        return False


def _resources() -> dict:
    out: dict = {}
    try:
        import psutil

        out["cpu"] = psutil.cpu_percent(interval=0.3)
        m = psutil.virtual_memory()
        out["ram_used"] = m.used // (1024 * 1024)
        out["ram_total"] = m.total // (1024 * 1024)
        out["ram_pct"] = int(m.percent)
        out["swap_used"] = psutil.swap_memory().used // (1024 * 1024)
        d = psutil.disk_usage("/")
        out["disk_used"] = round(d.used / (1024 ** 3), 1)
        out["disk_total"] = round(d.total / (1024 ** 3), 1)
        out["disk_pct"] = int(d.percent)
    except Exception:
        pass
    try:
        with open("/proc/uptime") as f:
            out["uptime"] = float(f.readline().split()[0])
    except Exception:
        pass
    return out


def _worker_count() -> int:
    """Online Celery worker tugunlari soni (-1 = noma'lum)."""
    try:
        from worker.celery_app import app

        replies = app.control.ping(timeout=2.0)
        return len(replies) if replies else 0
    except Exception:
        return -1


def _gather_system() -> tuple[dict, dict, int]:
    """Bloklaydigan qismlar (subprocess/psutil/celery) — to_thread ichida."""
    svcs = {name: _svc_active(name) for name, _ in _HOLAT_SERVICES}
    return svcs, _resources(), _worker_count()


async def build_holat_text() -> str:
    """Batafsil holat matnini yig'adi (/holat va avtomatik hisobot uchun)."""
    svcs, res, workers = await asyncio.to_thread(_gather_system)
    stats = await get_dashboard_stats()
    queue = await get_queue()

    svc_line = "  ".join(
        f"{'✅' if svcs.get(n) else '❌'}{label}" for n, label in _HOLAT_SERVICES
    )

    if res:
        up = res.get("uptime", 0)
        up_str = f"{int(up // 86400)} kun {int((up % 86400) // 3600)} soat"
        res_block = (
            f"🖥 CPU: <b>{res.get('cpu', '?')}%</b>\n"
            f"🧠 RAM: <b>{res.get('ram_used', '?')}/{res.get('ram_total', '?')} MB</b> "
            f"({res.get('ram_pct', '?')}%)\n"
            f"💱 Swap: {res.get('swap_used', '?')} MB band\n"
            f"📀 Disk: {res.get('disk_used', '?')}/{res.get('disk_total', '?')} GB "
            f"({res.get('disk_pct', '?')}%)\n"
            f"⏱ Uptime: {up_str}"
        )
    else:
        res_block = "🖥 (resurs ma'lumoti yo'q)"

    worker_str = f"{workers} ta online" if workers >= 0 else "noma'lum"
    arm_str = "🟢 qidirilmoqda" if svcs.get("subtitr-arm-hunt-se") else "🔴 to'xtagan"

    text = (
        "📊 <b>BOT HOLATI</b>\n\n"
        f"⚙️ <b>Servislar:</b>\n{svc_line}\n\n"
        f"💻 <b>Resurslar:</b>\n{res_block}\n\n"
        f"📈 <b>Bugun:</b>\n"
        f"✅ Tayyor: <b>{queue.get('done_today', 0)}</b>  "
        f"❌ Xato: <b>{queue.get('error_today', 0)}</b>  "
        f"⏳ Navbatda: <b>{len(queue.get('active', []))}</b>\n\n"
        f"👥 <b>Foydalanuvchilar:</b> {stats['total_users']} "
        f"(bugun yangi: {stats['new_users_today']})\n"
        f"💎 Obunachilar: {stats['active_subs']}\n"
        f"🎬 Jami video: {stats['total_videos']} "
        f"(✅{stats['done_videos']} ❌{stats['error_videos']})\n\n"
        f"⚙️ <b>Worker tugunlari:</b> {worker_str}\n"
        f"🎯 <b>ARM 24GB hunt:</b> {arm_str}"
    )
    return text


@router.message(Command("holat"))
async def cmd_holat(message: Message) -> None:
    """Admin: batafsil tizim holati (servislar, resurslar, navbat, statistika)."""
    if not _is_admin(message.from_user.id):
        return
    status_msg = await message.answer("📊 Holat yig'ilmoqda...")
    try:
        text = await build_holat_text()
    except Exception as exc:
        await status_msg.edit_text(f"❌ Holatni yig'ishda xato: {exc}")
        return
    await status_msg.edit_text(text, parse_mode="HTML")


@router.message(Command("grant"))
async def cmd_grant(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return  # admin emaslarga e'tibor bermaymiz

    args = message.text.split()[1:]
    if not args:
        await message.answer(
            "Foydalanish:\n"
            "/grant <tarif> [kun] — o'zingizga\n"
            "/grant <telegram_id> <tarif> [kun] — boshqaga\n"
            "tarif: free | basic | premium"
        )
        return

    if args[0].isdigit():
        target_id = int(args[0])
        plan = args[1] if len(args) > 1 else "basic"
        days = int(args[2]) if len(args) > 2 and args[2].isdigit() else 30
    else:
        target_id = message.from_user.id
        plan = args[0]
        days = int(args[1]) if len(args) > 1 and args[1].isdigit() else 30

    if plan not in TARIFFS:
        await message.answer("❌ Noto'g'ri tarif. Mavjud: free, basic, premium")
        return

    found = await set_plan(target_id, plan, days)
    if found:
        await message.answer(
            f"✅ {target_id} ga <b>{plan}</b> tarifi berildi ({days} kun).",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"⚠️ {target_id} topilmadi. U avval botga /start bossin."
        )
