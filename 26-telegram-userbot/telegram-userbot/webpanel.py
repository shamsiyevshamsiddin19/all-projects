"""Userbot uchun ChatGPT / OpenAI uslubidagi professional boshqaruv paneli.

Zamonaviy minimalist dark interfeys, to'liq SVG vektor ikonkalari (hech qanday xom emojilarsiz),
brute-force himoyasi, qidiruv-filtr, 100% mobil va barcha ekranlarga moslashuvchan.
Parol: 2501 (yoki .env dagi PANEL_PASSWORD / PANEL_TOKEN).
"""
import hashlib
import json
import os
import time

from aiohttp import web
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))
DATA = os.path.join(BASE, "data")

TOKEN = os.getenv("PANEL_TOKEN", "")
PASSWORD = os.getenv("PANEL_PASSWORD", "2501")
PORT = int(os.getenv("PANEL_PORT", "8123"))
HOST = os.getenv("PANEL_HOST", "127.0.0.1")

# Sessiya uchun xavfsiz hesh kalit
AUTH_SECRET = hashlib.sha256((TOKEN + PASSWORD + "userbot_secure_salt_2501").encode()).hexdigest()

# Brute force himoyasi: IP -> [urinish_vaqtlari]
LOGIN_ATTEMPTS = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 daqiqa

ACCOUNTS = [
    ("acc1", "@shamsiyev_shamsiddin"),
    ("acc2", "@Shamsiyevshamsiddin"),
    ("acc3", "@scarpiont"),
]
FEATURES = [
    ("autoreply", "Avto-javob", "Gemini AI yordamida tabiiy intellektual javob"),
    ("autodraft", "Qoralama (Draft)", "Javobni yubormasdan qoralama qilib saqlash"),
    ("autoread", "Avto-o'qish", "Kanal va guruhlarni avtomatik o'qilgan qilish"),
    ("autoai", "Yarim-avto taklif", "Kelgan xabarga AI taklifini tasdiqlash"),
]
FEAT_KEYS = {k for k, _, _ in FEATURES}
ACC_KEYS = {a for a, _ in ACCOUNTS}


def _sfile(acc):
    return os.path.join(DATA, f"state_{acc}.json")


def _statsfile(acc):
    return os.path.join(DATA, f"stats_{acc}.json")


def read_state(acc):
    try:
        with open(_sfile(acc), encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def read_stats(acc):
    try:
        with open(_statsfile(acc), encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def write_state(acc, d):
    os.makedirs(DATA, exist_ok=True)
    tmp = _sfile(acc) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _sfile(acc))


def feature_on(d, feat):
    if feat == "autoread":
        k = d.get("autoread_kinds")
        if k is not None:
            return len(k) > 0
        return bool(d.get("autoread"))
    return bool(d.get(feat))


def set_feature(acc, feat, value):
    d = read_state(acc)
    if feat == "autoread":
        d["autoread"] = value
        d["autoread_kinds"] = ["group", "channel", "bot"] if value else []
    else:
        d[feat] = value
    write_state(acc, d)


def get_client_ip(req):
    return req.headers.get("X-Forwarded-For", req.remote or "unknown").split(",")[0].strip()


def check_rate_limit(ip):
    now = time.time()
    attempts = [t for t in LOGIN_ATTEMPTS.get(ip, []) if now - t < LOCKOUT_SECONDS]
    LOGIN_ATTEMPTS[ip] = attempts
    return len(attempts) < MAX_FAILED_ATTEMPTS


def record_failed_attempt(ip):
    now = time.time()
    attempts = [t for t in LOGIN_ATTEMPTS.get(ip, []) if now - t < LOCKOUT_SECONDS]
    attempts.append(now)
    LOGIN_ATTEMPTS[ip] = attempts


def is_authenticated(req):
    # 1. URL token parametri orqali
    if req.query.get("token") and req.query.get("token") == TOKEN:
        return True
    # 2. Cookie sessiya tekshiruvi
    cookie_val = req.cookies.get("userbot_session")
    if cookie_val and cookie_val == AUTH_SECRET:
        return True
    # 3. Header orqali tekshiruv
    auth_hdr = req.headers.get("X-Userbot-Auth")
    if auth_hdr and (auth_hdr == AUTH_SECRET or auth_hdr == TOKEN):
        return True
    return False


async def api_login(req):
    ip = get_client_ip(req)
    if not check_rate_limit(ip):
        return web.json_response(
            {"ok": False, "error": "Urinishlar limiti oshdi. 5 daqiqadan so'ng qayta urinib ko'ring."},
            status=429
        )

    try:
        data = await req.json()
        pwd = str(data.get("password", "")).strip()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri so'rov"}, status=400)

    if pwd == PASSWORD or (TOKEN and pwd == TOKEN):
        # Muvaffaqiyatli kirishda urinishlar tarixini tozalash
        LOGIN_ATTEMPTS.pop(ip, None)
        resp = web.json_response({"ok": True, "auth": AUTH_SECRET})
        resp.set_cookie(
            "userbot_session",
            AUTH_SECRET,
            max_age=60 * 60 * 24 * 30,  # 30 kun
            path="/",
            httponly=False,
            samesite="Lax",
        )
        return resp

    record_failed_attempt(ip)
    remaining = MAX_FAILED_ATTEMPTS - len(LOGIN_ATTEMPTS.get(ip, []))
    err_msg = f"Parol noto'g'ri! (Qolgan urinishlar: {max(0, remaining)})"
    return web.json_response({"ok": False, "error": err_msg}, status=401)


async def api_logout(req):
    resp = web.json_response({"ok": True})
    resp.del_cookie("userbot_session", path="/")
    return resp


async def api_state(req):
    if not is_authenticated(req):
        return web.json_response({"error": "unauthorized"}, status=401)
    out = {}
    for acc, _ in ACCOUNTS:
        d = read_state(acc)
        out[acc] = {f: feature_on(d, f) for f, _, _ in FEATURES}
    return web.json_response(out)


async def api_stats(req):
    if not is_authenticated(req):
        return web.json_response({"error": "unauthorized"}, status=401)
    out = {}
    for acc, uname in ACCOUNTS:
        st = read_stats(acc)
        if not st:
            st = {
                "account": acc,
                "profile": {"username": uname.replace("@", ""), "first_name": acc},
                "summary": {},
                "created_channels": [],
                "created_groups": [],
            }
        out[acc] = st
    return web.json_response(out)


async def api_refresh_stats(req):
    if not is_authenticated(req):
        return web.json_response({"error": "unauthorized"}, status=401)
    os.makedirs(DATA, exist_ok=True)
    ts = str(int(time.time()))
    try:
        with open(os.path.join(DATA, "refresh_stats_all.flag"), "w", encoding="utf-8") as f:
            f.write(ts)
        for acc, _ in ACCOUNTS:
            with open(os.path.join(DATA, f"refresh_stats_{acc}.flag"), "w", encoding="utf-8") as f:
                f.write(ts)
        return web.json_response({"ok": True, "message": "Yangilash so'rovi yuborildi"})
    except Exception as e:  # noqa: BLE001
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def api_toggle(req):
    if not is_authenticated(req):
        return web.json_response({"error": "unauthorized"}, status=401)
    try:
        body = await req.json()
    except Exception:  # noqa: BLE001
        return web.json_response({"error": "bad json"}, status=400)
    acc = body.get("account")
    feat = body.get("feature")
    val = bool(body.get("value"))
    if acc not in ACC_KEYS or feat not in FEAT_KEYS:
        return web.json_response({"error": "bad"}, status=400)
    set_feature(acc, feat, val)
    return web.json_response({"ok": True})


async def favicon(req):
    svg_icon = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='#10a37f'>"
        "<rect x='3' y='3' width='18' height='18' rx='5'/>"
        "<circle cx='8.5' cy='10.5' r='1.5' fill='#fff'/>"
        "<circle cx='15.5' cy='10.5' r='1.5' fill='#fff'/>"
        "<path d='M8 15h8' stroke='#fff' stroke-width='2' stroke-linecap='round'/>"
        "</svg>"
    )
    return web.Response(text=svg_icon, content_type="image/svg+xml")


