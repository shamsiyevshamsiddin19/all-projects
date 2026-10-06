"""Kino bot web-admin — master (subtitr) domen dropdown'iga mos uslubda.

Kirish: master domen orqali proxy qilinganda `X-Admin-Proxy` sirini tekshiradi
(bitta parol master'da). To'g'ridan-to'g'ri kirishda Basic Auth (WEB_ADMIN_*)."""
from __future__ import annotations

import base64
import binascii
import hmac
import html
import math

from aiohttp import web

import config
import db
from . import theme

_NAV = [
    ("dash", "Dashboard", "/admin", "dash"),
    ("movies", "Kinolar", "/admin/movies", "movie"),
    ("series", "Seriallar", "/admin/series", "series"),
    ("channels", "Majburiy kanallar", "/admin/channels", "channel"),
    ("social", "Ijtimoiy tarmoqlar", "/admin/social", "social"),
    ("broadcast", "Xabar yuborish", "/admin/broadcast", "broadcast"),
    ("settings", "Sozlamalar", "/admin/settings", "settings"),
]


# ---------------------------------------------------------------- auth / prefix
def _prefix(request: web.Request) -> str:
    xf = request.headers.get("X-Forwarded-Prefix", "").rstrip("/")
    if xf:
        return xf
    if request.path.startswith("/kino/"):
        return "/kino"
    return ""


def _link(request: web.Request, path: str) -> str:
    return _prefix(request) + path


def _basic_ok(request: web.Request) -> bool:
    if not config.WEB_ADMIN_PASSWORD:
        return False
    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return False
    try:
        raw = base64.b64decode(header[6:]).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return False
    user, _, pwd = raw.partition(":")
    return hmac.compare_digest(user, config.WEB_ADMIN_USER) and hmac.compare_digest(
        pwd, config.WEB_ADMIN_PASSWORD
    )


def _unauthorized() -> web.Response:
    return web.Response(
        status=401, text="Avtorizatsiya talab qilinadi.",
        headers={"WWW-Authenticate": 'Basic realm="Kino Admin"'},
    )


def _guard(request: web.Request) -> web.Response | None:
    secret = config.WEB_BRIDGE_SECRET
    if secret and hmac.compare_digest(request.headers.get("X-Admin-Proxy", ""), secret):
        return None
    if config.WEB_ADMIN_PASSWORD:
        return None if _basic_ok(request) else _unauthorized()
    if secret:
        # faqat proxy orqali kirish mumkin
        return _unauthorized()
    return web.Response(
        content_type="text/html",
        text=_page(
            "<div style='max-width:560px;margin:60px auto;padding:0 20px'>"
            "<h1 style='font-size:20px'>Kino Admin</h1>"
            "<div class='panel'><div class='empty'>⚠️ Panel yopiq. <b>.env</b> da "
            "<code>WEB_ADMIN_PASSWORD</code> yoki <code>WEB_BRIDGE_SECRET</code> ni "
            "o'rnating.</div></div></div>"
        ),
    )


def _esc(v) -> str:
    return html.escape(str(v)) if v is not None else "—"


# ---------------------------------------------------------------- layout
def _page(body: str) -> str:
    return (
        "<!doctype html><html lang='uz'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Kino Admin</title><style>" + theme._STYLE + "</style></head>"
        "<body>" + body + "</body></html>"
    )


def _sidebar(request: web.Request, active: str) -> str:
    items = ""
    for key, label, href, ic in _NAV:
        cls = " class='active'" if key == active else ""
        items += f"<a href='{_link(request, href)}'{cls}>{theme.icon(ic)}<span>{label}</span></a>"
    return (
        "<aside class='sidebar'>"
        "<div class='brand' style='display:flex;align-items:center;gap:10px'>"
        "<span class='dot'>K</span>"
        + theme.bot_switcher(_prefix(request)) +
        "</div>"
        f"<nav class='nav'>{items}</nav></aside>"
    )


