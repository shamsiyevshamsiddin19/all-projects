"""Mustaqil bot admin paneli — Subtitr bot bilan bir xil dizayn va uslub."""
from __future__ import annotations
import base64
import binascii
import datetime as dt
import hmac
import html
import logging
import os
import shutil
import subprocess
import time

from aiohttp import web
from config import settings

logger = logging.getLogger(__name__)
_TZ = dt.timedelta(hours=5)

_STATUS_LABEL = {"pending": "Kutmoqda", "generating": "Tayyorlanmoqda",
                 "done": "Tayyor", "error": "Xato", "refunded": "Qaytarilgan"}
_STATUS_CLASS = {"pending": "warn", "generating": "warn", "done": "ok", "error": "bad", "refunded": "muted"}
_PAY_LABEL = {"pending": "Kutmoqda", "paid": "To'langan", "cancelled": "Bekor", "error": "Xato"}
_PAY_CLASS = {"pending": "warn", "paid": "ok", "cancelled": "muted", "error": "bad"}
_DOC_EMOJI = {"tezis": "📋", "mustaqil": "📝", "referat": "📄", "krasword": "🎯",
              "maqola": "📰", "slayd": "📊", "kurs": "📚", "diplom": "🎓"}

_SERVICES = [
    ("mustaqilbot", "Mustaqil Bot"),
    ("nginx", "Nginx"),
    ("postgresql", "PostgreSQL"),
]
_SERVICE_NAMES = {s[0] for s in _SERVICES}


# ─── auth ───

def _authorized(request: web.Request) -> bool:
    if not settings.admin_password:
        return False
    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return False
    try:
        raw = base64.b64decode(header[6:]).decode()
    except (binascii.Error, UnicodeDecodeError):
        return False
    user, _, pwd = raw.partition(":")
    return (hmac.compare_digest(user, settings.admin_user)
            and hmac.compare_digest(pwd, settings.admin_password))


def _guard(request: web.Request) -> web.Response | None:
    # Parol himoyasi foydalanuvchi so'roviga ko'ra OLIB TASHLANDI — barcha so'rov o'tadi.
    return None


# ─── helpers ───

def _esc(v) -> str:
    return html.escape(str(v)) if v is not None else "—"


def _fmt_dt(v: dt.datetime | None) -> str:
    return (v + _TZ).strftime("%d.%m %H:%M") if v else "—"


def _fmt_num(v: int) -> str:
    return f"{v:,}".replace(",", " ")


def _badge(text: str, cls: str = "muted") -> str:
    return f"<span class='badge {cls}'>{text}</span>"


def _kpi(label: str, num: str, note: str = "") -> str:
    note_h = f"<div class='note'>{note}</div>" if note else ""
    return (f"<div class='stat'><div class='label'>{label}</div>"
            f"<div class='num'>{num}</div>{note_h}</div>")


def _scroll(t: str) -> str:
    return f"<div class='scroll'>{t}</div>"


def _icon(name: str) -> str:
    paths = {
        "dash": "<rect x='3' y='3' width='7' height='7' rx='1'/><rect x='14' y='3' width='7' height='7' rx='1'/><rect x='3' y='14' width='7' height='7' rx='1'/><rect x='14' y='14' width='7' height='7' rx='1'/>",
        "users": "<path d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M22 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/>",
        "orders": "<path d='M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2'/><rect x='9' y='3' width='6' height='4' rx='1'/><path d='M9 12h6'/><path d='M9 16h4'/>",
        "pay": "<rect x='2' y='5' width='20' height='14' rx='2'/><path d='M2 10h20'/>",
        "ref": "<path d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><line x1='19' y1='8' x2='19' y2='14'/><line x1='22' y1='11' x2='16' y2='11'/>",
        "stats": "<line x1='6' y1='20' x2='6' y2='14'/><line x1='12' y1='20' x2='12' y2='4'/><line x1='18' y1='20' x2='18' y2='10'/>",
        "monitor": "<polyline points='22 12 18 12 15 21 9 3 6 12 2 12'/>",
        "logs": "<path d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/>",
        "env": "<path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><polyline points='14 2 14 8 20 8'/>",
        "broadcast": "<line x1='22' y1='2' x2='11' y2='13'/><polygon points='22 2 15 22 11 13 2 9 22 2'/>",
        "service": "<rect x='2' y='2' width='20' height='8' rx='2'/><rect x='2' y='14' width='20' height='8' rx='2'/>",
        "settings": "<circle cx='12' cy='12' r='3'/><path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z'/>",
    }
    return (
        "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' "
        "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
        + paths.get(name, "") + "</svg>"
    )


_NAV = [
    ("dash", "Dashboard", "/mustaqil/admin", "dash"),
    ("users", "Foydalanuvchilar", "/mustaqil/admin/users", "users"),
    ("orders", "Buyurtmalar", "/mustaqil/admin/orders", "orders"),
    ("payments", "To'lovlar", "/mustaqil/admin/payments", "pay"),
    ("referrals", "Referallar", "/mustaqil/admin/referrals", "ref"),
    ("settings", "Narx & Sozlama", "/mustaqil/admin/settings", "settings"),
    ("stats", "Statistika", "/mustaqil/admin/stats", "stats"),
    ("monitor", "Tizim Holati", "/mustaqil/admin/monitor", "monitor"),
    ("services", "Servislar", "/mustaqil/admin/services", "service"),
    ("logs", "Loglar", "/mustaqil/admin/logs", "logs"),
    ("env", ".env Muharrir", "/mustaqil/admin/env", "env"),
    ("broadcast", "Xabar Yuborish", "/mustaqil/admin/broadcast", "broadcast"),
]

