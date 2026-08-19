"""Videodagi so'zlardan tarjimali + tasniflangan lug'at tuzish (lug'at rejimi).

Segmentlardan noyob so'zlarni (paydo bo'lish tartibida) ajratib, har birini AI
orqali tarjima qiladi VA so'z turkumi (ot/fe'l/...) hamda yordamchi toifasini
(artikl/predlog/ko'makchi/bog'lovchi) aniqlaydi — PDF lug'at guruhlash uchun.
Gemini -> OpenAI fallback. Funksiya sinxron (asyncio.to_thread da chaqiriladi).
"""
from __future__ import annotations

import logging
import re

from config import settings
from worker import aiclient
from worker._llm import loads_lenient, to_payload

logger = logging.getLogger(__name__)

_LANG_NAME = {"uz": "o'zbek", "ru": "rus", "en": "ingliz"}

# So'z — ichki apostrof bilan ("don't", "we've", o'zbek "bo'ladi/to'g'ri")
_WORD_RE = re.compile(r"[^\W\d_]+(?:['’ʼʻ][^\W\d_]+)*", re.UNICODE)

_BATCH = 100        # bitta AI chaqiruvида tasniflanadigan so'zlar
_MAX_WORDS = 500    # juda uzun videolar uchun cheklov

# Deterministik yordamchi so'z tasnifi (LLM xato qilsa ham to'g'ri guruhlansin)
_HELPERS = {
    "en": {
        "artikl": {"a", "an", "the"},
        "predlog": {"in", "on", "at", "to", "for", "from", "with", "by", "of",
                    "about", "into", "onto", "over", "under", "above", "below",
                    "after", "before", "between", "through", "during", "without",
                    "against", "among", "around", "off", "out", "up", "down"},
        "bog'lovchi": {"and", "but", "or", "so", "because", "if", "when", "while",
                       "as", "that", "than", "though", "although", "since",
                       "unless", "whether", "nor", "yet"},
    },
    "ru": {
        "predlog": {"в", "во", "на", "с", "со", "к", "ко", "у", "о", "об", "по",
                    "за", "из", "от", "до", "для", "под", "над", "при", "про",
                    "без", "через", "между", "около"},
        "bog'lovchi": {"и", "а", "но", "или", "что", "чтобы", "если", "когда",
                       "потому", "хотя", "как", "чем", "то", "либо", "зато"},
    },
    "uz": {
        "ko'makchi": {"bilan", "uchun", "kabi", "singari", "sari", "qadar",
                      "tomon", "orqali", "uzra", "bo'yicha", "haqida", "keyin",
                      "oldin", "so'ng", "qarshi"},
        "bog'lovchi": {"va", "ham", "ammo", "lekin", "biroq", "yoki", "chunki",
                       "agar", "garchi", "basharti", "ya'ni", "yoxud", "balki"},
        "yuklama": {"faqat", "hatto", "axir", "naqadar", "qani"},
    },
}


def _norm_word(w: str) -> str:
    return (w or "").strip().lower().replace("’", "'").replace("ʼ", "'").replace("ʻ", "'")


def _helper_of(word: str, src_lang: str) -> str:
    """So'z yordamchi bo'lsa toifasini qaytaradi (artikl/predlog/ko'makchi/bog'lovchi)."""
    groups = _HELPERS.get((src_lang or "").lower())
    if not groups:
        return ""
    nw = _norm_word(word)
    for cat, words in groups.items():
        if nw in words:
            return cat
    return ""


def extract_unique_words(segments: list[dict]) -> list[str]:
    """Noyob so'zlar — video davomida paydo bo'lish tartibida (har biri 1 marta)."""
    seen: dict[str, None] = {}
    for seg in segments:
        for match in _WORD_RE.findall((seg.get("text") or "").lower()):
            if len(match) < 2:
                continue
            if match not in seen:
                seen[match] = None
                if len(seen) >= _MAX_WORDS:
                    return list(seen.keys())
    return list(seen.keys())


def _prompt(target_name: str, src_name: str) -> str:
    return (
        f"Sen ikki tilli lug'at va {src_name} tili grammatikasi mutaxassisisan. "
        f"Senga JSON obyekt beriladi: kalit = raqam, qiymat = bitta {src_name} "
        f"so'zi. Har bir so'z uchun JSON obyekt qaytar:\n"
        f'  "t" = {target_name} tilidagi eng asosiy ma\'nosi (qisqa, 1-3 so\'z),\n'
        f'  "p" = so\'z turkumi (FAQAT shu qiymatlardan biri, o\'zbekcha): '
        f"fe'l, olmosh, ravish — aks holda \"yo'q\",\n"
        f'  "h" = yordamchi so\'z toifasi (agar yordamchi bo\'lsa): '
        f"artikl, predlog, ko'makchi, bog'lovchi, yuklama, modal — aks holda \"yo'q\".\n"
        f"Masalan: {{\"0\":{{\"t\":\"...\",\"p\":\"fe'l\",\"h\":\"yo'q\"}}}}.\n"
        f"QAT'IY: AYNAN o'sha raqamli kalitlar bilan JSON obyekt qaytar. Faqat JSON."
    )


