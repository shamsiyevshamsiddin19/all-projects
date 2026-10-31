"""Umumiy poydevor: yo'llar, konstantalar, dataklasslar, matn yordamchilari."""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import io
from dataclasses import dataclass
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


def _force_utf8(stream_name: str) -> None:
    """Oqimni UTF-8 ga o'tkazadi.

    GUI rejimida (konsolsiz) yoki oqim qayta yo'naltirilganda `encoding` None
    bo'lishi mumkin — o'shanda `.lower()` AttributeError bilan dasturni
    ochilishidayoq to'xtatib qo'yardi."""
    stream = getattr(sys, stream_name, None)
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        return
    encoding = getattr(stream, "encoding", None) or ""
    if encoding.lower() != "utf-8":
        setattr(sys, stream_name, io.TextIOWrapper(buffer, encoding="utf-8", line_buffering=True))


_force_utf8("stdout")
_force_utf8("stderr")

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = None

KINO_DIR = Path.home() / "Videos"
if getattr(sys, 'frozen', False):
    # Installed app: the exe may live in a read-only location (Program Files),
    # so results go to a visible folder in Videos and working/support files go
    # to a per-user writable data directory.
    ROOT = Path(sys.executable).resolve().parent
    _DATA = Path(os.getenv("LOCALAPPDATA") or Path.home()) / "SubtitrDesktop"
    OUT_DIR = KINO_DIR / "Subtitr natijalar"
    TMP_DIR = _DATA / "Ishchi fayllar"
    MODEL_DIR = _DATA / "AI modellar"
    DICT_DIR = _DATA / "Lugatlar"
    CACHE_DIR = _DATA / "cache"
    LOG_DIR = _DATA / "logs"
else:
    # DIQQAT: bu fayl `subtitr/` paketi ichida. ROOT — dastur papkasi
    # (tools/, fonts/, .venv, cache shu yerda), ya'ni paketdan bitta
    # yuqorida. `.parent` ni olib tashlamang.
    ROOT = Path(__file__).resolve().parent.parent
    OUT_DIR = ROOT / "Tayyor natijalar"
    TMP_DIR = ROOT / "Ishchi fayllar"
    MODEL_DIR = ROOT / "AI modellar"
    DICT_DIR = ROOT / "Lugatlar"
    CACHE_DIR = ROOT / "cache"
    LOG_DIR = ROOT / "logs"

# O'rnatilgan ilova (Linux) manba ko'rinishida ishlaydi, lekin natijalar ilova
# papkasiga emas — ko'rinadigan Videolar papkasiga tushishi kerak. Yo'llarni
# launcher skripti muhit o'zgaruvchilari orqali beradi.
_kino_override = os.getenv("SUBTITR_KINO_DIR", "").strip()
if _kino_override:
    KINO_DIR = Path(_kino_override).expanduser()
_out_override = os.getenv("SUBTITR_OUT_DIR", "").strip()
if _out_override:
    OUT_DIR = Path(_out_override).expanduser()
_data_override = os.getenv("SUBTITR_DATA_DIR", "").strip()
if _data_override:
    _data_root = Path(_data_override).expanduser()
    TMP_DIR = _data_root / "Ishchi fayllar"
    MODEL_DIR = _data_root / "AI modellar"
    DICT_DIR = _data_root / "Lugatlar"
    CACHE_DIR = _data_root / "cache"
    LOG_DIR = _data_root / "logs"

ENV_FILE = ROOT / ".env"
VENV_DIR = ROOT / ".venv"
# O'rnatiladigan Python paketlar ro'yxati. Build skripti ham, ilova
# ichidagi "Paketlarni o'rnatish" ham AYNAN shu fayldan o'qiydi —
# ro'yxat ikki joyda yozilsa, biri eskirib qoladi.
REQUIREMENTS_FILE = ROOT / "desktop_requirements.txt"


def venv_python() -> Path:
    """Interpreter of the virtualenv shipped next to the processor."""
    return VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def resolve_tool(name: str) -> str:
    """Prefer a tool bundled next to the executable, then a dev `tools/` folder,
    else fall back to PATH."""
    fname = name + (".exe" if os.name == "nt" else "")
    for base in (ROOT, ROOT / "tools"):
        exe = base / fname
        if exe.exists():
            return str(exe)
    found = shutil.which(name)
    return found or name


