"""Transkriptдан qisqa, mazmunли sarlavha (fayl nomi uchun).

AI (Gemini -> OpenAI) bilan videoning nima haqida ekanini 2-4 so'zlik nom
qiladi va uni fayl nomiga mos qilib tozalaydi. Xato bo'lsa zaxira nom.
"""
from __future__ import annotations

import logging
import re

from config import settings
from worker import aiclient

logger = logging.getLogger(__name__)

_SYS = (
    "Senga video transkripti beriladi. Uning mavzusini bildiruvchi JUDA QISQA "
    "(2-4 so'z) sarlavha ber — matn qaysi tilda bo'lsa o'sha tilda. Faqat "
    "sarlavhani qaytar, qo'shtirnoq va izohsiz."
)


def _gemini(text: str) -> str:
    # max_output_tokens keng (100): 2.5 modellarda "thinking" tokenlari ham shu
    # limitga kiradi — tor limit bo'sh javob qaytarishi mumkin.
    return aiclient.gemini_generate(
        text, _SYS, model=settings.gemini_model,
        temperature=0.3, json_mode=False, max_output_tokens=100,
    )


def _claude(text: str) -> str:
    return aiclient.claude_generate(text, _SYS)


def _openai(text: str) -> str:
    return aiclient.openai_generate(text, _SYS, temperature=0.3, json_mode=False)


def slugify(name: str, fallback: str = "matn", max_len: int = 40) -> str:
    """Sarlavhani fayl nomiga mos qiladi (harf/raqam/tire, qisqa)."""
    name = (name or "").strip().replace("’", "").replace("ʻ", "").replace("'", "")
    name = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)  # belgilarni olib tashlash
    name = re.sub(r"[\s_-]+", "-", name).strip("-").lower()
    if len(name) > max_len:
        name = name[:max_len].rstrip("-")
    return name or fallback


def make_title(text: str, fallback: str = "matn") -> str:
    """Transkriptдан qisqa sarlavha (fayl nomi uchun, tozalangan)."""
    snippet = (text or "").strip()[:1500]
    if not snippet:
        return fallback
    for name, available, func in [
        ("gemini", aiclient.gemini_available(), _gemini),
        ("claude", aiclient.claude_available(), _claude),
        ("openai", aiclient.openai_available(), _openai),
    ]:
        if not available:
            continue
        try:
            raw = func(snippet)
            slug = slugify(raw, fallback)
            if slug and slug != fallback:
                logger.info("Sarlavha: '%s' -> '%s'", raw.strip()[:40], slug)
                return slug
        except Exception as exc:
            logger.warning("Sarlavha '%s' xato: %s", name, exc)
            continue
    return fallback
