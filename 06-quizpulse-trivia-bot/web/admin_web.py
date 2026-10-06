"""Web admin panel — Quiz bot.

Subtitr / Sessiya / Mustaqil / TATU LMS botlari bilan BIR XIL dizayn.
Master (subtitr) panel bu panelni /quiz/ ostida proxy qiladi:
X-Forwarded-Prefix=/quiz va X-Admin-Proxy=<sir> sarlavhalari bilan — bitta
domen, bitta parol. Ichki havolalar prefiks bilan ishlaydi (_PFX).
"""
from __future__ import annotations

import asyncio
import base64
import contextvars
import csv
import hmac
import html
import io
import logging

from aiogram.exceptions import TelegramForbiddenError
from aiohttp import web

import db
from config import settings
from parser import parse_quiz

log = logging.getLogger("quizadmin")

# Broadcast uchun bot havolasi (setup_admin_routes orqali beriladi)
_BOT = None

# Master panel bu panelni /quiz/ ostida proxy qiladi.
_PFX: contextvars.ContextVar[str] = contextvars.ContextVar("admin_pfx", default="")

PAGE_SIZE = 50


@web.middleware
async def _prefix_mw(request: web.Request, handler):
    _PFX.set((request.headers.get("X-Forwarded-Prefix", "") or "").rstrip("/"))
    return await handler(request)


def _redir(path: str) -> web.HTTPFound:
    return web.HTTPFound(_PFX.get() + path)


NAV = [
    ("dash", "Dashboard", "/admin", "dash"),
    ("quizzes", "Testlar", "/admin/quizzes", "box"),
    ("cats", "Kategoriyalar", "/admin/categories", "folder"),
    ("results", "Natijalar", "/admin/results", "pay"),
    ("top", "Reyting", "/admin/top", "stats"),
    ("users", "Foydalanuvchilar", "/admin/users", "users"),
    ("broadcast", "Xabar yuborish", "/admin/broadcast", "send"),
    ("settings", "Sozlamalar", "/admin/settings", "settings"),
]


def _esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def _fmt_num(v) -> str:
    return f"{int(v or 0):,}".replace(",", " ")


def _fmt_dt(dt) -> str:
    try:
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return _esc(dt)


def _limit_warnings(questions: list[dict]) -> str:
    long_q = sum(1 for q in questions if len(q["text"]) > 300)
    long_o = sum(1 for q in questions for o in q["options"] if len(str(o)) > 100)
    if not long_q and not long_o:
        return ""
    parts = []
    if long_q:
        parts.append(f"{long_q} ta savol matni")
    if long_o:
        parts.append(f"{long_o} ta variant")
    return f"<div class='note'>⚠️ {' va '.join(parts)} juda uzun — Telegram'da qisqartirilib ko'rsatiladi.</div>"


# ─── pagination / search ───

def _page_params(request: web.Request) -> tuple[int, str]:
    try:
        page = max(1, int(request.query.get("page", "1")))
    except ValueError:
        page = 1
    q = (request.query.get("q") or "").strip()
    return page, q


def _pager(base_path: str, page: int, total: int, q: str = "") -> str:
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    if pages <= 1:
        return ""
    qs = f"&q={_esc(q)}" if q else ""
    prev = (f"<a class='btn sm' href='{base_path}?page={page-1}{qs}'>← Oldingi</a>"
            if page > 1 else "<span class='btn sm' style='opacity:.4'>← Oldingi</span>")
    nxt = (f"<a class='btn sm' href='{base_path}?page={page+1}{qs}'>Keyingi →</a>"
           if page < pages else "<span class='btn sm' style='opacity:.4'>Keyingi →</span>")
    return (f"<div class='row' style='justify-content:space-between;margin-top:14px'>"
            f"{prev}<span class='muted' style='font-size:13px'>{page}/{pages}-sahifa · "
            f"jami {_fmt_num(total)} ta</span>{nxt}</div>")


def _search_box(base_path: str, q: str, placeholder: str = "Qidirish...") -> str:
    clear = f"<a class='btn' href='{base_path}'>✕</a>" if q else ""
    return (f"<form class='search' method='get' action='{base_path}'>"
            f"<input name='q' value='{_esc(q)}' placeholder='{_esc(placeholder)}'>"
            f"<button class='btn'>🔍 Qidirish</button>{clear}</form>")


# ─── auth ───

def _guard(request: web.Request):
    """Master proxydan (X-Admin-Proxy siri) kelsa — parolsiz. Aks holda Basic Auth."""
    secret = settings.QUIZ_BRIDGE_SECRET
    if secret and hmac.compare_digest(request.headers.get("X-Admin-Proxy", ""), secret):
        return None
    if not settings.ADMIN_PASSWORD:
        return None
    hdr = request.headers.get("Authorization", "")
    if hdr.startswith("Basic "):
        try:
            user, _, pw = base64.b64decode(hdr[6:]).decode().partition(":")
            if hmac.compare_digest(user, settings.ADMIN_USER) and hmac.compare_digest(
                pw, settings.ADMIN_PASSWORD
            ):
                return None
        except Exception:
            pass
    return web.Response(
        status=401, text="Auth required",
        headers={"WWW-Authenticate": 'Basic realm="Quiz Admin"'},
    )


# ─── icons ───

