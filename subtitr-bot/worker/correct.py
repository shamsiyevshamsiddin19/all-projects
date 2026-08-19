"""AI bilan subtitr matnini tuzatish (xom Whisper -> to'g'ri matn).

Whisper ayniqsa o'zbek tilini zaif yozadi (kam resursli til). Bu modul xom
ASR matnini LLM ga berib to'g'rilaydi — KONTEKST bilan (atrofdagi qatorlar)
va bo'laklarga bo'lib (uzun videolar uchun): har bo'lak fokuslanган, ammo
mavzu/atamani tushunish uchun atrofdagi qatorlarni ko'radi. Fallback:
avval Gemini (kuchli model), tugasa OpenAI.

Tarjima QILMAYDI — faqat o'sha tildagi imlo/so'z/tinishni tuzatadi.
"""
from __future__ import annotations

import logging

from config import settings
from worker import aiclient
from worker._llm import from_windowed_response, to_windowed_payload

logger = logging.getLogger(__name__)

_LANG_NAME = {"uz": "o'zbek", "ru": "rus", "en": "ingliz"}

# Bo'lak hajmi va kontekst (uzun videolar uchun — bitta ulkan chaqiruv emas)
_BATCH = 50
_CTX = 8


def _uz_extra() -> str:
    """O'zbek tiliga maxsus yo'riqnoma (alohida e'tibor)."""
    return (
        "- O'zbek LOTIN imlosi QAT'IY to'g'ri: o' (oʻ), g' (gʻ), sh, ch, ng. "
        "Masalan: bo'ladi, o'zbek, to'g'ri, yo'q, kerak, qiladi, mustaqillik.\n"
        "- ASR o'zbekchani ko'p buzadi: yaqin eshitilgan so'zni MAZMUNGA qarab "
        "to'g'ri so'z bilan almashtir (kontekstdan foydalan).\n"
        "- Diniy/arabcha iboralar to'g'ri: Alloh, Qur'on, payg'ambar, "
        "sallallohu alayhi vasallam, inshaalloh, omin, hadis, jannat.\n"
        "- Ruscha/inglizcha kirib qolgan so'zlarni o'zbekcha talaffuzda to'g'rila "
        "yoki asl shaklida qoldir (mazmunga qarab).\n"
        "Misol: {\"0\":\"faygamberimiz sallallahu alaihi\"} -> "
        "{\"0\":\"payg'ambarimiz sallallohu alayhi\"}\n"
    )


def _system_prompt(lang: str, lang_name: str) -> str:
    extra = _uz_extra() if lang == "uz" else (
        f"- {lang_name} imlo, tinish (.,!?) va bosh harflarni to'g'rila.\n"
        "- Yaqin eshitilgan so'zni mazmunga qarab to'g'ri so'z bilan almashtir.\n"
    )
    return (
        f"Sen — juda tajribali {lang_name} tili subtitr muharririsan. Senga JSON "
        f"obyekt beriladi: uchta qism — \"context_before\", \"translate\", "
        f"\"context_after\".\n"
        f"context_before va context_after — videoning atrofdagi qatorlari, FAQAT "
        f"mavzu, atama va gap oqimini tushunish uchun. Ularni TUZATMA va javobga "
        f"QO'SHMA.\n"
        f"FAQAT \"translate\" ichidagi qiymatlarni TABIIY, TO'G'RI {lang_name} "
        f"tiliga tuzat. ASR (avtomatik nutq tanish) ko'p xato qiladi: so'zni "
        f"noto'g'ri eshitadi, harf almashtiradi, so'zlarni qo'shib/ajratib "
        f"yuboradi, tinish va bosh harf qo'ymaydi.\n"
        + extra +
        f"QAT'IY: TARJIMA QILMA (til o'zgarmaydi). AYNAN o'sha raqamli kalitlar "
        f"bilan TEKIS (flat) JSON obyekt qaytar — faqat \"translate\" kalitlari "
        f"(kalit qo'shma, o'chirma, o'zgartirma). Izoh yo'q. Faqat JSON."
    )


def _gemini_raw(payload: str, system_prompt: str) -> str:
    return aiclient.gemini_generate(
        payload, system_prompt, model=settings.gemini_correct_model, temperature=0,
    )


def _openai_raw(payload: str, system_prompt: str) -> str:
    return aiclient.openai_generate(payload, system_prompt, temperature=0)


def _providers():
    return [
        ("gemini", aiclient.gemini_available(), _gemini_raw),
        ("claude", aiclient.claude_available(), aiclient.claude_generate),
        ("openai", aiclient.openai_available(), _openai_raw),
    ]


def _correct_window(
    texts: list[str], start: int, end: int, lang: str, lang_name: str
) -> dict[int, str]:
    """Bitta bo'lakni (range(start,end)) kontekst bilan tuzatadi."""
    payload = to_windowed_payload(texts, start, end, _CTX)
    system_prompt = _system_prompt(lang, lang_name)
    for name, available, raw_fn in _providers():
        if not available:
            continue
        try:
            content = raw_fn(payload, system_prompt)
            out, _matched = from_windowed_response(content, texts, start, end)
            logger.info("Tuzatish '%s' [%d:%d]", name, start, end)
            return out
        except Exception as exc:
            logger.warning(
                "'%s' tuzatish xatosi [%d:%d] (%s) — keyingi provayder",
                name, start, end, exc,
            )
            continue
    # Hech qaysi provayder ishlamadi — shu bo'lakni xom qoldiramiz
    return {i: texts[i] for i in range(start, end)}


def correct_segments(segments: list[dict], lang: str) -> list[dict]:
    """Segment/cue matnlarini AI bilan KONTEKSTLI, bo'laklab tuzatadi (joyida)."""
    if not settings.correct_enabled:
        return segments
    if lang not in settings.correct_lang_set:
        return segments
    if not segments:
        return segments

    lang_name = _LANG_NAME.get(lang, lang)
    texts = [s.get("text", "") for s in segments]

    corrected = list(texts)
    any_done = False
    for start in range(0, len(texts), _BATCH):
        end = min(start + _BATCH, len(texts))
        try:
            chunk = _correct_window(texts, start, end, lang, lang_name)
            for i, new_text in chunk.items():
                if new_text and new_text.strip():
                    corrected[i] = new_text.strip()
            any_done = True
        except Exception as exc:
            logger.warning("Bo'lak [%d:%d] tuzatilmadi: %s", start, end, exc)
            continue

    if not any_done:
        logger.info("Hech bir AI provayder ishlamadi — xom matn ishlatiladi")
        return segments

    for seg, new_text in zip(segments, corrected):
        if new_text.strip():
            seg["text"] = new_text.strip()
    return segments
