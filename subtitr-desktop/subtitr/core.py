"""Umumiy poydevor: yo'llar, konstantalar, dataklasslar, matn yordamchilari."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import io
from dataclasses import dataclass
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

ENV_FILE = ROOT / ".env"
VENV_DIR = ROOT / ".venv"


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


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Word:
    start: float
    end: float
    word: str


@dataclass
class ReadingPair:
    """Bitta GAP va uning tarjimasi — Yordamchi saytining `.md` formati uchun.

    `new_paragraph` nutqdagi uzoq jimlikdan keyin keladigan gapni belgilaydi
    (o'sha joyda `.md` da ikki bo'sh qator qo'yiladi)."""
    start: float
    end: float
    source: str
    target: str
    new_paragraph: bool


@dataclass
class ReadingBlock:
    """O'qish uchun matndagi bitta abzats (bir nechta subtitr bo'lagidan
    yig'ilgan). Vaqtlari saqlanadi — kerak bo'lsa videodagi joyini topish
    uchun."""
    start: float
    end: float
    text: str


def ensure_dirs() -> None:
    for path in (KINO_DIR, OUT_DIR, TMP_DIR, MODEL_DIR, DICT_DIR, CACHE_DIR):
        path.mkdir(parents=True, exist_ok=True)
    if load_dotenv and ENV_FILE.exists():
        load_dotenv(ENV_FILE)
    elif load_dotenv:
        load_dotenv()


def emit(kind: str, **data: Any) -> None:
    data["type"] = kind
    print(json.dumps(data, ensure_ascii=False), flush=True)


# Ish davomida nechta AI so'rovi ketgani. Boshlashdan oldingi baho taxminiy;
# bu esa haqiqiy son — ayniqsa yutilgan nutqni qayta o'qish so'rovlar sonini
# o'zgaruvchan qilgandan keyin kerak bo'ldi.
USAGE: dict[str, int] = {}


def _count(name: str, n: int = 1) -> None:
    USAGE[name] = USAGE.get(name, 0) + n


def reset_usage() -> None:
    USAGE.clear()


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


def ai_retry_backoff() -> None:
    """Pause before retrying after every provider failed (likely rate limited)."""
    import time
    delay = _env_float("AI_RETRY_BACKOFF_SEC", 6.0)
    if delay > 0:
        time.sleep(delay)


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
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


_JS_RUNTIME_CACHE: str | None = None


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