def _layout(request: web.Request, active: str, title: str, body: str) -> web.Response:
    inner = (
        "<input type='checkbox' id='navtoggle' class='navtoggle'>"
        + _sidebar(request, active)
        + "<label for='navtoggle' class='overlay'></label>"
        "<main class='content'>"
        "<div class='topbar'><label for='navtoggle' class='hamburger'>☰</label>"
        f"<span class='ttl'>{title}</span></div>"
        + body
        + "<div class='foot'>🎬 Kino Bot · Admin panel</div>"
        "</main>"
    )
    return web.Response(content_type="text/html", text=_page(f"<div class='layout'>{inner}</div>"))


def _pagehead(title: str, sub: str = "", action: str = "") -> str:
    sub_html = f"<div class='sub'>{sub}</div>" if sub else ""
    return f"<div class='pagehead'><div><h1>{title}</h1>{sub_html}</div>{action}</div>"


def _kpi(label, num, note="") -> str:
    note_html = f"<div class='note' style='margin:3px 0 0'>{note}</div>" if note else ""
    return f"<div class='stat'><div class='label'>{label}</div><div class='num'>{num}</div>{note_html}</div>"


# ================================================================== DASHBOARD
async def dashboard(request):
    if (g := _guard(request)) is not None:
        return g
    users = await db.fetchval("SELECT COUNT(*) FROM users")
    movies = await db.fetchval("SELECT COUNT(*) FROM movies")
    series = await db.fetchval("SELECT COUNT(*) FROM series")
    episodes = await db.fetchval("SELECT COUNT(*) FROM episodes")
    vm = await db.fetchval("SELECT COALESCE(SUM(views),0) FROM movies")
    vs = await db.fetchval("SELECT COALESCE(SUM(views),0) FROM series")
    channels = await db.fetchval("SELECT COUNT(*) FROM channels")

    statbar = (
        "<div class='statbar'>"
        + _kpi("Foydalanuvchilar", f"{users:,}".replace(",", " "))
        + _kpi("Kinolar", movies)
        + _kpi("Seriallar", series)
        + _kpi("Qismlar", episodes)
        + _kpi("Jami ko'rishlar", f"{int(vm)+int(vs):,}".replace(",", " "))
        + _kpi("Majburiy kanallar", channels)
        + "</div>"
    )

    # Kunlik yangi foydalanuvchilar (7 kun)
    rows = await db.fetch(
        """SELECT to_char(d, 'DD.MM') AS day, COALESCE(c,0) AS c FROM
             generate_series(current_date - 6, current_date, interval '1 day') d
             LEFT JOIN (SELECT date(created_at) dt, COUNT(*) c FROM users GROUP BY 1) u
               ON u.dt = d::date
           ORDER BY d"""
    )
    mx = max([int(r["c"]) for r in rows] + [1])
    bars = ""
    for r in rows:
        c = int(r["c"])
        hpix = int(c / mx * 120) if mx else 0
        bars += (
            f"<div class='bar'><div class='val'>{c or ''}</div>"
            f"<div class='barinner'><div class='fill' style='height:{hpix}px'></div></div>"
            f"<div class='lbl'>{r['day']}</div></div>"
        )

    # Top kinolar
    top = await db.fetch("SELECT name, code, views FROM movies ORDER BY views DESC LIMIT 8")
    trows = "".join(
        f"<tr><td>{_esc(t['name'])}</td><td class='muted'>{t['code']}</td>"
        f"<td>{t['views']}</td></tr>" for t in top
    ) or "<tr><td colspan='3' class='muted'>Hali kino yo'q.</td></tr>"

    body = (
        _pagehead("Dashboard", "Umumiy ko'rsatkichlar")
        + statbar
        + "<div class='panel'><h2 style='padding:16px 16px 0'>So'nggi 7 kun — yangi foydalanuvchilar</h2>"
        + f"<div class='chart'>{bars}</div></div>"
        + "<div class='panel'><h2 style='padding:16px 16px 0'>Top kinolar</h2>"
        + f"<div class='scroll'><table><thead><tr><th>Nomi</th><th>Kod</th><th>Ko'rishlar</th></tr></thead>"
        + f"<tbody>{trows}</tbody></table></div></div>"
    )
    return _layout(request, "dash", "Dashboard", body)


