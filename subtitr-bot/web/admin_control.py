"""Admin panel — TIZIM BOSHQARUVI (kuchaytirilgan).

web/admin.py dagi yuzaki monitor/logs/env/broadcast o'rniga to'liq nazorat:
- Servislar boshqaruvi (start/stop/restart) — bot, celery, redis, tunnel, ...
- Kengaytirilgan monitor (CPU/RAM/Swap/Disk barlar + servis salomatligi + navbat)
- Loglar (servis tanlash + faqat xato + avto-yangilanish)
- Xavfsiz .env muharrir (zaxira + xato ko'rsatish)
- Broadcast (matn + rasm + yetkazilish hisobi)

Renderlash yordamchilarini web.admin dan import qiladi (kech import — sikl yo'q).
systemctl/journalctl passwordless sudo orqali (server sudoers'da sozlangan).
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import time

from aiohttp import web

from web.admin import (
    _badge,
    _esc,
    _guard,
    _kpi,
    _layout,
    _pagehead,
    _scroll,
)

logger = logging.getLogger(__name__)

# Boshqariladigan servislar (faqat shu nomlarga amal qilinadi — xavfsizlik oq ro'yxat)
_SERVICES = [
    ("subtitr-bot", "Bot (Telegram + Web)"),
    ("subtitr-celery", "Celery Worker (video ishlovi)"),
    ("redis", "Redis (navbat brokeri)"),
    ("bgutil-pot", "bgutil POT (YouTube token)"),
    ("subtitr-tunnel", "Cloudflare Tunnel (Mini App)"),
    ("subtitr-ytdlp-update", "yt-dlp yangilash"),
    ("subtitr-arm-hunt", "ARM ovi (Osaka)"),
    ("subtitr-arm-hunt-se", "ARM ovi (Stockholm)"),
]
_SERVICE_NAMES = {s[0] for s in _SERVICES}
_ACTIONS = {"start", "stop", "restart"}

# Loglar uchun tanlanadigan birliklar
_LOG_UNITS = {
    "all": ["subtitr-bot", "subtitr-celery"],
    "subtitr-bot": ["subtitr-bot"],
    "subtitr-celery": ["subtitr-celery"],
    "redis": ["redis"],
    "bgutil-pot": ["bgutil-pot"],
    "subtitr-tunnel": ["subtitr-tunnel"],
}

_BC: dict = {"total": 0, "sent": 0, "failed": 0, "running": False, "ts": 0.0}


# ------------------------------------------------------------- system helpers

def _svc_status(name: str) -> str:
    try:
        r = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True, text=True, timeout=5,
        )
        return (r.stdout or r.stderr).strip() or "unknown"
    except Exception:
        return "error"


def _svc_action(name: str, action: str) -> bool:
    if name not in _SERVICE_NAMES or action not in _ACTIONS:
        return False
    try:
        r = subprocess.run(
            ["sudo", "-n", "systemctl", action, name],
            capture_output=True, text=True, timeout=25,
        )
        return r.returncode == 0
    except Exception:
        return False


def _svc_badge(status: str) -> str:
    cls = {"active": "ok", "inactive": "muted", "failed": "bad",
           "activating": "warn", "deactivating": "warn"}.get(status, "muted")
    label = {"active": "Ishlayapti", "inactive": "To'xtagan", "failed": "Xato",
             "activating": "Yonyapti", "deactivating": "O'chyapti"}.get(status, status)
    return _badge(label, cls)


def _cpu_percent() -> float:
    try:
        def read():
            with open("/proc/stat") as f:
                vals = list(map(int, f.readline().split()[1:]))
            idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
            return idle, sum(vals)
        i1, t1 = read()
        time.sleep(0.15)
        i2, t2 = read()
        dt = t2 - t1
        return round(100 * (1 - (i2 - i1) / dt), 1) if dt > 0 else 0.0
    except Exception:
        return 0.0


def _meminfo() -> dict:
    info = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                k, _, v = line.partition(":")
                info[k] = int(v.strip().split()[0])  # kB
    except Exception:
        pass
    return info


def _loadavg() -> tuple[float, float, float]:
    try:
        return os.getloadavg()
    except Exception:
        return (0.0, 0.0, 0.0)


def _uptime_str() -> str:
    try:
        with open("/proc/uptime") as f:
            up = float(f.readline().split()[0])
        d, h, m = int(up // 86400), int((up % 86400) // 3600), int((up % 3600) // 60)
        return f"{d} kun {h} soat {m} daqiqa"
    except Exception:
        return "—"


def _queue_depth() -> dict:
    out = {}
    for q in ("high", "default"):
        try:
            r = subprocess.run(["redis-cli", "-n", "0", "llen", q],
                               capture_output=True, text=True, timeout=4)
            out[q] = (r.stdout or "").strip() or "0"
        except Exception:
            out[q] = "?"
    return out


def _bar(label: str, pct: float, detail: str = "") -> str:
    pct = max(0.0, min(100.0, pct))
    color = "var(--ok)" if pct < 70 else ("var(--warn)" if pct < 90 else "var(--bad)")
    return (
        "<div style='margin-bottom:16px'>"
        "<div style='display:flex;justify-content:space-between;font-size:13px;"
        "margin-bottom:5px'>"
        f"<span><b>{label}</b></span><span class='muted'>{detail}</span></div>"
        "<div style='height:11px;background:var(--subtle);border:1px solid var(--border);"
        "border-radius:6px;overflow:hidden'>"
        f"<div style='height:100%;width:{pct:.0f}%;background:{color};"
        "transition:width .3s'></div></div></div>"
    )


def _auto_refresh(seconds: int, on: bool) -> str:
    if not on:
        return ""
    return f"<script>setTimeout(function(){{location.reload()}},{seconds * 1000})</script>"


def _toggle_link(base: str, query: dict, key: str, on_label: str, off_label: str) -> str:
    on = query.get(key) == "1"
    nq = dict(query)
    nq[key] = "0" if on else "1"
    qs = "&".join(f"{k}={v}" for k, v in nq.items() if v not in (None, ""))
    label = off_label if on else on_label
    return f"<a class='btn' href='{base}?{qs}'>{label}</a>"


# ------------------------------------------------------------- monitor

async def monitor(request: web.Request) -> web.Response:
    guard = _guard(request)
    if guard:
        return guard

    auto = request.query.get("auto") == "1"
    cpu = _cpu_percent()
    mem = _meminfo()
    mt = mem.get("MemTotal", 0) / 1048576       # GB
    ma = mem.get("MemAvailable", 0) / 1048576
    mu = mt - ma
    ram_pct = (mu / mt * 100) if mt else 0
    st = mem.get("SwapTotal", 0) / 1048576
    sf = mem.get("SwapFree", 0) / 1048576
    su = st - sf
    swap_pct = (su / st * 100) if st else 0
    du = shutil.disk_usage("/")
    disk_pct = du.used / du.total * 100 if du.total else 0
    la = _loadavg()

    bars = (
        "<div class='panel' style='padding:20px'>"
        + _bar("CPU", cpu, f"{cpu}%  ·  yuk: {la[0]:.2f} / {la[1]:.2f} / {la[2]:.2f}")
        + _bar("RAM", ram_pct, f"{mu:.2f} / {mt:.2f} GB  ({ram_pct:.0f}%)")
        + _bar("Swap", swap_pct, f"{su:.2f} / {st:.2f} GB  ({swap_pct:.0f}%)")
        + _bar("Disk", disk_pct,
               f"{du.used / 1073741824:.1f} / {du.total / 1073741824:.1f} GB  ({disk_pct:.0f}%)")
        + "</div>"
    )

    # Servis salomatligi
    svc_cards = ""
    for name, label in _SERVICES:
        svc_cards += (
            "<div class='stat'><div class='label'>" + _esc(label) + "</div>"
            "<div style='margin-top:6px'>" + _svc_badge(_svc_status(name)) + "</div></div>"
        )
    q = _queue_depth()
    kpis = (
        _kpi("Uptime", _uptime_str())
        + _kpi("Navbat (high)", q.get("high", "?"))
        + _kpi("Navbat (default)", q.get("default", "?"))
    )

    actions = (
        _toggle_link("/admin/monitor", dict(request.query), "auto",
                     "▶ Avto-yangilash", "⏸ Avto to'xtat")
        + " <a class='btn' href='/admin/monitor'>↻ Yangilash</a>"
    )
    body = (
        _pagehead("Tizim Holati", "Server resurslari (real vaqt)", actions)
        + f"<div class='statbar'>{kpis}</div>"
        + bars
        + "<h3 style='margin:22px 0 10px;font-size:15px'>Servislar salomatligi</h3>"
        + f"<div class='statbar'>{svc_cards}</div>"
        + _auto_refresh(5, auto)
    )
    return web.Response(content_type="text/html", text=_layout("monitor", "Tizim Holati", body))


# ------------------------------------------------------------- services control

async def services(request: web.Request) -> web.Response:
    guard = _guard(request)
    if guard:
        return guard
    done = request.query.get("done")
    msg = ""
    if done == "xato":
        msg = "<div class='badge bad' style='margin-bottom:14px'>✗ Amal bajarilmadi</div>"
    elif done:
        msg = f"<div class='badge ok' style='margin-bottom:14px'>✓ Bajarildi: {_esc(done)}</div>"

    rows = ""
    for name, label in _SERVICES:
        status = _svc_status(name)
        btns = ""
        for act, txt, cls in (("restart", "↻ Restart", "solid"),
                              ("stop", "⏹ To'xtatish", "danger"),
                              ("start", "▶ Yoqish", "")):
            btns += (
                f"<form method='post' action='/admin/services/{name}/{act}' "
                "style='display:inline-block;margin:0 4px 0 0'>"
                f"<button class='btn {cls}' type='submit'>{txt}</button></form>"
            )
        rows += (
            "<tr><td><b>" + _esc(label) + "</b>"
            f"<div class='muted' style='font-size:12px'>{name}</div></td>"
            f"<td>{_svc_badge(status)}</td>"
            f"<td style='white-space:nowrap'>{btns}</td></tr>"
        )
    table = (
        "<div class='panel'>"
        + _scroll("<table><thead><tr><th>Servis</th><th>Holat</th><th>Amal</th>"
                  f"</tr></thead><tbody>{rows}</tbody></table>")
        + "</div>"
    )
    note = (
        "<div class='panel' style='padding:14px;margin-top:14px'>"
        "<div class='muted' style='font-size:13px'>⚠️ <b>Bot</b> yoki <b>Redis</b> ni "
        "to'xtatsangiz bot vaqtincha ishlamaydi. <b>Celery</b> ni restart qilsangiz "
        "ishlanayotgan video qayta navbatga tushadi.</div></div>"
    )
    body = (
        _pagehead("Servislar boshqaruvi", "Barcha xizmatlarni boshqarish",
                  "<a class='btn' href='/admin/services'>↻ Yangilash</a>")
        + msg + table + note
    )
    return web.Response(content_type="text/html", text=_layout("services", "Servislar", body))


async def services_action(request: web.Request) -> web.Response:
    guard = _guard(request)
    if guard:
        return guard
    name = request.match_info["name"]
    action = request.match_info["action"]
    ok = await asyncio.to_thread(_svc_action, name, action)
    target = f"{action} {name}" if ok else "xato"
    return web.HTTPFound(f"/admin/services?done={target}")


# ------------------------------------------------------------- logs

async def logs(request: web.Request) -> web.Response:
    guard = _guard(request)
    if guard:
        return guard
    svc = request.query.get("svc", "all")
    if svc not in _LOG_UNITS:
        svc = "all"
    try:
        n = max(50, min(1000, int(request.query.get("n", "200"))))
    except ValueError:
        n = 200
    level = request.query.get("level", "all")
    auto = request.query.get("auto") == "1"

    cmd = ["sudo", "-n", "journalctl", "--no-pager", "-n", str(n)]
    for u in _LOG_UNITS[svc]:
        cmd += ["-u", u]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        text = proc.stdout or proc.stderr
    except Exception as e:
        text = f"Loglarni o'qib bo'lmadi: {e}"

    if level == "err":
        keep = ("error", "traceback", "exception", "critical", "warning", "fail")
        text = "\n".join(
            ln for ln in text.splitlines() if any(k in ln.lower() for k in keep)
        ) or "(xato/ogohlantirish topilmadi)"

    # Boshqaruv paneli (GET forma)
    def opt(value, cur, label):
        sel = " selected" if value == cur else ""
        return f"<option value='{value}'{sel}>{label}</option>"

    controls = (
        "<form method='get' action='/admin/logs' style='display:flex;gap:10px;"
        "flex-wrap:wrap;align-items:end;margin-bottom:14px'>"
        "<label class='field'>Servis<select name='svc'>"
        + opt("all", svc, "Bot + Celery")
        + opt("subtitr-bot", svc, "Bot")
        + opt("subtitr-celery", svc, "Celery")
        + opt("redis", svc, "Redis")
        + opt("bgutil-pot", svc, "bgutil")
        + opt("subtitr-tunnel", svc, "Tunnel")
        + "</select></label>"
        "<label class='field'>Qatorlar<select name='n'>"
        + "".join(opt(str(x), str(n), str(x)) for x in (100, 200, 500, 1000))
        + "</select></label>"
        "<label class='field'>Daraja<select name='level'>"
        + opt("all", level, "Hammasi")
        + opt("err", level, "Faqat xato/ogoh")
        + "</select></label>"
        f"<input type='hidden' name='auto' value='{'1' if auto else '0'}'>"
        "<button class='btn solid' type='submit'>Ko'rsatish</button>"
        "</form>"
    )
    refresh_btn = _toggle_link(
        "/admin/logs", {"svc": svc, "n": str(n), "level": level}, "auto",
        "▶ Avto-yangilash", "⏸ Avto to'xtat",
    )
    body = (
        _pagehead("Loglar", f"{svc} · oxirgi {n} qator", refresh_btn)
        + controls
        + "<div class='panel'><pre style='padding:16px;font-size:11px;overflow:auto;"
        "max-height:600px;white-space:pre-wrap;word-break:break-word;background:#0b0f0b;"
        f"color:#3ad13a;margin:0;border-radius:10px'>{_esc(text)}</pre></div>"
        + _auto_refresh(5, auto)
    )
    return web.Response(content_type="text/html", text=_layout("logs", "Loglar", body))


# ------------------------------------------------------------- env editor (safe)

def _env_path() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


async def env(request: web.Request) -> web.Response:
    guard = _guard(request)
    if guard:
        return guard
    try:
        with open(_env_path(), "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        content = ""
        logger.warning(".env o'qilmadi: %s", e)

    flag = request.query.get("msg")
    msg = ""
    if flag == "saved":
        msg = "<div class='badge ok' style='margin-bottom:14px'>✓ Saqlandi (zaxira: .env.bak)</div>"
    elif flag == "restarted":
        msg = "<div class='badge ok' style='margin-bottom:14px'>✓ Saqlandi va xizmatlar qayta ishga tushirildi</div>"
    elif flag == "error":
        msg = "<div class='badge bad' style='margin-bottom:14px'>✗ Saqlashda xato (loglarni ko'ring)</div>"

    form = (
        "<form method='post' action='/admin/env'>"
        "<div class='panel' style='padding:18px'>"
        "<textarea name='env_content' spellcheck='false' style='width:100%;height:440px;"
        "font-family:monospace;font-size:13px;padding:12px;border:1px solid var(--border);"
        "border-radius:8px;background:var(--bg);color:var(--text);margin-bottom:14px'>"
        f"{_esc(content)}</textarea>"
        "<div style='display:flex;gap:10px;flex-wrap:wrap'>"
        "<button class='btn solid' type='submit' name='action' value='save'>💾 Saqlash</button>"
        "<button class='btn danger' type='submit' name='action' value='restart' "
        "formnovalidate>💾 Saqlash va Restart (Bot &amp; Celery)</button>"
        "</div></div></form>"
    )
    body = (
        _pagehead(".env Muharrir", "Maxfiy sozlamalar — ehtiyot bo'ling")
        + msg + form
    )
    return web.Response(content_type="text/html", text=_layout("env", ".env", body))


async def env_save(request: web.Request) -> web.Response:
    guard = _guard(request)
    if guard:
        return guard
    data = await request.post()
    content = data.get("env_content", "")
    action = data.get("action", "save")
    path = _env_path()
    try:
        if os.path.exists(path):
            shutil.copy(path, path + ".bak")  # zaxira
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        logger.exception(".env saqlanmadi: %s", e)
        return web.HTTPFound("/admin/env?msg=error")

    if action == "restart":
        try:
            subprocess.Popen(["sudo", "-n", "systemctl", "restart",
                              "subtitr-bot", "subtitr-celery"])
        except Exception:
            logger.exception("restart ishga tushmadi")
        return web.HTTPFound("/admin/env?msg=restarted")
    return web.HTTPFound("/admin/env?msg=saved")


# ------------------------------------------------------------- broadcast

async def _do_broadcast(bot, text: str, photo: str = "") -> None:
    from db.base import async_session
    from sqlalchemy import select
    from db.models import User

    _BC.update(running=True, sent=0, failed=0, total=0, ts=time.time())
    try:
        async with async_session() as session:
            ids = (await session.execute(select(User.telegram_id))).scalars().all()
        _BC["total"] = len(ids)
        for uid in ids:
            try:
                if photo:
                    await bot.send_photo(uid, photo, caption=text or None, parse_mode="HTML")
                else:
                    await bot.send_message(uid, text, parse_mode="HTML")
                _BC["sent"] += 1
            except Exception:
                _BC["failed"] += 1
            await asyncio.sleep(0.05)  # Telegram rate-limit himoyasi
    except Exception as e:
        logger.exception("Broadcast xatosi: %s", e)
    finally:
        _BC["running"] = False


async def broadcast(request: web.Request) -> web.Response:
    guard = _guard(request)
    if guard:
        return guard
    status = ""
    if _BC["ts"]:
        state = "yuborilmoqda…" if _BC["running"] else "tugadi"
        status = (
            "<div class='panel' style='padding:14px;margin-bottom:14px'>"
            f"<b>Oxirgi broadcast:</b> {state}<br>"
            f"<span class='muted'>Jami: {_BC['total']} · Yuborildi: {_BC['sent']} · "
            f"Xato: {_BC['failed']}</span></div>"
        )
    form = (
        "<form method='post' action='/admin/broadcast'>"
        "<div class='panel' style='padding:18px;max-width:640px'>"
        "<label class='field' style='width:100%;margin-bottom:12px'>Xabar matni "
        "(HTML: &lt;b&gt;, &lt;i&gt;, &lt;a&gt;)"
        "<textarea name='message_text' style='width:100%;height:150px;padding:10px;"
        "border:1px solid var(--border);border-radius:8px;background:var(--bg);"
        "color:var(--text);margin-top:5px'></textarea></label>"
        "<label class='field' style='width:100%;margin-bottom:12px'>Rasm havolasi "
        "(ixtiyoriy — to'g'ridan-to'g'ri URL)"
        "<input type='text' name='photo_url' placeholder='https://…/rasm.jpg' "
        "style='width:100%;padding:10px;border:1px solid var(--border);border-radius:8px;"
        "background:var(--bg);color:var(--text);margin-top:5px'></label>"
        "<button class='btn solid' type='submit' "
        "onclick='return confirm(\"Barcha foydalanuvchilarga yuborilsinmi?\")'>"
        "📢 Barchaga Yuborish</button>"
        "</div></form>"
    )
    body = _pagehead("Xabar Yuborish", "Ommaviy xabarnoma (matn + rasm)") + status + form
    return web.Response(content_type="text/html", text=_layout("broadcast", "Broadcast", body))


async def broadcast_send(request: web.Request) -> web.Response:
    guard = _guard(request)
    if guard:
        return guard
    if _BC["running"]:
        return web.HTTPFound("/admin/broadcast")
    data = await request.post()
    text = (data.get("message_text") or "").strip()
    photo = (data.get("photo_url") or "").strip()
    bot = request.app.get("bot")
    if (text or photo) and bot:
        asyncio.create_task(_do_broadcast(bot, text, photo))
    return web.HTTPFound("/admin/broadcast")


# ------------------------------------------------------------- registration

def register(app: web.Application) -> None:
    """Kuchaytirilgan boshqaruv route'larini ulaydi (eski yuzaki'larni almashtiradi)."""
    app.router.add_get("/admin/monitor", monitor)
    app.router.add_get("/admin/services", services)
    app.router.add_post("/admin/services/{name}/{action}", services_action)
    app.router.add_get("/admin/logs", logs)
    app.router.add_get("/admin/env", env)
    app.router.add_post("/admin/env", env_save)
    app.router.add_get("/admin/broadcast", broadcast)
    app.router.add_post("/admin/broadcast", broadcast_send)
