"""Umumiy AI provayder qatlami (Gemini + OpenAI) — timeout va retry bilan.

Nega kerak: Gemini/OpenAI chaqiruvi to'rt modulda (translate/correct/vocab/
titler) takrorlanardi va hech birida timeout/retry yo'q edi:
  - tarmoq osilib qolsa Celery task soatgacha qotardi (navbat tiqilib,
    foydalanuvchi "AI javob bermayapti" deb o'ylardi);
  - Gemini 429 (daqiqalik RPM limiti) darhol OpenAI'ga tushardi — OpenAI
    kvotasi tugagan bo'lsa butun oyna ishlamay qolardi. 429 esa bir daqiqada
    o'zi tiklanadi — biroz kutib qayta urinish kifoya.

Bu modul beradi:
  - gemini_generate(): 120s HTTP timeout; 429 da 15s/30s, 5xx/tarmoqda 3s/8s
    kutib jami 3 urinish; bo'sh javob ham xato hisoblanadi (fallback ishlasin).
  - claude_generate(): Anthropic API (ikkinchi zaxira) — 120s timeout, SDK
    o'zi 429/5xx ni qayta uradi; kredit tugasa 30 daqiqa "o'lik" belgilanadi.
  - openai_generate(): 60s timeout; "insufficient_quota" kelsa provayder
    30 daqiqa "o'lik" deb belgilanadi — har oynada behuda urinmaymiz.
  - claude_available()/openai_available(): kvota-o'lik oynasini hisobga oladi.
"""
from __future__ import annotations

import logging
import time

from config import settings

logger = logging.getLogger(__name__)

_GEMINI_TIMEOUT_MS = 120_000   # 2 daqiqa — eng katta oyna ham sig'adi
_OPENAI_TIMEOUT_S = 60

_ATTEMPTS = 3
_WAITS_429 = [15, 30]   # RPM limiti har daqiqada tiklanadi
_WAITS_NET = [3, 8]     # 5xx / tarmoq / timeout

# Kvota/kredit tugagan provayderni shu vaqtgacha qayta urinmaymiz (monotonic)
_OPENAI_DEAD_S = 30 * 60
_openai_dead_until = 0.0
_CLAUDE_DEAD_S = 30 * 60
_claude_dead_until = 0.0
# Gemini bepul tarif KUNLIK kvotasi tugasa (RESOURCE_EXHAUSTED / PerDay) —
# 60 daqiqa o'lik deb belgilaymiz. Aks holda har bo'lak avval Gemini'ni sinab,
# 429 da 15-30s kutib, keyin Claude'ga o'tardi — uzun kinoda juda sekin.
_GEMINI_DEAD_S = 60 * 60
_gemini_dead_until = 0.0


def _is_daily_quota(exc: Exception) -> bool:
    """429 xatosi KUNLIK kvota tugashimi (per-minute limit emas)."""
    s = str(exc).lower()
    return (
        "resource_exhausted" in s
        or "perday" in s
        or "per day" in s
        or "free_tier" in s
        or "quotavalue" in s
    )


def gemini_available() -> bool:
    """Gemini ishlatsa bo'ladimi (kalit bor va kunlik-kvota oynasida emas)."""
    return bool(settings.gemini_api_key) and time.monotonic() >= _gemini_dead_until

# Claude javobi uchun yetarli chegara: eng katta oyna (50 qator tuzatish yoki
# 100 so'zlik lug'at JSON'i) ~6K token atrofida chiqadi.
_CLAUDE_MAX_TOKENS = 8000
_CLAUDE_TIMEOUT_S = 120


def _retry_wait(exc: Exception, attempt: int) -> int | None:
    """Xato qayta urinishga arzisa kutish soniyasini, aks holda None qaytaradi."""
    import httpx

    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 429:
        return _WAITS_429[min(attempt, len(_WAITS_429) - 1)]
    if isinstance(code, int) and code >= 500:
        return _WAITS_NET[min(attempt, len(_WAITS_NET) - 1)]
    if isinstance(exc, (httpx.TimeoutException, httpx.TransportError, ConnectionError)):
        return _WAITS_NET[min(attempt, len(_WAITS_NET) - 1)]
    return None