def _gemini(words: list[str], target_name: str, src_name: str) -> str:
    return aiclient.gemini_generate(
        to_payload(words), _prompt(target_name, src_name),
        model=settings.gemini_model, temperature=0.2,
    )


def _claude(words: list[str], target_name: str, src_name: str) -> str:
    return aiclient.claude_generate(to_payload(words), _prompt(target_name, src_name))


def _openai(words: list[str], target_name: str, src_name: str) -> str:
    return aiclient.openai_generate(
        to_payload(words), _prompt(target_name, src_name), temperature=0.2,
    )


def _parse(content: str, words: list[str]) -> tuple[list[dict], int]:
    data = loads_lenient(content)
    block = data if isinstance(data, dict) else {}
    out: list[dict] = []
    matched = 0
    for i, w in enumerate(words):
        v = block.get(str(i))
        if isinstance(v, dict):
            t = str(v.get("t", "")).strip()
            p = str(v.get("p", "")).strip()
            h = str(v.get("h", "")).strip()
        elif isinstance(v, (str, int, float)):
            t, p, h = str(v).strip(), "", ""
        else:
            t, p, h = "", "", ""
        out.append({"word": w, "translation": t or w, "pos": p, "helper": h})
        if t:
            matched += 1
    return out, matched


def _classify_chunk(words: list[str], target_name: str, src_name: str) -> list[dict]:
    providers = [
        ("gemini", aiclient.gemini_available(), _gemini),
        ("claude", aiclient.claude_available(), _claude),
        ("openai", aiclient.openai_available(), _openai),
    ]
    for name, available, func in providers:
        if not available:
            continue
        try:
            content = func(words, target_name, src_name)
            out, matched = _parse(content, words)
            if matched < max(1, len(words) // 2):
                raise ValueError(f"kam tarjima ({matched}/{len(words)})")
            return out
        except Exception as exc:
            logger.warning("Lug'at '%s' xato (%s) — keyingi provayder", name, exc)
            continue
    raise RuntimeError("Lug'at tuzilmadi (AI provayderlar ishlamadi)")


def build_vocabulary(
    segments: list[dict], target_lang: str, src_lang: str = ""
) -> list[dict]:
    """Segmentlardan tasniflangan lug'at — [{word,translation,pos,helper}, ...]
    (paydo bo'lish tartibida)."""
    words = extract_unique_words(segments)
    if not words:
        return []
    target_name = _LANG_NAME.get(target_lang, target_lang)
    src_name = _LANG_NAME.get((src_lang or "").lower(), "manba")

    _valid_h = {"artikl", "predlog", "ko'makchi", "bog'lovchi", "yuklama", "modal"}
    entries: list[dict] = []
    for i in range(0, len(words), _BATCH):
        chunk = words[i : i + _BATCH]
        entries.extend(_classify_chunk(chunk, target_name, src_name))
    # Yordamchi toifani deterministik aniqlash (LLM xato qilsa ham to'g'ri)
    for e in entries:
        det = _helper_of(e["word"], src_lang)
        if det:
            e["helper"] = det
        elif _norm_word(e.get("helper")) not in _valid_h:
            e["helper"] = ""
    logger.info("Lug'at tuzildi: %d so'z (%s<-%s)", len(entries), target_lang, src_lang)
    return entries


def build_vocab_map(
    segments: list[dict], target_lang: str, src_lang: str = ""
) -> dict[str, str]:
    """dual_vocab (video ustidagi lug'at) uchun {normalize(so'z): tarjima} map.

    build_vocabulary'dan foydalanadi, lekin natijani so'z->tarjima lug'atiga
    aylantiradi. So'z o'zi bilan bir xil tarjima (tarjima qilinmagan) tashlanadi
    — ekranda "the - the" kabi foydasiz juftlar chiqmasin.
    """
    # subtitles.normalize_word bilan bir xil kalit — scroll qatlamida
    # so'zlar aynan shu normalize bilan qidiriladi.
    from worker.subtitles import normalize_word

    entries = build_vocabulary(segments, target_lang, src_lang)
    out: dict[str, str] = {}
    for e in entries:
        w = normalize_word(e.get("word"))
        tr = str(e.get("translation") or "").strip()
        if w and tr and tr.lower() != w:
            out[w] = tr
    return out