FFMPEG = resolve_tool("ffmpeg")
FFPROBE = resolve_tool("ffprobe")
YTDLP = resolve_tool("yt-dlp")

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}
SUB_EXTS = {".srt", ".vtt"}

TARGET_LANG_NAMES = {
    "uz": "Uzbek",
    "en": "English",
    "ru": "Russian",
    "tr": "Turkish",
    "kk": "Kazakh",
    "tg": "Tajik",
    "ky": "Kyrgyz",
}

# Whisper tilni ikki xil ko'rinishda qaytaradi: Groq to'liq nomi bilan
# ("russian"), lokal faster-whisper ISO kodi bilan ("ru"). Til esa kod bo'ylab
# KALIT sifatida ishlatiladi — yordamchi so'zlar ro'yxati (HELPERS),
# transliteratsiya, kesh fayl nomi. Keltirilmasa, Groq bilan ishlangan har bir
# videoda yordamchi so'zlar aniqlanmay qoladi va lug'at "не, что, на, до"
# kabi so'zlar bilan to'lib ketadi.
_LANG_ALIASES = {
    "russian": "ru", "english": "en", "uzbek": "uz", "turkish": "tr",
    "kazakh": "kk", "tajik": "tg", "kyrgyz": "ky", "ukrainian": "uk",
    "azerbaijani": "az", "turkmen": "tk", "german": "de", "french": "fr",
    "spanish": "es", "italian": "it", "portuguese": "pt", "polish": "pl",
    "arabic": "ar", "persian": "fa", "korean": "ko", "japanese": "ja",
    "chinese": "zh", "hindi": "hi",
}
# Whisper til o'rniga ba'zan yozuv tizimi yoki axlat qaytaradi ("latin",
# "nn"). Bunday qiymat tarjima so'roviga "latin tilidan tarjima qil" bo'lib
# ketadi — uni til deb qabul qilmaymiz.
_LANG_NOT_A_LANGUAGE = {"latin", "cyrillic", "nn", "none", "unknown", "auto"}


def normalize_lang_code(value: str) -> str:
    """Til nomini ISO kodiga keltiradi. Tanimasa — bo'sh satr."""
    key = (value or "").strip().lower()
    if not key or key in _LANG_NOT_A_LANGUAGE:
        return ""
    if key in _LANG_ALIASES:
        return _LANG_ALIASES[key]
    if len(key) <= 3 and key.isalpha():
        return key
    base = key.split("-")[0].split("_")[0]
    return _LANG_ALIASES.get(base, base if len(base) <= 3 and base.isalpha() else "")


SOURCE_LANG_NAMES = {
    "auto": "auto-detected source language",
    "uz": "Uzbek",
    "en": "English",
    "ru": "Russian",
    "tr": "Turkish",
    "kk": "Kazakh",
    "tg": "Tajik",
    "ky": "Kyrgyz",
}