def _icon(name: str) -> str:
    paths = {
        "dash": "<rect x='3' y='3' width='7' height='7' rx='1'/><rect x='14' y='3' width='7' height='7' rx='1'/><rect x='3' y='14' width='7' height='7' rx='1'/><rect x='14' y='14' width='7' height='7' rx='1'/>",
        "users": "<path d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M22 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/>",
        "box": "<path d='M21 8v8a2 2 0 0 1-1 1.73l-7 4a2 2 0 0 1-2 0l-7-4A2 2 0 0 1 3 16V8a2 2 0 0 1 1-1.73l7-4a2 2 0 0 1 2 0l7 4A2 2 0 0 1 21 8z'/><polyline points='3.27 6.96 12 12.01 20.73 6.96'/><line x1='12' y1='22' x2='12' y2='12'/>",
        "pay": "<rect x='2' y='5' width='20' height='14' rx='2'/><path d='M2 10h20'/>",
        "settings": "<circle cx='12' cy='12' r='3'/><path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z'/>",
        "stats": "<line x1='18' y1='20' x2='18' y2='10'/><line x1='12' y1='20' x2='12' y2='4'/><line x1='6' y1='20' x2='6' y2='14'/>",
        "send": "<line x1='22' y1='2' x2='11' y2='13'/><polygon points='22 2 15 22 11 13 2 9 22 2'/>",
        "folder": "<path d='M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z'/>",
    }
    return ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' "
            "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
            + paths.get(name, "") + "</svg>")


# ─── style (subtitr/sessiya/mustaqil bilan bir xil) ───

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
.progress{height:10px;border-radius:6px;background:var(--subtle);overflow:hidden;margin:10px 0}
.progress > div{height:100%;background:var(--ok);transition:width .3s}
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


# ─── dropdown (bot tanlagich — Quiz bot qo'shilgan) ───

def _dropdown(p: str) -> str:
    if p:
        subtitr_url = "/admin"
    else:
        subtitr_url = settings.SUBTITR_ADMIN_URL
    quiz_url = f"{p}/admin" if p else "/admin"
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
    doc = _sv.format("<path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/>"
                     "<polyline points='14 2 14 8 20 8'/>"
                     "<line x1='16' y1='13' x2='8' y2='13'/>"
                     "<line x1='16' y1='17' x2='8' y2='17'/>")
    cart = _sv.format("<circle cx='9' cy='21' r='1'/><circle cx='20' cy='21' r='1'/>"
                      "<path d='M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6'/>")
    chart = _sv.format("<line x1='12' y1='20' x2='12' y2='10'/>"
                       "<line x1='18' y1='20' x2='18' y2='4'/>"
                       "<line x1='6' y1='20' x2='6' y2='16'/>")
    video = _sv.format("<polygon points='23 7 16 12 23 17 23 7'/>"
                       "<rect x='1' y='5' width='15' height='14' rx='2' ry='2'/>")
    bots = [(subtitr_url, film, "Subtitr bot", False),
            ("/sessiya/admin", book, "Sessiya bot", False),
            ("/mustaqil/admin", pencil, "Mustaqil bot", False),
            ("/tatulms/admin", cap, "TATU LMS bot", False),
            (quiz_url, quiz, "Quiz bot", True),
            ("/wstore/admin", cart, "wstore market", False),
            ("/portfolio/admin", chart, "Portfolio", False),
            ("/kino/admin", video, "Kino bot", False),
            ("/docs/admin", doc, "Document bot", False)]
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


def _layout(active: str, title: str, sub: str, body: str, extra_head: str = "") -> str:
    p = _PFX.get()
    nav = "".join(
        f"<a class='{'active' if k == active else ''}' href='{p}{u}'>{_icon(ic)}<span>{_esc(l)}</span></a>"
        for k, l, u, ic in NAV)
    if p:
        body = body.replace("'/admin", "'" + p + "/admin")
    sub_h = f"<div class='sub'>{_esc(sub)}</div>" if sub else ""
    return f"""<!doctype html><html lang='uz'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
{extra_head}
<title>{_esc(title)} · Quiz Admin</title><style>{_STYLE}</style></head><body>
<div class='layout'>
<input type='checkbox' id='navtoggle' class='navtoggle'>
<aside class='sidebar'>
  <div class='brand'><span class='dot'>Q</span>{_dropdown(p)}</div>
  <nav class='nav'>{nav}</nav>
</aside>
<label for='navtoggle' class='overlay'></label>
<main class='content'>
  <div class='topbar'><label for='navtoggle' class='hamburger'>☰</label><span class='ttl'>{_esc(title)}</span></div>
  <div class='pagehead'><div><h1>{_esc(title)}</h1>{sub_h}</div></div>
  {body}
  <div class='foot'>Quiz Bot · Admin panel</div>
</main></div>{_LABEL_SCRIPT}</body></html>"""


def _kpi(label: str, num, note: str = "") -> str:
    note_h = f"<div class='note' style='margin:3px 0 0'>{note}</div>" if note else ""
    return (f"<div class='stat'><div class='label'>{label}</div>"
            f"<div class='num'>{num}</div>{note_h}</div>")


def _bar_chart(pairs, w=520, h=160, pad=26):
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
        parts.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{bwid:.1f}' height='{bh:.1f}' rx='3' fill='#0d0d0d'/>")
        parts.append(f"<text x='{x+bwid/2:.1f}' y='{y-5:.1f}' font-size='11' text-anchor='middle' fill='#6e6e80'>{val}</text>")
        parts.append(f"<text x='{x+bwid/2:.1f}' y='{h-7:.1f}' font-size='10' text-anchor='middle' fill='#6e6e80'>{_esc(label)}</text>")
    return (f"<svg viewBox='0 0 {w} {h}' width='100%' style='max-width:{w}px;height:auto'>"
            + "".join(parts) + "</svg>")


def _pct_badge(correct: int, total: int) -> str:
    if not total:
        return "<span class='badge muted'>hali javob yo'q</span>"
    pct = round(correct / total * 100)
    cls = "ok" if pct >= 70 else ("warn" if pct >= 40 else "bad")
    return f"<span class='badge {cls}'>{pct}% ({correct}/{total})</span>"


# ====================================================================== PAGES

