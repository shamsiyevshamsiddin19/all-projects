import base64
import hmac
import html
import secrets
import time
import asyncio
import datetime as dt
from aiohttp import web
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from core.config import ADMIN_USER, ADMIN_PASSWORD
from core.database import db

_TASHKENT_OFFSET = dt.timedelta(hours=5)

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
  color:#fff;display:inline-flex;align-items:center;justify-content:center;
  font-size:13px}
.nav a{display:flex;align-items:center;gap:11px;padding:9px 11px;border-radius:8px;
  color:var(--muted);text-decoration:none;font-size:14px;margin-bottom:2px}
.nav a:hover{background:var(--subtle);color:var(--text)}
.nav a.active{background:var(--subtle);color:var(--text);font-weight:500}
.nav svg{width:18px;height:18px;flex:0 0 18px}
.content{margin-left:230px;flex:1;padding:26px 28px 64px;min-width:0;width:100%}
.topbar{display:none}
.overlay{display:none}
.hamburger{display:none}
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
.panel .inner{padding:16px}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px;min-width:520px}
th,td{text-align:left;padding:11px 16px;border-bottom:1px solid var(--border);
  white-space:nowrap}
th{color:var(--muted);font-weight:500;font-size:12px;text-transform:uppercase;
  letter-spacing:.04em}
tr:last-child td{border-bottom:none}
td.muted,.muted{color:var(--muted)}
.badge{display:inline-block;font-size:12px;padding:2px 9px;border-radius:20px;
  border:1px solid var(--border);white-space:nowrap}