HELPERS = {
    "en": {
        "article": {"a", "an", "the"},
        "preposition": {
            "in", "on", "at", "to", "for", "from", "with", "by", "of",
            "about", "into", "onto", "over", "under", "after", "before",
            "between", "through", "during", "without", "against", "around",
            "off", "up", "down", "as",
        },
        "conjunction": {
            "and", "but", "or", "so", "because", "if", "when", "while",
            "that", "than", "though", "although", "since", "unless", "yet",
        },
    },
    "uz": {
        "komakchi": {
            "bilan", "uchun", "kabi", "singari", "qadar", "tomon",
            "orqali", "haqida", "keyin", "oldin", "song", "qarshi",
        },
        "boglovchi": {
            "va", "ham", "ammo", "lekin", "biroq", "yoki", "chunki",
            "agar", "yani", "balki",
        },
    },
    "ru": {
        "preposition": {
            "v", "na", "s", "k", "u", "o", "po", "za", "iz", "ot",
            "do", "dlya", "pod", "nad", "pri", "pro", "bez", "cherez",
        },
        "conjunction": {"i", "a", "no", "ili", "chto", "esli", "kogda", "kak"},
        # Yuklama va olmoshlar chastota ro'yxatining tepasini egallab oladi,
        # lekin o'rganish uchun qiymati yo'q. "Yordamchi" deb belgilansa,
        # lug'atda alohida bo'limga tushadi va `.md` da belgilanmaydi.
        # (Kalitlar transliteratsiya qilingan — `helper_category` ga qarang.)
        "particle": {
            "b", "bi", "dazhe", "li", "ne", "neuzheli", "ni", "razve", "uzh",
            "ved", "zhe",
        },
        "pronoun": {
            "chey", "chto", "ee", "ego", "emu", "eta", "eti", "eto", "etot",
            "eyu", "ih", "im", "imi", "kto", "menya", "mi", "mne", "moe",
            "moi", "moy", "moya", "nam", "nami", "nas", "nash", "nasha",
            "nashi", "ney", "nih", "nim", "on", "ona", "oni", "ono", "sebe",
            "sebya", "svoe", "svoi", "svoy", "svoya", "ta", "te", "tebe",
            "tebya", "ti", "to", "tot", "tvoe", "tvoi", "tvoy", "tvoya",
            "vam", "vami", "vas", "vash", "vasha", "vashi", "vi", "ya",
        },
    },
}

COMMON_WORDS = {
    "hello": "salom",
    "hi": "salom",
    "yes": "ha",
    "no": "yo'q",
    "not": "emas",
    "i": "men",
    "you": "siz",
    "he": "u",
    "she": "u",
    "we": "biz",
    "they": "ular",
    "it": "u",
    "me": "menga",
    "my": "mening",
    "your": "sizning",
    "our": "bizning",
    "this": "bu",
    "that": "o'sha",
    "these": "bular",
    "those": "o'shalar",
    "is": "bo'ladi",
    "are": "bo'ladi",
    "was": "edi",
    "were": "edi",
    "be": "bo'lmoq",
    "have": "ega bo'lmoq",
    "has": "ega",
    "do": "qilmoq",
    "does": "qiladi",
    "did": "qildi",
    "will": "bo'ladi",
    "can": "qila oladi",
    "could": "qila olardi",
    "should": "kerak",
    "must": "shart",
    "go": "bormoq",
    "come": "kelmoq",
    "see": "ko'rmoq",
    "look": "qaramoq",
    "know": "bilmoq",
    "think": "o'ylamoq",
    "want": "xohlamoq",
    "need": "kerak bo'lmoq",
    "make": "qilmoq",
    "take": "olmoq",
    "give": "bermoq",
    "get": "olmoq",
    "say": "aytmoq",
    "tell": "aytmoq",
    "speak": "gapirmoq",
    "talk": "suhbatlashmoq",
    "work": "ishlamoq",
    "time": "vaqt",
    "day": "kun",
    "night": "tun",
    "man": "erkak",
    "woman": "ayol",
    "people": "odamlar",
    "friend": "do'st",
    "home": "uy",
    "house": "uy",
    "world": "dunyo",
    "life": "hayot",
    "love": "sevgi",
    "money": "pul",
    "good": "yaxshi",
    "bad": "yomon",
    "big": "katta",
    "small": "kichik",
    "new": "yangi",
    "old": "eski",
    "great": "zo'r",
    "right": "to'g'ri",
    "wrong": "noto'g'ri",
    "now": "hozir",
    "then": "keyin",
    "here": "bu yerda",
    "there": "u yerda",
    "why": "nega",
    "what": "nima",
    "who": "kim",
    "where": "qayerda",
    "when": "qachon",
    "how": "qanday",
    "and": "va",
    "but": "lekin",
    "or": "yoki",
    "because": "chunki",
    "for": "uchun",
    "with": "bilan",
    "in": "ichida",
    "on": "ustida",
    "to": "ga",
    "from": "dan",
    "of": "ning",
    "the": "",
    "a": "",
    "an": "",
}