async def _dashboard(request: web.Request):
    g = _guard(request)
    if g:
        return g
    pool = db.pool()
    n_quiz = await pool.fetchval("SELECT COUNT(*) FROM quizzes") or 0
    n_q = await pool.fetchval("SELECT COUNT(*) FROM questions") or 0
    n_users = await pool.fetchval("SELECT COUNT(*) FROM users") or 0
    n_att = await pool.fetchval("SELECT COUNT(*) FROM attempts") or 0
    avg = await pool.fetchval(
        "SELECT AVG(score::float/NULLIF(total,0)) FROM attempts WHERE total>0") or 0

    stat = (
        "<div class='statbar'>"
        + _kpi("Testlar", _fmt_num(n_quiz))
        + _kpi("Savollar", _fmt_num(n_q))
        + _kpi("Foydalanuvchilar", _fmt_num(n_users))
        + _kpi("Urinishlar", _fmt_num(n_att))
        + _kpi("O'rtacha ball", f"{round(avg*100)}%")
        + "</div>"
    )

    # kunlik urinishlar grafigi
    try:
        rows = await pool.fetch(
            "SELECT date_trunc('day', created_at) d, COUNT(*) c FROM attempts "
            "GROUP BY d ORDER BY d DESC LIMIT 14")
        pairs = [(r["d"].strftime("%d.%m"), r["c"]) for r in reversed(rows)]
        chart = ("<div class='panel' style='padding:16px'><h2>Urinishlar (kunlik)</h2>"
                 + _bar_chart(pairs) + "</div>")
    except Exception:
        chart = ""

    # so'nggi urinishlar
    rows = await pool.fetch(
        "SELECT username, user_id, quiz_name, score, total, created_at "
        "FROM attempts ORDER BY created_at DESC LIMIT 10")
    if rows:
        body_rows = ""
        for r in rows:
            pct = round(r["score"] / r["total"] * 100) if r["total"] else 0
            name = r["username"] and f"@{_esc(r['username'])}" or f"<span class='muted'>ID {r['user_id']}</span>"
            body_rows += (
                f"<tr><td>{name}</td><td>{_esc(r['quiz_name'])}</td>"
                f"<td>{r['score']}/{r['total']} ({pct}%)</td>"
                f"<td class='muted'>{_fmt_dt(r['created_at'])}</td></tr>")
        recent = (
            "<h2>So'nggi urinishlar</h2><div class='panel'><div class='scroll'><table>"
            "<thead><tr><th>Foydalanuvchi</th><th>Test</th><th>Natija</th><th>Vaqt</th></tr></thead>"
            f"<tbody>{body_rows}</tbody></table></div></div>")
    else:
        recent = "<div class='panel'><div class='empty'>Hali urinishlar yo'q.</div></div>"

    return web.Response(
        text=_layout("dash", "Dashboard", "Umumiy ko'rsatkichlar", stat + chart + recent),
        content_type="text/html")


async def _quizzes(request: web.Request):
    g = _guard(request)
    if g:
        return g
    page, q = _page_params(request)
    offset = (page - 1) * PAGE_SIZE
    total = await db.count_quizzes(active_only=False, search=q)
    quizzes = await db.list_quizzes(active_only=False, search=q, limit=PAGE_SIZE, offset=offset)

    newbtn = "<div class='row'><a class='btn solid' href='/admin/quizzes/new'>➕ Yangi test</a></div>"
    search = _search_box("/admin/quizzes", q, "Test nomi bo'yicha qidirish...")

    if not quizzes:
        empty_msg = "Hech narsa topilmadi." if q else "Hali test yo'q. Botga fayl/matn yuboring yoki bu yerdan qo'shing."
        body = newbtn + search + f"<div class='panel'><div class='empty'>{empty_msg}</div></div>"
        return web.Response(text=_layout("quizzes", "Testlar", "", body), content_type="text/html")

    ctx = f"?page={page}" + (f"&q={_esc(q)}" if q else "")
    rows = ""
    for quiz in quizzes:
        badge = ("<span class='badge ok'>faol</span>" if quiz["is_active"]
                 else "<span class='badge muted'>o'chiq</span>")
        toggle_label = "O'chirish" if quiz["is_active"] else "Yoqish"
        toggle_cls = "danger" if quiz["is_active"] else "ok"
        rows += (
            f"<tr><td class='muted'>#{quiz['id']}</td>"
            f"<td><a class='lk' href='/admin/quizzes/{quiz['id']}'>{_esc(quiz['name'])}</a></td>"
            f"<td>{quiz['q_count']}</td><td>{badge}</td>"
            f"<td class='muted'>{_fmt_dt(quiz['created_at'])}</td>"
            "<td>"
            f"<a class='btn sm' href='/admin/quizzes/{quiz['id']}'>✏️</a> "
            f"<form class='inline' method='post' action='/admin/quizzes/{quiz['id']}/toggle{ctx}'>"
            f"<button class='btn sm {toggle_cls}'>{toggle_label}</button></form> "
            f"<form class='inline' method='post' action='/admin/quizzes/{quiz['id']}/delete{ctx}' "
            "onsubmit='return confirm(\"Test va savollari o`chiriladi (ballar tarixi saqlanadi). Davom etilsinmi?\")'>"
            "<button class='btn sm danger'>🗑</button></form>"
            "</td></tr>")
    body = (newbtn + search + "<div class='panel'><div class='scroll'><table>"
            "<thead><tr><th>ID</th><th>Nomi</th><th>Savollar</th><th>Holat</th>"
            "<th>Sana</th><th>Amal</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div></div>"
            + _pager("/admin/quizzes", page, total, q))
    return web.Response(text=_layout("quizzes", "Testlar", f"Jami: {_fmt_num(total)} ta",
                                     body), content_type="text/html")