async def index(req):
    resp = web.Response(text=PAGE.replace("__TOKEN__", TOKEN), content_type="text/html")
    if req.query.get("token") == TOKEN:
        resp.set_cookie(
            "userbot_session",
            AUTH_SECRET,
            max_age=60 * 60 * 24 * 30,
            path="/",
            httponly=False,
            samesite="Lax",
        )
    return resp


PAGE = """<!doctype html>
<html lang="uz">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Userbot Studio</title>
<link rel="icon" type="image/svg+xml" href="/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-base: #0e0e0e;
    --bg-sidebar: #171717;
    --bg-card: #1c1c1c;
    --bg-card-hover: #242424;
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(255, 255, 255, 0.18);
    --text-primary: #ececec;
    --text-secondary: #b4b4b4;
    --text-muted: #737373;
    --brand: #10a37f;
    --brand-hover: #1a7f64;
    --brand-glow: rgba(16, 163, 127, 0.25);
    --accent-blue: #38bdf8;
    --danger: #ef4444;
    --sidebar-w: 260px;
    --radius-lg: 14px;
    --radius-md: 10px;
    --radius-sm: 6px;
    --radius-pill: 999px;
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  body {
    margin: 0;
    min-height: 100vh;
    background-color: var(--bg-base);
    color: var(--text-primary);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    display: flex;
    overflow-x: hidden;
  }

  /* VECTOR SVG ICONS */
  .icon {
    width: 18px;
    height: 18px;
    stroke: currentColor;
    fill: none;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
    flex-shrink: 0;
  }

  /* LAYOUT */
  .app-container {
    display: flex;
    width: 100%;
    min-height: 100vh;
  }

  /* CHATGPT STYLE SIDEBAR */
  .sidebar {
    width: var(--sidebar-w);
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border-subtle);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 16px 12px;
    flex-shrink: 0;
    height: 100vh;
    position: sticky;
    top: 0;
    z-index: 100;
  }

  .sidebar-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px 18px;
    border-bottom: 1px solid var(--border-subtle);
  }
  .brand-logo {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: var(--brand);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    box-shadow: 0 2px 8px var(--brand-glow);
  }
  .brand-text {
    font-size: 15px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--text-primary);
  }

  .sidebar-section-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    padding: 14px 10px 6px;
  }

  /* ACCOUNT SWITCHER */
  .account-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 12px;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.15s;
    margin-bottom: 2px;
    color: var(--text-secondary);
    border: 1px solid transparent;
  }
  .account-item:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
  }
  .account-item.active {
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-primary);
    border-color: var(--border-subtle);
  }
  .ai-left {
    display: flex;
    align-items: center;
    gap: 10px;
    overflow: hidden;
  }
  .ai-avatar {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    background: #2a2a2a;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    color: var(--text-secondary);
  }
  .account-item.active .ai-avatar {
    background: var(--brand);
    color: #fff;
  }
  .ai-name {
    font-size: 13px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .ai-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--brand);
    box-shadow: 0 0 6px var(--brand);
  }

  /* SIDEBAR FOOTER (USER & LOCK) */
  .sidebar-footer {
    padding-top: 14px;
    border-top: 1px solid var(--border-subtle);
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .user-profile-tile {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 10px;
    border-radius: var(--radius-md);
    background: rgba(255, 255, 255, 0.03);
  }
  .upt-user {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .upt-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #10a37f, #0284c7);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
  }
  .btn-logout {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 6px;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    transition: all 0.15s;
  }
  .btn-logout:hover {
    color: var(--danger);
    background: rgba(239, 68, 68, 0.1);
  }

  /* MAIN WORKSPACE */
  .main-workspace {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    height: 100vh;
    overflow-y: auto;
  }

  /* TOP APP BAR */
  .top-app-bar {
    position: sticky;
    top: 0;
    background: rgba(14, 14, 14, 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border-subtle);
    padding: 14px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 50;
  }
  .tab-title-group {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .mobile-menu-btn {
    display: none;
    background: transparent;
    border: none;
    color: var(--text-primary);
    cursor: pointer;
    padding: 4px;
  }
  .breadcrumbs {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-muted);
  }
  .bc-active {
    font-weight: 600;
    color: var(--text-primary);
  }
  .badge-status {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 8px;
    border-radius: var(--radius-pill);
    background: rgba(16, 163, 127, 0.12);
    color: var(--brand);
    font-size: 11px;
    font-weight: 600;
    border: 1px solid rgba(16, 163, 127, 0.25);
  }
  .badge-status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--brand);
    box-shadow: 0 0 6px var(--brand);
  }

  .topbar-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .btn-action {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    padding: 7px 14px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-action:hover {
    background: var(--bg-card-hover);
    border-color: var(--border-hover);
  }

  /* WORKSPACE CONTENT */
  .workspace-content {
    padding: 28px;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 28px;
  }

  /* SECTION TITLE */
  .section-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 14px;
    flex-wrap: wrap;
    gap: 8px;
  }
  .section-title {
    font-size: 16px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .section-desc {
    font-size: 13px;
    color: var(--text-muted);
  }

  /* METRIC STATS GRID */
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 14px;
  }
  .metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 110px;
    transition: all 0.2s;
  }
  .metric-card:hover {
    border-color: var(--border-hover);
    background: var(--bg-card-hover);
  }
  .mc-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: var(--text-muted);
  }
  .mc-label {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .mc-value {
    font-size: 28px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.02em;
    color: var(--text-primary);
    margin: 8px 0 2px;
  }
  .mc-sub {
    font-size: 12px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .mc-pill {
    font-size: 11px;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: var(--radius-sm);
    background: rgba(16, 163, 127, 0.15);
    color: var(--brand);
  }

  /* AUTOMATION CONTROLS (LINEAR STYLE) */
  .toggles-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 14px;
  }
  .toggle-tile {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 16px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.2s;
  }
  .toggle-tile:hover {
    border-color: var(--border-hover);
    background: var(--bg-card-hover);
  }
  .tt-left {
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }
  .tt-icon-wrap {
    width: 34px;
    height: 34px;
    border-radius: var(--radius-md);
    background: rgba(255, 255, 255, 0.05);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    margin-top: 2px;
  }
  .tt-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 2px;
  }
  .tt-desc {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.35;
  }

  /* SWITCH TOGGLE */
  .switch {
    position: relative;
    width: 44px;
    height: 24px;
    flex-shrink: 0;
  }
  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  .slider {
    position: absolute;
    inset: 0;
    background: #333333;
    border-radius: 999px;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .slider:before {
    content: "";
    position: absolute;
    width: 18px;
    height: 18px;
    left: 3px;
    top: 3px;
    background: #ffffff;
    border-radius: 50%;
    transition: all 0.2s ease;
  }
  input:checked + .slider {
    background: var(--brand);
  }
  input:checked + .slider:before {
    transform: translateX(20px);
  }

  /* OWNERSHIP SECTION */
  .ownership-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }
  .ownership-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 18px;
    display: flex;
    flex-direction: column;
  }
  .oc-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 12px;
    margin-bottom: 12px;
    border-bottom: 1px solid var(--border-subtle);
  }
  .oc-title {
    font-size: 14px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .oc-count {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    background: rgba(255, 255, 255, 0.06);
    padding: 2px 8px;
    border-radius: var(--radius-pill);
  }
  .search-box {
    margin-bottom: 10px;
    position: relative;
  }
  .search-input {
    width: 100%;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    padding: 7px 10px 7px 32px;
    font-size: 12px;
    outline: none;
    font-family: inherit;
  }
  .search-input:focus {
    border-color: var(--brand);
  }
  .search-icon {
    position: absolute;
    left: 9px;
    top: 8px;
    color: var(--text-muted);
    width: 14px;
    height: 14px;
  }
  .oc-list {
    max-height: 280px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding-right: 4px;
  }
  .oc-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 12px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: var(--radius-md);
    transition: all 0.15s;
    gap: 8px;
  }
  .oc-item:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--border-hover);
  }
  .oci-left {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }
  .oci-name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .oci-link {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: var(--accent-blue);
    text-decoration: none;
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(56, 189, 248, 0.08);
    transition: all 0.15s;
    flex-shrink: 0;
  }
  .oci-link:hover {
    background: rgba(56, 189, 248, 0.18);
    color: #fff;
  }
  .btn-copy {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 2px 4px;
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    transition: all 0.15s;
    flex-shrink: 0;
  }
  .btn-copy:hover {
    color: var(--brand);
    background: rgba(16, 163, 127, 0.1);
  }
  .oci-tag {
    font-size: 11px;
    font-weight: 600;
    color: var(--brand);
    background: rgba(16, 163, 127, 0.1);
    padding: 2px 7px;
    border-radius: 4px;
    flex-shrink: 0;
  }
  .oci-tag.admin {
    color: #f59e0b;
    background: rgba(245, 158, 11, 0.1);
  }

  /* NAV ITEMS IN SIDEBAR */
  .nav-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 12px;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.15s;
    margin-bottom: 2px;
    color: var(--text-secondary);
    border: 1px solid transparent;
  }
  .nav-item:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
  }
  .nav-item.active {
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-primary);
    border-color: var(--border-subtle);
  }

  /* ACC META BADGES */
  .acc-meta-badges {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .meta-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--text-muted);
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-subtle);
    padding: 4px 8px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .meta-pill strong {
    color: var(--text-primary);
  }
  .meta-pill.premium {
    color: #fbbf24;
    border-color: rgba(251, 191, 36, 0.3);
    background: rgba(251, 191, 36, 0.1);
  }

  /* RECENT DIALOGS */
  .recent-list-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 14px;
  }
  .recent-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 8px;
  }
  .recent-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 12px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: var(--radius-md);
    transition: all 0.15s;
    gap: 8px;
  }
  .recent-item:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--border-hover);
  }
  .recent-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
  }
  .type-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    text-transform: uppercase;
  }
  .type-badge.user { background: rgba(56, 189, 248, 0.15); color: #38bdf8; }
  .type-badge.group { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
  .type-badge.channel { background: rgba(16, 185, 129, 0.15); color: #10b981; }
  .type-badge.bot { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
  .unread-badge {
    background: #ef4444;
    color: #fff;
    font-size: 10px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: var(--radius-pill);
  }
  .time-badge {
    font-size: 11px;
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
  }

  /* SYSTEM DETAILS BOX (BOTTOM) */
  .sys-details-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 16px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
    font-size: 12px;
    color: var(--text-muted);
  }
  .sys-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .sys-val {
    color: var(--text-secondary);
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
  }

  /* OPENAI AUTH MODAL */
  #login-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    display: none;
    align-items: center;
    justify-content: center;
    padding: 20px;
    z-index: 1000;
  }
  .login-card {
    background: #181818;
    border: 1px solid var(--border-subtle);
    border-radius: 18px;
    padding: 38px 32px;
    width: 100%;
    max-width: 360px;
    text-align: center;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
  }
  .login-logo {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: var(--brand);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 18px;
    box-shadow: 0 4px 14px var(--brand-glow);
  }
  .login-card h2 {
    margin: 0 0 6px;
    font-size: 20px;
    font-weight: 700;
  }
  .login-card p {
    margin: 0 0 24px;
    font-size: 13px;
    color: var(--text-muted);
  }
  .pin-input {
    width: 100%;
    background: #242424;
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    color: #fff;
    font-size: 24px;
    letter-spacing: 10px;
    text-align: center;
    padding: 12px 10px;
    margin-bottom: 16px;
    outline: none;
    font-family: 'JetBrains Mono', monospace;
  }
  .pin-input:focus {
    border-color: var(--brand);
    box-shadow: 0 0 0 2px var(--brand-glow);
  }
  .btn-submit {
    width: 100%;
    background: var(--brand);
    border: none;
    border-radius: 10px;
    color: #fff;
    font-size: 14px;
    font-weight: 600;
    padding: 12px;
    cursor: pointer;
    transition: background 0.15s;
  }
  .btn-submit:hover {
    background: var(--brand-hover);
  }
  .login-err {
    color: var(--danger);
    font-size: 12px;
    margin-top: 10px;
    min-height: 18px;
  }
  .shake { animation: shake 0.4s ease-in-out; }
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-6px); }
    40%, 80% { transform: translateX(6px); }
  }

  /* TOAST */
  .toast {
    position: fixed;
    left: 50%;
    bottom: 24px;
    transform: translateX(-50%) translateY(20px);
    background: #262626;
    color: #fff;
    border: 1px solid var(--border-subtle);
    padding: 10px 20px;
    border-radius: var(--radius-pill);
    font-size: 13px;
    font-weight: 500;
    opacity: 0;
    transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
    pointer-events: none;
    z-index: 2000;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  }
  .toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }

  /* MOBILE BACKDROP */
  .sidebar-backdrop {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    z-index: 90;
  }

  /* RESPONSIVE BREAKPOINTS */
  @media (max-width: 1100px) {
    .ownership-grid {
      grid-template-columns: 1fr;
    }
  }
  @media (max-width: 768px) {
    .sidebar {
      position: fixed;
      left: -100%;
      top: 0;
      bottom: 0;
      height: 100vh;
      z-index: 100;
      transition: left 0.25s ease;
    }
    .sidebar.open {
      left: 0;
    }
    .sidebar-backdrop.open {
      display: block;
    }
    .mobile-menu-btn {
      display: flex;
    }
    .top-app-bar {
      padding: 12px 16px;
    }
    .workspace-content {
      padding: 16px;
      gap: 20px;
    }
    .metrics-grid {
      grid-template-columns: 1fr 1fr;
    }
    .toggles-grid {
      grid-template-columns: 1fr;
    }
    .recent-list {
      grid-template-columns: 1fr;
    }
  }
  @media (max-width: 480px) {
    .metrics-grid {
      grid-template-columns: 1fr;
    }
    .breadcrumbs span:not(.bc-active) {
      display: none;
    }
  }
</style>
</head>
<body>

<div class="app-container">
  <!-- MOBILE BACKDROP -->
  <div class="sidebar-backdrop" id="sidebar-backdrop" onclick="toggleMobileSidebar()"></div>

  <!-- CHATGPT STYLE SIDEBAR -->
  <aside class="sidebar" id="sidebar">
    <div>
      <div class="sidebar-header">
        <div class="brand-logo">
          <svg class="icon" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>
        </div>
        <div>
          <div class="brand-text">Userbot Studio</div>
          <div style="font-size:11px; color:var(--text-muted);">Shamsiddin Shamsiyev</div>
        </div>
      </div>

      <div class="sidebar-section-label">Akkauntlar</div>
      <div id="accounts-nav">
        <div class="account-item active" id="nav-acc1" onclick="selectAcc('acc1')">
          <div class="ai-left">
            <div class="ai-avatar">1</div>
            <div class="ai-name">@shamsiyev_shamsiddin</div>
          </div>
          <div class="ai-dot"></div>
        </div>
        <div class="account-item" id="nav-acc2" onclick="selectAcc('acc2')">
          <div class="ai-left">
            <div class="ai-avatar">2</div>
            <div class="ai-name">@Shamsiyevshamsiddin</div>
          </div>
          <div class="ai-dot" style="display:none;"></div>
        </div>
        <div class="account-item" id="nav-acc3" onclick="selectAcc('acc3')">
          <div class="ai-left">
            <div class="ai-avatar">3</div>
            <div class="ai-name">@scarpiont</div>
          </div>
          <div class="ai-dot" style="display:none;"></div>
        </div>
      </div>

      <div class="sidebar-section-label" style="margin-top:12px;">Navigatsiya</div>
      <div style="display:flex; flex-direction:column; gap:2px;">
        <div class="nav-item active" id="btn-nav-stats" onclick="scrollToSection('sec-stats', this)">
          <div class="ai-left">
            <svg class="icon" viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
            <span class="ai-name">Statistika</span>
          </div>
        </div>
        <div class="nav-item" id="btn-nav-toggles" onclick="scrollToSection('sec-toggles', this)">
          <div class="ai-left">
            <svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            <span class="ai-name">Rejimlar</span>
          </div>
        </div>
        <div class="nav-item" id="btn-nav-ownership" onclick="scrollToSection('sec-ownership', this)">
          <div class="ai-left">
            <svg class="icon" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
            <span class="ai-name">Kanal va Guruhlar</span>
          </div>
        </div>
        <div class="nav-item" id="btn-nav-recent" onclick="scrollToSection('sec-recent', this)">
          <div class="ai-left">
            <svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            <span class="ai-name">So'nggi Suhbatlar</span>
          </div>
        </div>
      </div>
    </div>

    <!-- SIDEBAR FOOTER -->
    <div class="sidebar-footer">
      <div class="user-profile-tile">
        <div class="upt-user">
          <div class="upt-avatar" id="sb-avatar">S</div>
          <div>
            <div style="font-weight:600; font-size:13px;" id="sb-name">Shamsiddin</div>
            <div style="font-size:11px; color:var(--text-muted);" id="sb-handle">@shamsiyev</div>
          </div>
        </div>
        <button class="btn-logout" onclick="logout()" title="Chiqish / Qulflash">
          <svg class="icon" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
        </button>
      </div>
    </div>
  </aside>

  <!-- MAIN WORKSPACE -->
  <main class="main-workspace">
    <!-- TOP APP BAR -->
    <header class="top-app-bar">
      <div class="tab-title-group">
        <button class="mobile-menu-btn" onclick="toggleMobileSidebar()" title="Menyu">
          <svg class="icon" viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
        </button>
        <div class="breadcrumbs">
          <span>Userbot</span>
          <span>/</span>
          <span class="bc-active" id="top-title">acc1</span>
        </div>
        <span class="badge-status"><span class="badge-status-dot"></span> Onlayn</span>
      </div>

      <div class="topbar-actions">
        <button class="btn-action" onclick="triggerLiveRefresh()" title="Telegram'dan jonli yangilash" id="btn-refresh">
          <svg class="icon" id="refresh-icon" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
          <span id="refresh-text">Yangilash</span>
        </button>
      </div>
    </header>

    <!-- CONTENT -->
    <div class="workspace-content">
      <!-- 1. AKKAUNT METRIKALARI -->
      <section id="sec-stats">
        <div class="section-header">
          <div>
            <div class="section-title">
              <svg class="icon" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              <span>Akkaunt Metrikalari</span>
            </div>
            <div class="section-desc" id="acc-header-desc">Telegram MTProto orqali olingan jonli ma'lumotlar</div>
          </div>
          <div class="acc-meta-badges">
            <span class="meta-pill" title="Telegram ID">ID: <strong id="acc-id">-</strong> <button class="btn-copy" onclick="copyId(document.getElementById('acc-id').textContent, event)" title="ID nusxalash"><svg class="icon" style="width:12px;height:12px;" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg></button></span>
            <span class="meta-pill">Tel: <strong id="acc-phone">-</strong></span>
            <span class="meta-pill" id="acc-premium-pill">Standart</span>
          </div>
        </div>

        <div class="metrics-grid">
          <!-- Shaxsiy chatlar -->
          <div class="metric-card">
            <div class="mc-top">
              <span class="mc-label">Shaxsiy Chatlar</span>
              <svg class="icon" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            </div>
            <div class="mc-value" id="m-priv">0</div>
            <div class="mc-sub">Muloqotdagi foydalanuvchilar</div>
          </div>

          <!-- Guruhlar -->
          <div class="metric-card">
            <div class="mc-top">
              <span class="mc-label">Guruhlar</span>
              <svg class="icon" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
            </div>
            <div class="mc-value" id="m-groups">0</div>
            <div class="mc-sub">
              <span>Men ochgan:</span>
              <span class="mc-pill" id="m-created-groups">0 ta</span>
            </div>
          </div>

          <!-- Kanallar -->
          <div class="metric-card">
            <div class="mc-top">
              <span class="mc-label">Kanallar</span>
              <svg class="icon" viewBox="0 0 24 24"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
            </div>
            <div class="mc-value" id="m-channels">0</div>
            <div class="mc-sub">
              <span>Men ochgan:</span>
              <span class="mc-pill" id="m-created-channels">0 ta</span>
            </div>
          </div>

          <!-- Botlar & Unread -->
          <div class="metric-card">
            <div class="mc-top">
              <span class="mc-label">Botlar</span>
              <svg class="icon" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path><line x1="8" y1="16" x2="8" y2="16"></line><line x1="16" y1="16" x2="16" y2="16"></line></svg>
            </div>
            <div class="mc-value" id="m-bots">0</div>
            <div class="mc-sub">
              <span>O'qilmagan:</span>
              <span style="color:#f87171; font-weight:600;" id="m-unread">0</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 2. USERBOT REJIMLARI -->
      <section id="sec-toggles">
        <div class="section-header">
          <div>
            <div class="section-title">
              <svg class="icon" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
              <span>Avtomatlashtirish Rejimlari</span>
            </div>
            <div class="section-desc">Userbot xususiyatlarini real vaqt rejimida yoqish yoki o'chirish</div>
          </div>
        </div>

        <div class="toggles-grid" id="toggles-container">
          <!-- Dinamik ravishda yuklanadi -->
        </div>
      </section>

      <!-- 3. MEN OCHGAN KANALLAR VA GURUHLAR RO'YXATI -->
      <section id="sec-ownership">
        <div class="section-header">
          <div>
            <div class="section-title">
              <svg class="icon" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg>
              <span>Mening Egaligimdagi Resurslar</span>
            </div>
            <div class="section-desc">Ushbu akkaunt orqali yaratilgan kanallar va guruhlar ro'yxati</div>
          </div>
        </div>

        <div class="ownership-grid">
          <!-- Men ochgan kanallar -->
          <div class="ownership-card">
            <div class="oc-header">
              <div class="oc-title">
                <svg class="icon" viewBox="0 0 24 24"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                <span>Men Ochgan Kanallar</span>
              </div>
              <span class="oc-count" id="count-created-ch">0 ta</span>
            </div>
            <div class="search-box">
              <svg class="icon search-icon" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              <input type="text" class="search-input" placeholder="Kanal nomini qidirish..." oninput="filterChannels(this.value)">
            </div>
            <div class="oc-list" id="list-created-ch">
              <div style="color:var(--text-muted); padding:10px; text-align:center;">Yuklanmoqda…</div>
            </div>
          </div>

          <!-- Men ochgan guruhlar -->
          <div class="ownership-card">
            <div class="oc-header">
              <div class="oc-title">
                <svg class="icon" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>
                <span>Men Ochgan Guruhlar</span>
              </div>
              <span class="oc-count" id="count-created-gr">0 ta</span>
            </div>
            <div class="search-box">
              <svg class="icon search-icon" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              <input type="text" class="search-input" placeholder="Guruh nomini qidirish..." oninput="filterGroups(this.value)">
            </div>
            <div class="oc-list" id="list-created-gr">
              <div style="color:var(--text-muted); padding:10px; text-align:center;">Yuklanmoqda…</div>
            </div>
          </div>

          <!-- Men admin bo'lgan chatlar -->
          <div class="ownership-card">
            <div class="oc-header">
              <div class="oc-title">
                <svg class="icon" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                <span>Admin Chatlar</span>
              </div>
              <span class="oc-count" id="count-admin-chats">0 ta</span>
            </div>
            <div class="search-box">
              <svg class="icon search-icon" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              <input type="text" class="search-input" placeholder="Admin chat qidirish..." oninput="filterAdminChats(this.value)">
            </div>
            <div class="oc-list" id="list-admin-chats">
              <div style="color:var(--text-muted); padding:10px; text-align:center;">Yuklanmoqda…</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 4. SO'NGGI SUHBATLAR (RECENT DIALOGS) -->
      <section id="sec-recent">
        <div class="section-header">
          <div>
            <div class="section-title">
              <svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
              <span>So'nggi Muloqotlar</span>
            </div>
            <div class="section-desc">Akkauntning eng oxirgi faol muloqotlari va chatlari</div>
          </div>
        </div>
        <div class="recent-list-card">
          <div class="recent-list" id="list-recent-dialogs">
            <div style="color:var(--text-muted); padding:10px; text-align:center;">Yuklanmoqda…</div>
          </div>
        </div>
      </section>

      <!-- 5. TIZIM VA SERVER STATUSI -->
      <section>
        <div class="sys-details-card">
          <div class="sys-item">
            <svg class="icon" viewBox="0 0 24 24"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>
            <span>Server:</span>
            <span class="sys-val">Hetzner CX23 (shamsiyev.uz)</span>
          </div>
          <div class="sys-item">
            <svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            <span>Faollik Vaqti:</span>
            <span class="sys-val">08:00 – 24:00 (UTC+5)</span>
          </div>
          <div class="sys-item">
            <svg class="icon" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
            <span>Flood Himoyasi:</span>
            <span class="sys-val">15 ta / 60s max</span>
          </div>
          <div class="sys-item">
            <svg class="icon" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
            <span>Model:</span>
            <span class="sys-val">Gemini Flash Latest</span>
          </div>
        </div>
      </section>
    </div>
  </main>
</div>

<!-- OPENAI / CHATGPT STYLE AUTH MODAL -->
<div id="login-overlay">
  <div class="login-card" id="login-box">
    <div class="login-logo">
      <svg class="icon" style="width:24px; height:24px;" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
    </div>
    <h2>Xavfsiz Kirish</h2>
    <p>Userbot paneliga kirish uchun PIN parolni kiriting</p>
    <form onsubmit="handleLogin(event)">
      <input type="password" id="pin-input" class="pin-input" placeholder="••••" maxlength="10" inputmode="numeric" pattern="[0-9]*" autofocus autocomplete="off">
      <button type="submit" class="btn-submit">Davom etish</button>
    </form>
    <div id="login-err" class="login-err"></div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const TOKEN = "__TOKEN__";
let currentAcc = "acc1";
let allStats = {};
let allStates = {};

const FEATURES = [
  ["autoreply", "Avto-javob", "Gemini AI orqali intellektual tabiiy javob"],
  ["autodraft", "Qoralama (Draft)", "Javobni yubormasdan qoralama qilib saqlash"],
  ["autoread", "Avto-o'qish", "Kanal va guruhlarni avtomatik o'qilgan qilish"],
  ["autoai", "Yarim-avto taklif", "Kelgan xabarga AI taklifini tayyorlash"]
];

function showToast(text) {
  const t = document.getElementById("toast");
  t.textContent = text;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 1800);
}

function getAuth() {
  return localStorage.getItem("userbot_auth") || "";
}

function showLogin() {
  document.getElementById("login-overlay").style.display = "flex";
  document.getElementById("pin-input").value = "";
  setTimeout(() => document.getElementById("pin-input").focus(), 100);
}

function hideLogin() {
  document.getElementById("login-overlay").style.display = "none";
}

function toggleMobileSidebar() {
  const sb = document.getElementById("sidebar");
  const bd = document.getElementById("sidebar-backdrop");
  sb.classList.toggle("open");
  bd.classList.toggle("open");
}

function scrollToSection(id, btn) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth' });
  if (btn) {
    document.querySelectorAll('.nav-item').forEach(e => e.classList.remove('active'));
    btn.classList.add('active');
  }
  if (window.innerWidth <= 768) toggleMobileSidebar();
}

function copyId(id, e) {
  if (e && e.stopPropagation) e.stopPropagation();
  if (!id || id === "-") return;
  navigator.clipboard.writeText(String(id)).then(() => {
    showToast("ID nusxalandi: " + id);
  }).catch(() => {
    showToast("Nusxa olinmadi");
  });
}

async function handleLogin(e) {
  if (e && e.preventDefault) e.preventDefault();
  const pwd = document.getElementById("pin-input").value.trim();
  if (!pwd) return;

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: pwd }),
      credentials: "same-origin"
    });
    const d = await res.json();
    if (res.ok && d.ok) {
      if (d.auth) localStorage.setItem("userbot_auth", d.auth);
      hideLogin();
      showToast("Xush kelibsiz! Panel yuklandi");
      refreshData();
    } else {
      const box = document.getElementById("login-box");
      box.classList.add("shake");
      document.getElementById("login-err").textContent = d.error || "Parol noto'g'ri!";
      setTimeout(() => box.classList.remove("shake"), 400);
    }
  } catch (err) {
    document.getElementById("login-err").textContent = "Tarmoq xatosi";
  }
}

async function logout() {
  await fetch("/api/logout", { method: "POST", credentials: "same-origin" });
  localStorage.removeItem("userbot_auth");
  showToast("Panel qulflandi");
  showLogin();
}

function selectAcc(acc) {
  currentAcc = acc;
  document.querySelectorAll(".account-item").forEach(el => {
    el.classList.remove("active");
    const dot = el.querySelector(".ai-dot");
    if (dot) dot.style.display = "none";
  });
  const navItem = document.getElementById("nav-" + acc);
  if (navItem) {
    navItem.classList.add("active");
    const dot = navItem.querySelector(".ai-dot");
    if (dot) dot.style.display = "block";
  }
  if (window.innerWidth <= 768) {
    const sb = document.getElementById("sidebar");
    if (sb.classList.contains("open")) toggleMobileSidebar();
  }
  render();
}

async function triggerLiveRefresh() {
  const auth = getAuth();
  showToast("Telegram'dan jonli yangilanmoqda…");
  try {
    await fetch("/api/refresh_stats", {
      method: "POST",
      headers: auth ? { "X-Userbot-Auth": auth } : {},
      credentials: "same-origin"
    });
    setTimeout(() => {
      refreshData();
      showToast("Statistika yangilandi");
    }, 3500);
  } catch (e) {
    refreshData();
  }
}

async function refreshData() {
  const auth = getAuth();
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get("token") || TOKEN;
  let q = urlToken ? "?token=" + encodeURIComponent(urlToken) : "";

  try {
    const [resState, resStats] = await Promise.all([
      fetch("/api/state" + q, { headers: auth ? { "X-Userbot-Auth": auth } : {}, credentials: "same-origin" }),
      fetch("/api/stats" + q, { headers: auth ? { "X-Userbot-Auth": auth } : {}, credentials: "same-origin" })
    ]);

    if (resState.status === 401 || resStats.status === 401) {
      showLogin();
      return;
    }

    if (resState.ok) allStates = await resState.json();
    if (resStats.ok) allStats = await resStats.json();
    hideLogin();
    render();
  } catch (err) {
    showLogin();
  }
}

function filterChannels(q) {
  const st = allStats[currentAcc] || {};
  const list = st.created_channels || [];
  const filtered = list.filter(c => (c.title || "").toLowerCase().includes(q.toLowerCase()) || (c.username || "").toLowerCase().includes(q.toLowerCase()));
  renderChannelsList(filtered);
}

function filterGroups(q) {
  const st = allStats[currentAcc] || {};
  const list = st.created_groups || [];
  const filtered = list.filter(g => (g.title || "").toLowerCase().includes(q.toLowerCase()) || (g.username || "").toLowerCase().includes(q.toLowerCase()));
  renderGroupsList(filtered);
}

function filterAdminChats(q) {
  const st = allStats[currentAcc] || {};
  const list = st.admin_chats || [];
  const filtered = list.filter(a => (a.title || "").toLowerCase().includes(q.toLowerCase()) || (a.username || "").toLowerCase().includes(q.toLowerCase()));
  renderAdminList(filtered);
}

function renderChannelsList(list) {
  const chBox = document.getElementById("list-created-ch");
  chBox.innerHTML = "";
  if (!list || list.length === 0) {
    chBox.innerHTML = '<div style="color:var(--text-muted); padding:14px; text-align:center;">Kanal topilmadi</div>';
    return;
  }
  list.forEach(ch => {
    const d = document.createElement("div");
    d.className = "oc-item";
    const userLink = ch.username ? `<a href="https://t.me/${ch.username}" target="_blank" rel="noopener" class="oci-link" title="Telegram'da ochish">@${ch.username}</a>` : '';
    d.innerHTML = `
      <div class="oci-left">
        <span class="oci-name" title="${ch.title}">${ch.title}</span>
        ${userLink}
        <button class="btn-copy" onclick="copyId('${ch.id}', event)" title="ID nusxalash">
          <svg class="icon" style="width:13px; height:13px;" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        </button>
      </div>
      <span class="oci-tag">Egasi</span>
    `;
    chBox.appendChild(d);
  });
}

function renderGroupsList(list) {
  const grBox = document.getElementById("list-created-gr");
  grBox.innerHTML = "";
  if (!list || list.length === 0) {
    grBox.innerHTML = '<div style="color:var(--text-muted); padding:14px; text-align:center;">Guruh topilmadi</div>';
    return;
  }
  list.forEach(gr => {
    const d = document.createElement("div");
    d.className = "oc-item";
    const userLink = gr.username ? `<a href="https://t.me/${gr.username}" target="_blank" rel="noopener" class="oci-link" title="Telegram'da ochish">@${gr.username}</a>` : '';
    d.innerHTML = `
      <div class="oci-left">
        <span class="oci-name" title="${gr.title}">${gr.title}</span>
        ${userLink}
        <button class="btn-copy" onclick="copyId('${gr.id}', event)" title="ID nusxalash">
          <svg class="icon" style="width:13px; height:13px;" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        </button>
      </div>
      <span class="oci-tag">Egasi</span>
    `;
    grBox.appendChild(d);
  });
}

function renderAdminList(list) {
  const box = document.getElementById("list-admin-chats");
  box.innerHTML = "";
  if (!list || list.length === 0) {
    box.innerHTML = '<div style="color:var(--text-muted); padding:14px; text-align:center;">Admin chat topilmadi</div>';
    return;
  }
  list.forEach(a => {
    const d = document.createElement("div");
    d.className = "oc-item";
    const userLink = a.username ? `<a href="https://t.me/${a.username}" target="_blank" rel="noopener" class="oci-link" title="Telegram'da ochish">@${a.username}</a>` : '';
    d.innerHTML = `
      <div class="oci-left">
        <span class="oci-name" title="${a.title}">${a.title}</span>
        ${userLink}
        <button class="btn-copy" onclick="copyId('${a.id}', event)" title="ID nusxalash">
          <svg class="icon" style="width:13px; height:13px;" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        </button>
      </div>
      <span class="oci-tag admin">Admin</span>
    `;
    box.appendChild(d);
  });
}

function renderRecentDialogs(list) {
  const box = document.getElementById("list-recent-dialogs");
  box.innerHTML = "";
  if (!list || list.length === 0) {
    box.innerHTML = '<div style="color:var(--text-muted); padding:14px; text-align:center; grid-column:1/-1;">Suhbatlar topilmadi</div>';
    return;
  }
  const typeLabels = { user: "Shaxsiy", group: "Guruh", channel: "Kanal", bot: "Bot" };
  list.forEach(item => {
    const d = document.createElement("div");
    d.className = "recent-item";
    const userLink = item.username ? `<a href="https://t.me/${item.username}" target="_blank" rel="noopener" class="oci-link" title="Telegram'da ochish">@${item.username}</a>` : '';
    const unreadPill = item.unread > 0 ? `<span class="unread-badge">${item.unread}</span>` : '';
    d.innerHTML = `
      <div class="oci-left">
        <span class="oci-name" title="${item.title}">${item.title}</span>
        ${userLink}
        <button class="btn-copy" onclick="copyId('${item.id}', event)" title="ID nusxalash">
          <svg class="icon" style="width:12px; height:12px;" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        </button>
      </div>
      <div class="recent-meta">
        ${unreadPill}
        <span class="type-badge ${item.type}">${typeLabels[item.type] || item.type}</span>
        ${item.date ? `<span class="time-badge">${item.date}</span>` : ''}
      </div>
    `;
    box.appendChild(d);
  });
}

function render() {
  const st = allStats[currentAcc] || {};
  const state = allStates[currentAcc] || {};
  const p = st.profile || {};
  const s = st.summary || {};

  // Top title & sidebar user
  document.getElementById("top-title").textContent = currentAcc + " · @" + (p.username || "user");
  document.getElementById("sb-handle").textContent = "@" + (p.username || currentAcc);
  const fullName = ((p.first_name || "") + " " + (p.last_name || "")).trim() || "Shamsiddin";
  document.getElementById("sb-name").textContent = fullName;
  document.getElementById("sb-avatar").textContent = (p.first_name || "S")[0].toUpperCase();
  document.getElementById("acc-header-desc").textContent = fullName + " (@" + (p.username || "") + ") Telegram profili";
  document.getElementById("acc-phone").textContent = p.phone ? "+" + p.phone : "Mavjud emas";
  document.getElementById("acc-id").textContent = p.id || "-";

  const premPill = document.getElementById("acc-premium-pill");
  if (p.premium) {
    premPill.textContent = "★ Premium";
    premPill.classList.add("premium");
  } else {
    premPill.textContent = "Standart";
    premPill.classList.remove("premium");
  }

  // Metrics
  document.getElementById("m-priv").textContent = s.private_chats || 0;
  document.getElementById("m-groups").textContent = s.groups || 0;
  document.getElementById("m-channels").textContent = s.channels || 0;
  document.getElementById("m-bots").textContent = s.bots || 0;
  document.getElementById("m-unread").textContent = s.unread_messages || 0;

  document.getElementById("m-created-groups").textContent = (s.created_groups_count || 0) + " ta";
  document.getElementById("m-created-channels").textContent = (s.created_channels_count || 0) + " ta";
  document.getElementById("count-created-ch").textContent = (s.created_channels_count || 0) + " ta";
  document.getElementById("count-created-gr").textContent = (s.created_groups_count || 0) + " ta";
  document.getElementById("count-admin-chats").textContent = (s.admin_chats_count || (st.admin_chats ? st.admin_chats.length : 0)) + " ta";

  // Lists
  renderChannelsList(st.created_channels || []);
  renderGroupsList(st.created_groups || []);
  renderAdminList(st.admin_chats || []);
  renderRecentDialogs(st.recent_dialogs || []);

  // Automation toggles
  const togBox = document.getElementById("toggles-container");
  togBox.innerHTML = "";

  const icons = {
    autoreply: '<svg class="icon" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
    autodraft: '<svg class="icon" viewBox="0 0 24 24"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>',
    autoread: '<svg class="icon" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>',
    autoai: '<svg class="icon" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path></svg>'
  };

  FEATURES.forEach(([f, label, desc]) => {
    const tile = document.createElement("div");
    tile.className = "toggle-tile";
    const checked = !!state[f];

    tile.innerHTML = `
      <div class="tt-left">
        <div class="tt-icon-wrap">${icons[f] || ''}</div>
        <div>
          <div class="tt-name">${label}</div>
          <div class="tt-desc">${desc}</div>
        </div>
      </div>
      <label class="switch">
        <input type="checkbox" ${checked ? "checked" : ""} onchange="toggleFeature('${f}', this.checked, '${label}')">
        <span class="slider"></span>
      </label>
    `;
    togBox.appendChild(tile);
  });
}

async function toggleFeature(feat, val, label) {
  const auth = getAuth();
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get("token") || TOKEN;
  let q = urlToken ? "?token=" + encodeURIComponent(urlToken) : "";

  try {
    const res = await fetch("/api/toggle" + q, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(auth ? { "X-Userbot-Auth": auth } : {})
      },
      credentials: "same-origin",
      body: JSON.stringify({ account: currentAcc, feature: feat, value: val })
    });
    if (res.ok) {
      if (!allStates[currentAcc]) allStates[currentAcc] = {};
      allStates[currentAcc][feat] = val;
      render();
      showToast(label + (val ? " yoqildi" : " o'chirildi"));
    }
  } catch (e) {
    showToast("O'zgartirishda xato yuz berdi");
  }
}

const pinInputEl = document.getElementById("pin-input");
pinInputEl.addEventListener("input", function() {
  document.getElementById("login-err").textContent = "";
  if (this.value.length === 4) handleLogin(new Event("submit"));
});

// Auto-refresh silent polling every 30s
setInterval(() => {
  if (document.visibilityState === 'visible' && document.getElementById("login-overlay").style.display === "none") {
    refreshData();
  }
}, 30000);

refreshData();
</script>
</body>
</html>"""


def main():
    if not TOKEN:
        print("PANEL_TOKEN sozlanmagan (.env). Panel ishga tushmaydi.")
        raise SystemExit(1)
    app = web.Application()
    app.add_routes([
        web.get("/", index),
        web.get("/login", index),
        web.get("/dashboard", index),
        web.get("/panel", index),
        web.get("/favicon.ico", favicon),
        web.post("/api/login", api_login),
        web.post("/api/logout", api_logout),
        web.get("/api/state", api_state),
        web.get("/api/stats", api_stats),
        web.post("/api/refresh_stats", api_refresh_stats),
        web.post("/api/toggle", api_toggle),
    ])
    print(f"Web panel: http://{HOST}:{PORT}/?token=***")
    web.run_app(app, host=HOST, port=PORT, print=None)


if __name__ == "__main__":
    main()