PHRASES = {
    "you know": "bilasizmi",
    "i mean": "aytmoqchimanki",
    "thank you": "rahmat",
    "thanks": "rahmat",
    "good morning": "xayrli tong",
    "good night": "xayrli tun",
    "how are you": "qalaysiz",
    "what are you doing": "nima qilyapsiz",
    "let's go": "ketdik",
}

WORD_RE = re.compile(r"[^\W\d_]+(?:['`][^\W\d_]+)*", re.UNICODE)

# Maps an English part-of-speech (or Uzbek helper category) to an Uzbek label.
POS_UZ = {
    "pronoun": "Olmosh", "noun": "Ot", "verb": "Fe'l", "adjective": "Sifat",
    "adverb": "Ravish", "article": "Artikl", "preposition": "Predlog",
    "auxiliary": "Yordamchi fe'l", "particle": "Yuklama", "conjunction": "Bog'lovchi",
    "numeral": "Son", "interjection": "Undov",
    # Uzbek helper categories used as a fallback when no pos is returned.
    "komakchi": "Ko'makchi", "boglovchi": "Bog'lovchi",
}
POS_ORDER = [
    "Olmosh", "Ot", "Fe'l", "Sifat", "Ravish", "Son", "Artikl",
    "Predlog", "Ko'makchi", "Yordamchi fe'l", "Yuklama", "Bog'lovchi",
    "Undov", "Boshqa",
]


def pos_label(entry: dict[str, Any]) -> str:
    pos_raw = str(entry.get("pos", "")).lower()
    if not pos_raw and entry.get("helper"):
        pos_raw = str(entry["helper"]).lower()
    for key, label in POS_UZ.items():
        if key in pos_raw:
            return label
    return "Boshqa"


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Word:
    start: float
    end: float
    word: str


@dataclass(frozen=True)
class ReadingPair:
    """Bitta GAP va uning tarjimasi — Yordamchi saytining `.md` formati uchun.

    `new_paragraph` nutqdagi uzoq jimlikdan keyin keladigan gapni belgilaydi
    (o'sha joyda `.md` da ikki bo'sh qator qo'yiladi)."""
    start: float
    end: float
    source: str
    target: str
    new_paragraph: bool


@dataclass(frozen=True)
class ReadingBlock:
    """O'qish uchun matndagi bitta abzats (bir nechta subtitr bo'lagidan
    yig'ilgan). Vaqtlari saqlanadi — kerak bo'lsa videodagi joyini topish
    uchun."""
    start: float
    end: float
    text: str


# ---------------------------------------------------------------------------
# Log
#
# Ilgari hech qanday log yo'q edi: xato faqat GUI'da bitta qator snackbar
# bo'lib chiqar va yo'qolardi, traceback esa butunlay tashlanardi. Endi har
# bir ish `logs/subtitr-YYYY-MM-DD.log` ga yoziladi.
#
# DIQQAT: logga API kalit TUSHMASLIGI kerak. `os.environ` hech qachon
# yozilmaydi, provayderdan kelgan matnlar esa `redact()` dan o'tadi.
# ---------------------------------------------------------------------------

log = logging.getLogger("subtitr")
# `setup_logging()` chaqirilmaguncha jim turadi — shunchaki import qilish
# (masalan testlarda) disk fayl yaratmasligi kerak.
log.addHandler(logging.NullHandler())

# Kalitga o'xshash ketma-ketliklar. Gemini kalitlari "AIza" dan ham, yangi
# formatda "AQ." dan ham boshlanadi.
_SECRET_RE = re.compile(
    r"\b(?:sk-ant-[\w-]+|sk-[\w-]{16,}|gsk_[\w-]+|AIza[\w-]{10,}|AQ\.[\w.-]+)",
    re.IGNORECASE,
)

LOG_KEEP_DAYS = 14


def redact(text: str) -> str:
    """Matndagi kalitga o'xshash qismlarni maskalaydi."""
    def mask(match: re.Match[str]) -> str:
        found = match.group(0)
        return f"{found[:6]}...{found[-4:]}" if len(found) > 14 else "***"

    return _SECRET_RE.sub(mask, text or "")