def _new_form(name: str, text: str) -> str:
    return (
        "<form class='formcard' method='post' action='/admin/quizzes/new'>"
        f"<label class='field'><span>Test nomi (ixtiyoriy)</span>"
        f"<input name='name' value='{_esc(name)}' placeholder='Masalan: Tarix testi'></label>"
        "<label class='field'><span>Savollar (matn — 2 formatdan biri)</span>"
        f"<textarea name='text' rows='10' placeholder='# Savol matni&#10;+ To&#39;g&#39;ri&#10;- Xato&#10;Izoh: tushuntirish'>{_esc(text)}</textarea></label>"
        "<button class='btn solid'>Yaratish</button></form>")


async def _quiz_new(request: web.Request):
    g = _guard(request)
    if g:
        return g
    if request.method == "POST":
        data = await request.post()
        name = (data.get("name") or "").strip()
        text = data.get("text") or ""
        questions = [q for q in parse_quiz(text) if len(q["options"]) >= 2]
        if not questions:
            body = ("<div class='note'>❌ Savol topilmadi. Formatni tekshiring.</div>"
                    + _new_form(name, text))
            return web.Response(text=_layout("quizzes", "Yangi test", "", body),
                                content_type="text/html")
        if not name:
            name = (questions[0]["text"][:40].strip() or "Yangi test")
        qid = await db.create_quiz(name, 0, questions)
        return _redir(f"/admin/quizzes/{qid}")
    return web.Response(
        text=_layout("quizzes", "Yangi test", "Matn joylab test yarating", _new_form("", "")),
        content_type="text/html")


async def _quiz_detail(request: web.Request):
    g = _guard(request)
    if g:
        return g
    qid = int(request.match_info["id"])
    quiz = await db.get_quiz(qid)
    if not quiz:
        return _redir("/admin/quizzes")
    questions = await db.get_questions(qid)
    q_stats = await db.question_stats(qid)
    stats_by_id = {r["id"]: r for r in q_stats}
    attempt_stats = await db.quiz_attempt_stats(qid)
    link = f"https://t.me/{_esc(settings.BOT_USERNAME)}?start=test_{qid}"

    back = "<div class='row'><a class='btn' href='/admin/quizzes'>← Orqaga</a></div>"
    share = f"<div class='note'>🔗 Ulashish havolasi: <code>{link}</code></div>"

    avg_pct = attempt_stats.get("avg_pct")
    kpi_row = (
        "<div class='statbar'>"
        + _kpi("Savollar", len(questions))
        + _kpi("Urinishlar", _fmt_num(attempt_stats.get("attempts") or 0))
        + _kpi("O'rtacha natija", f"{round(avg_pct*100)}%" if avg_pct is not None else "—")
        + "</div>"
    )

    # eng qiyin savollar — javob berilganlar orasida eng past aniqlik
    answered = [r for r in q_stats if r["total"]]
    hardest = sorted(answered, key=lambda r: r["correct"] / r["total"])[:3]
    hardest_html = ""
    if hardest:
        items = "".join(
            f"<div style='display:flex;justify-content:space-between;gap:10px;padding:6px 0;"
            f"border-bottom:1px solid var(--border)'>"
            f"<span>{_esc(r['text'][:70])}</span>{_pct_badge(r['correct'], r['total'])}</div>"
            for r in hardest)
        hardest_html = (
            "<div class='panel' style='padding:14px 16px'>"
            "<h2 style='margin-top:0'>🎯 Eng qiyin savollar</h2>" + items + "</div>")

    cats = await db.list_categories()
    cur_cat = quiz.get("category_id")
    cur_diff = quiz.get("difficulty") or ""
    cat_opts = "<option value=''>— Kategoriyasiz —</option>"
    for c in cats:
        s = " selected" if c["id"] == cur_cat else ""
        cat_opts += f"<option value='{c['id']}'{s}>{_esc(c['emoji'])} {_esc(c['name'])}</option>"
    diff_opts = ""
    for val, label in (("", "Avtomatik (aniqlikdan)"), ("easy", "🟢 Oson"),
                       ("medium", "🟡 O'rta"), ("hard", "🔴 Qiyin")):
        s = " selected" if val == cur_diff else ""
        diff_opts += f"<option value='{val}'{s}>{label}</option>"

    rename = (
        f"<form class='formcard' method='post' action='/admin/quizzes/{qid}/rename'>"
        f"<label class='field'><span>Test nomi</span>"
        f"<input name='name' value='{_esc(quiz['name'])}'></label>"
        f"<label class='field'><span>Tavsif (ixtiyoriy)</span>"
        f"<input name='description' value='{_esc(quiz.get('description') or '')}' "
        "placeholder='Qisqacha izoh (botda ko`rinadi)'></label>"
        f"<label class='field'><span>Kategoriya</span>"
        f"<select name='category_id'>{cat_opts}</select></label>"
        f"<label class='field'><span>Qiyinlik</span>"
        f"<select name='difficulty'>{diff_opts}</select></label>"
        "<button class='btn solid'>Saqlash</button></form>")

    blocks = ""
    for i, q in enumerate(questions, 1):
        opts = ""
        for j, o in enumerate(q["options"]):
            mark = " ✅" if j == q["correct"] else ""
            cls = " style='color:var(--ok);font-weight:600'" if j == q["correct"] else ""
            opts += f"<div{cls}>{chr(65+j)}) {_esc(o)}{mark}</div>"
        expl = (f"<div class='muted' style='font-size:13px;margin-top:6px'>💡 {_esc(q['explanation'])}</div>"
                if q.get("explanation") else "")
        st = stats_by_id.get(q["id"], {"correct": 0, "total": 0})
        blocks += (
            "<div class='panel' style='padding:14px 16px'>"
            "<div style='display:flex;justify-content:space-between;gap:10px;align-items:flex-start'>"
            f"<div style='font-weight:600'>{i}. {_esc(q['text'])}</div>"
            "<div style='white-space:nowrap'>"
            f"<a class='btn sm' href='/admin/questions/{q['id']}/edit'>✏️</a> "
            f"<form class='inline' method='post' action='/admin/questions/{q['id']}/delete' "
            "onsubmit='return confirm(\"O`chirilsinmi?\")'><button class='btn sm danger'>🗑</button></form>"
            "</div></div>"
            f"<div style='display:grid;gap:3px;font-size:14px;margin-top:8px'>{opts}</div>{expl}"
            f"<div style='margin-top:8px'>{_pct_badge(st['correct'], st['total'])}</div></div>")

    addf = (
        f"<form class='formcard' method='post' action='/admin/quizzes/{qid}/add'>"
        "<label class='field'><span>Savol qo'shish (matn)</span>"
        "<textarea name='text' rows='6' placeholder='# Yangi savol?&#10;+ To&#39;g&#39;ri&#10;- Xato'></textarea></label>"
        "<button class='btn solid'>Qo'shish</button></form>")

    body = (back + share + kpi_row + hardest_html + rename
            + f"<h2>Savollar ({len(questions)})</h2>" + blocks + addf)
    return web.Response(text=_layout("quizzes", _esc(quiz["name"]),
                                     f"{len(questions)} ta savol", body),
                        content_type="text/html")


