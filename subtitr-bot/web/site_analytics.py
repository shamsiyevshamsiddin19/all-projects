"""Portfolio (shamsiyev.uz) tashrif analitikasi.

Statik sayt (Cloudflare Pages) yengil beacon yuboradi -> shu modul qabul
qilib PostgreSQL (subtitr_db) ga yozadi. Admin panel boshqa panellar bilan
bir xil (chap sidebar) ko'rinishda: Umumiy dashboard + Mehmonlar (kim kirgani
aniq: shahar, ISP, tashriflar soni).

Marshrutlar mavjud admin app (aiohttp, 8080) ga qo'shiladi. Additive.
"""
from __future__ import annotations

import html
import logging
import time
from collections import deque

import web.admin as A  # mavjud panelning qolipi/uslubi (fully loaded)
from aiohttp import web
from sqlalchemy import text

from db.base import async_session

logger = logging.getLogger(__name__)

_ALLOW_ORIGINS = {"https://shamsiyev.uz", "https://www.shamsiyev.uz"}
_HITS: dict[str, deque] = {}
_RL_WINDOW = 60
_RL_MAX = 40


_DDL = [
    """CREATE TABLE IF NOT EXISTS site_visits (
        id BIGSERIAL PRIMARY KEY,
        ts TIMESTAMPTZ NOT NULL DEFAULT now(),
        visitor TEXT, path TEXT, referrer TEXT, country TEXT, ip TEXT,
        ua TEXT, browser TEXT, os TEXT, device TEXT, lang TEXT, screen TEXT, tz TEXT
    )""",
    "ALTER TABLE site_visits ADD COLUMN IF NOT EXISTS city TEXT",
    "ALTER TABLE site_visits ADD COLUMN IF NOT EXISTS region TEXT",
    "ALTER TABLE site_visits ADD COLUMN IF NOT EXISTS org TEXT",
    "CREATE INDEX IF NOT EXISTS idx_site_visits_ts ON site_visits (ts DESC)",
    "CREATE INDEX IF NOT EXISTS idx_site_visits_visitor ON site_visits (visitor)",
]


async def ensure_table(app: web.Application) -> None:
    try:
        async with async_session() as s:
            for stmt in _DDL:
                await s.execute(text(stmt))
            await s.commit()
        logger.info("site_visits jadvali tayyor")
    except Exception:
        logger.exception("site_visits jadvalini yaratib bo'lmadi")


# ----------------------------------------------------------------- helpers

def esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def _hdr(request, *names) -> str:
    for n in names:
        v = request.headers.get(n)
        if v:
            return v.split(",")[0].strip()
    return ""


def _client_ip(request) -> str:
    ip = _hdr(request, "X-Visitor-Ip", "Cf-Connecting-Ip", "X-Real-Ip", "X-Forwarded-For")
    if ip:
        return ip
    peer = request.transport.get_extra_info("peername") if request.transport else None
    return peer[0] if peer else "-"


def _country(request) -> str:
    v = (request.headers.get("X-Visitor-Country") or request.headers.get("Cf-Ipcountry") or "").strip().upper()
    return "" if v in ("", "XX", "T1") else v


def _parse_ua(ua: str):
    u = (ua or "").lower()
    os_ = ("iOS" if ("iphone" in u or "ipod" in u) else "iPadOS" if "ipad" in u
           else "Android" if "android" in u else "Windows" if "windows" in u
           else "macOS" if ("mac os" in u or "macintosh" in u) else "Linux" if "linux" in u else "Other")
    br = ("Edge" if "edg" in u else "Opera" if ("opr" in u or "opera" in u)
          else "Chrome" if ("chrome" in u or "crios" in u) else "Firefox" if ("firefox" in u or "fxios" in u)
          else "Safari" if "safari" in u else "Bot" if ("bot" in u or "spider" in u or "crawl" in u) else "Other")
    dev = ("tablet" if ("ipad" in u or "tablet" in u) else "mobile" if ("mobi" in u or "iphone" in u or "android" in u) else "desktop")
    return br, os_, dev


def _rate_ok(ip: str) -> bool:
    now = time.time()
    dq = _HITS.setdefault(ip, deque())
    while dq and now - dq[0] > _RL_WINDOW:
        dq.popleft()
    if len(dq) >= _RL_MAX:
        return False
    dq.append(now)
    return True