def _prune_old_logs(keep_days: int = LOG_KEEP_DAYS) -> None:
    """Eski log fayllarini o'chiradi — log papkasi ham cheksiz o'smasin."""
    import time

    cutoff = time.time() - keep_days * 86400
    try:
        entries = list(LOG_DIR.glob("subtitr-*.log*"))
    except OSError:
        return
    for item in entries:
        try:
            if item.stat().st_mtime < cutoff:
                item.unlink()
        except OSError:
            continue


def setup_logging() -> Path | None:
    """Kunlik log faylini ulaydi va uning yo'lini qaytaradi.

    Faqat `cli.main()` dan chaqiriladi: kutubxona sifatida import qilinganda
    (testlar) hech narsa yozilmaydi. Log yozib bo'lmasa (disk to'la, ruxsat
    yo'q) dastur TO'XTAMAYDI — log qulaylik, shart emas."""
    if any(not isinstance(h, logging.NullHandler) for h in log.handlers):
        return current_log_file()
    if os.getenv("SUBTITR_NO_LOG", "") in {"1", "true", "yes"}:
        return None
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = current_log_file()
        # Bitta kun ichida ham fayl cheksiz o'smasin (uzun kino + render
        # progressi ko'p qator beradi).
        handler = RotatingFileHandler(
            path, maxBytes=2 * 1024 * 1024, backupCount=2, encoding="utf-8"
        )
    except OSError:
        return None
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%H:%M:%S")
    )
    log.addHandler(handler)
    log.setLevel(logging.DEBUG if os.getenv("SUBTITR_DEBUG") else logging.INFO)
    log.propagate = False
    _prune_old_logs()
    return path


def current_log_file() -> Path:
    return LOG_DIR / f"subtitr-{datetime.now():%Y-%m-%d}.log"


# ---------------------------------------------------------------------------
# To'xtatish (Bekor qilish)
#
# Ilgari ilova protsessorga darhol SIGKILL yuborardi. SIGKILL ni ushlab
# bo'lmaydi, ya'ni `_prepare_data` dagi `finally: rmtree(job_tmp)` ISHLAMAY
# qolardi — uzun kinoda 1 GB lik WAV keshda qolib ketardi, yarim yozilgan
# `.mp4` esa natijalar papkasida turardi.
#
# Endi avval SIGTERM keladi: quyidagi ishlov beruvchi uni KeyboardInterrupt ga
# aylantiradi, shuning uchun hamma `finally` bloki ishlaydi va fayllar
# tozalanadi. Ilova SIGKILL ni faqat 4 soniya kutgandan keyin yuboradi.
# ---------------------------------------------------------------------------

def stop_child(proc: subprocess.Popen, name: str = "") -> None:
    """Ishga tushirilgan bolani (ffmpeg/yt-dlp) to'xtatadi.

    Avval SIGTERM: ffmpeg shunda faylni yopib chiqadi. 3 soniyadan keyin
    ham tirik bo'lsa — SIGKILL.

    Shart: Python KeyboardInterrupt bilan uzilganda bolasini O'ZI
    to'xtatishi kerak. Ilova "Bekor qilish" bosganda signal butun process
    guruhiga ketadi va ffmpeg baribir o'ladi, lekin buyruq qatorida Ctrl+C
    bosilganda yoki Python tushganda ffmpeg yetim bo'lib qolar va
    protsessorni band qilib ishlab turaverardi.
    """
    if proc.poll() is not None:
        return
    label = name or "bola jarayon"
    try:
        proc.terminate()
        proc.wait(timeout=3)
        log.info("%s to'xtatildi (SIGTERM)", label)
        return
    except subprocess.TimeoutExpired:
        pass
    except OSError:
        return
    try:
        proc.kill()
        proc.wait(timeout=2)
        log.warning("%s majburan o'ldirildi (SIGKILL)", label)
    except (OSError, subprocess.TimeoutExpired):
        pass