_STYLE = """
:root{--bg:#fff;--subtle:#f7f7f8;--border:#e5e5e5;--text:#0d0d0d;--muted:#6e6e80;
  --accent:#0d0d0d;--ok:#10a37f;--bad:#ef4444;--warn:#d97706}
*{box-sizing:border-box}
body{margin:0;background:var(--subtle);color:var(--text);
  font:15px/1.5 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
a{color:inherit}
.navtoggle{display:none}
.layout{display:flex;min-height:100vh}
.sidebar{width:230px;flex:0 0 230px;background:var(--bg);
  border-right:1px solid var(--border);padding:18px 14px;position:fixed;
  top:0;left:0;bottom:0;overflow-y:auto;z-index:30;transition:transform .2s ease}
.brand{font-weight:600;font-size:16px;padding:6px 10px 16px;display:flex;
  align-items:center;gap:9px}
.brand .dot{width:22px;height:22px;border-radius:7px;background:var(--accent);
  color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:13px}
.nav a{display:flex;align-items:center;gap:11px;padding:9px 11px;border-radius:8px;
  color:var(--muted);text-decoration:none;font-size:14px;margin-bottom:2px}
.nav a:hover{background:var(--subtle);color:var(--text)}
.nav a.active{background:var(--subtle);color:var(--text);font-weight:500}
.nav svg{width:18px;height:18px;flex:0 0 18px}
.content{margin-left:230px;flex:1;padding:26px 28px 64px;min-width:0;width:100%}
.topbar{display:none}
.hamburger{display:none}
.overlay{display:none}
.pagehead{display:flex;align-items:baseline;justify-content:space-between;
  gap:10px;margin-bottom:22px;flex-wrap:wrap}
.pagehead h1{font-size:21px;font-weight:600;margin:0}
.pagehead .sub{color:var(--muted);font-size:13px}
.btn{color:var(--muted);text-decoration:none;font-size:13px;border:1px solid var(--border);
  padding:6px 12px;border-radius:8px;background:var(--bg)}
.btn:hover{color:var(--text)}
.statbar{display:flex;background:var(--bg);border:1px solid var(--border);
  border-radius:12px;overflow-x:auto;margin-bottom:28px}
.stat{flex:1 0 auto;min-width:122px;padding:15px 18px;
  border-right:1px solid var(--border)}
.stat:last-child{border-right:none}
.stat .label{color:var(--muted);font-size:13px;margin-bottom:5px;white-space:nowrap}
.stat .num{font-size:24px;font-weight:600;letter-spacing:-.5px}
.stat .note{color:var(--muted);font-size:12px;margin-top:3px;white-space:nowrap}
h2{font-size:15px;font-weight:600;margin:0 0 12px}
.panel{background:var(--bg);border:1px solid var(--border);border-radius:12px;
  overflow:hidden;margin-bottom:26px}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px;min-width:520px}
th,td{text-align:left;padding:11px 16px;border-bottom:1px solid var(--border);white-space:nowrap}
th{color:var(--muted);font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:none}
.badge{display:inline-block;font-size:12px;padding:2px 9px;border-radius:20px;
  border:1px solid var(--border)}
.badge.ok{color:var(--ok);border-color:#bde9da}
.badge.bad{color:var(--bad);border-color:#f5c2c2}
.badge.warn{color:var(--warn);border-color:#f0d6a8}
.badge.muted{color:var(--muted)}
.badge.accentbadge{color:#fff;background:var(--accent);border-color:var(--accent)}
.empty{padding:22px 16px;color:var(--muted);font-size:14px}
.note{color:var(--muted);font-size:12px;margin:6px 2px 24px}
.search{display:flex;gap:8px;margin-bottom:18px}
.search input{flex:1;max-width:320px;padding:8px 12px;border:1px solid var(--border);
  border-radius:8px;font-size:14px;background:var(--bg);color:var(--text)}
.search button{padding:8px 16px;border:1px solid var(--accent);background:var(--accent);
  color:#fff;border-radius:8px;font-size:14px;cursor:pointer}
.filters{display:flex;gap:6px;margin-bottom:18px;flex-wrap:wrap}
.filters a{font-size:13px;padding:6px 12px;border:1px solid var(--border);
  border-radius:20px;text-decoration:none;color:var(--muted);background:var(--bg)}
.filters a.on{color:var(--text);border-color:var(--accent)}
.info{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}
.info .cell{padding:13px 16px;border-bottom:1px solid var(--border);border-right:1px solid var(--border)}
.info .k{color:var(--muted);font-size:12px;margin-bottom:3px}
.info .v{font-size:14px}
.actbar{display:flex;gap:22px;flex-wrap:wrap;align-items:flex-end;padding:16px}
.field{display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--muted)}
.field input,.field select{padding:8px 10px;border:1px solid var(--border);
  border-radius:8px;font-size:14px;background:var(--bg);color:var(--text);min-width:120px}
form.inline{display:flex;gap:8px;align-items:flex-end;margin:0}
button.btn{cursor:pointer;font:inherit}
.btn.solid{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn.danger{color:var(--bad);border-color:#f5c2c2;background:var(--bg)}
.btn.ok{color:var(--ok);border-color:#bde9da;background:var(--bg)}
.btn.sm{padding:4px 10px;font-size:12px}
.foot{color:var(--muted);font-size:12px;text-align:center;margin-top:8px}
@media(max-width:820px){
  .sidebar{transform:translateX(-100%)}
  #navtoggle:checked ~ .sidebar{transform:translateX(0)}
  #navtoggle:checked ~ .overlay{display:block;position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:25}
  .content{margin-left:0;padding:0 16px 56px}
  .topbar{display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:20;
    margin:0 -16px 18px;padding:13px 16px;background:var(--bg);border-bottom:1px solid var(--border)}
  .topbar .ttl{font-weight:600;font-size:16px}
  .hamburger{display:inline-flex;align-items:center;justify-content:center;
    width:38px;height:38px;border:1px solid var(--border);border-radius:9px;
    cursor:pointer;color:var(--text);font-size:18px;background:var(--bg)}
  .content{padding-top:16px}
  .statbar{overflow:hidden}
  .stat{flex:1 1 0;min-width:0;padding:8px 4px;text-align:center}
  .stat .label{font-size:8.5px;line-height:1.15;white-space:normal;overflow-wrap:anywhere}
  .stat .num{font-size:15px}
  .scroll{overflow-x:visible}
  thead{display:none}
  table{display:block;min-width:0;font-size:13.5px}
  tbody{display:block}
  tbody tr{display:block;padding:4px 0;border-bottom:1px solid var(--border)}
  tbody tr:last-child{border-bottom:none}
  td{display:flex;justify-content:space-between;align-items:center;gap:14px;
    padding:7px 16px;border:none;white-space:normal;text-align:right;word-break:break-word}
  td::before{content:attr(data-label);color:var(--muted);font-size:12px;
    font-weight:500;text-align:left;flex:0 0 38%;white-space:nowrap}
}
"""

_LABEL_SCRIPT = (
    "<script>(function(){"
    "document.querySelectorAll('table').forEach(function(t){"
    "var h=[].map.call(t.querySelectorAll('thead th'),function(x){return x.textContent;});"
    "[].forEach.call(t.querySelectorAll('tbody tr'),function(r){"
    "[].forEach.call(r.querySelectorAll('td'),function(d,i){"
    "if(h[i])d.setAttribute('data-label',h[i]);});});});})();</script>"
)

_BC: dict = {"total": 0, "sent": 0, "failed": 0, "running": False, "ts": 0.0}


