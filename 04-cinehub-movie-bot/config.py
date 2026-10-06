"""Bot sozlamalari — barcha qiymatlar .env faylidan o'qiladi."""
import os
from dotenv import load_dotenv

load_dotenv()


def _int_list(raw: str) -> list[int]:
    out = []
    for part in (raw or "").replace(" ", "").split(","):
        if part.isdigit() or (part.startswith("-") and part[1:].isdigit()):
            out.append(int(part))
    return out


# ==== TELEGRAM ====
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BOT_USERNAME = os.getenv("BOT_USERNAME", "").strip().lstrip("@")
ADMIN_IDS = _int_list(os.getenv("ADMIN_IDS", ""))

# ==== POSTGRESQL ====
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    _host = os.getenv("DB_HOST", "localhost")
    _port = os.getenv("DB_PORT", "5432")
    _name = os.getenv("DB_NAME", "kino")
    _user = os.getenv("DB_USER", "kino")
    _pass = os.getenv("DB_PASS", "")
    DATABASE_URL = f"postgresql://{_user}:{_pass}@{_host}:{_port}/{_name}"

# ==== TMDB ====
TMDB_KEY = os.getenv("TMDB_KEY", "").strip()

# ==== KANALLAR / GURUH ====
SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "").strip()
UPLOAD_CHANNEL = os.getenv("UPLOAD_CHANNEL", "").strip()
ARCHIVE_CHANNEL = os.getenv("ARCHIVE_CHANNEL", "").strip()

# ==== WEB ADMIN ====
WEB_ENABLED = os.getenv("WEB_ENABLED", "1").strip() not in ("0", "false", "no", "")
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))
WEB_ADMIN_USER = os.getenv("WEB_ADMIN_USER", "admin").strip()
WEB_ADMIN_PASSWORD = os.getenv("WEB_ADMIN_PASSWORD", "").strip()
# Master (subtitr) domen orqali proxy qilinganda ishlatiladigan umumiy sir.
WEB_BRIDGE_SECRET = os.getenv("WEB_BRIDGE_SECRET", "").strip()

# ==== BOSHQA ====
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylida ko'rsatilmagan!")