def _cors(origin):
    allow = origin if origin in _ALLOW_ORIGINS else "https://shamsiyev.uz"
    return {"Access-Control-Allow-Origin": allow, "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "86400"}


# ----------------------------------------------------------------- track

async def _track_options(request):
    return web.Response(status=204, headers=_cors(request.headers.get("Origin")))


async def _track(request):
    origin = request.headers.get("Origin")
    ip = _client_ip(request)
    if not _rate_ok(ip):
        return web.Response(status=429, headers=_cors(origin))
    try:
        data = await request.json()
    except Exception:
        data = {}
    ua = request.headers.get("User-Agent", "")[:400]
    br, os_, dev = _parse_ua(ua)
    row = {
        "visitor": str(data.get("v") or "")[:64], "path": str(data.get("p") or "/")[:300],
        "referrer": str(data.get("r") or "")[:400], "country": _country(request), "ip": ip[:64],
        "ua": ua, "browser": br, "os": os_, "device": dev,
        "lang": str(data.get("l") or "")[:16], "screen": str(data.get("s") or "")[:16],
        "tz": str(data.get("tz") or "")[:48],
        "city": _hdr(request, "X-Visitor-City")[:80], "region": _hdr(request, "X-Visitor-Region")[:80],
        "org": _hdr(request, "X-Visitor-Org")[:120],
    }
    try:
        async with async_session() as s:
            await s.execute(text(
                "INSERT INTO site_visits (visitor,path,referrer,country,ip,ua,browser,os,device,lang,screen,tz,city,region,org) "
                "VALUES (:visitor,:path,:referrer,:country,:ip,:ua,:browser,:os,:device,:lang,:screen,:tz,:city,:region,:org)"
            ), row)
            await s.commit()
    except Exception:
        logger.exception("site_visits insert xatosi")
        return web.Response(status=500, headers=_cors(origin))
    return web.Response(status=204, headers=_cors(origin))


# ----------------------------------------------------------------- layout

def _sidebar(active: str) -> str:
    nav = [("overview", "Umumiy", "/site/admin", "stats"),
           ("visitors", "Mehmonlar", "/site/admin/visitors", "users")]
    items = "".join(
        f"<a href='{href}'{(' class=' + chr(39) + 'active' + chr(39)) if key == active else ''}>{A._icon(icon)}<span>{esc(label)}</span></a>"
        for key, label, href, icon in nav)
    return ("<aside class='sidebar'>"
            "<div class='brand' style='display:flex;align-items:center;gap:10px'>"
            "<span class='dot'>P</span>" + A._botdropdown() + "</div>"
            f"<nav class='nav'>{items}</nav></aside>")


def _layout(active: str, title: str, body: str, refresh: bool = False) -> str:
    ref = "<script>setTimeout(function(){location.reload()},30000)</script>" if refresh else ""
    inner = (
        "<input type='checkbox' id='navtoggle' class='navtoggle'>"
        + _sidebar(active)
        + "<label for='navtoggle' class='overlay'></label>"
        "<main class='content'>"
        "<div class='topbar'><label for='navtoggle' class='hamburger'>☰</label>"
        f"<span class='ttl'>{esc(title)}</span></div>"
        + body + ref
        + "<div class='foot'>Portfolio · shamsiyev.uz analitika</div>"
        "</main>")
    return A._page_raw(f"<div class='layout'>{inner}</div>")


def _kpi(label, num, note=""):
    n = f"<div class='note'>{esc(note)}</div>" if note else ""
    return f"<div class='stat'><div class='label'>{esc(label)}</div><div class='num'>{esc(num)}</div>{n}</div>"


def _dist(rows):
    if not rows:
        return "<div class='empty'>Ma'lumot yo'q</div>"
    mx = max(r[1] for r in rows) or 1
    out = "".join(
        f"<div class='row'><span class='name' title='{esc(nm)}'>{esc(nm) or '—'}</span>"
        f"<span class='track'><span class='bar2' style='width:{int(c/mx*100)}%'></span></span>"
        f"<span class='cnt'>{c}</span></div>" for nm, c in rows)
    return f"<div class='panel'><div class='dist'>{out}</div></div>"


def _chart(daily):
    if not daily:
        return "<div class='empty'>Ma'lumot yo'q</div>"
    mx = max(r[1] for r in daily) or 1
    out = "".join(
        f"<div class='bar'><span class='val'>{c or ''}</span>"
        f"<span class='barinner'><span class='fill' style='height:{int(c/mx*100)}%'></span></span>"
        f"<span class='lbl'>{esc(d)}</span></div>" for d, c in daily)
    return f"<div class='panel'><div class='chart'>{out}</div></div>"


async def _q(s, sql, **kw):
    return (await s.execute(text(sql), kw)).fetchall()


async def _v(s, sql, **kw):
    r = (await s.execute(text(sql), kw)).fetchone()
    return (r[0] if r else 0) or 0


# ----------------------------------------------------------------- overview

async def _admin(request):
    g = A._guard(request)
    if g is not None:
        return g
    async with async_session() as s:
        online = await _v(s, "SELECT count(distinct visitor) FROM site_visits WHERE ts > now() - interval '5 minutes'")
        total = await _v(s, "SELECT count(*) FROM site_visits")
        uniq = await _v(s, "SELECT count(distinct visitor) FROM site_visits")
        today = await _v(s, "SELECT count(*) FROM site_visits WHERE ts >= date_trunc('day', now() at time zone 'Asia/Tashkent')")
        today_u = await _v(s, "SELECT count(distinct visitor) FROM site_visits WHERE ts >= date_trunc('day', now() at time zone 'Asia/Tashkent')")
        d7 = await _v(s, "SELECT count(*) FROM site_visits WHERE ts > now() - interval '7 days'")
        d30 = await _v(s, "SELECT count(*) FROM site_visits WHERE ts > now() - interval '30 days'")
        pages = await _q(s, "SELECT path, count(*) c FROM site_visits WHERE ts > now()-interval '30 days' GROUP BY path ORDER BY c DESC LIMIT 10")
        countries = await _q(s, "SELECT country, count(*) c FROM site_visits WHERE ts>now()-interval '30 days' AND country<>'' GROUP BY country ORDER BY c DESC LIMIT 10")
        refs = await _q(s, "SELECT referrer, count(*) c FROM site_visits WHERE ts>now()-interval '30 days' AND referrer<>'' GROUP BY referrer ORDER BY c DESC LIMIT 8")
        browsers = await _q(s, "SELECT browser, count(*) c FROM site_visits WHERE ts>now()-interval '30 days' GROUP BY browser ORDER BY c DESC LIMIT 6")
        devices = await _q(s, "SELECT device, count(*) c FROM site_visits WHERE ts>now()-interval '30 days' GROUP BY device ORDER BY c DESC")
        daily = await _q(s, "SELECT to_char(date_trunc('day', ts at time zone 'Asia/Tashkent'),'MM-DD') d, count(*) c FROM site_visits WHERE ts>now()-interval '14 days' GROUP BY 1 ORDER BY 1")
        recent = await _q(s, "SELECT to_char(ts at time zone 'Asia/Tashkent','MM-DD HH24:MI') t, path, coalesce(nullif(city,''),country) loc, browser, device, referrer, ip FROM site_visits ORDER BY ts DESC LIMIT 40")

    statbar = ("<div class='statbar'>"
               + _kpi("Hozir onlayn", online, "5 daqiqa")
               + _kpi("Bugun", today, f"{today_u} mehmon")
               + _kpi("7 kun", d7) + _kpi("30 kun", d30)
               + _kpi("Jami tashrif", total) + _kpi("Jami mehmon", uniq)
               + "</div>")

    if recent:
        rows = "".join(
            f"<tr><td>{esc(t)}</td><td>{esc(p)}</td><td>{esc(loc) or '—'}</td>"
            f"<td>{esc(br)}</td><td>{esc(dev)}</td><td>{esc(ref) or '—'}</td>"
            f"<td>{esc(ip)}</td></tr>" for t, p, loc, br, dev, ref, ip in recent)
        recent_tbl = ("<div class='panel scroll'><table><thead><tr><th>Vaqt</th><th>Sahifa</th>"
                      "<th>Joy</th><th>Brauzer</th><th>Qurilma</th><th>Referrer</th><th>IP</th></tr></thead>"
                      f"<tbody>{rows}</tbody></table></div>")
    else:
        recent_tbl = "<div class='panel'><div class='empty'>Hali tashrif yo'q. Saytga kirilgach shu yerda paydo bo'ladi.</div></div>"

    body = (A._pagehead("Umumiy", f"Hozir <b style='color:#10a37f'>{online}</b> onlayn")
            + statbar
            + "<h2>So'nggi 14 kun</h2>" + _chart(daily)
            + "<h2>Top sahifalar</h2>" + _dist(pages)
            + "<h2>Davlatlar</h2>" + _dist(countries)
            + "<h2>Referrerlar</h2>" + _dist(refs)
            + "<h2>Brauzer</h2>" + _dist(browsers)
            + "<h2>Qurilma</h2>" + _dist(devices)
            + "<h2>So'nggi tashriflar</h2>" + recent_tbl)
    return web.Response(content_type="text/html", text=_layout("overview", "Portfolio — Umumiy", body, refresh=True))


# ----------------------------------------------------------------- visitors (KIM)

async def _visitors(request):
    g = A._guard(request)
    if g is not None:
        return g
    async with async_session() as s:
        vis = await _q(s, """
            SELECT visitor,
              to_char(max(ts) at time zone 'Asia/Tashkent','MM-DD HH24:MI') last_t,
              to_char(min(ts) at time zone 'Asia/Tashkent','MM-DD HH24:MI') first_t,
              count(*) visits,
              max(country) country, max(nullif(city,'')) city, max(nullif(org,'')) org,
              max(device) device, max(browser) browser, max(os) os,
              (array_agg(ip ORDER BY ts DESC))[1] ip,
              (array_agg(path ORDER BY ts DESC))[1] last_path,
              (array_agg(nullif(referrer,'') ORDER BY ts DESC))[1] lref,
              (max(ts) > now() - interval '5 minutes') online
            FROM site_visits GROUP BY visitor ORDER BY max(ts) DESC LIMIT 200
        """)
    if not vis:
        body = A._pagehead("Mehmonlar", "Kim kirgani") + "<div class='panel'><div class='empty'>Hali mehmon yo'q.</div></div>"
        return web.Response(content_type="text/html", text=_layout("visitors", "Portfolio — Mehmonlar", body))

    rows = ""
    for (v, last_t, first_t, visits, country, city, org, device, browser, os_, ip, last_path, ref, online) in vis:
        loc = " ".join(x for x in [esc(city), esc(country)] if x) or "—"
        dot = "<span class='badge ok'>onlayn</span>" if online else esc(last_t)
        vb = f"<span class='badge accentbadge'>{visits}</span>"
        rows += (f"<tr><td>{dot}</td><td>{vb}</td><td>{loc}</td><td>{esc(org) or '—'}</td>"
                 f"<td>{esc(device)} · {esc(browser)}/{esc(os_)}</td><td>{esc(last_path)}</td>"
                 f"<td>{esc(ref) or '—'}</td><td>{esc(ip)}</td><td class='muted'>{esc(first_t)}</td></tr>")
    tbl = ("<div class='panel scroll'><table><thead><tr><th>Oxirgi</th><th>Tashrif</th><th>Joylashuv</th>"
           "<th>Internet (ISP)</th><th>Qurilma · Brauzer</th><th>Oxirgi sahifa</th><th>Manba</th>"
           "<th>IP</th><th>Birinchi</th></tr></thead>"
           f"<tbody>{rows}</tbody></table></div>")
    body = (A._pagehead("Mehmonlar", f"{len(vis)} ta noyob mehmon (oxirgi 200)")
            + "<div class='note'>Har qator — bitta mehmon. Joylashuv, ISP va tashriflar soni bilan.</div>"
            + tbl)
    return web.Response(content_type="text/html", text=_layout("visitors", "Portfolio — Mehmonlar", body, refresh=True))


# ----------------------------------------------------------------- setup

def setup_site_routes(app: web.Application) -> None:
    app.router.add_post("/site/track", _track)
    app.router.add_options("/site/track", _track_options)
    app.router.add_get("/site/admin", _admin)
    app.router.add_get("/site/admin/", _admin)
    app.router.add_get("/site/admin/visitors", _visitors)
    app.on_startup.append(ensure_table)
    logger.info("Portfolio analitika marshrutlari ulandi (/site/track, /site/admin, /site/admin/visitors)")