# ================================================================== MOVIES
async def movies(request):
    if (g := _guard(request)) is not None:
        return g
    q = request.query.get("q", "").strip()
    page = max(0, int(request.query.get("page", "0") or 0))
    per = 25
    if q:
        total = await db.fetchval("SELECT COUNT(*) FROM movies WHERE name ILIKE $1", f"%{q}%")
        rows = await db.fetch(
            "SELECT id, code, name, group_name, views FROM movies WHERE name ILIKE $1 ORDER BY id DESC OFFSET $2 LIMIT $3",
            f"%{q}%", page * per, per,
        )
    else:
        total = await db.fetchval("SELECT COUNT(*) FROM movies")
        rows = await db.fetch(
            "SELECT id, code, name, group_name, views FROM movies ORDER BY id DESC OFFSET $1 LIMIT $2",
            page * per, per,
        )

    body = _pagehead("Kinolar", f"Jami: {total}")
    body += (
        f"<form class='search' method='get' action='{_link(request, '/admin/movies')}'>"
        f"<input name='q' placeholder='Nomi bo‘yicha qidirish...' value='{_esc(q)}'>"
        "<button>Qidirish</button></form>"
    )
    trs = ""
    for r in rows:
        act = _link(request, "/admin/movies/delete")
        ren = _link(request, "/admin/movies/rename")
        trs += (
            "<tr>"
            f"<td class='muted'>{r['code']}</td>"
            f"<td><form class='inline' method='post' action='{ren}'>"
            f"<input type='hidden' name='id' value='{r['id']}'>"
            f"<input name='name' value='{_esc(r['name'])}' style='min-width:220px'>"
            "<button class='btn'>💾</button></form></td>"
            f"<td class='muted'>{_esc(r['group_name'])}</td>"
            f"<td>{r['views']}</td>"
            f"<td><form class='inline' method='post' action='{act}' onsubmit=\"return confirm('O‘chirilsinmi?')\">"
            f"<input type='hidden' name='id' value='{r['id']}'>"
            "<button class='btn danger'>O‘chirish</button></form></td>"
            "</tr>"
        )
    if not trs:
        trs = "<tr><td colspan='5' class='muted'>Hech narsa topilmadi.</td></tr>"
    body += (
        "<div class='panel'><div class='scroll'><table><thead><tr>"
        "<th>Kod</th><th>Nomi</th><th>Guruh</th><th>Ko'rishlar</th><th></th>"
        f"</tr></thead><tbody>{trs}</tbody></table></div></div>"
    )
    body += _pager(request, "/admin/movies", page, total, per, q)
    return _layout(request, "movies", "Kinolar", body)


async def movies_delete(request):
    if (g := _guard(request)) is not None:
        return g
    data = await request.post()
    await db.execute("DELETE FROM movies WHERE id = $1", int(data["id"]))
    raise web.HTTPFound(_link(request, "/admin/movies"))


async def movies_rename(request):
    if (g := _guard(request)) is not None:
        return g
    data = await request.post()
    await db.execute("UPDATE movies SET name = $1 WHERE id = $2", data["name"].strip(), int(data["id"]))
    raise web.HTTPFound(_link(request, "/admin/movies"))