async def _quiz_rename(request: web.Request):
    g = _guard(request)
    if g:
        return g
    qid = int(request.match_info["id"])
    data = await request.post()
    name = (data.get("name") or "").strip()
    if name:
        await db.rename_quiz(qid, name[:200])
    # tavsif
    desc = (data.get("description") or "").strip()
    await db.pool().execute("UPDATE quizzes SET description=$2 WHERE id=$1",
                            qid, desc[:500] or None)
    # kategoriya
    cat_raw = (data.get("category_id") or "").strip()
    cat_id = int(cat_raw) if cat_raw.isdigit() else None
    await db.set_quiz_category(qid, cat_id)
    # qiyinlik
    diff = (data.get("difficulty") or "").strip()
    await db.set_quiz_difficulty(qid, diff if diff in ("easy", "medium", "hard") else None)
    return _redir(f"/admin/quizzes/{qid}")


async def _quiz_add(request: web.Request):
    g = _guard(request)
    if g:
        return g
    qid = int(request.match_info["id"])
    data = await request.post()
    text = data.get("text") or ""
    questions = [q for q in parse_quiz(text) if len(q["options"]) >= 2]
    if questions:
        await db.add_questions(qid, questions)
    return _redir(f"/admin/quizzes/{qid}")


async def _question_edit(request: web.Request):
    g = _guard(request)
    if g:
        return g
    qid = int(request.match_info["qid"])
    q = await db.get_question(qid)
    if not q:
        return _redir("/admin/quizzes")
    if request.method == "POST":
        data = await request.post()
        text = (data.get("text") or "").strip()
        opts = [ln.strip() for ln in (data.get("options") or "").splitlines() if ln.strip()]
        try:
            correct = int(data.get("correct") or 1) - 1
        except ValueError:
            correct = 0
        correct = max(0, min(correct, len(opts) - 1)) if opts else 0
        expl = (data.get("explanation") or "").strip()
        if text and len(opts) >= 2:
            await db.update_question(qid, text, opts, correct, expl)
        return _redir(f"/admin/quizzes/{q['quiz_id']}")
    opts_txt = "\n".join(q["options"])
    body = (
        f"<div class='row'><a class='btn' href='/admin/quizzes/{q['quiz_id']}'>← Orqaga</a></div>"
        "<form class='formcard' method='post' action='/admin/questions/" + str(qid) + "/edit'>"
        f"<label class='field'><span>Savol matni</span><input name='text' value='{_esc(q['text'])}'></label>"
        f"<label class='field'><span>Variantlar (har qatorda bittadan)</span>"
        f"<textarea name='options' rows='5'>{_esc(opts_txt)}</textarea></label>"
        f"<label class='field'><span>To'g'ri variant raqami (1 dan boshlab)</span>"
        f"<input name='correct' type='number' min='1' value='{q['correct']+1}'></label>"
        f"<label class='field'><span>Izoh (ixtiyoriy)</span>"
        f"<input name='explanation' value='{_esc(q.get('explanation') or '')}'></label>"
        "<button class='btn solid'>Saqlash</button></form>")
    return web.Response(text=_layout("quizzes", "Savolni tahrirlash", "", body),
                        content_type="text/html")


async def _question_delete(request: web.Request):
    g = _guard(request)
    if g:
        return g
    qid = int(request.match_info["qid"])
    q = await db.get_question(qid)
    await db.delete_question(qid)
    return _redir(f"/admin/quizzes/{q['quiz_id']}" if q else "/admin/quizzes")


async def _quiz_toggle(request: web.Request):
    g = _guard(request)
    if g:
        return g
    qid = int(request.match_info["id"])
    quiz = await db.get_quiz(qid)
    if quiz:
        await db.set_quiz_active(qid, not quiz["is_active"])
    return _redir("/admin/quizzes" + ("?" + request.query_string if request.query_string else ""))


async def _quiz_delete(request: web.Request):
    g = _guard(request)
    if g:
        return g
    await db.delete_quiz(int(request.match_info["id"]))
    return _redir("/admin/quizzes" + ("?" + request.query_string if request.query_string else ""))


