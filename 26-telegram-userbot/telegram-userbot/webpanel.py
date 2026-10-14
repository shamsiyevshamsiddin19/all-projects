"""Userbot uchun ChatGPT / Linear uslubidagi professional boshqaruv paneli.

Zamonaviy minimalist dark interfeys, san'at darajasidagi chap panel (Sidebar),
alohida modulli ko'rinishlar (Dashboard, Kanallarim, Guruhlarim, Admin Chatlar, Suhbatlar, AI Rejimlari, Server),
to'liq SVG vektor ikonkalari (hech qanday xom emojilarsiz), brute-force himoyasi,
qidiruv-filtr, 100% mobil va barcha ekranlarga moslashuvchan.
Parol: 2501 (yoki .env dagi PANEL_PASSWORD / PANEL_TOKEN).
"""
import hashlib
import json
import os
import re
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
    ("autoreply", "Avto-javob", "Gemini AI yordamida shaxsiy chatlarda intellektual va tabiiy javob"),
    ("autodraft", "Qoralama (Draft)", "Javobni to'g'ridan-to'g'ri yubormasdan qoralama qilib saqlash"),
    ("autoread", "Avto-o'qish", "Kanallar va guruhlarni fon rejimida avtomatik o'qilgan qilish"),
    ("autoai", "Yarim-avto taklif", "Kelgan xabarga AI taklifini ko'rib chiqib tasdiqlash"),
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


def read_progress(acc):
    pfile = os.path.join(DATA, f"progress_{acc}.json")
    if os.path.exists(pfile):
        try:
            with open(pfile, encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            pass
    return {"status": "done", "percent": 100, "current": 0}


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
                "admin_chats": [],
                "recent_dialogs": [],
            }
        st["progress"] = read_progress(acc)
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
            prog_file = os.path.join(DATA, f"progress_{acc}.json")
            try:
                with open(prog_file, "w", encoding="utf-8") as pf:
                    json.dump({"status": "collecting", "percent": 5, "current": 0, "updated_at": time.time()}, pf)
            except Exception:  # noqa: BLE001
                pass
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


async def api_avatar(req):
    chat_id = req.match_info.get("id", "").strip()
    if not chat_id or not re.match(r"^-?[0-9a-zA-Z_]+$", chat_id):
        return web.Response(status=400)

    # Agar chat_id acc1/acc2/acc3 bo'lsa, profil ID sini topamiz
    if chat_id in ACC_KEYS:
        st = read_stats(chat_id)
        if st and st.get("profile", {}).get("id"):
            chat_id = str(st["profile"]["id"])

    file_path = os.path.join(DATA, "avatars", f"{chat_id}.jpg")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return web.FileResponse(
            file_path,
            headers={
                "Cache-Control": "public, max-age=604800, immutable",
                "Content-Type": "image/jpeg",
            },
        )
    return web.Response(status=204)


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


def load_page():
    html_path = os.path.join(BASE, "index.html")
    if os.path.exists(html_path):
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:  # noqa: BLE001
            pass
    return "<!doctype html><html><body><h1>Userbot Studio</h1><p>index.html yuklanmadi</p></body></html>"


async def index(req):
    content = load_page().replace("__TOKEN__", TOKEN)
    resp = web.Response(text=content, content_type="text/html")
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
        web.get("/api/avatar/{id}", api_avatar),
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
