import os
import sys

from dotenv import load_dotenv

load_dotenv()

# --- Akkaunt (sessiya) tanlash ---------------------------------------------
# Ishga tushirishda akkaunt nomini argument bilan berish mumkin:
#   python userbot.py acc1
# Berilmasa .env dagi SESSION yoki "userbot" ishlatiladi.
if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
    SESSION = sys.argv[1]
else:
    SESSION = os.getenv("SESSION", "userbot")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)
# Telethon sessiya fayli: sessions/<akkaunt>.session
SESSION_PATH = os.path.join(SESSIONS_DIR, SESSION)

# --- API kalitlari ----------------------------------------------------------
# Har bir akkaunt uchun alohida kalit ishlatmoqchi bo'lsangiz, .env da
# akkaunt nomiga qarab qo'ying, masalan:  API_ID_ACC1=...  API_HASH_ACC1=...
_suffix = SESSION.upper()
API_ID = int(os.getenv(f"API_ID_{_suffix}", os.getenv("API_ID", "0")))
API_HASH = os.getenv(f"API_HASH_{_suffix}", os.getenv("API_HASH", ""))

PREFIX = os.getenv("PREFIX", ".")

# --- Gemini AI --------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

# O'z akkauntlaringiz ID lari (avto-javob ular bir-biriga javob bermasligi uchun).
# .env da: OWN_ACCOUNT_IDS=111,222,333
OWN_ACCOUNT_IDS = {
    int(x) for x in os.getenv("OWN_ACCOUNT_IDS", "").replace(" ", "").split(",") if x
}

# --- Avto-javob ban himoyasi ---
# Ishlash soatlari (mahalliy vaqt, 0-24). Masalan "8-24" = 08:00..24:00.
_ah = os.getenv("ACTIVE_HOURS", "8-24")
try:
    ACTIVE_START, ACTIVE_END = (int(x) for x in _ah.split("-"))
except Exception:  # noqa: BLE001
    ACTIVE_START, ACTIVE_END = 0, 24
# Server UTC da. Mahalliy vaqt uchun soat farqi (O'zbekiston = +5).
TZ_OFFSET = int(os.getenv("TZ_OFFSET", "5"))
# Global limit: shu oyna (soniya) ichida jami maksimal avto-javob.
GLOBAL_WINDOW = int(os.getenv("GLOBAL_WINDOW", "60"))
GLOBAL_MAX = int(os.getenv("GLOBAL_MAX", "15"))
# Odamsimon kechikish (soniya, min..max) — javobdan oldin "yozmoqda" bilan kutadi.
HUMAN_DELAY_MIN = float(os.getenv("HUMAN_DELAY_MIN", "2"))
HUMAN_DELAY_MAX = float(os.getenv("HUMAN_DELAY_MAX", "5"))

# --- Web boshqaruv paneli ---
PANEL_URL = os.getenv("PANEL_URL", "")      # masalan http://178.104.25.218:8080
PANEL_TOKEN = os.getenv("PANEL_TOKEN", "")  # maxfiy kalit
PANEL_PORT = int(os.getenv("PANEL_PORT", "8080"))

if not API_ID or not API_HASH:
    raise SystemExit(
        f"[{SESSION}] API_ID/API_HASH sozlanmagan. .env faylini to'ldiring "
        "(namuna: .env.example)."
    )