# ================================================================== SERIES
async def series(request):
    if (g := _guard(request)) is not None:
        return g
    rows = await db.fetch(
        """SELECT s.id, s.code, s.name, s.views,
                  (SELECT COUNT(*) FROM episodes e WHERE e.series_id = s.id) AS eps
           FROM series s ORDER BY s.id DESC"""
    )
    trs = ""
    for r in rows:
        act = _link(request, "/admin/series/delete")
        ren = _link(request, "/admin/series/rename")
        trs += (
            "<tr>"
            f"<td class='muted'>{r['code']}</td>"
            f"<td><form class='inline' method='post' action='{ren}'>"
            f"<input type='hidden' name='id' value='{r['id']}'>"
            f"<input name='name' value='{_esc(r['name'])}' style='min-width:220px'>"
            "<button class='btn'>💾</button></form></td>"
            f"<td>{r['eps']}</td><td>{r['views']}</td>"
            f"<td><form class='inline' method='post' action='{act}' onsubmit=\"return confirm('Serial va barcha qismlari o‘chirilsinmi?')\">"
            f"<input type='hidden' name='id' value='{r['id']}'>"
            "<button class='btn danger'>O‘chirish</button></form></td>"
            "</tr>"
        )
    if not trs:
        trs = "<tr><td colspan='5' class='muted'>Hali serial yo'q.</td></tr>"
    body = (
        _pagehead("Seriallar", f"Jami: {len(rows)}")
        + "<div class='panel'><div class='scroll'><table><thead><tr>"
        "<th>Kod</th><th>Nomi</th><th>Qismlar</th><th>Ko'rishlar</th><th></th>"
        f"</tr></thead><tbody>{trs}</tbody></table></div></div>"
    )
    return _layout(request, "series", "Seriallar", body)


async def series_delete(request):
    if (g := _guard(request)) is not None:
        return g
    data = await request.post()
    await db.execute("DELETE FROM series WHERE id = $1", int(data["id"]))
    raise web.HTTPFound(_link(request, "/admin/series"))


async def series_rename(request):
    if (g := _guard(request)) is not None:
        return g
    data = await request.post()
    await db.execute("UPDATE series SET name = $1 WHERE id = $2", data["name"].strip(), int(data["id"]))
    raise web.HTTPFound(_link(request, "/admin/series"))


# ================================================================== CHANNELS
async def channels(request):
    if (g := _guard(request)) is not None:
        return g
    rows = await db.fetch("SELECT id, channel_id, title, link FROM channels ORDER BY id")
    trs = ""
    for r in rows:
        act = _link(request, "/admin/channels/delete")
        trs += (
            f"<tr><td>{_esc(r['title'])}</td><td class='muted'>{_esc(r['channel_id'])}</td>"
            f"<td><a href='{_esc(r['link'])}' target='_blank'>havola</a></td>"
            f"<td><form class='inline' method='post' action='{act}'>"
            f"<input type='hidden' name='id' value='{r['id']}'>"
            "<button class='btn danger'>O‘chirish</button></form></td></tr>"
        )
    if not trs:
        trs = "<tr><td colspan='4' class='muted'>Majburiy kanal yo'q.</td></tr>"
    add = _link(request, "/admin/channels/add")
    body = (
        _pagehead("Majburiy kanallar", "Obuna talab qilinadigan kanallar")
        + "<div class='panel'><div class='actbar'>"
        f"<form class='inline' method='post' action='{add}'>"
        "<label class='field'>Kanal (@username yoki ID)<input name='channel' placeholder='@mychannel'></label>"
        "<button class='btn solid'>➕ Qo‘shish</button></form></div></div>"
        + "<div class='panel'><div class='scroll'><table><thead><tr>"
        "<th>Nomi</th><th>ID</th><th>Havola</th><th></th>"
        f"</tr></thead><tbody>{trs}</tbody></table></div></div>"
        "<div class='note'>Botni kanalga <b>admin</b> qilishni unutmang.</div>"
    )
    return _layout(request, "channels", "Majburiy kanallar", body)


async def channels_add(request):
    if (g := _guard(request)) is not None:
        return g
    data = await request.post()
    ident = (data.get("channel") or "").strip()
    bot = request.app.get("bot")
    if bot and ident:
        try:
            chat = await bot.get_chat(ident)
            if chat.username:
                link = f"https://t.me/{chat.username}"
            else:
                link = await bot.export_chat_invite_link(chat.id)
            await db.execute(
                "INSERT INTO channels (channel_id, title, link) VALUES ($1,$2,$3)",
                str(chat.id), chat.title, link,
            )
        except Exception:
            pass
    raise web.HTTPFound(_link(request, "/admin/channels"))


