"""Sozlamalar — .env fayldan o'qiladi."""
import os
from dotenv import load_dotenv

load_dotenv()

# Instagram / Meta
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID", "")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "verify_me")

# Instagram Login API (IGAA... token) — graph.instagram.com ishlatiladi
GRAPH_VERSION = "v21.0"
GRAPH_URL = f"https://graph.instagram.com/{GRAPH_VERSION}"

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

# Bot xatti-harakati
BOT_PERSONA = os.getenv(
    "BOT_PERSONA",
    "Sen do'stona va qisqa javob beradigan Instagram yordamchisisan. O'zbek tilida javob ber.",
)
MAX_REPLY_CHARS = int(os.getenv("MAX_REPLY_CHARS", "500"))


def check():
    """Zarur sozlamalar borligini tekshiradi."""
    missing = [
        name
        for name, val in {
            "IG_ACCESS_TOKEN": IG_ACCESS_TOKEN,
            "IG_ACCOUNT_ID": IG_ACCOUNT_ID,
            "GEMINI_API_KEY": GEMINI_API_KEY,
        }.items()
        if not val
    ]
    if missing:
        raise RuntimeError(
            "Quyidagi sozlamalar .env faylda to'ldirilmagan: " + ", ".join(missing)
        )