def _page_raw(body: str) -> str:
    return (
        "<!doctype html><html lang='uz'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Mustaqil Admin</title><style>" + _STYLE + "</style></head>"
        "<body>" + body + _LABEL_SCRIPT + "</body></html>"
    )


def _sidebar(active: str) -> str:
    items = ""
    for key, label, href, icon in _NAV:
        cls = " class='active'" if key == active else ""
        items += f"<a href='{href}'{cls}>{_icon(icon)}<span>{label}</span></a>"
    # Barcha panellar bitta domen (subtitr cloudflare tunnel) orqali ochiladi —
    # nisbiy yo'llar ishlatamiz (subtitr bot dropdown'i bilan bir xil).
    _sv = ("<svg viewBox='0 0 24 24' width='20' height='20' fill='none' stroke='currentColor' "
           "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>{}</svg>")
    film = _sv.format("<rect x='2' y='4' width='20' height='16' rx='2'/>"
                      "<path d='M2 9h20M2 15h20M7 4v16M17 4v16'/>")
    book = _sv.format("<path d='M4 19.5A2.5 2.5 0 0 1 6.5 17H20'/>"
                      "<path d='M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z'/>")
    pencil = _sv.format("<path d='M12 20h9'/><path d='M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z'/>")
    cap = _sv.format("<path d='M22 10 12 5 2 10l10 5 10-5Z'/>"
                     "<path d='M6 12v5c0 1 2.7 2.5 6 2.5s6-1.5 6-2.5v-5'/>")
    quiz = _sv.format("<circle cx='12' cy='12' r='10'/>"
                      "<path d='M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3'/>"
                      "<line x1='12' y1='17' x2='12.01' y2='17'/>")
    cart = _sv.format("<circle cx='9' cy='21' r='1'/>"
                      "<circle cx='20' cy='21' r='1'/>"
                      "<path d='M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6'/>")
    chart = _sv.format("<line x1='18' y1='20' x2='18' y2='10'/><line x1='12' y1='20' x2='12' y2='4'/><line x1='6' y1='20' x2='6' y2='14'/>")
    bots = [("/admin", film, "Subtitr bot", False),
            ("/sessiya/admin", book, "Sessiya bot", False),
            ("/mustaqil/admin", pencil, "Mustaqil bot", True),
            ("/tatulms/admin", cap, "TATU LMS bot", False),
            ("/quiz/admin", quiz, "Quiz bot", False),
            ("/wstore/admin", cart, "wstore market", False),
            ("/site/admin", chart, "Portfolio", False)]
    cur = next((b for b in bots if b[3]), bots[0])
    opts = ""
    for url, svg, label, act in bots:
        a = " active" if act else ""
        opts += f"<a class='botopt{a}' href='{url}'>{svg}<span>{label}</span></a>"
    chev = ("<svg class='botchev' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
            "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
            "<polyline points='6 9 12 15 18 9'/></svg>")
    return (
        "<aside class='sidebar'>"
        "<div class='brand'><span class='dot'>M</span><span>Bot boshqaruv</span></div>"
        "<style>.botdd{position:relative;flex:1;min-width:0;margin-bottom:6px}"
        ".botcur{list-style:none;display:flex;align-items:center;gap:9px;padding:9px 11px;"
        "border:1px solid #e5e5e5;border-radius:10px;background:#fff;cursor:pointer;color:#0d0d0d;"
        "font-size:13.5px;font-weight:600;user-select:none}"
        ".botcur::-webkit-details-marker{display:none}.botcur:hover{background:#f7f7f8}"
        ".botcur svg,.botopt svg{width:18px;height:18px;flex:0 0 18px}"
        ".botnm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
        ".botcur .botchev{width:15px;height:15px;flex:0 0 15px;color:#6e6e80;transition:transform .2s}"
        ".botdd[open] .botchev{transform:rotate(180deg)}"
        ".botmenu{position:absolute;top:calc(100% + 6px);left:0;right:0;z-index:60;background:#fff;"
        "border:1px solid #e5e5e5;border-radius:12px;box-shadow:0 14px 34px rgba(0,0,0,.13);padding:6px}"
        ".botopt{display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;"
        "color:#6e6e80;text-decoration:none;font-size:13.5px;font-weight:500;margin-bottom:2px}"
        ".botopt:last-child{margin-bottom:0}.botopt:hover{background:#f7f7f8;color:#0d0d0d}"
        ".botopt.active{background:#0d0d0d;color:#fff}</style>"
        f"<details class='botdd'><summary class='botcur'>{cur[1]}"
        f"<span class='botnm'>{cur[2]}</span>{chev}</summary>"
        f"<div class='botmenu'>{opts}</div></details>"
        "<script>document.addEventListener('click',function(e){"
        "document.querySelectorAll('details.botdd[open]').forEach(function(d){"
        "if(!d.contains(e.target))d.removeAttribute('open');});});</script>"
        f"<nav class='nav'>{items}</nav></aside>"
    )


def _layout(active: str, page_title: str, body: str) -> str:
    inner = (
        "<input type='checkbox' id='navtoggle' class='navtoggle'>"
        + _sidebar(active)
        + "<label for='navtoggle' class='overlay'></label>"
        "<main class='content'>"
        "<div class='topbar'>"
        "<label for='navtoggle' class='hamburger'>☰</label>"
        f"<span class='ttl'>{page_title}</span></div>"
        + body
        + "<div class='foot'>Mustaqil Bot · Admin panel</div>"
        "</main>"
    )
    return _page_raw(f"<div class='layout'>{inner}</div>")


def _pagehead(title: str, sub: str = "", action: str = "") -> str:
    sub_h = f"<div class='sub'>{sub}</div>" if sub else ""
    return f"<div class='pagehead'><div><h1>{title}</h1>{sub_h}</div>{action}</div>"


def _cell(k: str, v: str) -> str:
    return f"<div class='cell'><div class='k'>{k}</div><div class='v'>{v}</div></div>"


# ─── dashboard ───

def _bar_chart(pairs, w=520, h=160, pad=26):
    """Oddiy SVG ustunli grafik. pairs = [(label, value), ...]."""
    if not pairs or not any(v for _, v in pairs):
        return "<div class='empty' style='padding:18px'>Ma'lumot yo'q</div>"
    mx = max(v for _, v in pairs) or 1
    n = len(pairs)
    iw, ih = w - pad * 2, h - pad * 2
    bw = iw / n
    parts = [f"<line x1='{pad}' y1='{pad+ih}' x2='{w-pad}' y2='{pad+ih}' stroke='#e5e5e5'/>"]
    for i, (label, val) in enumerate(pairs):
        bh = (val / mx) * ih
        x = pad + i * bw + bw * 0.18
        bwid = bw * 0.64
        y = pad + ih - bh
        parts.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{bwid:.1f}' height='{bh:.1f}' "
                     "rx='3' fill='#0d0d0d'/>")
        parts.append(f"<text x='{x+bwid/2:.1f}' y='{y-5:.1f}' font-size='11' "
                     f"text-anchor='middle' fill='#6e6e80'>{val}</text>")
        parts.append(f"<text x='{x+bwid/2:.1f}' y='{h-7:.1f}' font-size='10' "
                     f"text-anchor='middle' fill='#6e6e80'>{label}</text>")
    return (f"<svg viewBox='0 0 {w} {h}' width='100%' style='max-width:{w}px;height:auto'>"
            + "".join(parts) + "</svg>")