async def channels_delete(request):
    if (g := _guard(request)) is not None:
        return g
    data = await request.post()
    await db.execute("DELETE FROM channels WHERE id = $1", int(data["id"]))
    raise web.HTTPFound(_link(request, "/admin/channels"))


# ================================================================== SOCIAL
async def social(request):
    if (g := _guard(request)) is not None:
        return g
    rows = await db.fetch("SELECT id, platform, url FROM social_links ORDER BY id")
    trs = ""
    for r in rows:
        act = _link(request, "/admin/social/delete")
        trs += (
            f"<tr><td>{_esc(r['platform'])}</td>"
            f"<td><a href='{_esc(r['url'])}' target='_blank'>{_esc(r['url'])}</a></td>"
            f"<td><form class='inline' method='post' action='{act}'>"
            f"<input type='hidden' name='id' value='{r['id']}'>"
            "<button class='btn danger'>O‘chirish</button></form></td></tr>"
        )
    if not trs:
        trs = "<tr><td colspan='3' class='muted'>Ijtimoiy havola yo'q.</td></tr>"
    add = _link(request, "/admin/social/add")
    body = (
        _pagehead("Ijtimoiy tarmoqlar", "Obuna oynasida ko'rsatiladi")
        + "<div class='panel'><div class='actbar'>"
        f"<form class='inline' method='post' action='{add}'>"
        "<label class='field'>Havola<input name='url' placeholder='https://instagram.com/...' style='min-width:280px'></label>"
        "<button class='btn solid'>➕ Qo‘shish</button></form></div></div>"
        + "<div class='panel'><div class='scroll'><table><thead><tr>"
        f"<th>Platforma</th><th>URL</th><th></th></tr></thead><tbody>{trs}</tbody></table></div></div>"
    )
    return _layout(request, "social", "Ijtimoiy tarmoqlar", body)


async def social_add(request):
    if (g := _guard(request)) is not None:
        return g
    from handlers.admin import _detect_platform
    data = await request.post()
    url = (data.get("url") or "").strip()
    if url.startswith("http"):
        await db.execute(
            "INSERT INTO social_links (platform, url) VALUES ($1,$2)", _detect_platform(url), url
        )
    raise web.HTTPFound(_link(request, "/admin/social"))


async def social_delete(request):
    if (g := _guard(request)) is not None:
        return g
    data = await request.post()
    await db.execute("DELETE FROM social_links WHERE id = $1", int(data["id"]))
    raise web.HTTPFound(_link(request, "/admin/social"))


# ================================================================== SETTINGS
async def settings(request):
    if (g := _guard(request)) is not None:
        return g
    sig = await db.get_signature()
    fs = await db.get_force_sub()
    save = _link(request, "/admin/settings")
    body = (
        _pagehead("Sozlamalar")
        + "<div class='panel'><div class='actbar'>"
        f"<form method='post' action='{save}' style='display:flex;flex-direction:column;gap:16px;width:100%'>"
        f"<label class='field'>Post manbasi (signature)"
        f"<input name='signature' value='{_esc(sig)}' style='max-width:360px'></label>"
        "<label class='field'>Majburiy obuna"
        "<select name='force_sub' style='max-width:200px'>"
        f"<option value='1'{' selected' if fs else ''}>Yoqilgan</option>"
        f"<option value='0'{' selected' if not fs else ''}>O'chirilgan</option>"
        "</select></label>"
        "<div><button class='btn solid'>💾 Saqlash</button></div>"
        "</form></div></div>"
    )
    return _layout(request, "settings", "Sozlamalar", body)