def install_signal_handlers() -> None:
    """SIGTERM ni KeyboardInterrupt ga aylantiradi (SIGINT allaqachon shunday).

    `SUBTITR_OWN_PROCESS_GROUP=1` berilsa, jarayon o'zini alohida process
    guruhiga o'tkazadi — shunda ilova butun daraxtni (python + ffmpeg +
    yt-dlp va ularning bolalari) bitta signal bilan to'xtata oladi.
    Buyruq qatorida bu YOQILMAYDI: aks holda terminaldagi Ctrl+C jarayonga
    yetib bormay qoladi."""
    import signal

    def on_term(signum: int, _frame: Any) -> None:
        log.info("to'xtatish signali keldi (%s)", signum)
        raise KeyboardInterrupt

    for name in ("SIGTERM", "SIGHUP"):
        sig = getattr(signal, name, None)
        if sig is not None:
            try:
                signal.signal(sig, on_term)
            except (OSError, ValueError):
                pass

    if os.name != "nt" and os.getenv("SUBTITR_OWN_PROCESS_GROUP", "") in {"1", "true", "yes"}:
        try:
            os.setpgrp()
        except OSError:
            pass


# Tashlandiq ish papkasi shu muddatdan keyin o'chiriladi. Uzoq olingan:
# ishlab turgan uzun render ham papkasiga bir necha soat hech narsa
# yozmasligi mumkin (va ikkinchi nusxa ishlab turgan bo'lishi ham mumkin).
ORPHAN_TMP_HOURS = 12


def clean_orphan_tmp(max_age_hours: float = ORPHAN_TMP_HOURS) -> int:
    """Tugamay qolgan ishlardan qolgan vaqtinchalik papkalarni o'chiradi.

    Ilgari dastur SIGKILL bilan o'ldirilganda (yoki tushganda) bu papkalar
    abadiy qolib ketardi — har biri audio/WAV bilan yuzlab megabayt."""
    import time

    cutoff = time.time() - max_age_hours * 3600
    freed = 0
    try:
        entries = list(TMP_DIR.iterdir())
    except OSError:
        return 0
    for item in entries:
        # "yuklamalar" — bu kesh, tashlandiq ish papkasi emas.
        if item.name == "yuklamalar" or not item.is_dir():
            continue
        try:
            if item.stat().st_mtime >= cutoff:
                continue
            size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
        except OSError:
            continue
        shutil.rmtree(item, ignore_errors=True)
        if not item.exists():
            freed += size
    if freed:
        log.info("tashlandiq ishchi fayllar o'chirildi: %d bayt", freed)
    return freed


def ensure_dirs() -> None:
    for path in (KINO_DIR, OUT_DIR, TMP_DIR, MODEL_DIR, DICT_DIR, CACHE_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)
    if load_dotenv and ENV_FILE.exists():
        load_dotenv(ENV_FILE)
    elif load_dotenv:
        load_dotenv()


def emit(kind: str, **data: Any) -> None:
    data["type"] = kind
    print(json.dumps(data, ensure_ascii=False), flush=True)
    # Butun progress izi logga ham tushadi: ilova yopilgandan keyin "nima
    # bo'ldi?" degan savolga javob beradigan yagona joy shu.
    message = str(data.get("message") or "")
    if kind == "error":
        log.error("XATO: %s", redact(message))
    elif kind == "done":
        log.info("tugadi: %s", redact(message) if message else _done_summary(data))
    elif message:
        percent = data.get("progress")
        prefix = f"[{float(percent) * 100:3.0f}%] " if isinstance(percent, (int, float)) else ""
        log.info("%s%s", prefix, redact(message))


def _done_summary(data: dict[str, Any]) -> str:
    """`done` hodisasining qisqa mazmuni (butun JSON emas — fayl shishmasin)."""
    parts = [
        f"{key}={data[key]}"
        for key in ("mode", "transcriber", "translator", "outDir", "path", "freed")
        if data.get(key) not in (None, "")
    ]
    outputs = data.get("outputs")
    if isinstance(outputs, list):
        parts.append(f"fayllar={len(outputs)}")
    usage = data.get("usage")
    if isinstance(usage, dict) and usage:
        parts.append("so'rovlar=" + ",".join(f"{k}:{v}" for k, v in usage.items()))
    return " ".join(parts) or "ok"