async def _results(request: web.Request):
    g = _guard(request)
    if g:
        return g
    page, q = _page_params(request)
    offset = (page - 1) * PAGE_SIZE
    total = await db.count_results(search=q)
    rows = await db.list_results(search=q, limit=PAGE_SIZE, offset=offset)

    search = _search_box("/admin/results", q, "Test yoki foydalanuvchi bo'yicha...")
    expbtn = "<div class='row'><a class='btn solid' href='/admin/results/export.csv'>⬇️ Excel (CSV) eksport</a></div>"

    if not rows:
        empty_msg = "Hech narsa topilmadi." if q else "Hali natija yo'q."
        body = expbtn + search + f"<div class='panel'><div class='empty'>{empty_msg}</div></div>"
        return web.Response(text=_layout("results", "Natijalar", "", body), content_type="text/html")

    mode_lbl = {"practice": "🎓 Mashq", "exam": "📝 Imtihon", "group": "👥 Guruh"}
    body_rows = ""
    for r in rows:
        pct = round(r["score"] / r["total"] * 100) if r["total"] else 0
        cls = "ok" if pct >= 70 else ("warn" if pct >= 50 else "bad")
        name = r["username"] and f"@{_esc(r['username'])}" or f"<span class='muted'>ID {r['user_id']}</span>"
        mode = mode_lbl.get(r.get("mode"), "<span class='muted'>—</span>")
        body_rows += (
            f"<tr><td>{name}</td><td>{_esc(r['quiz_name'])}</td>"
            f"<td>{r['score']}/{r['total']}</td>"
            f"<td><span class='badge {cls}'>{pct}%</span></td>"
            f"<td>{mode}</td>"
            f"<td class='muted'>{_fmt_dt(r['created_at'])}</td></tr>")
    body = (expbtn + search + "<div class='panel'><div class='scroll'><table>"
            "<thead><tr><th>Foydalanuvchi</th><th>Test</th><th>Ball</th><th>Foiz</th>"
            "<th>Rejim</th><th>Vaqt</th></tr></thead>"
            f"<tbody>{body_rows}</tbody></table></div></div>"
            + _pager("/admin/results", page, total, q))
    return web.Response(text=_layout("results", "Natijalar", f"Jami: {_fmt_num(total)} ta",
                                     body), content_type="text/html")


async def _results_export(request: web.Request):
    g = _guard(request)
    if g:
        return g
    rows = await db.pool().fetch(
        "SELECT username, user_id, quiz_name, score, total, mode, duration_sec, created_at "
        "FROM attempts ORDER BY created_at DESC")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Foydalanuvchi", "User ID", "Test", "Ball", "Jami", "Foiz",
                "Rejim", "Davomiylik(s)", "Vaqt"])
    for r in rows:
        pct = round(r["score"] / r["total"] * 100) if r["total"] else 0
        w.writerow([r["username"] or "", r["user_id"], r["quiz_name"],
                    r["score"], r["total"], pct, r["mode"] or "",
                    r["duration_sec"] or "", _fmt_dt(r["created_at"])])
    data = ("﻿" + buf.getvalue()).encode("utf-8")  # BOM — Excel UTF-8 uchun
    return web.Response(body=data, headers={
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": "attachment; filename=natijalar.csv",
    })


# ─── broadcast (fon vazifasi + progress) ───

_broadcast_state = {"running": False, "sent": 0, "failed": 0, "blocked": 0, "total": 0, "done": False}


async def _run_broadcast(text: str) -> None:
    st = _broadcast_state
    uids = await db.all_user_ids()
    st.update(running=True, sent=0, failed=0, blocked=0, total=len(uids), done=False)
    for uid in uids:
        try:
            await _BOT.send_message(uid, text)
            st["sent"] += 1
        except TelegramForbiddenError:
            await db.mark_blocked(uid)
            st["blocked"] += 1
        except Exception:
            log.exception("Broadcast xato (uid=%s)", uid)
            st["failed"] += 1
        await asyncio.sleep(0.05)
    st["running"] = False
    st["done"] = True


async def _broadcast(request: web.Request):
    g = _guard(request)
    if g:
        return g
    st = _broadcast_state
    warn = ""
    if request.method == "POST" and not st["running"]:
        data = await request.post()
        text = (data.get("text") or "").strip()
        if not text:
            warn = "<div class='note'>Matn bo'sh.</div>"
        elif _BOT is None:
            warn = "<div class='note'>Bot ulanmagan.</div>"
        else:
            asyncio.create_task(_run_broadcast(text))
            return _redir("/admin/broadcast")

    if st["running"]:
        pct = round(st["sent"] / st["total"] * 100) if st["total"] else 0
        msg = (
            f"<div class='panel' style='padding:16px'>"
            f"<div style='font-weight:600;margin-bottom:6px'>📤 Yuborilmoqda...</div>"
            f"<div class='progress'><div style='width:{pct}%'></div></div>"
            f"<div class='muted' style='font-size:13px'>{st['sent']}/{st['total']} yuborildi "
            f"· {st['blocked']} bloklagan · {st['failed']} xato</div></div>")
        head = "<meta http-equiv='refresh' content='2'>"
        return web.Response(
            text=_layout("broadcast", "Xabar yuborish", "Fon jarayonda", msg, extra_head=head),
            content_type="text/html")

    if st["done"] and not warn:
        warn = (f"<div class='note'>✅ Yakunlandi: <b>{st['sent']}</b> yuborildi · "
               f"{st['blocked']} bot bloklagan · {st['failed']} boshqa xato</div>")

    form = (
        "<form class='formcard' method='post' action='/admin/broadcast' "
        "onsubmit='return confirm(\"Barcha foydalanuvchilarga yuborilsinmi?\")'>"
        "<label class='field'><span>Xabar matni (HTML mumkin)</span>"
        "<textarea name='text' rows='6' placeholder='Assalomu alaykum! ...'></textarea></label>"
        "<button class='btn solid'>📤 Hammaga yuborish</button></form>")
    return web.Response(text=_layout("broadcast", "Xabar yuborish",
                                     "Barcha foydalanuvchilarga", warn + form),
                        content_type="text/html")