.badge.ok{color:var(--ok);border-color:#bde9da}
.badge.bad{color:var(--bad);border-color:#f5c2c2}
.badge.warn{color:var(--warn);border-color:#f0d6a8}
.badge.muted{color:var(--muted)}
.badge.accentbadge{color:#fff;background:var(--accent);border-color:var(--accent)}
.empty{padding:22px 16px;color:var(--muted);font-size:14px}
.field{display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--muted)}
.field select,.field input,.field textarea{padding:8px 10px;border:1px solid var(--border);
  border-radius:8px;font-size:14px;background:var(--bg);color:var(--text);min-width:120px;font-family:inherit}
.field textarea{min-width:100%;resize:vertical}
form.inline{display:flex;gap:8px;align-items:flex-end;margin:0}
form.stack{display:flex;flex-direction:column;gap:12px;margin:0}
button.btn{cursor:pointer;font:inherit}
.btn.solid{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn.danger{color:var(--bad);border-color:#f5c2c2;background:var(--bg)}
.btn.ok{color:var(--ok);border-color:#bde9da;background:var(--bg)}
.foot{color:var(--muted);font-size:12px;text-align:center;margin-top:8px}
@media(max-width:820px){
  .sidebar{transform:translateX(-100%)}
  #navtoggle:checked ~ .sidebar{transform:translateX(0)}
  #navtoggle:checked ~ .overlay{display:block;position:fixed;inset:0;
    background:rgba(0,0,0,.35);z-index:25}
  .content{margin-left:0;padding:0 16px 56px}
  .topbar{display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:20;
    margin:0 -16px 18px;padding:13px 16px;background:var(--bg);
    border-bottom:1px solid var(--border)}
  .topbar .ttl{font-weight:600;font-size:16px}
  .hamburger{display:inline-flex;align-items:center;justify-content:center;
    width:38px;height:38px;border:1px solid var(--border);border-radius:9px;
    cursor:pointer;color:var(--text);font-size:18px;background:var(--bg)}
  .content{padding-top:16px}
  .statbar{display:flex;overflow:hidden}
  .stat{flex:1 1 0;min-width:0;padding:8px 4px;text-align:center}
  .stat .label{font-size:8.5px;line-height:1.15;white-space:normal;
    overflow-wrap:anywhere;margin-bottom:2px}
  .stat .num{font-size:15px}
  .stat .note{font-size:8px;white-space:normal;line-height:1.15}
  .scroll{overflow-x:visible}
  thead{display:none}
  table{display:block;min-width:0;font-size:13.5px}
  tbody{display:block}
  tbody tr{display:block;padding:4px 0;border-bottom:1px solid var(--border)}
  tbody tr:last-child{border-bottom:none}
  td{display:flex;justify-content:space-between;align-items:center;gap:14px;
    padding:7px 16px;border:none;white-space:normal;text-align:right;
    word-break:break-word}
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

def _icon(name: str) -> str:
    paths = {
        "dash": "<rect x='3' y='3' width='7' height='7' rx='1'/><rect x='14' y='3' width='7' height='7' rx='1'/><rect x='3' y='14' width='7' height='7' rx='1'/><rect x='14' y='14' width='7' height='7' rx='1'/>",
        "users": "<path d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M22 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/>",
        "settings": "<circle cx='12' cy='12' r='3'/><path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z'/>",
        "broadcast": "<path d='M4 11v2a1 1 0 0 0 1 1h1l4 4V6l-4 4H5a1 1 0 0 0-1 1z'/><path d='M15.5 8.5a5 5 0 0 1 0 7'/><path d='M18.5 5.5a9 9 0 0 1 0 13'/>",
    }
    return (
        "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' "
        "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
        + paths.get(name, "") + "</svg>"
    )

_NAV = [
    ("dash", "Dashboard", "/docs/admin", "dash"),
    ("users", "Foydalanuvchilar", "/docs/admin/users", "users"),
    ("broadcast", "Xabar yuborish", "/docs/admin/broadcast", "broadcast"),
    ("settings", "Sozlamalar", "/docs/admin/settings", "settings"),
]

# --- Basic-auth rate limiting (in-memory, per-process) ---
_MAX_FAILURES = 5
_FAILURE_WINDOW = 300  # seconds
_failed_logins: dict[str, list[float]] = {}

def _client_ip(request: web.Request) -> str:
    return request.remote or "unknown"

def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    attempts = [t for t in _failed_logins.get(ip, []) if now - t < _FAILURE_WINDOW]
    _failed_logins[ip] = attempts
    return len(attempts) >= _MAX_FAILURES

def _record_failure(ip: str):
    _failed_logins.setdefault(ip, []).append(time.time())

def _authorized(request: web.Request) -> bool:
    if not ADMIN_PASSWORD:
        return False
    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return False
    try:
        raw = base64.b64decode(header[6:]).decode("utf-8")
    except Exception:
        return False
    user, _, pwd = raw.partition(":")
    return hmac.compare_digest(user, ADMIN_USER) and hmac.compare_digest(pwd, ADMIN_PASSWORD)

def _unauthorized() -> web.Response:
    return web.Response(
        status=401,
        text="Avtorizatsiya talab qilinadi.",
        headers={"WWW-Authenticate": 'Basic realm="Document Convertor Admin"'},
    )

def _too_many_requests() -> web.Response:
    return web.Response(status=429, text="Juda ko'p noto'g'ri urinish. Birozdan keyin qayta urinib ko'ring.")

# --- CSRF (double-submit cookie) ---
_CSRF_COOKIE = "csrf_token"

def _get_or_issue_csrf(request: web.Request) -> tuple[str, bool]:
    token = request.cookies.get(_CSRF_COOKIE)
    if token:
        return token, False
    return secrets.token_hex(16), True

def _check_csrf(request: web.Request, form_token: str) -> bool:
    cookie_token = request.cookies.get(_CSRF_COOKIE)
    if not cookie_token or not form_token:
        return False
    return hmac.compare_digest(cookie_token, form_token)

def _page_raw(body: str) -> str:
    return (
        "<!doctype html><html lang='uz'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Document Convertor Admin</title><style>" + _STYLE + "</style></head>"
        "<body>" + body + _LABEL_SCRIPT + "</body></html>"
    )


def _bot_dropdown(active_label: str) -> str:
    _sv = ("<svg viewBox='0 0 24 24' width='18' height='18' fill='none' stroke='currentColor' "
           "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>{}</svg>")

    film = _sv.format("<rect x='2' y='4' width='20' height='16' rx='2'/><path d='M2 9h20M2 15h20M7 4v16M17 4v16'/>")
    book = _sv.format("<path d='M4 19.5A2.5 2.5 0 0 1 6.5 17H20'/><path d='M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z'/>")
    pencil = _sv.format("<path d='M12 20h9'/><path d='M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z'/>")
    cap = _sv.format("<path d='M22 10 12 5 2 10l10 5 10-5Z'/><path d='M6 12v5c0 1 2.7 2.5 6 2.5s6-1.5 6-2.5v-5'/>")
    quiz = _sv.format("<circle cx='12' cy='12' r='10'/><path d='M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3'/><line x1='12' y1='17' x2='12.01' y2='17'/>")
    cart = _sv.format("<circle cx='9' cy='21' r='1'/><circle cx='20' cy='21' r='1'/><path d='M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6'/>")
    chart = _sv.format("<line x1='12' y1='20' x2='12' y2='10'/><line x1='18' y1='20' x2='18' y2='4'/><line x1='6' y1='20' x2='6' y2='16'/>")
    video = _sv.format("<polygon points='23 7 16 12 23 17 23 7'/><rect x='1' y='5' width='15' height='14' rx='2' ry='2'/>")
    doc = _sv.format("<path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><polyline points='14 2 14 8 20 8'/><line x1='16' y1='13' x2='8' y2='13'/><line x1='16' y1='17' x2='8' y2='17'/>")

    bots = [
        ("/admin", film, "Subtitr bot"),
        ("/sessiya/admin", book, "Sessiya bot"),
        ("/mustaqil/admin", pencil, "Mustaqil bot"),
        ("/tatulms/admin", cap, "TATU LMS bot"),
        ("/quiz/admin", quiz, "Quiz bot"),
        ("/wstore/admin", cart, "wstore market"),
        ("/portfolio/admin", chart, "Portfolio"),
        ("/kino/admin", video, "Kino bot"),
        ("/docs/admin", doc, "Document bot")
    ]

    opts = ""
    cur_svg = film
    for url, svg, label in bots:
        is_act = (label == active_label)
        if is_act:
            cur_svg = svg
        a_cls = " active" if is_act else ""
        opts += f"<a class='botopt{a_cls}' href='{url}'>{svg}<span>{label}</span></a>"

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
        f"<details class='botdd'><summary class='botcur'>{cur_svg}"
        f"<span class='botnm'>{active_label}</span>{chev}</summary>"
        f"<div class='botmenu'>{opts}</div></details>"
        "<script>document.addEventListener('click',function(e){"
        "document.querySelectorAll('details.botdd[open]').forEach(function(d){"
        "if(!d.contains(e.target))d.removeAttribute('open');});});</script>"
    )

def _sidebar(active: str) -> str:
    items = ""
    for key, label, href, icon in _NAV:
        cls = " class='active'" if key == active else ""
        items += f"<a href='{href}'{cls}>{_icon(icon)}<span>{label}</span></a>"
    return (
        "<aside class='sidebar'>"
        "<div class='brand' style='display:flex;align-items:center;gap:10px'>"
        "<span class='dot'>D</span>"
        "" + _bot_dropdown('Document bot') + "</div>"
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
        + "<div class='foot'>Document Convertor · Admin panel</div>"
        "</main>"
    )
    return _page_raw(f"<div class='layout'>{inner}</div>")

def _setup_needed_page() -> str:
    return _page_raw(
        "<div style='max-width:560px;margin:60px auto;padding:0 20px'>"
        "<h1 style='font-size:20px'>Document Convertor Admin</h1>"
        "<div class='panel'><div class='empty'>"
        "⚠️ Admin panel yopiq. <b>.env</b> faylida <code>ADMIN_PASSWORD</code> "
        "ni o'rnating va botni qayta ishga tushiring.</div></div></div>"
    )

def _guard(request: web.Request) -> web.Response | None:
    if not ADMIN_PASSWORD:
        return web.Response(content_type="text/html", text=_setup_needed_page())
    ip = _client_ip(request)
    if _is_rate_limited(ip):
        return _too_many_requests()
    if not _authorized(request):
        _record_failure(ip)
        return _unauthorized()
    return None

def _respond(text: str, csrf_new: bool, csrf_token: str) -> web.Response:
    resp = web.Response(content_type="text/html", text=text)
    if csrf_new:
        resp.set_cookie(_CSRF_COOKIE, csrf_token, httponly=True, samesite="Strict")
    return resp

def _pagehead(title: str, sub: str = "", action: str = "") -> str:
    sub_html = f"<div class='sub'>{sub}</div>" if sub else ""
    return f"<div class='pagehead'><div><h1>{title}</h1>{sub_html}</div>{action}</div>"

def _kpi(label: str, num: str, note: str = "") -> str:
    note_html = f"<div class='note'>{note}</div>" if note else ""
    return f"<div class='stat'><div class='label'>{label}</div><div class='num'>{num}</div>{note_html}</div>"

def _fmt_dt(value: dt.datetime | None) -> str:
    return (value + _TASHKENT_OFFSET).strftime("%d.%m %H:%M") if value else "—"

def _esc(value) -> str:
    return html.escape(str(value)) if value is not None else "—"

async def dash_page(request: web.Request):
    g = _guard(request)
    if g: return g

    stats = await db.get_stats()
    total = stats.get('total', 0)
    today = stats.get('today', 0)

    async with db.pool.acquire() as conn:
        channels_count = await conn.fetchval("SELECT COUNT(*) FROM channels")

    stat = (
        "<div class='statbar'>"
        + _kpi("Foydalanuvchilar", str(total))
        + _kpi("Bugun qo'shilganlar", str(today))
        + _kpi("Kanallar", str(channels_count))
        + "</div>"
    )

    async with db.pool.acquire() as conn:
        recent_users = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC LIMIT 10")

    rows = ""
    for r in recent_users:
        name = _esc(r['full_name']) or "—"
        uname = f"@{r['username']}" if r.get('username') else f"ID: {r['chat_id']}"
        date = _fmt_dt(r['created_at'])
        rows += f"<tr><td>{name}</td><td>{uname}</td><td>{date}</td></tr>"

    table = (
        "<div class='panel'><h2 style='padding:16px 16px 0'>So'nggi foydalanuvchilar</h2><div class='scroll'>"
        "<table><thead><tr><th>Ism</th><th>Username/ID</th><th>Qo'shilgan sana</th></tr></thead>"
        f"<tbody>{rows or '<tr><td colspan=\"3\" class=\"empty\">Foydalanuvchilar yoq</td></tr>'}</tbody></table>"
        "</div></div>"
    )

    csrf_token, csrf_new = _get_or_issue_csrf(request)
    return _respond(
        _layout("dash", "Dashboard", _pagehead("Dashboard", "Umumiy statistika") + stat + table),
        csrf_new, csrf_token,
    )

async def users_page(request: web.Request):
    g = _guard(request)
    if g: return g

    async with db.pool.acquire() as conn:
        all_users = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC LIMIT 100")

    rows = ""
    for r in all_users:
        name = _esc(r['full_name']) or "—"
        uname = f"@{r['username']}" if r.get('username') else f"ID: {r['chat_id']}"
        date = _fmt_dt(r['created_at'])
        mode = _esc(r.get('mode') or 'Oddiy')
        rows += f"<tr><td>{name}</td><td>{uname}</td><td>{mode}</td><td>{date}</td></tr>"

    table = (
        "<div class='panel'><div class='scroll'>"
        "<table><thead><tr><th>Ism</th><th>Username/ID</th><th>Rejim</th><th>Qo'shilgan sana</th></tr></thead>"
        f"<tbody>{rows or '<tr><td colspan=\"4\" class=\"empty\">Foydalanuvchilar yoq</td></tr>'}</tbody></table>"
        "</div></div>"
    )

    csrf_token, csrf_new = _get_or_issue_csrf(request)
    return _respond(
        _layout("users", "Foydalanuvchilar", _pagehead("Foydalanuvchilar", "Oxirgi 100 ta foydalanuvchi") + table),
        csrf_new, csrf_token,
    )

async def settings_page(request: web.Request):
    g = _guard(request)
    if g: return g

    notice = ""
    if request.method == "POST":
        data = await request.post()
        if not _check_csrf(request, data.get("csrf", "")):
            return web.Response(status=403, text="CSRF token noto'g'ri. Sahifani qayta yuklang.")
        if "add_channel" in data and data["add_channel"].strip():
            await db.add_channel(data["add_channel"].strip())
        elif "del_channel" in data:
            await db.delete_channel(int(data["del_channel"]))
        elif "toggle_sub" in data:
            current = await db.get_setting('subscription_active')
            new_val = '0' if current == '1' else '1'
            await db.set_setting('subscription_active', new_val)
        raise web.HTTPFound("/docs/admin/settings")

    csrf_token, csrf_new = _get_or_issue_csrf(request)

    sub_active = (await db.get_setting('subscription_active')) == '1'
    sub_badge = "<span class='badge ok'>YONIQ</span>" if sub_active else "<span class='badge muted'>O'CHIQ</span>"
    toggle_label = "O'chirish" if sub_active else "Yoqish"

    channels = await db.get_channels()
    rows = ""
    for ch in channels:
        rows += (
            f"<tr><td>{_esc(ch['channel_id'])}</td><td style='text-align:right'>"
            f"<form method='POST' class='inline'>"
            f"<input type='hidden' name='csrf' value='{csrf_token}'>"
            f"<input type='hidden' name='del_channel' value='{ch['id']}'>"
            f"<button class='btn danger'>O'chirish</button></form></td></tr>"
        )

    table = (
        "<div class='panel'><div class='scroll'>"
        "<table><thead><tr><th>Kanal ID / Username</th><th>Amal</th></tr></thead>"
        f"<tbody>{rows or '<tr><td colspan=\"2\" class=\"empty\">Kanallar yoq</td></tr>'}</tbody></table>"
        "</div></div>"
    )

    add_form = (
        f"<form method='POST' class='inline' style='margin-bottom:16px;'>"
        f"<input type='hidden' name='csrf' value='{csrf_token}'>"
        "<div class='field'><input type='text' name='add_channel' placeholder='-100... yoki @kanal' required></div>"
        "<button type='submit' class='btn solid'>Kanal qo'shish</button></form>"
    )

    sub_panel = (
        "<div class='panel'><div class='inner' style='display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap'>"
        f"<div><h2 style='margin-bottom:4px'>Majburiy obuna holati</h2>{sub_badge}</div>"
        f"<form method='POST'><input type='hidden' name='csrf' value='{csrf_token}'>"
        f"<input type='hidden' name='toggle_sub' value='1'>"
        f"<button class='btn {'danger' if sub_active else 'ok'}'>{toggle_label}</button></form>"
        "</div></div>"
    )

    return _respond(
        _layout("settings", "Sozlamalar", _pagehead("Majburiy Obuna", "Kanallarni boshqarish") + sub_panel + add_form + table),
        csrf_new, csrf_token,
    )

async def broadcast_page(request: web.Request):
    g = _guard(request)
    if g: return g

    result_html = ""
    if request.method == "POST":
        data = await request.post()
        if not _check_csrf(request, data.get("csrf", "")):
            return web.Response(status=403, text="CSRF token noto'g'ri. Sahifani qayta yuklang.")
        text = (data.get("text") or "").strip()
        if text:
            bot = request.app["bot"]
            chat_ids = await db.get_all_chat_ids()
            sent, failed = 0, 0
            for chat_id in chat_ids:
                while True:
                    try:
                        await bot.send_message(chat_id, text)
                        sent += 1
                        break
                    except TelegramRetryAfter as e:
                        await asyncio.sleep(e.retry_after)
                    except TelegramForbiddenError:
                        failed += 1
                        break
                    except Exception:
                        failed += 1
                        break
                await asyncio.sleep(0.05)
            result_html = (
                f"<div class='panel'><div class='inner'>"
                f"Yuborildi: <b>{sent}</b> ta, Xato: <b>{failed}</b> ta (jami {len(chat_ids)})"
                f"</div></div>"
            )

    csrf_token, csrf_new = _get_or_issue_csrf(request)
    form = (
        f"<form method='POST' class='panel stack' style='padding:16px'>"
        f"<input type='hidden' name='csrf' value='{csrf_token}'>"
        "<div class='field'><label>Xabar matni</label>"
        "<textarea name='text' rows='6' placeholder='Barcha foydalanuvchilarga yuboriladigan xabar...' required></textarea></div>"
        "<div><button type='submit' class='btn solid'>Yuborish</button></div>"
        "</form>"
    )

    return _respond(
        _layout("broadcast", "Xabar yuborish", _pagehead("Xabar yuborish", "Barcha foydalanuvchilarga tarqatma xabar") + result_html + form),
        csrf_new, csrf_token,
    )

def setup_admin_app(bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/docs/admin", dash_page)
    app.router.add_get("/docs/admin/users", users_page)
    app.router.add_get("/docs/admin/broadcast", broadcast_page)
    app.router.add_post("/docs/admin/broadcast", broadcast_page)
    app.router.add_get("/docs/admin/settings", settings_page)
    app.router.add_post("/docs/admin/settings", settings_page)
    return app