async def _dash_charts():
    try:
        from db.crud import admin_chart_data
        d = await admin_chart_data()
        return (
            "<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));"
            "gap:16px;margin-bottom:26px'>"
            "<div class='panel' style='padding:16px'><h2>Yangi foydalanuvchilar (kunlik)</h2>"
            + _bar_chart(d["users"]) + "</div>"
            "<div class='panel' style='padding:16px'><h2>Daromad (kunlik, ming so'm)</h2>"
            + _bar_chart(d["revenue"]) + "</div></div>")
    except Exception:
        return ""


async def _dashboard(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    from db.crud import admin_dashboard
    s = await admin_dashboard()
    kpis = (
        _kpi("Foydalanuvchilar", _fmt_num(s["total_users"]), f"bugun +{s['new_today']}")
        + _kpi("Buyurtmalar", _fmt_num(s["total_orders"]), f"bugun +{s['orders_today']}")
        + _kpi("Bajarilgan", _fmt_num(s["done_orders"]))
        + _kpi("Daromad", _fmt_num(s["revenue"]) + " so'm", f"bugun +{_fmt_num(s['revenue_today'])}")
    )
    charts = await _dash_charts()
    body = (
        _pagehead("Dashboard", "Umumiy holat",
                  "<a class='btn' href='/mustaqil/admin'>↻ Yangilash</a>")
        + f"<div class='statbar'>{kpis}</div>"
        + charts
    )
    return web.Response(content_type="text/html", text=_layout("dash", "Dashboard", body))


# ─── users ───

async def _users(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    from db.crud import admin_list_users
    search = request.query.get("q", "")
    rows = await admin_list_users(search)
    search_box = (
        "<form class='search' method='get' action='/mustaqil/admin/users'>"
        f"<input type='text' name='q' placeholder='@username yoki ID' value='{_esc(search)}'>"
        "<button>Qidirish</button></form>"
    )
    if not rows:
        table = "<div class='panel'><div class='empty'>Topilmadi.</div></div>"
    else:
        body_r = ""
        for u in rows:
            uname = f"@{_esc(u['username'])}" if u["username"] else f"id{u['id']}"
            banned = _badge("Ban", "bad") if u["is_banned"] else ""
            body_r += (
                "<tr>"
                f"<td class='muted'>#{u['id']}</td>"
                f"<td><a href='/mustaqil/admin/users/{u['id']}'>{uname}</a> {banned}</td>"
                f"<td>{_fmt_num(u['balance'])} so'm</td>"
                f"<td>{u['referral_count']}</td>"
                f"<td>{u['orders_count']}</td>"
                f"<td class='muted'>{_fmt_dt(u['last_active'])}</td></tr>"
            )
        head = "<tr><th>ID</th><th>Foydalanuvchi</th><th>Balans</th><th>Referallar</th><th>Buyurtmalar</th><th>Faollik</th></tr>"
        table = f"<div class='panel'>{_scroll(f'<table><thead>{head}</thead><tbody>{body_r}</tbody></table>')}</div>"
    body = _pagehead("Foydalanuvchilar", f"{len(rows)} ta") + search_box + table
    return web.Response(content_type="text/html", text=_layout("users", "Foydalanuvchilar", body))


async def _user_detail(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    from db.crud import admin_get_user, admin_add_balance, ban_user
    uid = int(request.match_info["id"])
    u = await admin_get_user(uid)
    if not u:
        return web.Response(status=404, text="Topilmadi")

    uname = f"@{_esc(u['username'])}" if u["username"] else "—"
    info = (
        "<div class='panel'><div class='info'>"
        + _cell("Telegram ID", str(u["id"]))
        + _cell("Username", uname)
        + _cell("Balans", f"{_fmt_num(u['balance'])} so'm")
        + _cell("Referallar", str(u["referral_count"]))
        + _cell("Referal bonus", f"{_fmt_num(u['referral_earned'])} so'm")
        + _cell("Buyurtmalar", str(u["orders_count"]))
        + _cell("Jami sarflangan", f"{_fmt_num(u['total_spent'])} so'm")
        + _cell("Holat", _badge("Ban", "bad") if u["is_banned"] else _badge("Faol", "ok"))
        + _cell("Ro'yxatdan", _fmt_dt(u["created_at"]))
        + "</div></div>"
    )
    ban_btn = (
        f"<form class='inline' method='post' action='/mustaqil/admin/users/{uid}/ban'>"
        f"<input type='hidden' name='banned' value='{'0' if u['is_banned'] else '1'}'>"
        f"<button class='btn {'ok' if u['is_banned'] else 'danger'}'>"
        f"{'Ban olib tashlash' if u['is_banned'] else 'Bloklash'}</button></form>"
    )
    add_bal = (
        f"<form class='inline' method='post' action='/mustaqil/admin/users/{uid}/balance'>"
        "<label class='field'>Miqdor (so'm)<input type='number' name='amount' value='10000' min='0'></label>"
        "<button class='btn solid'>Balans qo'shish</button></form>"
    )
    actions = f"<div class='panel'><div class='actbar'>{ban_btn}{add_bal}</div></div>"

    # Buyurtmalar jadvali
    orders_rows = ""
    for o in (u.get("orders") or []):
        emoji = _DOC_EMOJI.get(o["doc_type"], "📄")
        st_badge = _badge(_STATUS_LABEL.get(o["status"], o["status"]), _STATUS_CLASS.get(o["status"], "muted"))
        orders_rows += (
            "<tr>"
            f"<td class='muted'>#{o['id']}</td>"
            f"<td>{emoji} {_esc(o['doc_type'])}</td>"
            f"<td>{_esc(o['topic'][:40])}</td>"
            f"<td>{st_badge}</td>"
            f"<td>{_fmt_num(o['price'])} so'm</td>"
            f"<td class='muted'>{_fmt_dt(o['created_at'])}</td></tr>"
        )
    orders_head = "<tr><th>ID</th><th>Tur</th><th>Mavzu</th><th>Holat</th><th>Narx</th><th>Sana</th></tr>"
    orders_table = (f"<div class='panel'>{_scroll(f'<table><thead>{orders_head}</thead><tbody>{orders_rows}</tbody></table>')}</div>"
                    if orders_rows else "<div class='panel'><div class='empty'>Buyurtma yo'q.</div></div>")

    body = (
        _pagehead(uname, f"Foydalanuvchi #{uid}", "<a class='btn' href='/mustaqil/admin/users'>← Orqaga</a>")
        + info + "<h2>Amallar</h2>" + actions
        + "<h2>Buyurtmalar</h2>" + orders_table
    )
    return web.Response(content_type="text/html", text=_layout("users", "Foydalanuvchi", body))


async def _user_ban(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    from db.crud import ban_user
    uid = int(request.match_info["id"])
    data = await request.post()
    await ban_user(uid, data.get("banned", "1") == "1")
    return web.HTTPFound(f"/mustaqil/admin/users/{uid}")


async def _user_balance(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    from db.crud import admin_add_balance
    uid = int(request.match_info["id"])
    data = await request.post()
    try:
        amount = int(data.get("amount", 0))
    except ValueError:
        amount = 0
    if amount > 0:
        await admin_add_balance(uid, amount)
    return web.HTTPFound(f"/mustaqil/admin/users/{uid}")


# ─── orders ───

async def _orders(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    from db.crud import admin_list_orders
    status = request.query.get("status") or None
    rows = await admin_list_orders(status)
    chips = [("", "Hammasi"), ("pending", "Kutmoqda"), ("generating", "Tayyorlanmoqda"),
             ("done", "Tayyor"), ("error", "Xato")]
    filters = "<div class='filters'>"
    for val, label in chips:
        on = " on" if (val or None) == status else ""
        href = "/mustaqil/admin/orders" + (f"?status={val}" if val else "")
        filters += f"<a class='{on.strip()}' href='{href}'>{label}</a>"
    filters += "</div>"
    if not rows:
        table = "<div class='panel'><div class='empty'>Buyurtma yo'q.</div></div>"
    else:
        body_r = ""
        for o in rows:
            emoji = _DOC_EMOJI.get(o["doc_type"], "📄")
            uname = f"@{_esc(o['username'])}" if o.get("username") else f"id{o['user_id']}"
            st = _badge(_STATUS_LABEL.get(o["status"], o["status"]), _STATUS_CLASS.get(o["status"], "muted"))
            ai_prov = _badge(o.get("ai_provider") or "—", "muted")
            if o["status"] == "refunded" or o["price"] <= 0:
                refund = "—"
            else:
                refund = (
                    f"<form class='inline' method='post' action='/mustaqil/admin/orders/{o['id']}/refund' "
                    "onsubmit=\"return confirm('Narx balansga qaytarilsinmi?')\">"
                    "<button class='btn danger sm'>↩ Qaytarish</button></form>"
                )
            body_r += (
                "<tr>"
                f"<td class='muted'>#{o['id']}</td>"
                f"<td>{uname}</td>"
                f"<td>{emoji} {_esc(o['doc_type'])}</td>"
                f"<td>{_esc(o['topic'][:35])}</td>"
                f"<td>{st}</td>"
                f"<td>{ai_prov}</td>"
                f"<td>{_fmt_num(o['price'])} so'm</td>"
                f"<td class='muted'>{_fmt_dt(o['created_at'])}</td>"
                f"<td>{refund}</td></tr>"
            )
        head = "<tr><th>ID</th><th>Foydalanuvchi</th><th>Tur</th><th>Mavzu</th><th>Holat</th><th>AI</th><th>Narx</th><th>Sana</th><th>Amal</th></tr>"
        table = f"<div class='panel'>{_scroll(f'<table><thead>{head}</thead><tbody>{body_r}</tbody></table>')}</div>"
    body = _pagehead("Buyurtmalar", f"{len(rows)} ta") + filters + table
    return web.Response(content_type="text/html", text=_layout("orders", "Buyurtmalar", body))


# ─── payments ───

async def _payments(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    from db.crud import admin_list_payments
    rows = await admin_list_payments()
    if not rows:
        table = "<div class='panel'><div class='empty'>To'lov yo'q.</div></div>"
    else:
        body_r = ""
        for p in rows:
            uname = f"@{_esc(p['username'])}" if p.get("username") else f"id{p['user_id']}"
            st = _badge(_PAY_LABEL.get(p["status"], p["status"]), _PAY_CLASS.get(p["status"], "muted"))
            body_r += (
                "<tr>"
                f"<td class='muted'>#{p['id']}</td>"
                f"<td>{uname}</td>"
                f"<td>{_fmt_num(p['amount'])} so'm</td>"
                f"<td>{st}</td>"
                f"<td class='muted'>{_esc(p['merchant_trans_id'][:20])}</td>"
                f"<td class='muted'>{_fmt_dt(p['paid_at'] or p['created_at'])}</td></tr>"
            )
        head = "<tr><th>ID</th><th>Foydalanuvchi</th><th>Summa</th><th>Holat</th><th>Trans ID</th><th>Sana</th></tr>"
        table = f"<div class='panel'>{_scroll(f'<table><thead>{head}</thead><tbody>{body_r}</tbody></table>')}</div>"
    body = _pagehead("To'lovlar", f"{len(rows)} ta") + table
    return web.Response(content_type="text/html", text=_layout("payments", "To'lovlar", body))


# ─── referrals ───

async def _referrals(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    from db.base import async_session
    from db.models import Referral, User
    from sqlalchemy import select, func
    async with async_session() as s:
        rows = (await s.execute(
            select(Referral, User.username.label("rr_name"))
            .join(User, Referral.referrer_id == User.id, isouter=True)
            .order_by(Referral.created_at.desc()).limit(100)
        )).all()
        total_bonus = await s.scalar(select(func.sum(Referral.bonus_amount)).where(Referral.bonus_awarded == True)) or 0

    kpis = (
        _kpi("Jami referallar", str(len(rows)))
        + _kpi("To'lov qilganlar", str(sum(1 for r, _ in rows if r.bonus_awarded)))
        + _kpi("Jami bonus", _fmt_num(total_bonus) + " so'm")
    )
    body_r = ""
    for ref, rr_name in rows:
        awarded = _badge("✓ Bonus berildi", "ok") if ref.bonus_awarded else _badge("Kutmoqda", "muted")
        body_r += (
            "<tr>"
            f"<td>{rr_name or ref.referrer_id}</td>"
            f"<td class='muted'>{ref.referee_id}</td>"
            f"<td>{awarded}</td>"
            f"<td>{_fmt_num(ref.bonus_amount)} so'm</td>"
            f"<td class='muted'>{_fmt_dt(ref.created_at)}</td></tr>"
        )
    head = "<tr><th>Taklif qiluvchi</th><th>Yangi foydalanuvchi</th><th>Holat</th><th>Bonus</th><th>Sana</th></tr>"
    table = (f"<div class='panel'>{_scroll(f'<table><thead>{head}</thead><tbody>{body_r}</tbody></table>')}</div>"
             if body_r else "<div class='panel'><div class='empty'>Referal yo'q.</div></div>")
    body = (
        _pagehead("Referallar", f"{len(rows)} ta")
        + f"<div class='statbar'>{kpis}</div>"
        + table
    )
    return web.Response(content_type="text/html", text=_layout("referrals", "Referallar", body))


# ─── order refund ───

async def _order_refund(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    from db.crud import admin_refund_order
    oid = int(request.match_info["id"])
    await admin_refund_order(oid)
    return web.HTTPFound(request.headers.get("Referer", "/mustaqil/admin/orders"))


# ─── settings (narx & sozlamalar) ───

from config import DOC_TYPES  # noqa: E402


async def _settings(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    saved = request.query.get("saved")
    note = "<div class='badge ok' style='margin-bottom:16px'>✓ Saqlandi (darrov kuchga kirdi)</div>" if saved else ""

    # Narx jadval-shakli: 1 birlik narxi + eng kam narx + referal bonus
    _inp = "width:110px;padding:7px 9px;border:1px solid var(--border);border-radius:7px;background:var(--bg);color:var(--text)"
    rows = ""
    for key, info in DOC_TYPES.items():
        rows += (
            "<tr>"
            f"<td>{info['emoji']} {_esc(info['label'])}<div class='muted' style='font-size:11px'>"
            f"{info['cmin']}-{info['cmax']} {info['unit']}</div></td>"
            f"<td><input type='number' name='perunit_{key}' value='{settings.per_unit(key)}' min='0' style='{_inp}'></td>"
            f"<td><input type='number' name='minprice_{key}' value='{settings.min_price(key)}' min='0' style='{_inp}'></td>"
            f"<td><input type='number' name='ref_{key}' value='{settings.ref_bonus(key)}' min='0' style='{_inp}'></td>"
            "</tr>"
        )
    price_table = (
        "<div class='panel'><div class='scroll'><table><thead><tr>"
        f"<th>Hujjat turi</th><th>1 birlik narxi</th><th>Eng kam narx</th><th>Referal bonus</th>"
        "</tr></thead><tbody>" + rows + "</tbody></table></div></div>"
        "<div class='note'>Buyurtma narxi = <b>1 birlik narxi × sahifa/slayd/so'z soni</b> "
        "(lekin eng kam narxdan past emas). Talaba sonni o'zi kiritadi.</div>"
    )

    maint = settings.maintenance()
    maint_opt_on = "selected" if maint else ""
    maint_opt_off = "" if maint else "selected"
    general = (
        "<div class='panel' style='padding:18px;max-width:460px'>"
        "<label class='field' style='width:100%;margin-bottom:14px'>Minimal balans to'ldirish (so'm)"
        f"<input type='number' name='min_topup' value='{settings.eff_min_topup()}' min='0' "
        "style='width:100%;margin-top:5px'></label>"
        "<label class='field' style='width:100%'>Texnik tanaffus (yangi buyurtma qabul qilinmaydi)"
        "<select name='maintenance' style='width:100%;margin-top:5px'>"
        f"<option value='0' {maint_opt_off}>O'chiq — bot ishlayapti</option>"
        f"<option value='1' {maint_opt_on}>Yoniq — texnik tanaffus</option>"
        "</select></label></div>"
    )

    body = (
        _pagehead("Narx & Sozlama", "Narxlar darrov yangilanadi — bot qayta ishga tushishi shart emas")
        + note
        + "<form method='post' action='/mustaqil/admin/settings'>"
        + "<h2>💰 Narxlar va referal bonuslar</h2>" + price_table
        + "<h2>⚙️ Umumiy sozlamalar</h2>" + general
        + "<button class='btn solid' type='submit' style='margin-top:16px'>💾 Hammasini saqlash</button>"
        + "</form>"
    )
    return web.Response(content_type="text/html", text=_layout("settings", "Narx & Sozlama", body))


async def _settings_save(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    from db.crud import save_settings_bulk, load_settings
    from config import apply_overrides
    data = await request.post()
    out: dict[str, str] = {}
    for key in DOC_TYPES:
        for prefix in ("perunit_", "minprice_", "ref_"):
            field = prefix + key
            raw = data.get(field)
            if raw is not None:
                try:
                    out[field] = str(max(0, int(raw)))
                except (ValueError, TypeError):
                    pass
    for field in ("min_topup", "maintenance"):
        raw = data.get(field)
        if raw is not None:
            try:
                out[field] = str(max(0, int(raw)))
            except (ValueError, TypeError):
                pass
    if out:
        await save_settings_bulk(out)
        apply_overrides(await load_settings())  # jonli yangilash
    return web.HTTPFound("/mustaqil/admin/settings?saved=1")


# ─── monitor ───

def _bar(label: str, pct: float, detail: str = "") -> str:
    pct = max(0.0, min(100.0, pct))
    color = "var(--ok)" if pct < 70 else ("var(--warn)" if pct < 90 else "var(--bad)")
    return (
        "<div style='margin-bottom:16px'>"
        "<div style='display:flex;justify-content:space-between;font-size:13px;margin-bottom:5px'>"
        f"<span><b>{label}</b></span><span class='muted'>{detail}</span></div>"
        "<div style='height:11px;background:var(--subtle);border:1px solid var(--border);"
        "border-radius:6px;overflow:hidden'>"
        f"<div style='height:100%;width:{pct:.0f}%;background:{color};transition:width .3s'></div>"
        "</div></div>"
    )


async def _monitor(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        vals = list(map(int, line.split()[1:]))
        idle = vals[3]; total = sum(vals)
        time.sleep(0.1)
        with open("/proc/stat") as f:
            line2 = f.readline()
        vals2 = list(map(int, line2.split()[1:]))
        idle2 = vals2[3]; total2 = sum(vals2)
        cpu_pct = round(100 * (1 - (idle2 - idle) / (total2 - total)), 1) if (total2 - total) else 0
    except Exception:
        cpu_pct = 0

    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, _, v = line.partition(":")
                mem[k] = int(v.strip().split()[0])
        mt = mem.get("MemTotal", 1) / 1048576
        ma = mem.get("MemAvailable", 0) / 1048576
        ram_pct = ((mt - ma) / mt * 100) if mt else 0
    except Exception:
        mt = ma = 1; ram_pct = 0

    try:
        du = shutil.disk_usage("/")
        disk_pct = du.used / du.total * 100 if du.total else 0
    except Exception:
        du = type("d", (), {"used": 0, "total": 1})()
        disk_pct = 0

    try:
        with open("/proc/uptime") as f:
            up = float(f.readline().split()[0])
        d, h, m = int(up // 86400), int((up % 86400) // 3600), int((up % 3600) // 60)
        uptime_str = f"{d} kun {h} soat {m} daqiqa"
    except Exception:
        uptime_str = "—"

    bars = (
        "<div class='panel' style='padding:20px'>"
        + _bar("CPU", cpu_pct, f"{cpu_pct}%")
        + _bar("RAM", ram_pct, f"{(mt-ma):.2f} / {mt:.2f} GB ({ram_pct:.0f}%)")
        + _bar("Disk", disk_pct, f"{du.used/1073741824:.1f} / {du.total/1073741824:.1f} GB ({disk_pct:.0f}%)")
        + "</div>"
    )
    svc_cards = ""
    for name, label in _SERVICES:
        try:
            r = subprocess.run(["systemctl", "is-active", name],
                               capture_output=True, text=True, timeout=5)
            st = r.stdout.strip()
        except Exception:
            st = "unknown"
        cls = {"active": "ok", "inactive": "muted", "failed": "bad"}.get(st, "muted")
        lbl = {"active": "Ishlayapti", "inactive": "To'xtagan", "failed": "Xato"}.get(st, st)
        svc_cards += f"<div class='stat'><div class='label'>{_esc(label)}</div><div style='margin-top:6px'>{_badge(lbl, cls)}</div></div>"

    body = (
        _pagehead("Tizim Holati", uptime_str, "<a class='btn' href='/mustaqil/admin/monitor'>↻ Yangilash</a>")
        + bars
        + "<h3 style='margin:22px 0 10px;font-size:15px'>Servislar salomatligi</h3>"
        + f"<div class='statbar'>{svc_cards}</div>"
    )
    return web.Response(content_type="text/html", text=_layout("monitor", "Tizim Holati", body))


# ─── services ───

async def _services(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    done = request.query.get("done", "")
    msg = f"<div class='badge ok' style='margin-bottom:14px'>✓ {_esc(done)}</div>" if done else ""
    rows = ""
    for name, label in _SERVICES:
        try:
            r = subprocess.run(["systemctl", "is-active", name], capture_output=True, text=True, timeout=5)
            st = r.stdout.strip()
        except Exception:
            st = "unknown"
        cls = {"active": "ok", "inactive": "muted", "failed": "bad"}.get(st, "muted")
        lbl = {"active": "Ishlayapti", "inactive": "To'xtagan", "failed": "Xato"}.get(st, st)
        btns = ""
        for act, txt, bcls in (("restart", "↻ Restart", "solid"), ("stop", "⏹ To'xtatish", "danger"), ("start", "▶ Yoqish", "")):
            btns += (f"<form method='post' action='/mustaqil/admin/services/{name}/{act}' style='display:inline-block;margin:0 4px 0 0'>"
                     f"<button class='btn {bcls}'>{txt}</button></form>")
        rows += (f"<tr><td><b>{_esc(label)}</b><div class='muted' style='font-size:12px'>{name}</div></td>"
                 f"<td>{_badge(lbl, cls)}</td><td style='white-space:nowrap'>{btns}</td></tr>")
    table = (f"<div class='panel'>{_scroll('<table><thead><tr><th>Servis</th><th>Holat</th><th>Amal</th></tr></thead><tbody>'+ rows +'</tbody></table>')}</div>")
    body = _pagehead("Servislar", "", "<a class='btn' href='/mustaqil/admin/services'>↻</a>") + msg + table
    return web.Response(content_type="text/html", text=_layout("services", "Servislar", body))


async def _services_action(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    import asyncio as aio
    name = request.match_info["name"]
    action = request.match_info["action"]
    if name not in _SERVICE_NAMES or action not in {"start", "stop", "restart"}:
        return web.HTTPFound("/mustaqil/admin/services?done=xato")
    ok = await aio.to_thread(
        lambda: subprocess.run(["sudo", "-n", "systemctl", action, name],
                               capture_output=True, timeout=25).returncode == 0
    )
    return web.HTTPFound(f"/mustaqil/admin/services?done={'✓ ' + action + ' ' + name if ok else 'Xato'}")


# ─── logs ───

async def _logs(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    try:
        n = max(50, min(500, int(request.query.get("n", "200"))))
    except ValueError:
        n = 200
    try:
        proc = subprocess.run(
            ["sudo", "-n", "journalctl", "-u", "mustaqilbot", "--no-pager", "-n", str(n)],
            capture_output=True, text=True, timeout=8
        )
        text = proc.stdout or proc.stderr or "(log bo'sh)"
    except Exception as e:
        text = f"Loglarni o'qib bo'lmadi: {e}"
    body = (
        _pagehead("Loglar", f"mustaqilbot · oxirgi {n} qator",
                  "<a class='btn' href='/mustaqil/admin/logs'>↻ Yangilash</a>")
        + f"<div class='panel'><pre style='padding:16px;font-size:11px;overflow:auto;"
        f"max-height:600px;white-space:pre-wrap;word-break:break-word;"
        f"background:#0b0f0b;color:#3ad13a;margin:0;border-radius:10px'>{_esc(text)}</pre></div>"
    )
    return web.Response(content_type="text/html", text=_layout("logs", "Loglar", body))


# ─── env editor ───

def _env_path() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


async def _env(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    try:
        with open(_env_path(), "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        content = ""
    flag = request.query.get("msg", "")
    msg = ""
    if flag == "saved":
        msg = "<div class='badge ok' style='margin-bottom:14px'>✓ Saqlandi</div>"
    elif flag == "restarted":
        msg = "<div class='badge ok' style='margin-bottom:14px'>✓ Saqlandi va restart qilindi</div>"
    elif flag == "error":
        msg = "<div class='badge bad' style='margin-bottom:14px'>✗ Saqlashda xato</div>"
    form = (
        "<form method='post' action='/mustaqil/admin/env'>"
        "<div class='panel' style='padding:18px'>"
        "<textarea name='env_content' spellcheck='false' style='width:100%;height:440px;"
        "font-family:monospace;font-size:13px;padding:12px;border:1px solid var(--border);"
        "border-radius:8px;background:var(--bg);color:var(--text);margin-bottom:14px'>"
        f"{_esc(content)}</textarea>"
        "<div style='display:flex;gap:10px'>"
        "<button class='btn solid' name='action' value='save'>💾 Saqlash</button>"
        "<button class='btn danger' name='action' value='restart'>💾 Saqlash va Restart</button>"
        "</div></div></form>"
    )
    body = _pagehead(".env Muharrir", "Sozlamalar") + msg + form
    return web.Response(content_type="text/html", text=_layout("env", ".env", body))


async def _env_save(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    data = await request.post()
    content = data.get("env_content", "")
    action = data.get("action", "save")
    path = _env_path()
    try:
        if os.path.exists(path):
            shutil.copy(path, path + ".bak")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        logger.exception(".env saqlanmadi: %s", e)
        return web.HTTPFound("/mustaqil/admin/env?msg=error")
    if action == "restart":
        subprocess.Popen(["sudo", "-n", "systemctl", "restart", "mustaqilbot"])
        return web.HTTPFound("/mustaqil/admin/env?msg=restarted")
    return web.HTTPFound("/mustaqil/admin/env?msg=saved")


# ─── broadcast ───

async def _broadcast(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    status = ""
    if _BC["ts"]:
        state = "yuborilmoqda…" if _BC["running"] else "tugadi"
        status = (f"<div class='panel' style='padding:14px;margin-bottom:14px'>"
                  f"<b>Oxirgi broadcast:</b> {state}<br>"
                  f"<span class='muted'>Jami: {_BC['total']} · Yuborildi: {_BC['sent']} · Xato: {_BC['failed']}</span></div>")
    form = (
        "<form method='post' action='/mustaqil/admin/broadcast'>"
        "<div class='panel' style='padding:18px;max-width:640px'>"
        "<label class='field' style='width:100%;margin-bottom:12px'>Xabar matni (HTML)"
        "<textarea name='message_text' style='width:100%;height:150px;padding:10px;"
        "border:1px solid var(--border);border-radius:8px;background:var(--bg);"
        "color:var(--text);margin-top:5px'></textarea></label>"
        "<button class='btn solid' onclick='return confirm(\"Barchaga yuborilsinmi?\")'>📢 Barchaga Yuborish</button>"
        "</div></form>"
    )
    body = _pagehead("Xabar Yuborish", "Ommaviy xabarnoma") + status + form
    return web.Response(content_type="text/html", text=_layout("broadcast", "Broadcast", body))


async def _broadcast_send(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    if _BC["running"]:
        return web.HTTPFound("/mustaqil/admin/broadcast")
    data = await request.post()
    text_msg = (data.get("message_text") or "").strip()
    bot = request.app.get("bot")
    if text_msg and bot:
        import asyncio
        asyncio.create_task(_do_broadcast(bot, text_msg))
    return web.HTTPFound("/mustaqil/admin/broadcast")


async def _do_broadcast(bot, text: str):
    import asyncio
    from db.base import async_session
    from db.models import User
    from sqlalchemy import select
    _BC.update(running=True, sent=0, failed=0, total=0, ts=time.time())
    try:
        async with async_session() as s:
            ids = (await s.execute(select(User.id))).scalars().all()
        _BC["total"] = len(ids)
        for uid in ids:
            try:
                await bot.send_message(uid, text, parse_mode="HTML")
                _BC["sent"] += 1
            except Exception:
                _BC["failed"] += 1
            await asyncio.sleep(0.05)
    except Exception as e:
        logger.exception("Broadcast xatosi: %s", e)
    finally:
        _BC["running"] = False


# ─── stats ───

async def _stats(request: web.Request) -> web.Response:
    g = _guard(request)
    if g is not None:
        return g
    from db.base import async_session
    from db.models import Order, User
    from sqlalchemy import select, func
    async with async_session() as s:
        by_type = (await s.execute(
            select(Order.doc_type, func.count(Order.id))
            .where(Order.status == "done")
            .group_by(Order.doc_type)
        )).all()
        by_ai = (await s.execute(
            select(Order.ai_provider, func.count(Order.id))
            .where(Order.status == "done")
            .group_by(Order.ai_provider)
        )).all()

    from config import DOC_TYPES
    doc_rows = ""
    for dtype, cnt in sorted(by_type, key=lambda x: -x[1]):
        info = DOC_TYPES.get(dtype, {})
        doc_rows += _kpi(f"{info.get('emoji','📄')} {info.get('label', dtype)}", str(cnt))
    ai_rows = ""
    for prov, cnt in by_ai:
        ai_rows += _kpi(prov or "Noma'lum", str(cnt), "ta buyurtma")

    body = (
        _pagehead("Statistika", "Bajarilgan buyurtmalar tahlili")
        + "<h2>Hujjat turlari bo'yicha</h2>"
        + (f"<div class='statbar'>{doc_rows}</div>" if doc_rows else "<div class='panel'><div class='empty'>Hali buyurtma yo'q.</div></div>")
        + "<h2>AI provayder bo'yicha</h2>"
        + (f"<div class='statbar'>{ai_rows}</div>" if ai_rows else "<div class='panel'><div class='empty'>—</div></div>")
    )
    return web.Response(content_type="text/html", text=_layout("stats", "Statistika", body))


def setup_admin_routes(app: web.Application, bot=None) -> None:
    app["bot"] = bot
    app.router.add_get("/mustaqil/admin", _dashboard)
    app.router.add_get("/mustaqil/admin/", _dashboard)
    app.router.add_get("/mustaqil/admin/users", _users)
    app.router.add_get("/mustaqil/admin/users/{id}", _user_detail)
    app.router.add_post("/mustaqil/admin/users/{id}/ban", _user_ban)
    app.router.add_post("/mustaqil/admin/users/{id}/balance", _user_balance)
    app.router.add_get("/mustaqil/admin/orders", _orders)
    app.router.add_post("/mustaqil/admin/orders/{id}/refund", _order_refund)
    app.router.add_get("/mustaqil/admin/payments", _payments)
    app.router.add_get("/mustaqil/admin/referrals", _referrals)
    app.router.add_get("/mustaqil/admin/settings", _settings)
    app.router.add_post("/mustaqil/admin/settings", _settings_save)
    app.router.add_get("/mustaqil/admin/stats", _stats)
    app.router.add_get("/mustaqil/admin/monitor", _monitor)
    app.router.add_get("/mustaqil/admin/services", _services)
    app.router.add_post("/mustaqil/admin/services/{name}/{action}", _services_action)
    app.router.add_get("/mustaqil/admin/logs", _logs)
    app.router.add_get("/mustaqil/admin/env", _env)
    app.router.add_post("/mustaqil/admin/env", _env_save)
    app.router.add_get("/mustaqil/admin/broadcast", _broadcast)
    app.router.add_post("/mustaqil/admin/broadcast", _broadcast_send)