async def _top(request: web.Request):
    g = _guard(request)
    if g:
        return g
    rows = await db.leaderboard(limit=30)
    if not rows:
        body = "<div class='panel'><div class='empty'>Hali reyting yo'q.</div></div>"
        return web.Response(text=_layout("top", "Reyting", "", body), content_type="text/html")
    medals = ["🥇", "🥈", "🥉"]
    body_rows = ""
    for i, r in enumerate(rows):
        m = medals[i] if i < 3 else str(i + 1)
        name = r["username"] and f"@{_esc(r['username'])}" or f"<span class='muted'>ID {r['user_id']}</span>"
        pct = round((r["best"] or 0) * 100)
        body_rows += (f"<tr><td>{m}</td><td>{name}</td>"
                      f"<td><span class='badge ok'>{pct}%</span></td>"
                      f"<td class='muted'>{r['tries']}</td></tr>")
    body = ("<div class='panel'><div class='scroll'><table>"
            "<thead><tr><th>#</th><th>Foydalanuvchi</th><th>O'rtacha</th><th>Urinish</th></tr></thead>"
            f"<tbody>{body_rows}</tbody></table></div></div>")
    return web.Response(text=_layout("top", "Reyting", "O'rtacha natija bo'yicha",
                                     body), content_type="text/html")


async def _users(request: web.Request):
    g = _guard(request)
    if g:
        return g
    page, q = _page_params(request)
    offset = (page - 1) * PAGE_SIZE
    total = await db.count_users(search=q)
    rows = await db.list_users(search=q, limit=PAGE_SIZE, offset=offset)

    search = _search_box("/admin/users", q, "Ism yoki username bo'yicha...")
    if not rows:
        empty_msg = "Hech narsa topilmadi." if q else "Hali foydalanuvchi yo'q."
        body = search + f"<div class='panel'><div class='empty'>{empty_msg}</div></div>"
        return web.Response(text=_layout("users", "Foydalanuvchilar", "", body), content_type="text/html")
    body_rows = ""
    for r in rows:
        uname = f"@{_esc(r['username'])}" if r["username"] else "<span class='muted'>—</span>"
        blocked = " <span class='badge muted'>bloklagan</span>" if r["is_blocked"] else ""
        body_rows += (
            f"<tr><td class='muted'>{r['id']}</td>"
            f"<td>{_esc(r['first_name'])}{blocked}</td><td>{uname}</td>"
            f"<td>{r['attempts']}</td>"
            f"<td class='muted'>{_fmt_dt(r['created_at'])}</td></tr>")
    body = (search + "<div class='panel'><div class='scroll'><table>"
            "<thead><tr><th>ID</th><th>Ism</th><th>Username</th><th>Urinish</th><th>Sana</th></tr></thead>"
            f"<tbody>{body_rows}</tbody></table></div></div>"
            + _pager("/admin/users", page, total, q))
    return web.Response(text=_layout("users", "Foydalanuvchilar", f"Jami: {_fmt_num(total)}",
                                     body), content_type="text/html")


async def _settings(request: web.Request):
    g = _guard(request)
    if g:
        return g
    shuffle = await db.get_setting("shuffle", "1" if settings.DEFAULT_SHUFFLE else "0")
    timer = await db.get_setting("timer", str(settings.DEFAULT_QUESTION_TIME))
    user_create = await db.get_setting("user_create", "0")
    sel = lambda v, x: " selected" if v == x else ""
    body = f"""
    <form class='formcard' method='post' action='/admin/settings'>
      <label class='field'><span>Savol va variantlarni aralashtirish</span>
        <select name='shuffle'>
          <option value='1'{sel(shuffle,'1')}>Yoqilgan</option>
          <option value='0'{sel(shuffle,'0')}>O'chirilgan</option>
        </select></label>
      <label class='field'><span>Imtihon rejimida har savolga vaqt (sekund, 0 = default 30; 5–600)</span>
        <input type='number' name='timer' value='{_esc(timer)}' min='0' max='600'></label>
      <label class='field'><span>Oddiy foydalanuvchilar ham test yarata olsinmi?</span>
        <select name='user_create'>
          <option value='0'{sel(user_create,'0')}>Yo'q (faqat adminlar)</option>
          <option value='1'{sel(user_create,'1')}>Ha, ruxsat</option>
        </select></label>
      <button class='btn solid'>Saqlash</button>
    </form>
    <div class='note'>Bu sozlamalar yangi boshlanadigan testlarga ta'sir qiladi. Mashq rejimi
      har doim vaqtsiz. Guruhda vaqt 0 bo'lsa, avtomatik 20 sekund qo'llaniladi.</div>
    <div class='panel' style='padding:16px'>
      <h2 style='margin-top:0'>Bot</h2>
      <div class='muted' style='font-size:14px'>Username: @{_esc(settings.BOT_USERNAME)}</div>
    </div>"""
    return web.Response(text=_layout("settings", "Sozlamalar", "", body), content_type="text/html")


async def _settings_save(request: web.Request):
    g = _guard(request)
    if g:
        return g
    data = await request.post()
    shuffle = "1" if data.get("shuffle") == "1" else "0"
    try:
        timer = int(data.get("timer", "0"))
    except ValueError:
        timer = 0
    timer = 0 if timer <= 0 else max(5, min(600, timer))
    user_create = "1" if data.get("user_create") == "1" else "0"
    await db.set_setting("shuffle", shuffle)
    await db.set_setting("timer", str(timer))
    await db.set_setting("user_create", user_create)
    return _redir("/admin/settings")


# ─── kategoriyalar ───