async def settings_save(request):
    if (g := _guard(request)) is not None:
        return g
    data = await request.post()
    await db.execute(
        "UPDATE settings SET signature = $1, force_sub_status = $2 WHERE id = 1",
        (data.get("signature") or "").strip(),
        1 if data.get("force_sub") == "1" else 0,
    )
    raise web.HTTPFound(_link(request, "/admin/settings"))


# ================================================================== BROADCAST
async def broadcast(request):
    if (g := _guard(request)) is not None:
        return g
    cnt = await db.fetchval("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
    act = _link(request, "/admin/broadcast")
    body = (
        _pagehead("Xabar yuborish", f"Faol foydalanuvchilar: {cnt}")
        + "<div class='panel'><div class='actbar'>"
        f"<form method='post' action='{act}' style='display:flex;flex-direction:column;gap:14px;width:100%'>"
        "<label class='field'>Matn (HTML mumkin)"
        "<textarea name='text' rows='6' style='min-width:100%;max-width:640px' "
        "placeholder='Reklama matni...'></textarea></label>"
        "<div><button class='btn solid' onclick=\"return confirm('Barchaga yuborilsinmi?')\">🚀 Yuborish</button></div>"
        "</form></div></div>"
        "<div class='note'>Rasm/video/albom yuborish uchun Telegram admin panelidagi REKLAMA bo'limidan foydalaning.</div>"
    )
    return _layout(request, "broadcast", "Xabar yuborish", body)


async def broadcast_send(request):
    if (g := _guard(request)) is not None:
        return g
    import asyncio
    data = await request.post()
    text = (data.get("text") or "").strip()
    bot = request.app.get("bot")
    if bot and text:
        async def _run():
            rows = await db.fetch("SELECT chat_id FROM users WHERE is_active = TRUE")
            for r in rows:
                try:
                    await bot.send_message(r["chat_id"], text)
                except Exception:
                    await db.execute("UPDATE users SET is_active = FALSE WHERE chat_id = $1", r["chat_id"])
                await asyncio.sleep(0.05)
        asyncio.create_task(_run())
    raise web.HTTPFound(_link(request, "/admin/broadcast"))


# ---------------------------------------------------------------- pager
def _pager(request, base, page, total, per, q="") -> str:
    pages = max(1, math.ceil(total / per))
    if pages <= 1:
        return ""
    qs = f"&q={html.escape(q)}" if q else ""
    out = "<div class='pager'>"
    for p in range(pages):
        if abs(p - page) > 3 and p not in (0, pages - 1):
            continue
        on = " class='on'" if p == page else ""
        out += f"<a{on} href='{_link(request, base)}?page={p}{qs}'>{p + 1}</a>"
    return out + "</div>"


# ---------------------------------------------------------------- registration
def setup_admin_routes(app: web.Application, bot=None):
    app["bot"] = bot
    routes = [
        ("GET", "/admin", dashboard),
        ("GET", "/admin/", dashboard),
        ("GET", "/admin/movies", movies),
        ("POST", "/admin/movies/delete", movies_delete),
        ("POST", "/admin/movies/rename", movies_rename),
        ("GET", "/admin/series", series),
        ("POST", "/admin/series/delete", series_delete),
        ("POST", "/admin/series/rename", series_rename),
        ("GET", "/admin/channels", channels),
        ("POST", "/admin/channels/add", channels_add),
        ("POST", "/admin/channels/delete", channels_delete),
        ("GET", "/admin/social", social),
        ("POST", "/admin/social/add", social_add),
        ("POST", "/admin/social/delete", social_delete),
        ("GET", "/admin/settings", settings),
        ("POST", "/admin/settings", settings_save),
        ("GET", "/admin/broadcast", broadcast),
        ("POST", "/admin/broadcast", broadcast_send),
    ]
    # Ham to'g'ridan-to'g'ri (/admin...), ham master proxy ostida (/kino/admin...)
    for method, path, handler in routes:
        app.router.add_route(method, path, handler)
        app.router.add_route(method, "/kino" + path, handler)