def gemini_generate(
    payload: str,
    system_prompt: str,
    *,
    model: str,
    temperature: float = 0.0,
    json_mode: bool = True,
    max_output_tokens: int | None = None,
) -> str:
    """Gemini chaqiruvi — timeout va 429/5xx/tarmoq retry bilan. Matn qaytaradi."""
    from google import genai
    from google.genai import types

    from worker import usage

    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=_GEMINI_TIMEOUT_MS),
    )
    cfg: dict = {"system_instruction": system_prompt, "temperature": temperature}
    if json_mode:
        cfg["response_mime_type"] = "application/json"
    if max_output_tokens:
        cfg["max_output_tokens"] = max_output_tokens

    global _gemini_dead_until
    for attempt in range(_ATTEMPTS):
        usage.bump("gemini")  # har urinish — haqiqiy so'rov (RPD hisobiga kiradi)
        try:
            resp = client.models.generate_content(
                model=model,
                contents=payload,
                config=types.GenerateContentConfig(**cfg),
            )
        except Exception as exc:
            # KUNLIK kvota tugagan bo'lsa — 60 daqiqa o'lik deb belgilab, DARHOL
            # chiqamiz (kutmaymiz): keyingi bo'laklar to'g'ridan-to'g'ri Claude'ga.
            if _is_daily_quota(exc):
                _gemini_dead_until = time.monotonic() + _GEMINI_DEAD_S
                logger.warning(
                    "Gemini KUNLIK kvotasi tugagan — %d daqiqa qayta urinilmaydi "
                    "(tarjima Claude/OpenAI bilan davom etadi)",
                    _GEMINI_DEAD_S // 60,
                )
                raise
            wait = _retry_wait(exc, attempt)
            if wait is None or attempt == _ATTEMPTS - 1:
                raise
            logger.warning(
                "Gemini xatosi (urinish %d/%d, %ds kutiladi): %s",
                attempt + 1, _ATTEMPTS, wait, exc,
            )
            time.sleep(wait)
            continue

        text = (resp.text or "").strip()
        if text:
            return text
        # Bo'sh javob (safety-blok yoki token tugashi) — bir marta qayta urinamiz
        if attempt == _ATTEMPTS - 1:
            break
        logger.warning("Gemini bo'sh javob qaytardi (urinish %d/%d)", attempt + 1, _ATTEMPTS)
        time.sleep(2)

    raise ValueError("Gemini bo'sh javob qaytardi")


def claude_available() -> bool:
    """Claude ishlatsa bo'ladimi (kalit bor va kredit-o'lik oynasida emas)."""
    return bool(settings.anthropic_api_key) and time.monotonic() >= _claude_dead_until


def claude_generate(payload: str, system_prompt: str) -> str:
    """Claude (Anthropic) chaqiruvi — ikkinchi zaxira provayder.

    Diqqat: temperature yuborilmaydi — Opus 4.7+ modellarda sampling
    parametrlari 400 xato qaytaradi. SDK 429/5xx ni o'zi qayta uradi.
    JSON talab prompt orqali; javob fence bilan kelsa loads_lenient tozalaydi.
    """
    global _claude_dead_until
    import anthropic

    from worker import usage

    usage.bump("claude")
    # base_url qat'iy — mashinadagi ANTHROPIC_BASE_URL (boshqa dastur proxysi)
    # so'rovni begona serverga olib ketmasin.
    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key,
        base_url="https://api.anthropic.com",
        timeout=_CLAUDE_TIMEOUT_S,
        max_retries=2,
    )
    try:
        resp = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=_CLAUDE_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": payload}],
        )
    except Exception as exc:
        if "credit balance is too low" in str(exc):
            _claude_dead_until = time.monotonic() + _CLAUDE_DEAD_S
            logger.warning(
                "Claude krediti tugagan — %d daqiqa qayta urinilmaydi",
                _CLAUDE_DEAD_S // 60,
            )
        raise

    text = "".join(
        b.text for b in resp.content if getattr(b, "type", "") == "text"
    ).strip()
    if not text:
        raise ValueError("Claude bo'sh javob qaytardi")
    return text


def openai_available() -> bool:
    """OpenAI ishlatsa bo'ladimi (kalit bor va kvota-o'lik oynasida emas)."""
    return bool(settings.openai_api_key) and time.monotonic() >= _openai_dead_until


def openai_generate(
    payload: str,
    system_prompt: str,
    *,
    temperature: float = 0.0,
    json_mode: bool = True,
) -> str:
    """OpenAI chaqiruvi — timeout bilan; kvota tugasa provayder vaqtincha o'chadi."""
    global _openai_dead_until
    from openai import OpenAI

    from worker import usage

    usage.bump("openai")
    client = OpenAI(
        api_key=settings.openai_api_key,
        timeout=_OPENAI_TIMEOUT_S,
        max_retries=1,
    )
    kwargs: dict = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": payload},
        ],
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    # GPT-5 oilasi maxsus temperature ni qabul qilmaydi (faqat default)
    if not settings.openai_model.lower().startswith("gpt-5"):
        kwargs["temperature"] = temperature
    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception as exc:
        if "insufficient_quota" in str(exc):
            _openai_dead_until = time.monotonic() + _OPENAI_DEAD_S
            logger.warning(
                "OpenAI kvotasi tugagan — %d daqiqa qayta urinilmaydi",
                _OPENAI_DEAD_S // 60,
            )
        raise

    content = (resp.choices[0].message.content or "").strip()
    if not content:
        raise ValueError("OpenAI bo'sh javob qaytardi")
    return content