async def _categories(request: web.Request):
    g = _guard(request)
    if g:
        return g
    cats = await db.list_categories()
    unc = await db.uncategorized_count(active_only=False)

    form = (
        "<form class='formcard' method='post' action='/admin/categories/new'>"
        "<div class='row' style='margin-bottom:0'>"
        "<label class='field' style='flex:0 0 90px;margin:0'><span>Emoji</span>"
        "<input name='emoji' value='📁' maxlength='4'></label>"
        "<label class='field' style='flex:1;margin:0'><span>Nomi</span>"
        "<input name='name' placeholder='Masalan: Tarix' required></label>"
        "<label class='field' style='flex:0 0 100px;margin:0'><span>Tartib</span>"
        "<input name='position' type='number' value='0'></label>"
        "</div><button class='btn solid' style='margin-top:12px'>➕ Qo'shish</button></form>")

    if not cats:
        body = form + "<div class='panel'><div class='empty'>Hali kategoriya yo'q.</div></div>"
        return web.Response(text=_layout("cats", "Kategoriyalar",
                                         f"Kategoriyasiz testlar: {unc}", body),
                            content_type="text/html")
    rows = ""
    for c in cats:
        rows += (
            "<tr>"
            f"<td>{_esc(c['emoji'])}</td>"
            f"<td><b>{_esc(c['name'])}</b></td>"
            f"<td>{c['q_count']}</td>"
            f"<td class='muted'>{c['position']}</td>"
            "<td>"
            "<form class='inline' method='post' action='/admin/categories/"
            f"{c['id']}/edit'>"
            f"<input name='emoji' value='{_esc(c['emoji'])}' maxlength='4' "
            "style='width:52px;padding:4px 6px;border:1px solid var(--border);border-radius:6px'> "
            f"<input name='name' value='{_esc(c['name'])}' "
            "style='width:130px;padding:4px 6px;border:1px solid var(--border);border-radius:6px'> "
            f"<input name='position' type='number' value='{c['position']}' "
            "style='width:56px;padding:4px 6px;border:1px solid var(--border);border-radius:6px'> "
            "<button class='btn sm'>💾</button></form> "
            f"<form class='inline' method='post' action='/admin/categories/{c['id']}/delete' "
            "onsubmit='return confirm(\"O`chirilsinmi? Testlar kategoriyasiz qoladi.\")'>"
            "<button class='btn sm danger'>🗑</button></form>"
            "</td></tr>")
    body = (form + "<div class='panel'><div class='scroll'><table>"
            "<thead><tr><th>Emoji</th><th>Nomi</th><th>Testlar</th><th>Tartib</th><th>Amal</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div></div>"
            f"<div class='note'>Kategoriyasiz testlar: {unc} ta. Testni kategoriyaga biriktirish — "
            "test sahifasida.</div>")
    return web.Response(text=_layout("cats", "Kategoriyalar", f"Jami: {len(cats)} ta", body),
                        content_type="text/html")


async def _category_new(request: web.Request):
    g = _guard(request)
    if g:
        return g
    data = await request.post()
    name = (data.get("name") or "").strip()
    emoji = (data.get("emoji") or "📁").strip() or "📁"
    try:
        pos = int(data.get("position") or 0)
    except ValueError:
        pos = 0
    if name:
        await db.create_category(name[:60], emoji[:8], pos)
    return _redir("/admin/categories")


async def _category_edit(request: web.Request):
    g = _guard(request)
    if g:
        return g
    cid = int(request.match_info["id"])
    data = await request.post()
    name = (data.get("name") or "").strip()
    emoji = (data.get("emoji") or "📁").strip() or "📁"
    try:
        pos = int(data.get("position") or 0)
    except ValueError:
        pos = 0
    if name:
        await db.update_category(cid, name[:60], emoji[:8], pos)
    return _redir("/admin/categories")


async def _category_delete(request: web.Request):
    g = _guard(request)
    if g:
        return g
    await db.delete_category(int(request.match_info["id"]))
    return _redir("/admin/categories")


# ====================================================================== SETUP

def setup_admin_routes(app: web.Application, bot=None) -> None:
    global _BOT
    _BOT = bot
    app.middlewares.append(_prefix_mw)
    r = app.router
    r.add_get("/admin", _dashboard)
    r.add_get("/admin/", _dashboard)
    r.add_get("/admin/quizzes", _quizzes)
    # "new" — {id} dan OLDIN (aks holda id='new' bo'lib qoladi)
    r.add_get("/admin/quizzes/new", _quiz_new)
    r.add_post("/admin/quizzes/new", _quiz_new)
    r.add_get("/admin/quizzes/{id}", _quiz_detail)
    r.add_post("/admin/quizzes/{id}/toggle", _quiz_toggle)
    r.add_post("/admin/quizzes/{id}/delete", _quiz_delete)
    r.add_post("/admin/quizzes/{id}/rename", _quiz_rename)
    r.add_post("/admin/quizzes/{id}/add", _quiz_add)
    r.add_get("/admin/questions/{qid}/edit", _question_edit)
    r.add_post("/admin/questions/{qid}/edit", _question_edit)
    r.add_post("/admin/questions/{qid}/delete", _question_delete)
    r.add_get("/admin/categories", _categories)
    r.add_post("/admin/categories/new", _category_new)
    r.add_post("/admin/categories/{id}/edit", _category_edit)
    r.add_post("/admin/categories/{id}/delete", _category_delete)
    r.add_get("/admin/results", _results)
    r.add_get("/admin/results/export.csv", _results_export)
    r.add_get("/admin/top", _top)
    r.add_get("/admin/users", _users)
    r.add_get("/admin/broadcast", _broadcast)
    r.add_post("/admin/broadcast", _broadcast)
    r.add_get("/admin/settings", _settings)
    r.add_post("/admin/settings", _settings_save)
