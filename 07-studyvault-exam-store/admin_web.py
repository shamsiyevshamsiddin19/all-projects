"""Web admin panel — sessiyabot. Subtitr/Mustaqil bot bilan BIR XIL dizayn.

Bo'limlar: Dashboard, Foydalanuvchilar, Bazalar (qo'shish/tahrirlash/o'chirish),
To'lovlar, Referallar, Sozlamalar (tag, majburiy obuna, kanallar CRUD).
Chap sidebar + bot tanlagich (dropdown) + responsive (telefon). Basic Auth.

Bu panel master (subtitr) panel orqali /sessiya/ ostida proxy qilinadi:
X-Forwarded-Prefix=/sessiya va X-Admin-Proxy=<sir> sarlavhalari bilan — bitta
domen, bitta parol. Shuning uchun ichki havolalar prefiks bilan ishlaydi (_PFX).
"""
from __future__ import annotations

import base64
import contextvars
import hmac
import html
import os
import shutil
import subprocess
import time

from aiohttp import web

SESSIYA_SERVICE = "sessiyabot"

import db
from config import settings

_BOT = None  # main.py setup_admin_routes orqali beradi (kanal getChat uchun)

# Master (subtitr) panel bu panelni /sessiya/ ostida proxy qiladi.
_PFX: contextvars.ContextVar[str] = contextvars.ContextVar("admin_pfx", default="")

CURRENT_BOT = "sessiya"


@web.middleware
async def _prefix_mw(request: web.Request, handler):
    _PFX.set((request.headers.get("X-Forwarded-Prefix", "") or "").rstrip("/"))
    return await handler(request)


def _redir(path: str) -> web.HTTPFound:
    """Prefiks bilan redirect (proxy ostida ham to'g'ri ishlasin)."""
    return web.HTTPFound(_PFX.get() + path)


NAV = [
    ("dash", "Dashboard", "/admin", "dash"),
    ("users", "Foydalanuvchilar", "/admin/users", "users"),
    ("products", "Bazalar", "/admin/products", "box"),
    ("payments", "To'lovlar", "/admin/payments", "pay"),
    ("refs", "Referallar", "/admin/referrals", "ref"),
    ("stats", "Statistika", "/admin/stats", "stats"),
    ("monitor", "Tizim holati", "/admin/monitor", "monitor"),
    ("logs", "Loglar", "/admin/logs", "logs"),
    ("settings", "Sozlamalar", "/admin/settings", "settings"),
]


def _esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def _fmt_num(v) -> str:
    return f"{int(v or 0):,}".replace(",", " ")


# ─── auth ───

def _guard(request: web.Request):
    # Parol himoyasi foydalanuvchi so'roviga ko'ra OLIB TASHLANDI — barcha so'rov o'tadi.
    return None


# ─── icons (thin SVG) ───

def _icon(name: str) -> str:
    paths = {
        "dash": "<rect x='3' y='3' width='7' height='7' rx='1'/><rect x='14' y='3' width='7' height='7' rx='1'/><rect x='3' y='14' width='7' height='7' rx='1'/><rect x='14' y='14' width='7' height='7' rx='1'/>",
        "users": "<path d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M22 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/>",
        "box": "<path d='M21 8v8a2 2 0 0 1-1 1.73l-7 4a2 2 0 0 1-2 0l-7-4A2 2 0 0 1 3 16V8a2 2 0 0 1 1-1.73l7-4a2 2 0 0 1 2 0l7 4A2 2 0 0 1 21 8z'/><polyline points='3.27 6.96 12 12.01 20.73 6.96'/><line x1='12' y1='22' x2='12' y2='12'/>",
        "pay": "<rect x='2' y='5' width='20' height='14' rx='2'/><path d='M2 10h20'/>",
        "ref": "<path d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><line x1='19' y1='8' x2='19' y2='14'/><line x1='22' y1='11' x2='16' y2='11'/>",
        "settings": "<circle cx='12' cy='12' r='3'/><path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z'/>",
        "stats": "<line x1='18' y1='20' x2='18' y2='10'/><line x1='12' y1='20' x2='12' y2='4'/><line x1='6' y1='20' x2='6' y2='14'/>",
        "monitor": "<path d='M22 12h-4l-3 9L9 3l-3 9H2'/>",
        "logs": "<path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><polyline points='14 2 14 8 20 8'/><line x1='16' y1='13' x2='8' y2='13'/><line x1='16' y1='17' x2='8' y2='17'/>",
    }
    return ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' "
            "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
            + paths.get(name, "") + "</svg>")