# Ish davomida nechta AI so'rovi ketgani. Boshlashdan oldingi baho taxminiy;
# bu esa haqiqiy son — ayniqsa yutilgan nutqni qayta o'qish so'rovlar sonini
# o'zgaruvchan qilgandan keyin kerak bo'ldi.
USAGE: dict[str, int] = {}


def _count(name: str, n: int = 1) -> None:
    USAGE[name] = USAGE.get(name, 0) + n


def reset_usage() -> None:
    USAGE.clear()
    AI_DISABLED.clear()


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def ai_throttle() -> None:
    """Small pause after a successful AI call to stay under provider rate limits.

    Paid providers (OpenAI/Gemini) tolerate a tiny gap; only Groq's free tier
    really needs it. Configurable via AI_THROTTLE_SEC (default 0.5s).
    """
    import time
    delay = _env_float("AI_THROTTLE_SEC", 0.5)
    if delay > 0:
        time.sleep(delay)


# Tarjima to'plami bir necha marta ishlamasa, ikkiga bo'lib qayta urinamiz;
# shundan kichik to'plam uchun bo'lish foyda bermaydi.
AI_MIN_SPLIT_BATCH = 8


def ai_retry_backoff(attempt: int = 0) -> None:
    """Hamma provayder tushgandan keyingi kutish — eksponensial.

    Ilgari bu qat'iy 6 soniya edi va 5 marta takrorlanardi: bitta to'plam
    uchun 30 soniya behuda kutish va 20 ta API chaqiruvi. Endi kutish
    6 -> 12 -> 24 (`AI_RETRY_MAX_SEC` gacha) bo'ladi, urinishlar soni esa
    kamaytirildi — chunki muvaffaqiyatsizlikdan keyin to'plam baribir
    ikkiga bo'linib qayta so'raladi."""
    import random
    import time

    base = _env_float("AI_RETRY_BACKOFF_SEC", 6.0)
    if base <= 0:
        return
    cap = _env_float("AI_RETRY_MAX_SEC", 30.0)
    delay = min(base * (2 ** max(0, attempt)), cap)
    # Kichik tasodifiy qo'shimcha: bir vaqtda ketgan so'rovlar limitga
    # birgalikda qayta urilib qolmasin.
    time.sleep(delay + random.uniform(0, min(1.0, delay * 0.1)))


# Qayta urinishga ARZIMAYDIGAN xatolar. Yaroqsiz kalit yoki yo'q model
# ikkinchi urinishda ham o'sha javobni qaytaradi — 5 marta urinish faqat
# vaqt yo'qotadi va foydalanuvchini kutib o'tiradi.
_AUTH_ERROR_RE = re.compile(
    r"\b(401|403)\b|invalid[\s_-]*api[\s_-]*key|incorrect api key|api key not valid"
    r"|authentication|unauthorized|permission[\s_-]*denied|credit balance",
    re.I,
)
_BAD_REQUEST_RE = re.compile(
    r"\b(400|404|422)\b|not[\s_-]*found|does not exist"
    r"|invalid[\s_-]*request|unsupported|decommissioned",
    re.I,
)


def error_kind(exc: BaseException) -> str:
    """Xatoni turkumlaydi: "auth" | "bad_request" | "retry"."""
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    if isinstance(status, int):
        if status in (401, 403):
            return "auth"
        if status in (400, 404, 422):
            return "bad_request"
        return "retry"  # 429 va 5xx — kutib qayta urinamiz
    text = str(exc)
    if _AUTH_ERROR_RE.search(text):
        return "auth"
    if _BAD_REQUEST_RE.search(text):
        return "bad_request"
    return "retry"


# Ish davomida o'chirib qo'yilgan provayderlar: nom -> sabab. Kaliti yaroqsiz
# bo'lgan provayderga har bir to'plam uchun qaytib murojaat qilishning
# ma'nosi yo'q (uzun kinoda bu yuzlab befoyda chaqiruv bo'lardi).
AI_DISABLED: dict[str, str] = {}


