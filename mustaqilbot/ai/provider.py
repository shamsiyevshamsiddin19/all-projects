"""Claude (asosiy) + OpenAI (zaxira) AI provayder.

Mantiq:
  1. Claude bilan urinib ko'riladi (streaming — katta hujjatlar uchun majburiy)
  2. RateLimit / overload / tarmoq xatosida OpenAI ga o'tiladi
  3. Qaysi provayder ishlatilgani qaytariladi

generate_with_search — Claude server-tomonidagi web_search vositasi bilan
(haqiqiy manbalar/statistika uchun); OpenAI'da qidiruv yo'q — oddiy generate.
"""
from __future__ import annotations
import logging
from config import settings

logger = logging.getLogger(__name__)

_claude_client = None
_openai_client = None

# gpt-4o-mini chiqish chegarasi — 16384 token
_OPENAI_MAX_OUT = 16000
_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search", "max_uses": 4}


def _claude():
    global _claude_client
    if _claude_client is None and settings.anthropic_api_key:
        import anthropic
        _claude_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _claude_client


def _openai():
    global _openai_client
    if _openai_client is None and settings.openai_api_key:
        from openai import AsyncOpenAI
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _text_of(msg) -> str:
    return "".join(b.text for b in msg.content if b.type == "text")


async def generate(system_prompt: str, user_prompt: str,
                   max_tokens: int = 8000, model: str | None = None) -> tuple[str, str]:
    """Matn generatsiya qiladi. (text, provider) qaytaradi."""
    import anthropic

    client = _claude()
    if client:
        try:
            # Streaming — katta max_tokens da HTTP timeout bo'lmasligi uchun
            async with client.messages.stream(
                model=model or settings.claude_model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            ) as stream:
                msg = await stream.get_final_message()
            if msg.stop_reason == "max_tokens":
                logger.warning("Claude javobi max_tokens=%s chegarasida uzildi "
                               "(chiqish: %s token)", max_tokens, msg.usage.output_tokens)
            return _text_of(msg), "claude"
        except (anthropic.RateLimitError,
                anthropic.InternalServerError,
                anthropic.APIConnectionError) as e:
            # 429 / 5xx (529 overloaded ham) / tarmoq — zaxiraga o'tamiz
            logger.warning("Claude vaqtincha ishlamayapti (%s) — OpenAI ga o'tilmoqda: %s",
                           type(e).__name__, e)
        except anthropic.APIStatusError as e:
            logger.error("Claude xatosi (%s): %s", e.status_code, e.message)
            raise

    # OpenAI zaxira
    oa = _openai()
    if oa:
        resp = await oa.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=min(max_tokens, _OPENAI_MAX_OUT),
            temperature=0.7,
        )
        text = resp.choices[0].message.content or ""
        return text, "openai"

    raise RuntimeError("AI provayderlar sozlanmagan (ANTHROPIC_API_KEY yoki OPENAI_API_KEY kerak)")


async def generate_with_search(system_prompt: str, user_prompt: str,
                               max_tokens: int = 8000,
                               model: str | None = None,
                               max_searches: int = 4) -> tuple[str, str]:
    """Web search bilan generatsiya (haqiqiy manbalar). Xatoda oddiy generate."""
    import anthropic

    client = _claude()
    if not client or not settings.web_search_on():
        return await generate(system_prompt, user_prompt, max_tokens, model)

    tool = dict(_SEARCH_TOOL, max_uses=max_searches)
    messages = [{"role": "user", "content": user_prompt}]
    try:
        msg = None
        for _ in range(5):  # pause_turn davomiy siklidan himoya
            msg = await client.messages.create(
                model=model or settings.claude_model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=messages,
                tools=[tool],
            )
            if msg.stop_reason == "pause_turn":
                # Server-tool sikli to'xtagan — davom ettiramiz
                messages = [
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": msg.content},
                ]
                continue
            break
        return _text_of(msg), "claude"
    except anthropic.BadRequestError as e:
        # Web search qo'llab-quvvatlanmasa (eski tool nomi va h.k.) — oddiy yo'l
        logger.warning("Web search ishlamadi (400: %s) — oddiy generatsiya", e.message)
        return await generate(system_prompt, user_prompt, max_tokens, model)
    except (anthropic.RateLimitError,
            anthropic.InternalServerError,
            anthropic.APIConnectionError) as e:
        logger.warning("Claude search vaqtincha ishlamadi (%s) — oddiy generatsiya",
                       type(e).__name__)
        return await generate(system_prompt, user_prompt, max_tokens, model)


async def generate_json(system_prompt: str, user_prompt: str,
                        max_tokens: int = 4000, model: str | None = None) -> tuple[str, str]:
    """JSON javob so'rash (krossvord, slayd uchun)."""
    sys = (system_prompt +
           "\n\nFAQAT to'g'ri, to'liq va yopilgan JSON qaytaring — "
           "markdown belgilari (```), izoh yoki boshqa matn qo'shmang.")
    return await generate(sys, user_prompt, max_tokens, model)