# ─── style (subtitr/mustaqil bilan bir xil) ───

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
  padding:6px 12px;border-radius:8px;background:var(--bg);cursor:pointer;font:inherit;
  display:inline-block}
.btn:hover{color:var(--text)}
.btn.solid{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn.danger{color:var(--bad);border-color:#f5c2c2;background:var(--bg)}
.btn.ok{color:var(--ok);border-color:#bde9da;background:var(--bg)}
.btn.sm{padding:4px 10px;font-size:12px}
.statbar{display:flex;background:var(--bg);border:1px solid var(--border);
  border-radius:12px;overflow-x:auto;margin-bottom:28px}
.stat{flex:1 0 auto;min-width:122px;padding:15px 18px;border-right:1px solid var(--border)}
.stat:last-child{border-right:none}
.stat .label{color:var(--muted);font-size:13px;margin-bottom:5px;white-space:nowrap}
.stat .num{font-size:24px;font-weight:600;letter-spacing:-.5px}
.stat .note{color:var(--muted);font-size:12px;margin-top:3px;white-space:nowrap}
h2{font-size:15px;font-weight:600;margin:22px 0 12px}
.panel{background:var(--bg);border:1px solid var(--border);border-radius:12px;
  overflow:hidden;margin-bottom:26px}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px;min-width:520px}
th,td{text-align:left;padding:11px 16px;border-bottom:1px solid var(--border);white-space:nowrap}
th{color:var(--muted);font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:none}
td.muted,.muted{color:var(--muted)}
td code,code{background:var(--subtle);padding:2px 7px;border-radius:6px;font-size:12.5px;
  font-family:ui-monospace,Menlo,Consolas,monospace}
.badge{display:inline-block;font-size:12px;padding:2px 9px;border-radius:20px;border:1px solid var(--border)}
.badge.ok{color:var(--ok);border-color:#bde9da}
.badge.bad{color:var(--bad);border-color:#f5c2c2}
.badge.warn{color:var(--warn);border-color:#f0d6a8}
.badge.muted{color:var(--muted)}
.empty{padding:22px 16px;color:var(--muted);font-size:14px;text-align:center}
.note{color:var(--muted);font-size:12.5px;margin:6px 2px 18px}
.search{display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap;align-items:center}
.search input{flex:1;max-width:320px;padding:8px 12px;border:1px solid var(--border);
  border-radius:8px;font-size:14px;background:var(--bg);color:var(--text)}
.filters{display:flex;gap:6px;margin-bottom:18px;flex-wrap:wrap}
.filters a{font-size:13px;padding:6px 12px;border:1px solid var(--border);
  border-radius:20px;text-decoration:none;color:var(--muted);background:var(--bg)}
.filters a.on{color:var(--text);border-color:var(--accent)}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:18px}
form.inline{display:inline-block;margin:0}
.field{display:block;margin-bottom:14px;font-size:13px;color:var(--muted)}
.field span{display:block;margin-bottom:6px;font-weight:500}
.field input,.field select,.field textarea{width:100%;padding:9px 12px;border:1px solid var(--border);
  border-radius:8px;font-size:14px;font-family:inherit;background:var(--bg);color:var(--text)}
.field input:focus,.field textarea:focus,.field select:focus{outline:none;border-color:var(--accent)}
.formcard{background:var(--bg);border:1px solid var(--border);border-radius:12px;
  padding:20px;max-width:560px;margin-bottom:26px}
a.lk{color:var(--text);text-decoration:underline}
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


# ─── helpers ───

def _kpi(label: str, num, note: str = "") -> str:
    note_h = f"<div class='note' style='margin:3px 0 0'>{note}</div>" if note else ""
    return (f"<div class='stat'><div class='label'>{label}</div>"
            f"<div class='num'>{num}</div>{note_h}</div>")


def _status_b(status: str) -> str:
    cls = {"paid": "ok", "pending": "warn", "created": "muted",
           "replaced": "muted", "cancelled": "muted"}.get(status, "bad")
    return f"<span class='badge {cls}'>{_esc(status)}</span>"


def _dropdown(p: str) -> str:
    """Bot tanlagich. Proxy ostida (p='/sessiya') hammasi shu domen ildizida."""
    if p:
        subtitr_url, sessiya_url, mustaqil_url = "/admin", f"{p}/admin", "/mustaqil/admin"
    else:
        subtitr_url = os.getenv(
            "SUBTITR_ADMIN_URL",
            "https://comes-reforms-preferences-anytime.trycloudflare.com/admin")
        sessiya_url, mustaqil_url = "/admin", "/mustaqil/admin"
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
    bots = [(subtitr_url, film, "Subtitr bot", False),
            (sessiya_url, book, "Sessiya bot", True),
            (mustaqil_url, pencil, "Mustaqil bot", False),
            ("/tatulms/admin", cap, "TATU LMS bot", False),
            ("/quiz/admin", quiz, "Quiz bot", False),
            ("/wstore/admin", cart, "wstore market", False),
            ("/site/admin", chart, "Portfolio", False)]
    cur = next((b for b in bots if b[3]), bots[0])
    opts = ""
    for url, svg, label, act in bots:
        a = " active" if act else ""
        opts += f"<a class='botopt{a}' href='{_esc(url)}'>{svg}<span>{label}</span></a>"
    chev = ("<svg class='botchev' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
            "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
            "<polyline points='6 9 12 15 18 9'/></svg>")
    return (
        "<style>.botdd{position:relative;flex:1;min-width:0}"
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
    )


def _layout(active: str, title: str, sub: str, body: str) -> str:
    p = _PFX.get()
    nav = "".join(
        f"<a class='{'active' if k == active else ''}' href='{p}{u}'>{_icon(ic)}<span>{_esc(l)}</span></a>"
        for k, l, u, ic in NAV)
    # Body ichidagi ichki havolalarni (href='/admin..., action='/admin...) prefikslash
    if p:
        body = body.replace("'/admin", "'" + p + "/admin")
    sub_h = f"<div class='sub'>{_esc(sub)}</div>" if sub else ""
    return f"""<!doctype html><html lang='uz'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{_esc(title)} · Sessiya Admin</title><style>{_STYLE}</style></head><body>
<div class='layout'>
<input type='checkbox' id='navtoggle' class='navtoggle'>
<aside class='sidebar'>
  <div class='brand'><span class='dot'>S</span>{_dropdown(p)}</div>
  <nav class='nav'>{nav}</nav>
</aside>
<label for='navtoggle' class='overlay'></label>
<main class='content'>
  <div class='topbar'><label for='navtoggle' class='hamburger'>☰</label><span class='ttl'>{_esc(title)}</span></div>
  <div class='pagehead'><div><h1>{_esc(title)}</h1>{sub_h}</div></div>
  {body}
  <div class='foot'>Sessiya Bot · Admin panel</div>
</main></div>{_LABEL_SCRIPT}</body></html>"""


# ====================================================================== PAGES

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
                     f"text-anchor='middle' fill='#6e6e80'>{_esc(label)}</text>")
    return (f"<svg viewBox='0 0 {w} {h}' width='100%' style='max-width:{w}px;height:auto'>"
            + "".join(parts) + "</svg>")


async def _dash_charts():
    """Kunlik yangi foydalanuvchi + daromad grafiklari (xato bo'lsa jim o'tadi)."""
    try:
        reg = await db.pool().fetch(
            "SELECT date_trunc('day', created_at) d, COUNT(*) c FROM users "
            "GROUP BY d ORDER BY d DESC LIMIT 14")
        rev = await db.pool().fetch(
            "SELECT date_trunc('day', created_at) d, COALESCE(SUM(amount),0) v "
            "FROM payments WHERE status='paid' GROUP BY d ORDER BY d DESC LIMIT 14")
        reg_pairs = [(r["d"].strftime("%d.%m"), r["c"]) for r in reversed(reg)]
        rev_pairs = [(r["d"].strftime("%d.%m"), int(r["v"]) // 1000) for r in reversed(rev)]
        return (
            "<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));"
            "gap:16px;margin-bottom:26px'>"
            "<div class='panel' style='padding:16px'><h2>Yangi foydalanuvchilar (kunlik)</h2>"
            + _bar_chart(reg_pairs) + "</div>"
            "<div class='panel' style='padding:16px'><h2>Daromad (kunlik, ming so'm)</h2>"
            + _bar_chart(rev_pairs) + "</div></div>")
    except Exception:
        return ""


# ─── monitor / logs / stats ───

def _bar(label, pct, text=""):
    pct = max(0.0, min(100.0, pct))
    color = "var(--bad)" if pct >= 85 else ("var(--warn)" if pct >= 65 else "var(--accent)")
    return (f"<div style='margin-bottom:16px'>"
            f"<div style='display:flex;justify-content:space-between;font-size:13px;margin-bottom:6px'>"
            f"<span>{label}</span><span class='muted'>{text}</span></div>"
            f"<div style='height:9px;background:var(--subtle);border:1px solid var(--border);"
            f"border-radius:6px;overflow:hidden'>"
            f"<div style='height:100%;width:{pct:.0f}%;background:{color};"
            f"border-radius:6px'></div></div></div>")


def _svc_status(name):
    try:
        r = subprocess.run(["systemctl", "is-active", name],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return "unknown"


def _read_system():
    try:
        with open("/proc/stat") as f:
            v = list(map(int, f.readline().split()[1:]))
        idle, total = v[3], sum(v)
        time.sleep(0.1)
        with open("/proc/stat") as f:
            v2 = list(map(int, f.readline().split()[1:]))
        idle2, total2 = v2[3], sum(v2)
        cpu = round(100 * (1 - (idle2 - idle) / (total2 - total)), 1) if total2 > total else 0
    except Exception:
        cpu = 0
    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, _, val = line.partition(":")
                mem[k] = int(val.strip().split()[0])
        mt = mem.get("MemTotal", 1) / 1048576
        ma = mem.get("MemAvailable", 0) / 1048576
        ram = (mt - ma) / mt * 100 if mt else 0
    except Exception:
        mt = ma = 1
        ram = 0
    try:
        du = shutil.disk_usage("/")
        disk = du.used / du.total * 100 if du.total else 0
    except Exception:
        du = None
        disk = 0
    try:
        with open("/proc/uptime") as f:
            up = float(f.readline().split()[0])
        uptime = f"{int(up//86400)} kun {int((up%86400)//3600)} soat {int((up%3600)//60)} daqiqa"
    except Exception:
        uptime = "—"
    return {"cpu": cpu, "ram": ram, "mt": mt, "ma": ma, "disk": disk, "du": du,
            "uptime": uptime}


async def _monitor(request):
    g = _guard(request)
    if g is not None:
        return g
    s = _read_system()
    du = s["du"]
    disk_txt = f"{du.used/1073741824:.1f} / {du.total/1073741824:.1f} GB" if du else "—"
    bars = ("<div class='panel' style='padding:20px'>"
            + _bar("CPU", s["cpu"], f"{s['cpu']}%")
            + _bar("RAM", s["ram"], f"{s['mt']-s['ma']:.2f} / {s['mt']:.2f} GB ({s['ram']:.0f}%)")
            + _bar("Disk", s["disk"], f"{disk_txt} ({s['disk']:.0f}%)") + "</div>")
    st = _svc_status(SESSIYA_SERVICE)
    cls = {"active": "ok", "inactive": "muted", "failed": "bad"}.get(st, "muted")
    lbl = {"active": "Ishlayapti", "inactive": "To'xtagan", "failed": "Xato"}.get(st, st)
    svc = ("<div class='statbar'>"
           f"<div class='stat'><div class='label'>Bot xizmati</div>"
           f"<div style='margin-top:6px'><span class='badge {cls}'>{lbl}</span></div></div>"
           f"<div class='stat'><div class='label'>Server ishlashi</div>"
           f"<div class='num' style='font-size:15px'>{_esc(s['uptime'])}</div></div></div>")
    body = bars + "<h2 style='margin:22px 0 12px'>Bot va server</h2>" + svc
    return web.Response(content_type="text/html",
                        text=_layout("monitor", "Tizim holati", s["uptime"], body))


async def _logs(request):
    g = _guard(request)
    if g is not None:
        return g
    try:
        n = max(50, min(500, int(request.query.get("n", "200"))))
    except ValueError:
        n = 200
    try:
        p = subprocess.run(["journalctl", "-u", SESSIYA_SERVICE, "--no-pager", "-n", str(n)],
                           capture_output=True, text=True, timeout=8)
        txt = p.stdout or p.stderr or "(log bo'sh)"
    except Exception as e:
        txt = f"Loglarni o'qib bo'lmadi: {e}"
    body = ("<div class='panel'><pre style='padding:16px;font-size:11px;overflow:auto;"
            "max-height:600px;white-space:pre-wrap;word-break:break-word;"
            f"background:#0b0f0b;color:#3ad13a;margin:0;border-radius:10px'>{_esc(txt)}</pre></div>")
    return web.Response(content_type="text/html",
                        text=_layout("logs", "Loglar", f"{SESSIYA_SERVICE} · oxirgi {n} qator", body))


async def _stats(request):
    g = _guard(request)
    if g is not None:
        return g
    users = await db.count_users()
    prods = await db.count_products()
    paid = await db.pool().fetchval("SELECT COUNT(*) FROM payments WHERE status='paid'")
    revenue = await db.pool().fetchval("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='paid'")
    refs = await db.pool().fetchval("SELECT COUNT(*) FROM referrals")
    pending = await db.pool().fetchval("SELECT COUNT(*) FROM payments WHERE status<>'paid'")
    cards = (_kpi("Foydalanuvchilar", _fmt_num(users)) + _kpi("Bazalar", _fmt_num(prods))
             + _kpi("To'langan", _fmt_num(paid)) + _kpi("Kutilmoqda", _fmt_num(pending))
             + _kpi("Daromad", _fmt_num(revenue) + " so'm") + _kpi("Referallar", _fmt_num(refs)))
    charts = await _dash_charts()
    body = f"<div class='statbar'>{cards}</div>{charts}"
    return web.Response(content_type="text/html",
                        text=_layout("stats", "Statistika", "Batafsil ko'rsatkichlar", body))


async def _dashboard(request):
    g = _guard(request)
    if g is not None:
        return g
    users = await db.count_users()
    prods = await db.count_products()
    paid = await db.pool().fetchval("SELECT COUNT(*) FROM payments WHERE status='paid'")
    revenue = await db.pool().fetchval("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='paid'")
    refs = await db.pool().fetchval("SELECT COUNT(*) FROM referrals")
    cards = (
        _kpi("Foydalanuvchilar", users)
        + _kpi("Bazalar", prods)
        + _kpi("To'langan", paid)
        + _kpi("Daromad", _fmt_num(revenue) + " so'm")
        + _kpi("Referallar", refs))
    rows = await db.pool().fetch(
        "SELECT id,chat_id,base_num,amount,status,created_at FROM payments ORDER BY id DESC LIMIT 12")
    trs = "".join(
        f"<tr><td class='muted'>#{r['id']}</td><td>{r['chat_id']}</td><td>{_esc(r['base_num'])}</td>"
        f"<td>{_fmt_num(r['amount'])}</td><td>{_status_b(r['status'])}</td>"
        f"<td class='muted'>{_esc(str(r['created_at'])[:16])}</td></tr>" for r in rows)
    table = (
        "<h2>So'nggi to'lovlar</h2>"
        "<div class='panel'><div class='scroll'><table><thead><tr><th>ID</th><th>Chat</th>"
        "<th>Baza</th><th>Summa</th><th>Holat</th><th>Sana</th></tr></thead><tbody>"
        f"{trs or '<tr><td class=empty colspan=6>To&#39;lov yo&#39;q</td></tr>'}</tbody></table></div></div>")
    charts = await _dash_charts()
    body = f"<div class='statbar'>{cards}</div>{charts}{table}"
    return web.Response(content_type="text/html",
                        text=_layout("dash", "Dashboard", "Umumiy ko'rsatkichlar", body))


async def _users(request):
    g = _guard(request)
    if g is not None:
        return g
    q = (request.query.get("q") or "").strip()
    cols = "chat_id,username,first_name,last_name,phone,step,created_at"
    if q and q.lstrip("-").isdigit():
        rows = await db.pool().fetch(f"SELECT {cols} FROM users WHERE chat_id=$1", int(q))
    elif q:
        like = f"%{q.lstrip('@')}%"
        rows = await db.pool().fetch(
            f"SELECT {cols} FROM users WHERE username ILIKE $1 OR first_name ILIKE $1 "
            f"OR last_name ILIKE $1 OR phone ILIKE $1 ORDER BY created_at DESC LIMIT 100", like)
    else:
        rows = await db.pool().fetch(f"SELECT {cols} FROM users ORDER BY created_at DESC LIMIT 100")

    def cell(v):
        return _esc(v) if v else "<span class='muted'>—</span>"

    trs = ""
    for r in rows:
        uname = f"@{_esc(r['username'])}" if r['username'] else "<span class='muted'>—</span>"
        full = " ".join(x for x in (r['first_name'], r['last_name']) if x)
        trs += (f"<tr><td><code>{r['chat_id']}</code></td><td>{uname}</td>"
                f"<td>{cell(full)}</td><td>{cell(r['phone'])}</td><td>{cell(r['step'])}</td>"
                f"<td class='muted'>{_esc(str(r['created_at'])[:16])}</td></tr>")
    total = await db.count_users()
    body = (
        f"<form class='search' method='get' action='/admin/users'>"
        f"<input name='q' placeholder='ID, @username, ism yoki telefon' value='{_esc(q)}'>"
        f"<button class='btn solid' type='submit'>Qidirish</button>"
        f"<span class='muted'>Jami: {total}</span></form>"
        "<div class='panel'><div class='scroll'><table><thead><tr><th>Chat ID</th><th>Username</th>"
        "<th>Ism</th><th>Telefon</th><th>Bosqich</th><th>Qo'shilgan</th></tr></thead><tbody>"
        f"{trs or '<tr><td class=empty colspan=6>Topilmadi</td></tr>'}</tbody></table></div></div>")
    return web.Response(content_type="text/html",
                        text=_layout("users", "Foydalanuvchilar", "Qidiruv: ID, username, ism, telefon", body))


# ---------------------------------------------------------------- BAZALAR CRUD

_COURSES = ["1-kurs", "2-kurs", "3-kurs", "4-kurs"]


async def _products(request):
    g = _guard(request)
    if g is not None:
        return g
    rows = await db.all_products()
    saved = request.query.get("saved")
    note = f"<div class='badge ok' style='margin-bottom:16px'>✓ {_esc(saved)}</div>" if saved else ""
    trs = ""
    for p in rows:
        trs += (
            f"<tr><td><code>{_esc(p['code'])}</code></td><td><b>{_esc(p['name'])}</b></td>"
            f"<td>{_esc(p['course'])}</td><td>{_esc(p['subject'])}</td>"
            f"<td class='muted' style='max-width:240px;overflow:hidden;text-overflow:ellipsis'>{_esc(p['description'])}</td>"
            f"<td style='white-space:nowrap'>"
            f"<a class='btn sm' href='/admin/products/edit?code={_esc(p['code'])}'>Tahrirlash</a> "
            f"<form class='inline' method='post' action='/admin/products/delete' "
            f"onsubmit=\"return confirm('O&#39;chirilsinmi?')\">"
            f"<input type='hidden' name='code' value='{_esc(p['code'])}'>"
            f"<button class='btn danger sm'>O'chirish</button></form></td></tr>")
    body = (
        f"{note}<div class='row'><a class='btn solid' href='/admin/products/edit'>➕ Yangi baza</a>"
        f"<span class='muted'>{len(rows)} ta</span></div>"
        "<div class='panel'><div class='scroll'><table><thead><tr><th>Kod</th><th>Nomi</th>"
        "<th>Kurs</th><th>Fan</th><th>Tavsif</th><th>Amal</th></tr></thead><tbody>"
        f"{trs or '<tr><td class=empty colspan=6>Baza yo&#39;q</td></tr>'}</tbody></table></div></div>")
    return web.Response(content_type="text/html",
                        text=_layout("products", "Bazalar", "Qo'shish · tahrirlash · o'chirish", body))


async def _product_edit(request):
    g = _guard(request)
    if g is not None:
        return g
    code = request.query.get("code", "")
    p = await db.product_by_code(code) if code else None
    is_new = p is None
    v = (lambda f: _esc(p[f]) if p else "")
    opts = "".join(f"<option {'selected' if (p and p['course']==c) else ''}>{c}</option>" for c in _COURSES)
    title = "Yangi baza qo'shish" if is_new else f"Tahrirlash: {p['name']}"
    body = (
        "<div class='formcard'><form method='post' action='/admin/products/save'>"
        f"<input type='hidden' name='orig_code' value='{v('code')}'>"
        f"<label class='field'><span>Kod (ID)</span><input name='code' value='{v('code')}' required></label>"
        f"<label class='field'><span>Nomi</span><input name='name' value='{v('name')}' required></label>"
        f"<label class='field'><span>Kurs</span><select name='course'>{opts}</select></label>"
        f"<label class='field'><span>Fan</span><input name='subject' value='{v('subject')}'></label>"
        f"<label class='field'><span>Tavsif</span><textarea name='description' rows='3'>{v('description')}</textarea></label>"
        f"<label class='field'><span>Fayl ID (Telegram file_id)</span>"
        f"<textarea name='file_id' rows='2'>{v('file_id')}</textarea></label>"
        "<div class='row'><button class='btn solid' type='submit'>Saqlash</button>"
        "<a class='btn' href='/admin/products'>Bekor qilish</a></div></form></div>")
    return web.Response(content_type="text/html",
                        text=_layout("products", title, "Baza ma'lumotlari", body))


async def _product_save(request):
    g = _guard(request)
    if g is not None:
        return g
    d = await request.post()
    orig = str(d.get("orig_code", "")).strip()
    code = str(d.get("code", "")).strip()
    name = str(d.get("name", "")).strip()
    course = str(d.get("course", "")).strip()
    subject = str(d.get("subject", "")).strip()
    desc = str(d.get("description", "")).strip()
    fid = str(d.get("file_id", "")).strip()
    if not code:
        return _redir("/admin/products?saved=Kod bo'sh")
    try:
        if orig and await db.product_by_code(orig):
            await db.update_product(orig, code, name, course, subject, desc, fid)
        else:
            await db.add_product(code, name, course, subject, desc, fid)
        return _redir("/admin/products?saved=Saqlandi")
    except Exception:
        return _redir("/admin/products?saved=Xato (kod takrorlangan bo'lishi mumkin)")


async def _product_delete(request):
    g = _guard(request)
    if g is not None:
        return g
    d = await request.post()
    await db.delete_product(str(d.get("code", "")))
    return _redir("/admin/products?saved=O'chirildi")


# ---------------------------------------------------------------- payments

async def _payments(request):
    g = _guard(request)
    if g is not None:
        return g
    st = request.query.get("status", "")
    valid = ("paid", "pending", "created", "cancelled", "failed", "replaced")
    if st in valid:
        rows = await db.pool().fetch(
            "SELECT id,chat_id,base_num,hwid,amount,status,created_at FROM payments WHERE status=$1 ORDER BY id DESC LIMIT 150", st)
    else:
        rows = await db.pool().fetch(
            "SELECT id,chat_id,base_num,hwid,amount,status,created_at FROM payments ORDER BY id DESC LIMIT 150")
    trs = "".join(
        f"<tr><td class='muted'>#{r['id']}</td><td>{r['chat_id']}</td><td>{_esc(r['base_num'])}</td>"
        f"<td><code>{_esc(r['hwid'])}</code></td><td>{_fmt_num(r['amount'])}</td><td>{_status_b(r['status'])}</td>"
        f"<td class='muted'>{_esc(str(r['created_at'])[:16])}</td></tr>" for r in rows)
    filt = "".join(
        f"<a class='{'on' if st == s else ''}' href='/admin/payments?status={s}'>{s or 'hammasi'}</a>"
        for s in ("", "paid", "pending", "created", "cancelled"))
    body = (
        f"<div class='filters'>{filt}</div>"
        "<div class='panel'><div class='scroll'><table><thead><tr><th>ID</th><th>Chat</th>"
        "<th>Baza</th><th>HWID</th><th>Summa</th><th>Holat</th><th>Sana</th></tr></thead><tbody>"
        f"{trs or '<tr><td class=empty colspan=7>To&#39;lov yo&#39;q</td></tr>'}</tbody></table></div></div>")
    return web.Response(content_type="text/html",
                        text=_layout("payments", "To'lovlar", f"{len(rows)} ta ko'rsatildi", body))


async def _referrals(request):
    g = _guard(request)
    if g is not None:
        return g
    rows = await db.referral_leaderboard()
    trs = "".join(
        f"<tr><td class='muted'>{i}</td><td><code>{r['referrer_id']}</code></td><td><b>{r['total']}</b></td></tr>"
        for i, r in enumerate(rows[:100], 1))
    body = (
        "<div class='panel'><div class='scroll'><table><thead><tr><th>#</th><th>Referrer ID</th>"
        "<th>Takliflar</th></tr></thead><tbody>"
        f"{trs or '<tr><td class=empty colspan=3>Referal yo&#39;q</td></tr>'}</tbody></table></div></div>")
    return web.Response(content_type="text/html",
                        text=_layout("refs", "Referallar", "Reyting (Top 100)", body))


# ---------------------------------------------------------------- SOZLAMALAR

async def _settings(request):
    g = _guard(request)
    if g is not None:
        return g
    s = await db.get_settings()
    saved = request.query.get("saved")
    note = f"<div class='badge ok' style='margin-bottom:16px'>✓ {_esc(saved)}</div>" if saved else ""
    price = await db.get_base_price()
    tag = _esc(s.get("global_tag", ""))
    force = s.get("force_sub", False)
    force_b = "ok" if force else "muted"
    force_lbl = "YONIQ" if force else "O'CHIQ"
    toggle_lbl = "O'chirish" if force else "Yoqish"
    channels = s.get("channels", [])
    ch_rows = ""
    for c in channels:
        ch_rows += (f"<tr><td><b>{_esc(c.get('title'))}</b></td><td><code>{_esc(c.get('id'))}</code></td>"
                    f"<td><a class='lk' href='{_esc(c.get('link'))}'>havola</a></td>"
                    f"<td><form class='inline' method='post' action='/admin/settings/channel-del'>"
                    f"<input type='hidden' name='id' value='{_esc(c.get('id'))}'>"
                    f"<button class='btn danger sm'>O'chirish</button></form></td></tr>")
    body = (
        f"{note}"
        "<h2>💰 Baza narxi</h2>"
        "<div class='formcard'><form method='post' action='/admin/settings/price'>"
        "<label class='field'><span>Bitta baza narxi (so'm) — darrov kuchga kiradi</span>"
        f"<input type='number' name='base_price' value='{price}' min='0' required></label>"
        "<button class='btn solid' type='submit'>Saqlash</button></form></div>"
        "<h2>Global tag</h2>"
        "<div class='formcard'><form method='post' action='/admin/settings/tag'>"
        f"<label class='field'><span>Har faylga qo'shiladigan matn</span>"
        f"<textarea name='global_tag' rows='3'>{tag}</textarea></label>"
        "<button class='btn solid' type='submit'>Saqlash</button></form></div>"
        "<h2>Majburiy obuna</h2>"
        f"<div class='row'><span class='badge {force_b}'>{force_lbl}</span>"
        "<form class='inline' method='post' action='/admin/settings/forcesub'>"
        f"<button class='btn sm'>{toggle_lbl}</button></form></div>"
        "<div class='panel'><div class='scroll'><table><thead><tr><th>Kanal</th><th>ID</th>"
        "<th>Havola</th><th>Amal</th></tr></thead><tbody>"
        f"{ch_rows or '<tr><td class=empty colspan=4>Kanal yo&#39;q</td></tr>'}</tbody></table></div></div>"
        "<div class='formcard'><form method='post' action='/admin/settings/channel-add'>"
        "<label class='field'><span>Kanal qo'shish — @username yoki -100... ID (bot kanalda admin bo'lishi kerak)</span>"
        "<input name='channel' placeholder='@kanal yoki -100123...'></label>"
        "<button class='btn solid' type='submit'>Qo'shish</button></form></div>")
    return web.Response(content_type="text/html",
                        text=_layout("settings", "Sozlamalar", "Tag, majburiy obuna, kanallar", body))


async def _set_price(request):
    g = _guard(request)
    if g is not None:
        return g
    d = await request.post()
    try:
        price = max(0, int(d.get("base_price", "0")))
    except (ValueError, TypeError):
        return _redir("/admin/settings?saved=Narx noto'g'ri")
    await db.set_base_price(price)
    return _redir("/admin/settings?saved=Narx saqlandi")


async def _set_tag(request):
    g = _guard(request)
    if g is not None:
        return g
    d = await request.post()
    await db.set_global_tag(str(d.get("global_tag", "")).strip())
    return _redir("/admin/settings?saved=Tag saqlandi")


async def _toggle_forcesub(request):
    g = _guard(request)
    if g is not None:
        return g
    s = await db.get_settings()
    s["force_sub"] = not s.get("force_sub", False)
    await db.save_settings(s)
    return _redir("/admin/settings?saved=O'zgartirildi")


async def _channel_add(request):
    g = _guard(request)
    if g is not None:
        return g
    d = await request.post()
    ref = str(d.get("channel", "")).strip()
    if not ref or _BOT is None:
        return _redir("/admin/settings?saved=Kanal bo'sh")
    try:
        chat = await _BOT.get_chat(ref)
        link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else "")
        s = await db.get_settings()
        s.setdefault("channels", []).append({"id": chat.id, "title": chat.title, "link": link})
        await db.save_settings(s)
        return _redir("/admin/settings?saved=Kanal qo'shildi")
    except Exception:
        return _redir("/admin/settings?saved=Xato (bot kanalda adminmi?)")


async def _channel_del(request):
    g = _guard(request)
    if g is not None:
        return g
    d = await request.post()
    cid = str(d.get("id", ""))
    s = await db.get_settings()
    s["channels"] = [c for c in s.get("channels", []) if str(c.get("id")) != cid]
    await db.save_settings(s)
    return _redir("/admin/settings?saved=Kanal o'chirildi")


def setup_admin_routes(app: web.Application, bot=None) -> None:
    global _BOT
    _BOT = bot
    app.middlewares.append(_prefix_mw)
    r = app.router
    r.add_get("/admin", _dashboard)
    r.add_get("/admin/", _dashboard)
    r.add_get("/admin/users", _users)
    r.add_get("/admin/products", _products)
    r.add_get("/admin/products/edit", _product_edit)
    r.add_post("/admin/products/save", _product_save)
    r.add_post("/admin/products/delete", _product_delete)
    r.add_get("/admin/payments", _payments)
    r.add_get("/admin/referrals", _referrals)
    r.add_get("/admin/stats", _stats)
    r.add_get("/admin/monitor", _monitor)
    r.add_get("/admin/logs", _logs)
    r.add_get("/admin/settings", _settings)
    r.add_post("/admin/settings/price", _set_price)
    r.add_post("/admin/settings/tag", _set_tag)
    r.add_post("/admin/settings/forcesub", _toggle_forcesub)
    r.add_post("/admin/settings/channel-add", _channel_add)
    r.add_post("/admin/settings/channel-del", _channel_del)