def disable_provider(name: str, reason: str) -> None:
    if name not in AI_DISABLED:
        AI_DISABLED[name] = reason
        log.warning("provayder o'chirildi (%s): %s", name, redact(reason)[:200])
        emit(
            "progress",
            message=f"Diqqat: {name} o'chirildi — {redact(reason)[:120]}",
            progress=0.4,
        )


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    log.debug("ishga tushdi: %s", " ".join(cmd[:3]))
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        # ffmpeg/ffprobe/yt-dlp xatosi ko'p joyda jimgina yutiladi
        # (`if proc.returncode == 0:` ko'rinishida) — logda esa qoladi.
        tail = (proc.stderr or "").strip()[-600:]
        log.warning(
            "%s kod %d bilan tugadi: %s",
            Path(cmd[0]).name, proc.returncode, redact(tail) or "(stderr bo'sh)",
        )
    return proc


def require_disk_space(video: Path, where: Path, factor: float = 2.5) -> None:
    """Ish boshlashdan oldin disk joyini tekshiradi.

    Joy tugasa ffmpeg tushunarsiz xato beradi ("Invalid argument",
    "Error writing trailer"), foydalanuvchi esa sababini bilmaydi. Shu
    sababli oldindan aytamiz.

    `factor` — videoning o'ziga nisbatan kerakli joy: ajratilgan WAV audio
    (~1 GB/soat) + render qilingan chiqish + ASS/SRT fayllar.
    """
    try:
        need = int(video.stat().st_size * factor)
        free = shutil.disk_usage(where).free
    except OSError:
        return  # o'lchab bo'lmasa to'xtatmaymiz
    if free >= need:
        return
    gb = 1024 ** 3
    raise RuntimeError(
        f"Diskda joy yetarli emas: {free / gb:.1f} GB bo'sh, "
        f"taxminan {need / gb:.1f} GB kerak ({where}). "
        "Joy bo'shatib qaytadan urinib ko'ring — "
        "Sozlamalar > Disk keshi dan ham bo'shatish mumkin."
    )


def require_tool(name: str) -> None:
    resolved = {"ffmpeg": FFMPEG, "ffprobe": FFPROBE}.get(name, name)
    if os.path.isfile(resolved) or shutil.which(resolved):
        return
    raise RuntimeError(f"{name} topilmadi. Uni dastur papkasiga yoki PATH ga qo'shing.")


def safe_stem(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^\w\-.]+", "_", stem, flags=re.UNICODE).strip("._")
    return stem or "video"


def is_url(value: str) -> bool:
    return bool(re.match(r"^https?://", (value or "").strip(), re.IGNORECASE))



def model_candidates(primary_env: str, default: str, fallback_env: str, fallbacks: list[str]) -> list[str]:
    # Bo'sh ("") env qiymati ham default sifatida qabul qilinadi — shunda ilova
    # meros bo'lgan noto'g'ri ANTHROPIC_MODEL kabi qiymatlarni "" bilan tozalab,
    # kod ichidagi standart modelga qaytishi mumkin bo'ladi.
    raw = [os.getenv(primary_env) or default, *os.getenv(fallback_env, "").split(","), *fallbacks]
    out: list[str] = []
    for item in raw:
        model = (item or "").strip()
        if model and model not in out:
            out.append(model)
    return out


def words_from_segments(segments: list[Segment]) -> list[Word]:
    out: list[Word] = []
    for seg in segments:
        items = WORD_RE.findall(seg.text)
        if not items:
            continue
        dur = max(0.1, seg.end - seg.start)
        slot = dur / len(items)
        for i, word in enumerate(items):
            start = seg.start + i * slot
            end = min(seg.end, start + max(0.18, slot * 0.8))
            out.append(Word(start, end, word))
    return out


def normalize_word(word: str) -> str:
    return word.lower().strip("`'\".,!?;:()[]{}")


def wrap_lines(text: str, limit: int, max_lines: int = 2) -> list[str]:
    if isinstance(text, list):
        text = " ".join(str(x) for x in text)
    if not isinstance(text, str):
        text = str(text)
    words = " ".join((text or "").split()).split()
    if not words:
        return []
    lines: list[str] = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > limit and len(lines) < max_lines - 1:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines[:max_lines]


def wrap_text(text: str, limit: int) -> str:
    return "\n".join(wrap_lines(text, limit, max_lines=3))
