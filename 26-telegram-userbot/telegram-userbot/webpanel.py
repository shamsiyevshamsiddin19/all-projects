"""Userbot uchun Apple VisionOS uslubidagi zamonaviy web boshqaruv paneli.

Sozlamalarni (data/state_<acc>.json) va batafsil akkaunt/chat statistikalarini
(data/stats_<acc>.json) xavfsiz boshqarish.
Parol: 2501 (yoki .env dagi PANEL_PASSWORD / PANEL_TOKEN).
"""
import hashlib
import json
import os

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

ACCOUNTS = [
    ("acc1", "@shamsiyev_shamsiddin"),
    ("acc2", "@Shamsiyevshamsiddin"),
    ("acc3", "@scarpiont"),
]
FEATURES = [
    ("autoreply", "Avto-javob", "Gemini AI orqali intellektual tabiiy javob"),
    ("autodraft", "Qoralama (shaxsiy)", "Javobni yubormasdan qoralama (draft) qilib qo'yish"),
    ("autoread", "Avto-o'qish", "Kanal va guruhlarni avtomatik o'qilgan qilish"),
    ("autoai", "Yarim-avto taklif", "Kelgan xabarga AI javob taklifini tasdiqlash"),
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
    try:
        data = await req.json()
        pwd = str(data.get("password", "")).strip()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri so'rov"}, status=400)

    if pwd == PASSWORD or (TOKEN and pwd == TOKEN):
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
    return web.json_response({"ok": False, "error": "Parol noto'g'ri!"}, status=401)


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
<title>Shamsiyev · Userbot Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-dark: #07090e;
    --spatial-glass: rgba(28, 32, 45, 0.72);
    --spatial-card: rgba(22, 26, 38, 0.78);
    --spatial-card-hover: rgba(30, 35, 52, 0.85);
    --spatial-border: rgba(255, 255, 255, 0.12);
    --spatial-border-active: rgba(255, 255, 255, 0.28);
    --spatial-highlight: inset 0 1px 1px 0 rgba(255, 255, 255, 0.2);
    --accent-cyan: #38bdf8;
    --accent-blue: #0284c7;
    --accent-blue-glow: rgba(56, 189, 248, 0.4);
    --accent-green: #10b981;
    --accent-amber: #f59e0b;
    --accent-purple: #8b5cf6;
    --text-main: #ffffff;
    --text-sub: rgba(255, 255, 255, 0.72);
    --text-dim: rgba(255, 255, 255, 0.45);
    --radius-window: 28px;
    --radius-card: 20px;
    --radius-inner: 14px;
    --radius-pill: 999px;
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  body {
    margin: 0;
    min-height: 100vh;
    background-color: var(--bg-dark);
    background-image: 
      radial-gradient(at 0% 0%, rgba(14, 165, 233, 0.15) 0px, transparent 45%),
      radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.14) 0px, transparent 45%),
      radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.1) 0px, transparent 40%),
      url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.015'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    background-attachment: fixed;
    color: var(--text-main);
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    padding: 30px 18px 60px;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  /* SPATIAL CANVAS (VISION PRO SHELL) */
  .spatial-canvas {
    width: 100%;
    max-width: 1240px;
    background: var(--spatial-glass);
    backdrop-filter: blur(45px);
    -webkit-backdrop-filter: blur(45px);
    border: 1px solid var(--spatial-border);
    border-radius: var(--radius-window);
    box-shadow: 0 35px 80px -15px rgba(0, 0, 0, 0.8), var(--spatial-highlight);
    display: flex;
    min-height: 840px;
    overflow: hidden;
    position: relative;
  }

  /* LEFT FLOATING VERTICAL DOCK */
  .spatial-dock {
    width: 82px;
    background: rgba(14, 17, 26, 0.65);
    border-right: 1px solid var(--spatial-border);
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px 0 20px;
    gap: 16px;
    flex-shrink: 0;
  }
  .dock-btn {
    width: 46px;
    height: 46px;
    border-radius: 14px;
    background: transparent;
    border: 1px solid transparent;
    color: var(--text-dim);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    cursor: pointer;
    transition: all 0.22s cubic-bezier(0.2, 0.8, 0.2, 1);
  }
  .dock-btn:hover {
    color: var(--text-main);
    background: rgba(255, 255, 255, 0.08);
    border-color: var(--spatial-border);
  }
  .dock-btn.active {
    color: var(--accent-cyan);
    background: rgba(56, 189, 248, 0.16);
    border-color: rgba(56, 189, 248, 0.4);
    box-shadow: 0 0 16px var(--accent-blue-glow);
  }
  .dock-divider {
    width: 36px;
    height: 1px;
    background: var(--spatial-border);
    margin: 4px 0;
  }
  .dock-spacer { flex: 1; }
  .btn-power {
    color: #f87171 !important;
  }
  .btn-power:hover {
    background: rgba(239, 68, 68, 0.2) !important;
    border-color: rgba(239, 68, 68, 0.4) !important;
  }

  /* MAIN WORKSPACE */
  .spatial-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 24px 28px 30px;
    overflow-y: auto;
    overflow-x: hidden;
  }

  /* TOP NAVIGATION BAR */
  .spatial-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;
  }
  .account-tabs {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(14, 18, 28, 0.6);
    padding: 6px;
    border-radius: var(--radius-pill);
    border: 1px solid var(--spatial-border);
  }
  .tab-pill {
    padding: 8px 18px;
    border-radius: var(--radius-pill);
    font-size: 13px;
    font-weight: 600;
    color: var(--text-sub);
    background: transparent;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .tab-pill:hover {
    color: var(--text-main);
  }
  .tab-pill.active {
    background: rgba(255, 255, 255, 0.12);
    color: var(--text-main);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3), var(--spatial-highlight);
  }
  .tab-pill.active .pill-dot {
    background: var(--accent-cyan);
    box-shadow: 0 0 8px var(--accent-cyan);
  }
  .pill-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--text-dim);
  }

  .topbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .btn-round {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid var(--spatial-border);
    color: var(--text-main);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-round:hover {
    background: rgba(255, 255, 255, 0.14);
    transform: scale(1.05);
  }
  .user-badge {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid var(--spatial-border);
    padding: 4px 14px 4px 6px;
    border-radius: var(--radius-pill);
  }
  .user-badge-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #0284c7, #8b5cf6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
  }

  /* SPATIAL DASHBOARD GRID */
  .spatial-grid {
    display: grid;
    grid-template-columns: 280px 1fr 340px;
    grid-template-rows: auto auto auto;
    gap: 20px;
  }

  /* CARDS */
  .card {
    background: var(--spatial-card);
    backdrop-filter: blur(28px);
    -webkit-backdrop-filter: blur(28px);
    border: 1px solid var(--spatial-border);
    border-radius: var(--radius-card);
    padding: 20px;
    box-shadow: 0 16px 36px -8px rgba(0, 0, 0, 0.5), var(--spatial-highlight);
    position: relative;
    transition: all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
  }
  .card:hover {
    border-color: var(--spatial-border-active);
    transform: translateY(-2px);
  }
  .card-label {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  /* WIDGET 1: MEMBERS / AKKAUNTLAR */
  .members-card {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .avatar-stack {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
  }
  .stack-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid #141724;
    background: linear-gradient(135deg, #38bdf8, #2563eb);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
    margin-right: -10px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
    cursor: pointer;
    transition: transform 0.2s;
  }
  .stack-avatar:hover { transform: translateY(-3px) scale(1.1); z-index: 10; }
  .stack-avatar.a2 { background: linear-gradient(135deg, #8b5cf6, #ec4899); }
  .stack-avatar.a3 { background: linear-gradient(135deg, #10b981, #06b6d4); }
  .stack-more {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid #141724;
    background: rgba(255, 255, 255, 0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    color: var(--text-sub);
  }
  .profile-details {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: var(--radius-inner);
    padding: 12px 14px;
  }
  .p-name { font-size: 15px; font-weight: 700; margin-bottom: 2px; }
  .p-user { font-size: 13px; color: var(--accent-cyan); font-family: 'JetBrains Mono', monospace; }
  .p-meta { font-size: 12px; color: var(--text-dim); margin-top: 6px; display: flex; justify-content: space-between; }

  /* WIDGET 2: THERMOSTAT GAUGE */
  .gauge-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .gauge-container {
    position: relative;
    width: 170px;
    height: 170px;
    margin: 8px 0 16px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .gauge-svg {
    transform: rotate(-90deg);
  }
  .gauge-bg {
    stroke: rgba(255, 255, 255, 0.08);
    stroke-width: 10;
    fill: none;
  }
  .gauge-bar {
    stroke: url(#gauge-gradient);
    stroke-width: 10;
    stroke-linecap: round;
    fill: none;
    stroke-dasharray: 440;
    stroke-dashoffset: 140;
    transition: stroke-dashoffset 0.8s ease;
  }
  .gauge-content {
    position: absolute;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .gauge-val {
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -0.02em;
    font-family: 'JetBrains Mono', monospace;
  }
  .gauge-sub {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .gauge-btn-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    width: 100%;
  }
  .g-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--spatial-border);
    border-radius: 12px;
    padding: 8px 4px;
    color: var(--text-sub);
    font-size: 11px;
    font-weight: 600;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .g-btn:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
  .g-btn.on { background: rgba(56, 189, 248, 0.18); border-color: rgba(56, 189, 248, 0.4); color: var(--accent-cyan); }

  /* WIDGET 3: ACTIVITY WAVE CHART */
  .wave-card {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .wave-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .wave-title-big {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.02em;
    display: flex;
    align-items: baseline;
    gap: 8px;
  }
  .wave-title-big span { font-size: 14px; font-weight: 500; color: var(--text-dim); }
  .wave-svg { width: 100%; height: 85px; margin: 10px 0; }
  .wave-pill-group {
    display: flex;
    gap: 6px;
    background: rgba(255, 255, 255, 0.05);
    padding: 3px;
    border-radius: var(--radius-pill);
  }
  .wave-pill {
    padding: 4px 10px;
    border-radius: var(--radius-pill);
    font-size: 11px;
    font-weight: 600;
    color: var(--text-dim);
    background: transparent;
    border: none;
    cursor: pointer;
  }
  .wave-pill.active { background: rgba(255, 255, 255, 0.15); color: #fff; }
  .wave-bottom-chips {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--text-dim);
    padding-top: 6px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
  }

  /* WIDGET 4: SECURITY DOORS (DUAL LOCKS) */
  .dual-doors {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
  }
  .door-mini {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--spatial-border);
    border-radius: var(--radius-inner);
    padding: 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 100px;
  }
  .door-icon {
    font-size: 22px;
    margin-bottom: 6px;
  }
  .door-label { font-size: 13px; font-weight: 700; color: #fff; }
  .door-status { font-size: 11px; color: var(--accent-green); font-weight: 600; }

  /* WIDGET 5: ENERGY BAR CHART (XABARLAR STATISTIKASI) */
  .bar-chart-card {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .bar-chart {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    height: 110px;
    padding: 10px 0 4px;
    gap: 8px;
  }
  .bar-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    height: 100%;
    justify-content: flex-end;
  }
  .bar-stick {
    width: 14px;
    background: rgba(255, 255, 255, 0.12);
    border-radius: 999px;
    transition: height 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
  }
  .bar-col.active .bar-stick {
    background: var(--accent-cyan);
    box-shadow: 0 0 16px var(--accent-blue-glow);
  }
  .bar-day { font-size: 11px; color: var(--text-dim); }

  /* WIDGET 6: CHATLAR & AUDITORIYA (DETAILED BREAKDOWN) */
  .chats-hero-card {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    background: rgba(24, 28, 42, 0.8);
  }
  .chat-stat-box {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-inner);
    padding: 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.2s;
  }
  .chat-stat-box:hover {
    background: rgba(255, 255, 255, 0.06);
    border-color: var(--accent-cyan);
  }
  .cs-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  .cs-icon { font-size: 24px; }
  .cs-badge {
    font-size: 11px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-sub);
  }
  .cs-num {
    font-size: 28px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.02em;
    color: #fff;
  }
  .cs-desc { font-size: 12px; color: var(--text-dim); }
  .cs-owner {
    font-size: 11px;
    color: var(--accent-cyan);
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    font-weight: 600;
  }

  /* LIST OF CREATED CHANNELS & GROUPS */
  .ownership-section {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  .owner-list-box {
    max-height: 240px;
    overflow-y: auto;
    padding-right: 6px;
  }
  .owner-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    background: rgba(255, 255, 255, 0.025);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    margin-bottom: 8px;
    transition: all 0.15s;
  }
  .owner-item:hover {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(56, 189, 248, 0.3);
  }
  .oi-title { font-weight: 600; font-size: 13px; color: #f1f5f9; }
  .oi-tag { font-size: 11px; color: var(--accent-cyan); background: rgba(56, 189, 248, 0.12); padding: 2px 6px; border-radius: 6px; }

  /* WIDGET 7: RIGHT TOGGLE CARDS (LIGHT, STEREO, MONITORING, TV IN REFERENCE) */
  .controls-sidebar {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .toggle-card {
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid var(--spatial-border);
    border-radius: var(--radius-inner);
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.25s;
  }
  .toggle-card:hover {
    background: rgba(255, 255, 255, 0.06);
    border-color: var(--spatial-border-active);
  }
  .tc-left { display: flex; align-items: center; gap: 12px; }
  .tc-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
  }
  .tc-name { font-size: 14px; font-weight: 600; color: #fff; }
  .tc-desc { font-size: 11px; color: var(--text-dim); }

  /* SWITCH TOGGLE */
  .sw { position: relative; width: 48px; height: 28px; flex: 0 0 auto; }
  .sw input { opacity: 0; width: 0; height: 0; }
  .sl {
    position: absolute; inset: 0;
    background: rgba(255, 255, 255, 0.12);
    border-radius: 999px;
    transition: all 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
    cursor: pointer;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  .sl:before {
    content: ""; position: absolute;
    width: 22px; height: 22px; left: 2px; top: 2px;
    background: #ffffff; border-radius: 50%;
    transition: all 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  }
  input:checked + .sl {
    background: var(--accent-cyan);
    border-color: rgba(56, 189, 248, 0.8);
    box-shadow: 0 0 16px var(--accent-blue-glow);
  }
  input:checked + .sl:before {
    transform: translateX(20px);
  }

  /* WIDGET 8: MEDIA PLAYER STYLE (COFFIN IN IMAGE) */
  .player-card {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .player-top { display: flex; align-items: center; gap: 12px; }
  .player-art {
    width: 44px; height: 44px; border-radius: 10px;
    background: linear-gradient(135deg, #0284c7, #6366f1);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
  }
  .player-track { font-size: 13px; font-weight: 700; color: #fff; }
  .player-artist { font-size: 11px; color: var(--text-dim); }
  .player-bar {
    width: 100%; height: 4px; background: rgba(255, 255, 255, 0.1);
    border-radius: 999px; margin: 14px 0 6px; overflow: hidden;
  }
  .player-prog { width: 68%; height: 100%; background: var(--accent-cyan); box-shadow: 0 0 10px var(--accent-cyan); }
  .player-controls {
    display: flex; align-items: center; justify-content: space-between;
    font-size: 14px; color: var(--text-sub);
  }
  .btn-play {
    width: 32px; height: 32px; border-radius: 50%;
    background: #fff; color: #000;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
  }

  /* LOGIN MODAL */
  #login-overlay {
    position: fixed; inset: 0;
    background: rgba(7, 9, 14, 0.82);
    backdrop-filter: blur(45px); -webkit-backdrop-filter: blur(45px);
    display: none; align-items: center; justify-content: center;
    padding: 20px; z-index: 2000;
  }
  .login-card {
    background: rgba(26, 30, 44, 0.88);
    border: 1px solid var(--spatial-border);
    border-radius: 26px; padding: 40px 32px;
    width: 100%; max-width: 370px; text-align: center;
    box-shadow: 0 35px 70px rgba(0, 0, 0, 0.8), 0 0 40px var(--accent-blue-glow);
  }
  .lock-circle {
    width: 60px; height: 60px; border-radius: 18px;
    background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; margin: 0 auto 16px;
    border: 1px solid rgba(56, 189, 248, 0.3);
  }
  .pin-input {
    width: 100%; background: rgba(0, 0, 0, 0.4);
    border: 1px solid var(--spatial-border); border-radius: 14px;
    color: #fff; font-size: 26px; letter-spacing: 12px;
    text-align: center; padding: 14px; margin-bottom: 20px;
    outline: none; font-family: 'JetBrains Mono', monospace;
  }
  .pin-input:focus { border-color: var(--accent-cyan); box-shadow: 0 0 16px var(--accent-blue-glow); }
  .btn-submit {
    width: 100%; background: linear-gradient(135deg, #0284c7, #38bdf8);
    border: none; border-radius: 14px; color: #fff;
    font-size: 15px; font-weight: 700; padding: 14px; cursor: pointer;
    box-shadow: 0 6px 20px rgba(2, 132, 199, 0.4);
  }
  .shake { animation: shake 0.4s ease-in-out; }
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-8px); }
    40%, 80% { transform: translateX(8px); }
  }

  /* TOAST */
  .toast {
    position: fixed; left: 50%; bottom: 28px;
    transform: translateX(-50%) translateY(20px);
    background: rgba(28, 32, 45, 0.95);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    color: #fff; border: 1px solid var(--spatial-border);
    padding: 12px 24px; border-radius: var(--radius-pill);
    font-size: 13px; font-weight: 600; opacity: 0;
    transition: all 0.25s; pointer-events: none; z-index: 3000;
  }
  .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

  /* RESPONSIVE */
  @media (max-width: 1100px) {
    .spatial-grid { grid-template-columns: 1fr 1fr; }
    .chats-hero-card { grid-template-columns: 1fr 1fr; }
    .ownership-section { grid-template-columns: 1fr; }
  }
  @media (max-width: 768px) {
    body { padding: 10px; }
    .spatial-canvas { flex-direction: column; }
    .spatial-dock { width: 100%; height: 60px; flex-direction: row; border-right: none; border-bottom: 1px solid var(--spatial-border); padding: 0 16px; }
    .spatial-grid { grid-template-columns: 1fr; }
    .chats-hero-card { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<div class="spatial-canvas">
  <!-- LEFT FLOATING DOCK -->
  <div class="spatial-dock">
    <button class="dock-btn active" onclick="switchView('overview')" title="Dashboard">🏠</button>
    <button class="dock-btn" onclick="switchView('chats')" title="Chatlar va Auditoriya">💬</button>
    <button class="dock-btn" onclick="switchView('toggles')" title="Userbot Rejimlari">🎛</button>
    <button class="dock-btn" onclick="switchView('analytics')" title="Statistika">📊</button>
    <div class="dock-divider"></div>
    <button class="dock-btn" onclick="refreshData()" title="Yangilash">🔄</button>
    <div class="dock-spacer"></div>
    <button class="dock-btn btn-power" onclick="logout()" title="Panelni qulflash">🔒</button>
  </div>

  <!-- MAIN WORKSPACE -->
  <div class="spatial-body">
    <!-- TOP BAR -->
    <div class="spatial-topbar">
      <div class="account-tabs">
        <button class="tab-pill active" onclick="selectAcc('acc1')" id="tab-acc1">
          <span class="pill-dot"></span> acc1 · @shamsiyev_shamsiddin
        </button>
        <button class="tab-pill" onclick="selectAcc('acc2')" id="tab-acc2">
          <span class="pill-dot"></span> acc2 · @Shamsiyevshamsiddin
        </button>
        <button class="tab-pill" onclick="selectAcc('acc3')" id="tab-acc3">
          <span class="pill-dot"></span> acc3 · @scarpiont
        </button>
      </div>

      <div class="topbar-right">
        <button class="btn-round" onclick="refreshData()" title="Ma'lumotlarni yangilash">⚡</button>
        <div class="user-badge">
          <div class="user-badge-avatar" id="avatar-circle">SS</div>
          <span id="badge-name" style="font-weight: 600;">Shamsiddin</span>
        </div>
      </div>
    </div>

    <!-- SPATIAL DASHBOARD GRID -->
    <div class="spatial-grid">
      <!-- 1. MEMBERS / AKKAUNT CARD -->
      <div class="card members-card">
        <div class="card-label">Akkaunt Profili <span style="color:var(--accent-cyan);">● Faol</span></div>
        <div class="avatar-stack">
          <div class="stack-avatar" onclick="selectAcc('acc1')" title="acc1">1</div>
          <div class="stack-avatar a2" onclick="selectAcc('acc2')" title="acc2">2</div>
          <div class="stack-avatar a3" onclick="selectAcc('acc3')" title="acc3">3</div>
          <div class="stack-more">+3</div>
        </div>
        <div class="profile-details">
          <div class="p-name" id="prof-name">Yuklanmoqda…</div>
          <div class="p-user" id="prof-user">@username</div>
          <div class="p-meta">
            <span>Tel: <strong id="prof-phone">-</strong></span>
            <span>ID: <strong id="prof-id">-</strong></span>
          </div>
        </div>
      </div>

      <!-- 2. ACTIVITY WAVE CHART -->
      <div class="card wave-card">
        <div class="wave-head">
          <div>
            <div class="card-label">Bugungi Faollik</div>
            <div class="wave-title-big"><span id="wave-total">300+</span> <span>chat faol</span></div>
          </div>
          <div class="wave-pill-group">
            <button class="wave-pill active">Bugun</button>
            <button class="wave-pill">Hafta</button>
          </div>
        </div>
        <svg class="wave-svg" viewBox="0 0 300 70">
          <defs>
            <linearGradient id="wave-grad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.5"/>
              <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.0"/>
            </linearGradient>
          </defs>
          <path d="M0,45 Q40,15 80,35 T160,20 T240,40 T300,10 L300,70 L0,70 Z" fill="url(#wave-grad)"/>
          <path d="M0,45 Q40,15 80,35 T160,20 T240,40 T300,10" fill="none" stroke="#38bdf8" stroke-width="3" stroke-linecap="round"/>
        </svg>
        <div class="wave-bottom-chips">
          <span>AI Javoblari: <strong style="color:#fff;" id="wave-ai">Faol</strong></span>
          <span>Kechikish: <strong style="color:var(--accent-cyan);">2.4s</strong></span>
          <span>Holat: <strong style="color:var(--accent-green);">Optimal</strong></span>
        </div>
      </div>

      <!-- 3. THERMOSTAT CIRCULAR GAUGE -->
      <div class="card gauge-card">
        <div class="card-label" style="width:100%;">Tizim Yuklamasi & Holati</div>
        <div class="gauge-container">
          <svg class="gauge-svg" width="160" height="160" viewBox="0 0 160 160">
            <defs>
              <linearGradient id="gauge-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#38bdf8"/>
                <stop offset="100%" stop-color="#0284c7"/>
              </linearGradient>
            </defs>
            <circle class="gauge-bg" cx="80" cy="80" r="68"/>
            <circle class="gauge-bar" id="gauge-arc" cx="80" cy="80" r="68"/>
          </svg>
          <div class="gauge-content">
            <div class="gauge-val" id="gauge-num">98%</div>
            <div class="gauge-sub">Uptime</div>
          </div>
        </div>
        <div class="gauge-btn-row">
          <div class="g-btn on" id="g-reply"><span>🤖</span>Avto</div>
          <div class="g-btn" id="g-draft"><span>✍️</span>Draft</div>
          <div class="g-btn on" id="g-read"><span>👁</span>Read</div>
          <div class="g-btn" id="g-ai"><span>📝</span>Taklif</div>
        </div>
      </div>

      <!-- 4. CHATLAR & AUDITORIYA (HERO BREAKDOWN) -->
      <div class="card chats-hero-card">
        <div class="chat-stat-box">
          <div class="cs-top">
            <span class="cs-icon">👤</span>
            <span class="cs-badge">Shaxsiy</span>
          </div>
          <div class="cs-num" id="stat-priv">0</div>
          <div class="cs-desc">Muloqotdagi odamlar</div>
          <div class="cs-owner">Yozishmalar faol</div>
        </div>

        <div class="chat-stat-box">
          <div class="cs-top">
            <span class="cs-icon">👥</span>
            <span class="cs-badge">Guruhlar</span>
          </div>
          <div class="cs-num" id="stat-groups">0</div>
          <div class="cs-desc">A'zo bo'lingan guruhlar</div>
          <div class="cs-owner" id="owner-groups-count">Men ochgan: 0 ta</div>
        </div>

        <div class="chat-stat-box">
          <div class="cs-top">
            <span class="cs-icon">📢</span>
            <span class="cs-badge">Kanallar</span>
          </div>
          <div class="cs-num" id="stat-channels">0</div>
          <div class="cs-desc">A'zo bo'lingan kanallar</div>
          <div class="cs-owner" id="owner-channels-count">Men ochgan: 0 ta</div>
        </div>

        <div class="chat-stat-box">
          <div class="cs-top">
            <span class="cs-icon">🤖</span>
            <span class="cs-badge">Botlar</span>
          </div>
          <div class="cs-num" id="stat-bots">0</div>
          <div class="cs-desc">Ulangan Telegram botlar</div>
          <div class="cs-owner">O'qilmagan: <span id="stat-unread">0</span></div>
        </div>
      </div>

      <!-- 5. OCHILGAN KANALLAR VA GURUHLAR RO'YXATI -->
      <div class="card ownership-section">
        <div>
          <div class="card-label">📢 Men Ochgan Kanallar (<span id="count-ch">0</span>)</div>
          <div class="owner-list-box" id="list-channels">
            <div style="color:var(--text-dim); padding:10px;">Yuklanmoqda…</div>
          </div>
        </div>
        <div>
          <div class="card-label">👥 Men Ochgan Guruhlar (<span id="count-gr">0</span>)</div>
          <div class="owner-list-box" id="list-groups">
            <div style="color:var(--text-dim); padding:10px;">Yuklanmoqda…</div>
          </div>
        </div>
      </div>

      <!-- 6. SECURITY DUAL LOCKS -->
      <div class="card dual-doors">
        <div class="door-mini">
          <div>
            <div class="door-icon">🛡</div>
            <div class="door-label">Anti-Ban Filter</div>
          </div>
          <div class="door-status">Cheklov: 15 / 60s</div>
        </div>
        <div class="door-mini">
          <div>
            <div class="door-icon">⏰</div>
            <div class="door-label">Ish Vaqti Rejimi</div>
          </div>
          <div class="door-status">08:00 – 24:00 (UTC+5)</div>
        </div>
      </div>

      <!-- 7. BAR CHART WIDGET -->
      <div class="card bar-chart-card">
        <div class="card-label">Haftalik Xabarlar Taqvimi</div>
        <div class="bar-chart">
          <div class="bar-col"><div class="bar-stick" style="height: 45%;"></div><div class="bar-day">Du</div></div>
          <div class="bar-col"><div class="bar-stick" style="height: 65%;"></div><div class="bar-day">Se</div></div>
          <div class="bar-col active"><div class="bar-stick" style="height: 90%;"></div><div class="bar-day">Ch</div></div>
          <div class="bar-col"><div class="bar-stick" style="height: 70%;"></div><div class="bar-day">Pa</div></div>
          <div class="bar-col"><div class="bar-stick" style="height: 55%;"></div><div class="bar-day">Ju</div></div>
          <div class="bar-col"><div class="bar-stick" style="height: 80%;"></div><div class="bar-day">Sh</div></div>
          <div class="bar-col"><div class="bar-stick" style="height: 60%;"></div><div class="bar-day">Ya</div></div>
        </div>
      </div>

      <!-- 8. CONTROLS TOGGLES (LIGHT/STEREO STYLE) -->
      <div class="card controls-sidebar">
        <div class="card-label">Userbot Rejimlari</div>
        <div id="toggles-box">
          <!-- Dinamik toggllar -->
        </div>
      </div>
    </div>
  </div>
</div>

<!-- PIN MODAL -->
<div id="login-overlay">
  <div class="login-card" id="login-box">
    <div class="lock-circle">🔐</div>
    <h2 style="margin:0 0 8px; font-size:22px; font-weight:700;">Shamsiyev Studio</h2>
    <p style="color:var(--text-sub); font-size:13px; margin:0 0 24px;">VisionOS paneliga kirish uchun PIN kodni kiriting</p>
    <form onsubmit="handleLogin(event)">
      <input type="password" id="pin-input" class="pin-input" placeholder="••••" maxlength="10" inputmode="numeric" pattern="[0-9]*" autofocus autocomplete="off">
      <button type="submit" class="btn-submit">Panelga Kirish</button>
    </form>
    <div id="login-err" style="color:#f87171; font-size:13px; margin-top:12px; min-height:18px;"></div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const TOKEN = "__TOKEN__";
let currentAcc = "acc1";
let allStats = {};
let allStates = {};

const FEATURES = [
  ["autoreply", "Avto-javob", "Gemini AI intellektual javob"],
  ["autodraft", "Qoralama (Draft)", "Javobni qoralama qilib qo'yish"],
  ["autoread", "Avto-o'qish", "Kanal/guruhlarni avto-o'qish"],
  ["autoai", "Yarim-avto taklif", "Xabarga taklif tayyorlash"]
];

function showToast(text) {
  const t = document.getElementById("toast");
  t.textContent = text;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 1600);
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

async function handleLogin(e) {
  e.preventDefault();
  const pwd = document.getElementById("pin-input").value.trim();
  if (!pwd) return;

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: pwd })
    });
    const d = await res.json();
    if (res.ok && d.ok) {
      if (d.auth) localStorage.setItem("userbot_auth", d.auth);
      hideLogin();
      showToast("Xush kelibsiz! 👋");
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
  await fetch("/api/logout", { method: "POST" });
  localStorage.removeItem("userbot_auth");
  showToast("Panel qulflandi 🔒");
  showLogin();
}

function selectAcc(acc) {
  currentAcc = acc;
  document.querySelectorAll(".tab-pill").forEach(el => el.classList.remove("active"));
  const tab = document.getElementById("tab-" + acc);
  if (tab) tab.classList.add("active");
  render();
}

function switchView(view) {
  showToast("Bo'lim: " + view);
}

async function refreshData() {
  const auth = getAuth();
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get("token") || TOKEN;
  let q = urlToken ? "?token=" + encodeURIComponent(urlToken) : "";

  try {
    const [resState, resStats] = await Promise.all([
      fetch("/api/state" + q, { headers: auth ? { "X-Userbot-Auth": auth } : {} }),
      fetch("/api/stats" + q, { headers: auth ? { "X-Userbot-Auth": auth } : {} })
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

function render() {
  const st = allStats[currentAcc] || {};
  const state = allStates[currentAcc] || {};
  const p = st.profile || {};
  const s = st.summary || {};

  // Profile details
  document.getElementById("prof-name").textContent = (p.first_name || "") + " " + (p.last_name || "");
  document.getElementById("prof-user").textContent = "@" + (p.username || "noma'lum");
  document.getElementById("prof-phone").textContent = p.phone ? "+" + p.phone : "-";
  document.getElementById("prof-id").textContent = p.id || "-";
  document.getElementById("badge-name").textContent = p.first_name || "Shamsiddin";
  document.getElementById("avatar-circle").textContent = (p.first_name || "S")[0].toUpperCase();

  // Summary counts
  document.getElementById("stat-priv").textContent = s.private_chats || 0;
  document.getElementById("stat-groups").textContent = s.groups || 0;
  document.getElementById("stat-channels").textContent = s.channels || 0;
  document.getElementById("stat-bots").textContent = s.bots || 0;
  document.getElementById("stat-unread").textContent = s.unread_messages || 0;
  document.getElementById("wave-total").textContent = (s.total_chats || 0) + "+";

  document.getElementById("owner-groups-count").textContent = "Men ochgan: " + (s.created_groups_count || 0) + " ta";
  document.getElementById("owner-channels-count").textContent = "Men ochgan: " + (s.created_channels_count || 0) + " ta";
  document.getElementById("count-ch").textContent = s.created_channels_count || 0;
  document.getElementById("count-gr").textContent = s.created_groups_count || 0;

  // Channels list
  const chBox = document.getElementById("list-channels");
  chBox.innerHTML = "";
  const createdCh = st.created_channels || [];
  if (createdCh.length === 0) {
    chBox.innerHTML = '<div style="color:var(--text-dim); padding:10px;">Kanal topilmadi</div>';
  } else {
    createdCh.forEach(ch => {
      const d = document.createElement("div");
      d.className = "owner-item";
      d.innerHTML = `<span class="oi-title">📢 ${ch.title}</span><span class="oi-tag">Egasi</span>`;
      chBox.appendChild(d);
    });
  }

  // Groups list
  const grBox = document.getElementById("list-groups");
  grBox.innerHTML = "";
  const createdGr = st.created_groups || [];
  if (createdGr.length === 0) {
    grBox.innerHTML = '<div style="color:var(--text-dim); padding:10px;">Guruh topilmadi</div>';
  } else {
    createdGr.forEach(gr => {
      const d = document.createElement("div");
      d.className = "owner-item";
      d.innerHTML = `<span class="oi-title">👥 ${gr.title}</span><span class="oi-tag">Egasi</span>`;
      grBox.appendChild(d);
    });
  }

  // Right switches (Toggles)
  const togBox = document.getElementById("toggles-box");
  togBox.innerHTML = "";
  FEATURES.forEach(([f, label, desc]) => {
    const card = document.createElement("div");
    card.className = "toggle-card";
    const checked = !!state[f];

    card.innerHTML = `
      <div class="tc-left">
        <div class="tc-icon">${f === 'autoreply' ? '🤖' : (f === 'autodraft' ? '✍️' : (f === 'autoread' ? '👁' : '📝'))}</div>
        <div>
          <div class="tc-name">${label}</div>
          <div class="tc-desc">${desc}</div>
        </div>
      </div>
      <label class="sw">
        <input type="checkbox" ${checked ? "checked" : ""} onchange="toggleFeature('${f}', this.checked, '${label}')">
        <span class="sl"></span>
      </label>
    `;
    togBox.appendChild(card);
  });

  // Gauge quick buttons state
  document.getElementById("g-reply").className = "g-btn " + (state.autoreply ? "on" : "");
  document.getElementById("g-draft").className = "g-btn " + (state.autodraft ? "on" : "");
  document.getElementById("g-read").className = "g-btn " + (state.autoread ? "on" : "");
  document.getElementById("g-ai").className = "g-btn " + (state.autoai ? "on" : "");
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
      body: JSON.stringify({ account: currentAcc, feature: feat, value: val })
    });
    if (res.ok) {
      if (!allStates[currentAcc]) allStates[currentAcc] = {};
      allStates[currentAcc][feat] = val;
      render();
      showToast(label + (val ? " yoqildi 🟢" : " o'chirildi ⚪️"));
    }
  } catch (e) {
    showToast("Tarmoq xatosi ❌");
  }
}

document.getElementById("pin-input").addEventListener("input", function() {
  if (this.value.length === 4) handleLogin(new Event("submit"));
});

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
        web.post("/api/login", api_login),
        web.post("/api/logout", api_logout),
        web.get("/api/state", api_state),
        web.get("/api/stats", api_stats),
        web.post("/api/toggle", api_toggle),
    ])
    print(f"Web panel: http://{HOST}:{PORT}/?token=***")
    web.run_app(app, host=HOST, port=PORT, print=None)


if __name__ == "__main__":
    main()
