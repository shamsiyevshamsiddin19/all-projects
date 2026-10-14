"""Userbot uchun Apple VisionOS uslubidagi zamonaviy web boshqaruv paneli.

Sozlamalarni (data/state_<acc>.json) brauzer orqali xavfsiz boshqarish.
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


def read_state(acc):
    try:
        with open(_sfile(acc), encoding="utf-8") as f:
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
    # Agar to'g'ri token bilan kelsa, sessiya cookie-ni avtomatik o'rnatamiz
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
<title>Userbot Boshqaruv Paneli</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-dark: #0b0d14;
    --glass-bg: rgba(26, 31, 46, 0.65);
    --glass-inner: rgba(255, 255, 255, 0.04);
    --border-glass: rgba(255, 255, 255, 0.12);
    --border-glass-hover: rgba(255, 255, 255, 0.22);
    --text-primary: #ffffff;
    --text-secondary: rgba(255, 255, 255, 0.65);
    --text-muted: rgba(255, 255, 255, 0.4);
    --accent-blue: #0ea5e9;
    --accent-glow: rgba(14, 165, 233, 0.4);
    --accent-green: #10b981;
    --shadow-spatial: 0 24px 48px -12px rgba(0, 0, 0, 0.6), inset 0 1px 1px 0 rgba(255, 255, 255, 0.15);
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  body {
    margin: 0;
    min-height: 100vh;
    background-color: var(--bg-dark);
    background-image: 
      radial-gradient(at 0% 0%, rgba(14, 165, 233, 0.15) 0px, transparent 50%),
      radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
      radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.1) 0px, transparent 50%);
    background-attachment: fixed;
    color: var(--text-primary);
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 15px;
    line-height: 1.5;
    display: flex;
    justify-content: center;
    align-items: flex-start;
  }
  .wrap {
    width: 100%;
    max-width: 520px;
    padding: 36px 18px 80px;
    margin: 0 auto;
  }

  /* HEADER - VisionOS Bar */
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding: 14px 18px;
    background: var(--glass-bg);
    backdrop-filter: blur(32px);
    -webkit-backdrop-filter: blur(32px);
    border: 1px solid var(--border-glass);
    border-radius: 20px;
    box-shadow: var(--shadow-spatial);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .bot-icon {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.8), rgba(99, 102, 241, 0.8));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: 0 4px 14px rgba(14, 165, 233, 0.3);
  }
  .brand-title {
    font-size: 16px;
    font-weight: 700;
    letter-spacing: -0.01em;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    background: rgba(16, 185, 129, 0.16);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
  }
  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 8px #10b981;
  }
  .brand-sub {
    font-size: 12px;
    color: var(--text-muted);
  }
  .btn-lock {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid var(--border-glass);
    color: var(--text-secondary);
    border-radius: 12px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .btn-lock:hover {
    background: rgba(239, 68, 68, 0.18);
    color: #f87171;
    border-color: rgba(239, 68, 68, 0.35);
  }

  /* ACCORDION CARDS - Vision Pro Glass Card */
  .acc-card {
    background: var(--glass-bg);
    backdrop-filter: blur(32px);
    -webkit-backdrop-filter: blur(32px);
    border: 1px solid var(--border-glass);
    border-radius: 22px;
    margin-bottom: 20px;
    overflow: hidden;
    box-shadow: var(--shadow-spatial);
    transition: border-color 0.25s, transform 0.25s;
  }
  .acc-card:hover {
    border-color: var(--border-glass-hover);
  }
  .acc-head {
    padding: 15px 20px;
    background: var(--glass-inner);
    border-bottom: 1px solid var(--border-glass);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .acc-tag {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 3px 9px;
    border-radius: 8px;
    background: rgba(14, 165, 233, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(14, 165, 233, 0.3);
  }
  .acc-name {
    font-weight: 600;
    font-size: 14px;
    color: #f1f5f9;
  }

  /* ROWS */
  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    transition: background 0.2s;
  }
  .row:last-child {
    border-bottom: none;
  }
  .row:hover {
    background: rgba(255, 255, 255, 0.03);
  }
  .feat-info {
    flex: 1;
    padding-right: 16px;
  }
  .feat-title {
    font-size: 15px;
    font-weight: 600;
    color: #f8fafc;
    margin-bottom: 2px;
  }
  .feat-desc {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.35;
  }

  /* SWITCH TOGGLE - Apple VisionOS style */
  .sw {
    position: relative;
    width: 50px;
    height: 30px;
    flex: 0 0 auto;
  }
  .sw input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  .sl {
    position: absolute;
    inset: 0;
    background: rgba(255, 255, 255, 0.12);
    border-radius: 999px;
    transition: all 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
    cursor: pointer;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  .sl:before {
    content: "";
    position: absolute;
    width: 24px;
    height: 24px;
    left: 2px;
    top: 2px;
    background: #ffffff;
    border-radius: 50%;
    transition: all 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  }
  input:checked + .sl {
    background: var(--accent-blue);
    border-color: rgba(14, 165, 233, 0.8);
    box-shadow: 0 0 16px var(--accent-glow);
  }
  input:checked + .sl:before {
    transform: translateX(20px);
    background: #ffffff;
  }

  /* LOGIN MODAL - VisionOS Spatial Card */
  #login-overlay {
    position: fixed;
    inset: 0;
    background: rgba(9, 10, 15, 0.75);
    backdrop-filter: blur(40px);
    -webkit-backdrop-filter: blur(40px);
    display: none;
    align-items: center;
    justify-content: center;
    padding: 20px;
    z-index: 1000;
  }
  .login-card {
    background: rgba(28, 33, 49, 0.85);
    border: 1px solid var(--border-glass);
    border-radius: 26px;
    padding: 38px 30px;
    width: 100%;
    max-width: 360px;
    text-align: center;
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.7), 0 0 40px rgba(14, 165, 233, 0.2);
  }
  .lock-circle {
    width: 60px;
    height: 60px;
    border-radius: 18px;
    background: rgba(14, 165, 233, 0.15);
    color: #38bdf8;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    margin: 0 auto 18px;
    border: 1px solid rgba(14, 165, 233, 0.3);
    box-shadow: 0 0 20px rgba(14, 165, 233, 0.25);
  }
  .login-card h2 {
    margin: 0 0 8px;
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.01em;
  }
  .login-card p {
    margin: 0 0 24px;
    font-size: 13px;
    color: var(--text-secondary);
  }
  .pin-input {
    width: 100%;
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    color: #ffffff;
    font-size: 26px;
    letter-spacing: 10px;
    text-align: center;
    padding: 14px 10px;
    margin-bottom: 20px;
    outline: none;
    transition: all 0.25s;
    font-family: inherit;
  }
  .pin-input:focus {
    border-color: var(--accent-blue);
    box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.3);
    background: rgba(0, 0, 0, 0.5);
  }
  .btn-submit {
    width: 100%;
    background: linear-gradient(135deg, #0284c7, #0ea5e9);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 15px;
    color: #fff;
    font-size: 15px;
    font-weight: 600;
    padding: 14px;
    cursor: pointer;
    box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
    transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  }
  .btn-submit:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(14, 165, 233, 0.5);
  }
  .btn-submit:active {
    transform: translateY(0);
  }
  .login-err {
    color: #f87171;
    font-size: 13px;
    font-weight: 500;
    margin-top: 14px;
    min-height: 20px;
  }

  /* TOAST */
  .toast {
    position: fixed;
    left: 50%;
    bottom: 28px;
    transform: translateX(-50%) translateY(20px);
    background: rgba(28, 33, 49, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    color: #fff;
    border: 1px solid var(--border-glass);
    padding: 11px 22px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 600;
    opacity: 0;
    transition: all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
    pointer-events: none;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5);
    z-index: 2000;
  }
  .toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }

  .shake {
    animation: shake 0.4s ease-in-out;
  }
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-8px); }
    40%, 80% { transform: translateX(8px); }
  }

  .foot {
    color: var(--text-muted);
    font-size: 12px;
    margin-top: 36px;
    text-align: center;
  }
</style>
</head>
<body>

<div class="wrap">
  <div class="header">
    <div class="brand">
      <div class="bot-icon">🤖</div>
      <div>
        <div class="brand-title">
          Userbot Panel
          <span class="status-badge"><span class="status-dot"></span> Faol</span>
        </div>
        <div class="brand-sub">Shamsiddin Shamsiyev</div>
      </div>
    </div>
    <button class="btn-lock" id="btn-lock" onclick="logout()" title="Panelni qulflash">🔒 Chiqish</button>
  </div>

  <div id="app">
    <div style="text-align:center; padding: 40px 0; color: var(--text-muted);">Yuklanmoqda…</div>
  </div>

  <div class="foot">
    Hetzner CX23 · shamsiyev.uz · O'zgarishlar 5 soniyada qo'llanadi.
  </div>
</div>

<!-- PIN / PAROL OYNASI -->
<div id="login-overlay">
  <div class="login-card" id="login-box">
    <div class="lock-circle">🔐</div>
    <h2>Xavfsiz Kirish</h2>
    <p>Boshqaruv paneliga kirish uchun parolni kiriting</p>
    <form onsubmit="handleLogin(event)">
      <input type="password" id="pin-input" class="pin-input" placeholder="••••" maxlength="10" inputmode="numeric" pattern="[0-9]*" autofocus autocomplete="off">
      <button type="submit" class="btn-submit">Panelga kirish</button>
    </form>
    <div class="login-err" id="login-err"></div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const TOKEN = "__TOKEN__";
const FEATURES = [
  ["autoreply", "Avto-javob", "Gemini AI orqali intellektual tabiiy javob"],
  ["autodraft", "Qoralama (shaxsiy)", "Javobni yubormasdan qoralama (draft) qilib qo'yish"],
  ["autoread", "Avto-o'qish", "Kanal va guruhlarni avtomatik o'qilgan qilish"],
  ["autoai", "Yarim-avto taklif", "Kelgan xabarga AI taklifini tasdiqlash"]
];
const ACCOUNTS = [
  ["acc1", "@shamsiyev_shamsiddin"],
  ["acc2", "@Shamsiyevshamsiddin"],
  ["acc3", "@scarpiont"]
];

const app = document.getElementById("app");
const toast = document.getElementById("toast");
const overlay = document.getElementById("login-overlay");
const loginBox = document.getElementById("login-box");
const pinInput = document.getElementById("pin-input");
const loginErr = document.getElementById("login-err");
let toastTimer;

function showToast(text) {
  toast.textContent = text;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 1500);
}

function getStoredAuth() {
  return localStorage.getItem("userbot_auth") || "";
}

function showLogin() {
  overlay.style.display = "flex";
  pinInput.value = "";
  loginErr.textContent = "";
  setTimeout(() => pinInput.focus(), 100);
}

function hideLogin() {
  overlay.style.display = "none";
}

async function handleLogin(e) {
  e.preventDefault();
  const pwd = pinInput.value.trim();
  if (!pwd) return;

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: pwd })
    });
    const data = await res.json();
    if (res.ok && data.ok) {
      if (data.auth) {
        localStorage.setItem("userbot_auth", data.auth);
      }
      hideLogin();
      showToast("Xush kelibsiz! 👋");
      load();
    } else {
      loginBox.classList.add("shake");
      loginErr.textContent = data.error || "Parol noto'g'ri!";
      setTimeout(() => loginBox.classList.remove("shake"), 400);
    }
  } catch (err) {
    loginErr.textContent = "Tarmoq xatosi, qayta urinib ko'ring";
  }
}

async function logout() {
  await fetch("/api/logout", { method: "POST" });
  localStorage.removeItem("userbot_auth");
  showToast("Panel qulflandi 🔒");
  showLogin();
}

async function load() {
  const auth = getStoredAuth();
  let url = "/api/state";
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get("token") || TOKEN;
  if (urlToken) url += "?token=" + encodeURIComponent(urlToken);

  try {
    const res = await fetch(url, {
      headers: auth ? { "X-Userbot-Auth": auth } : {}
    });

    if (res.status === 401 || res.status === 403) {
      showLogin();
      return;
    }
    if (!res.ok) {
      app.innerHTML = '<div style="text-align:center; padding:30px; color:#ef4444;">Yuklashda xatolik yuz berdi.</div>';
      return;
    }

    const st = await res.json();
    hideLogin();
    app.innerHTML = "";

    for (const [acc, uname] of ACCOUNTS) {
      const card = document.createElement("div");
      card.className = "acc-card";

      const head = document.createElement("div");
      head.className = "acc-head";
      head.innerHTML = `<span class="acc-name">${uname}</span><span class="acc-tag">${acc}</span>`;
      card.appendChild(head);

      for (const [f, label, desc] of FEATURES) {
        const row = document.createElement("div");
        row.className = "row";

        const info = document.createElement("div");
        info.className = "feat-info";
        info.innerHTML = `<div class="feat-title">${label}</div><div class="feat-desc">${desc}</div>`;

        const sw = document.createElement("label");
        sw.className = "sw";
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.checked = !!(st[acc] && st[acc][f]);
        const sl = document.createElement("span");
        sl.className = "sl";

        cb.addEventListener("change", () => toggle(acc, f, cb.checked, label));

        sw.appendChild(cb);
        sw.appendChild(sl);
        row.appendChild(info);
        row.appendChild(sw);
        card.appendChild(row);
      }

      app.appendChild(card);
    }
  } catch (err) {
    showLogin();
  }
}

async function toggle(acc, feat, val, label) {
  const auth = getStoredAuth();
  let url = "/api/toggle";
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get("token") || TOKEN;
  if (urlToken) url += "?token=" + encodeURIComponent(urlToken);

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(auth ? { "X-Userbot-Auth": auth } : {})
      },
      body: JSON.stringify({ account: acc, feature: feat, value: val })
    });
    if (res.ok) {
      showToast(label + (val ? " yoqildi 🟢" : " o'chirildi ⚪️"));
    } else {
      showToast("O'zgartirishda xato yuz berdi ❌");
    }
  } catch (e) {
    showToast("Tarmoq xatosi ❌");
  }
}

// Avtomatik PIN kiritilganda (4 xona) submit qilish
pinInput.addEventListener("input", () => {
  if (pinInput.value.length === 4) {
    handleLogin(new Event("submit"));
  }
});

load();
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
        web.post("/api/toggle", api_toggle),
    ])
    print(f"Web panel: http://{HOST}:{PORT}/?token=***")
    web.run_app(app, host=HOST, port=PORT, print=None)


if __name__ == "__main__":
    main()
