"""Matn tarjimasi: AI provayderlar, glossariy, so'z ro'yxati."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from .core import AI_MIN_SPLIT_BATCH, COMMON_WORDS, PHRASES, SOURCE_LANG_NAMES, Segment, TARGET_LANG_NAMES, WORD_RE, _count, _env_float, ai_retry_backoff, ai_throttle, emit, model_candidates, normalize_word
from .cache import _cache_enabled, _load_json, _save_json


def json_object_from_text(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def indexed_values(data: dict[str, Any], count: int, fallback: list[str]) -> tuple[list[str], list[str], list[str]]:
    block = data.get("translate")
    if not isinstance(block, dict):
        block = data
    out_tr: list[str] = []
    out_pos: list[str] = []
    out_lemma: list[str] = []
    for i in range(count):
        value = block.get(str(i)) if isinstance(block, dict) else None
        pos = ""
        lemma = ""
        if isinstance(value, dict):
            pos = str(value.get("pos") or "").lower().strip()
            lemma = str(value.get("lemma") or value.get("base") or "").strip()
            value = value.get("t") or value.get("translation") or value.get("text")
        text = str(value).strip() if value is not None else ""
        out_tr.append(text or fallback[i])
        out_pos.append(pos)
        out_lemma.append(lemma)
    return out_tr, out_pos, out_lemma


def subtitle_prompt(target_lang: str, source_lang: str, glossary: dict[str, str] | None = None) -> str:
    target_name = TARGET_LANG_NAMES.get(target_lang, target_lang)
    source_name = SOURCE_LANG_NAMES.get(source_lang, source_lang or "source language")
    gloss = ""
    if glossary:
        pairs = "; ".join(f"{k} = {v}" for k, v in list(glossary.items())[:60])
        gloss = (
            "Names/terms glossary — ALWAYS use exactly these target forms for "
            f"consistency across the whole film: {pairs}\n"
        )
    return (
        "You are an expert film subtitle translator.\n"
        f"Translate from {source_name} to natural spoken {target_name}.\n"
        + gloss +
        "Input is a JSON object with context_before, translate, and context_after.\n"
        "Use context_before/context_after only to understand pronouns, tone, and continuity.\n"
        "Return a flat JSON object for translate keys only, with exactly the same numeric keys.\n"
        "Rules:\n"
        "- Keep each subtitle concise, natural, and easy to read on screen.\n"
        "- Preserve names, brands, numbers, jokes, questions, warnings, and emotional tone.\n"
        "- Avoid word-for-word translation when it sounds unnatural.\n"
        "- Remove filler words only when they add no meaning.\n"
        "- For Uzbek, use clear everyday Uzbek Latin script with correct apostrophes.\n"
        "- No explanations, no markdown, JSON only."
    )


def ai_translate_batch(
    texts: list[str],
    target_lang: str,
    source_lang: str = "",
    before: list[str] | None = None,
    after: list[str] | None = None,
    glossary: dict[str, str] | None = None,
) -> tuple[list[str], str]:
    if not texts:
        return [], ""
    prompt = subtitle_prompt(target_lang, source_lang, glossary)
    payload = json.dumps(
        {
            "context_before": before or [],
            "translate": {str(i): text for i, text in enumerate(texts)},
            "context_after": after or [],
        },
        ensure_ascii=False,
    )

    providers = [
        ("openai", bool(os.getenv("OPENAI_API_KEY")), translate_openai),
        ("claude", bool(os.getenv("ANTHROPIC_API_KEY")), translate_claude),
        ("gemini", bool(os.getenv("GEMINI_API_KEY")), translate_gemini),
        ("groq", bool(os.getenv("GROQ_API_KEY")), translate_groq),
    ]
    # Umuman kalit yo'q bo'lsa — kutish va qayta urinishning ma'nosi yo'q
    # (ilgari har bir to'plam uchun 30 soniya behuda kutilardi).
    if not any(enabled for _, enabled, _ in providers):
        return [offline_translate_text(text) for text in texts], "offline_dictionary"

    errors: list[str] = []

    for attempt in range(5):
        for name, enabled, fn in providers:
            if not enabled:
                continue
            try:
                data = fn(prompt, payload)
                parsed = json_object_from_text(data)
                out_tr, _, _ = indexed_values(parsed, len(texts), texts)
                matched = sum(1 for i, value in enumerate(out_tr) if value and value != texts[i])
                # Javob to'liq bo'lmasa qolgan qatorlar asl matn bilan qoladi —
                # to'plamni bo'lib qayta so'raganimiz ma'qul.
                need = max(1, int(len(texts) * _env_float("TRANSLATE_MIN_COVERAGE", 0.8)))
                if matched < need:
                    raise RuntimeError(f"AI javobida tarjima kam ({matched}/{len(texts)})")
                ai_throttle()
                return out_tr, name
            except Exception as exc:
                errors.append(f"{name}: {exc}")
                continue
        ai_retry_backoff()

    # Katta to'plam bir marta ishlamasligi ko'pincha vaqtinchalik (limit yoki
    # javob uzunligi) — ikkiga bo'lib qayta urinamiz. Aks holda 50 ta qator
    # jimgina tarjimasiz qolib ketadi.
    if len(texts) > AI_MIN_SPLIT_BATCH:
        half = len(texts) // 2
        left, lp = ai_translate_batch(
            texts[:half], target_lang, source_lang, before, texts[half:half + 4], glossary
        )
        right, rp = ai_translate_batch(
            texts[half:], target_lang, source_lang, texts[max(0, half - 4):half], after, glossary
        )
        provider = lp if lp != "offline_dictionary" else rp
        return left + right, provider

    emit(
        "progress",
        message=f"Diqqat: {len(texts)} qator tarjima qilinmadi (AI javob bermadi)",
        progress=0.5,
    )
    return [offline_translate_text(text) for text in texts], "offline_dictionary"


def translate_openai(prompt: str, payload: str) -> str:
    _count("translate")
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    last_error: Exception | None = None
    for model in model_candidates(
        "OPENAI_MODEL",
        "gpt-4o-mini",
        "OPENAI_FALLBACK_MODELS",
        ["gpt-4o"],
    ):
        try:
            if hasattr(client, "responses"):
                try:
                    resp = client.responses.create(
                        model=model,
                        input=[
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": payload},
                        ],
                        text={"format": {"type": "json_object"}, "verbosity": "low"},
                        reasoning={"effort": os.getenv("OPENAI_REASONING_EFFORT", "low")},
                    )
                    text = getattr(resp, "output_text", "") or ""
                    if text:
                        return text
                except Exception as exc:
                    last_error = exc
            resp = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": payload},
                ],
            )
            return resp.choices[0].message.content or "{}"
        except Exception as exc:
            last_error = exc
            continue
    raise RuntimeError(f"OpenAI tarjima ishlamadi: {last_error}")


def translate_claude(prompt: str, payload: str) -> str:
    _count("translate")
    from anthropic import Anthropic

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192"))
    # Tarjima uchun "thinking" kerak emas — uni o'chirib token tejaymiz
    # (Sonnet 5 da u sukut bo'yicha YOQILGAN va qo'shimcha token yeydi).
    # ANTHROPIC_THINKING=adaptive qilib fikrlashni yoqish mumkin.
    thinking_off = os.getenv("ANTHROPIC_THINKING", "disabled").strip().lower() in {"disabled", "off", "none", ""}

    def _extract(resp: Any) -> str:
        return "".join(
            getattr(block, "text", "")
            for block in (resp.content or [])
            if getattr(block, "type", "") == "text"
        ).strip()

    last_error: Exception | None = None
    for model in model_candidates(
        "ANTHROPIC_MODEL",
        "claude-sonnet-5",
        "ANTHROPIC_FALLBACK_MODELS",
        ["claude-haiku-4-5"],
    ):
        base: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": prompt,
            "messages": [{"role": "user", "content": payload}],
        }
        # Avval thinking'ni o'chirib urinamiz; ba'zi modellar (masalan Fable 5)
        # disabled'ni qabul qilmaydi — u holda thinking'siz zaxira urinish.
        attempts = [{**base, "thinking": {"type": "disabled"}}, base] if thinking_off else [base]
        for kwargs in attempts:
            try:
                text = _extract(client.messages.create(**kwargs))
                if text:
                    return text
            except Exception as exc:
                last_error = exc
                continue
    raise RuntimeError(f"Claude tarjima ishlamadi: {last_error}")


def translate_gemini(prompt: str, payload: str) -> str:
    _count("translate")
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    last_error: Exception | None = None
    for model in model_candidates(
        "GEMINI_MODEL",
        "gemini-2.5-pro",
        "GEMINI_FALLBACK_MODELS",
        ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
    ):
        try:
            resp = client.models.generate_content(
                model=model,
                contents=payload,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    temperature=0.15,
                    response_mime_type="application/json",
                ),
            )
            return resp.text or "{}"
        except Exception as exc:
            last_error = exc
            continue
    raise RuntimeError(f"Gemini tarjima ishlamadi: {last_error}")


# Groq matn modellarini vaqti-vaqti bilan iste'moldan chiqaradi (llama-3.3-70b
# va llama-3.1-8b shunday yo'qoldi va tarjima jimgina oflayn lug'atga tushib
# qoldi). Shuning uchun nom topilmasa, hisobdagi mavjud modellar so'raladi.
_GROQ_DISCOVERED_MODEL: str | None = None

# Tarjimaga yaramaydigan (nutq, xavfsizlik, TTS) modellar.
_GROQ_SKIP_MODEL_RE = re.compile(r"whisper|tts|guard|orpheus|embed", re.I)


def _groq_available_model(client: Any) -> str | None:
    """Hisobda mavjud, matn uchun yaroqli birinchi modelni topadi."""
    global _GROQ_DISCOVERED_MODEL
    if _GROQ_DISCOVERED_MODEL:
        return _GROQ_DISCOVERED_MODEL
    try:
        ids = sorted(m.id for m in client.models.list().data)
    except Exception:
        return None
    usable = [m for m in ids if not _GROQ_SKIP_MODEL_RE.search(m)]
    if not usable:
        return None
    # Kattaroq model odatda sifatliroq — nomidagi eng katta raqamga qarab.
    def size(name: str) -> float:
        found = re.findall(r"(\d+(?:\.\d+)?)\s*b\b", name, re.I)
        return max((float(x) for x in found), default=0.0)
    usable.sort(key=size, reverse=True)
    _GROQ_DISCOVERED_MODEL = usable[0]
    return _GROQ_DISCOVERED_MODEL


def translate_groq(prompt: str, payload: str) -> str:
    _count("translate")
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    last_error: Exception | None = None
    candidates = model_candidates(
        "GROQ_TEXT_MODEL",
        "openai/gpt-oss-120b",
        "GROQ_TEXT_FALLBACK_MODELS",
        ["openai/gpt-oss-20b", "qwen/qwen3.8-27b"],
    )
    discovered = _GROQ_DISCOVERED_MODEL
    if discovered and discovered not in candidates:
        candidates.append(discovered)

    for attempt in range(2):
        for model in candidates:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": payload},
                ],
                "temperature": 0.15,
            }
            try:
                try:
                    resp = client.chat.completions.create(response_format={"type": "json_object"}, **kwargs)
                except Exception:
                    resp = client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or "{}"
            except Exception as exc:
                last_error = exc
                continue
        if attempt == 0:
            # Hech biri ishlamadi — ehtimol modellar nomi eskirgan. Hisobdagi
            # mavjud ro'yxatdan yaroqlisini topib, yana bir marta urinamiz.
            found = _groq_available_model(client)
            if not found or found in candidates:
                break
            candidates = [found]
    raise RuntimeError(f"Groq tarjima ishlamadi: {last_error}")


def offline_translate_text(text: str) -> str:
    """Kalitsiz ishlaydigan zaxira tarjima — faqat ichki lug'at asosida.

    Lug'at qamrovi past bo'lsa bo'sh satr qaytaradi: yarim tarjima qilingan
    aralash matn ekranda aytilmagan so'zlar bo'lib ko'rinadi, bo'sh satr esa
    faqat originalni qoldiradi (`SUBTITR_OFFLINE_MIN_COVERAGE` bilan sozlanadi)."""
    source = " ".join(text.split())
    if not source:
        return ""

    # Avval ko'p so'zli iboralar ("thank you" -> "rahmat"), keyin alohida so'zlar.
    working = source
    phrase_hits = 0
    for phrase, translation in PHRASES.items():
        working, n = re.subn(r"\b" + re.escape(phrase) + r"\b", translation, working, flags=re.I)
        if n:
            phrase_hits += n * len(phrase.split())

    parts: list[str] = []
    total = len(re.findall(r"\w[\w']*", source, re.UNICODE))
    known = phrase_hits
    for token in re.findall(r"[A-Za-z']+|[^\w\s]+|\s+|\w+", working, re.UNICODE):
        if token.isspace() or re.fullmatch(r"[^\w\s]+", token):
            parts.append(token)
            continue
        key = token.lower().strip("'")
        translated = COMMON_WORDS.get(key)
        if translated is None:
            translated = token
        else:
            known += 1
        if token[:1].isupper() and translated:
            translated = translated[:1].upper() + translated[1:]
        parts.append(translated)

    # So'zma-so'z almashtirish gap tuzilishini saqlamaydi: uzun gapda natija
    # hech kim aytmagan matnga aylanadi. Shu sababli faqat qisqa va to'liq
    # lug'atda bor satrlarni qaytaramiz ("thank you" -> "rahmat"), qolganini
    # bo'sh qoldiramiz — ekranda faqat original eshitilgan matn qoladi.
    max_words = int(os.getenv("SUBTITR_OFFLINE_MAX_WORDS", "4"))
    min_coverage = _env_float("SUBTITR_OFFLINE_MIN_COVERAGE", 1.0)
    if not total or total > max_words or (known / total) < min_coverage:
        return ""
    return " ".join("".join(parts).split())


def translate_segments(
    segments: list[Segment],
    target_lang: str,
    source_lang: str,
    progress_lo: float = 0.40,
    progress_hi: float = 0.56,
    cache_path: Path | None = None,
    glossary: dict[str, str] | None = None,
) -> tuple[list[Segment], str]:
    # Kattaroq batch = kamroq API chaqiruvi va kamroq takroriy prompt/kontekst
    # tokeni; sifat saqlanadi. Kontekst atigi bir necha satr — pronoun/oxang
    # uchun yetarli, lekin ortiqcha token yig'maydi. Env orqali sozlanadi.
    batch = max(10, int(os.getenv("TRANSLATE_BATCH", "50")))
    ctx = max(0, int(os.getenv("TRANSLATE_CONTEXT", "4")))
    total = len(segments)

    # Checkpoint: oldingi (uzilib qolgan) ishdan tayyor tarjimalarni yuklaymiz.
    # Kalit — bo'lak tartib raqami emas, matnning o'zi: bo'laklarga bo'lish
    # o'zgarsa, indeks bo'yicha kesh tarjimalarni boshqa qatorlarga yopishtirib
    # yuboradi (ekranda aytilmagan gap paydo bo'ladi).
    cached: dict[str, str] = {}
    if cache_path is not None and _cache_enabled():
        data = _load_json(cache_path)
        if isinstance(data, dict):
            cached = {str(k): str(v) for k, v in data.items()}
    keys = [_text_key(seg.text) for seg in segments]
    out_texts: list[str | None] = [cached.get(key) for key in keys]
    provider = "cache" if any(t is not None for t in out_texts) else ""

    for start in range(0, total, batch):
        end_i = min(start + batch, total)
        idxs = list(range(start, end_i))
        done = end_i
        frac = done / total if total else 1.0
        if all(out_texts[i] is not None for i in idxs):
            emit("progress", message=f"Tarjima {done}/{total} (keshdan)",
                 progress=progress_lo + (progress_hi - progress_lo) * frac)
            continue
        chunk = segments[start:end_i]
        before = [seg.text for seg in segments[max(0, start - ctx):start]]
        after = [seg.text for seg in segments[end_i:end_i + ctx]]
        translated, provider = ai_translate_batch(
            [seg.text for seg in chunk],
            target_lang,
            source_lang=source_lang,
            before=before,
            after=after,
            glossary=glossary,
        )
        for j, i in enumerate(idxs):
            out_texts[i] = translated[j] if j < len(translated) else chunk[j].text
            cached[keys[i]] = out_texts[i] or ""
        if cache_path is not None and _cache_enabled():
            _save_json(cache_path, cached)  # har batchdan keyin saqlaymiz
        emit("progress", message=f"Tarjima {done}/{total}",
             progress=progress_lo + (progress_hi - progress_lo) * frac)

    # Bo'sh satr — "bu qatorni tarjima qilib bo'lmadi" degani; originalni
    # tarjima o'rniga qo'ymaymiz (aks holda bir gap ikki marta ko'rinadi).
    out = [
        Segment(
            segments[i].start,
            segments[i].end,
            segments[i].text if out_texts[i] is None else out_texts[i],
        )
        for i in range(total)
    ]
    return out, provider


def _text_key(text: str) -> str:
    """Kesh kaliti: matnning o'zidan (indeksdan emas) hosil qilinadi."""
    norm = " ".join((text or "").split()).lower()
    return hashlib.sha1(norm.encode("utf-8", "replace")).hexdigest()[:16]


def build_glossary(segments: list[Segment], target_lang: str, source_lang: str) -> dict[str, str]:
    """Film davomida izchillik uchun tez-tez uchraydigan ismlar/atamalarni
    bir marta tarjima qilib, {manba: nishon} lug'atini qaytaradi. AI kaliti
    bo'lmasa yoki ism topilmasa — bo'sh (izchillik faqat AI bilan mazmunli)."""
    has_ai = any(os.getenv(k) for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY"))
    if not has_ai:
        return {}
    # Bosh harfli (ism/atama nomzodi) tokenlarni chastota bo'yicha yig'amiz.
    freq: dict[str, int] = {}
    for seg in segments:
        for tok in WORD_RE.findall(seg.text):
            if len(tok) >= 2 and tok[:1].isupper() and not tok.isupper():
                freq[tok] = freq.get(tok, 0) + 1
    candidates = [w for w, c in sorted(freq.items(), key=lambda x: -x[1]) if c >= 3][:40]
    if not candidates:
        return {}
    try:
        translations, _pos, _lemma, _prov = translate_word_list(candidates, target_lang)
    except Exception:
        return {}
    glossary: dict[str, str] = {}
    for src, tgt in zip(candidates, translations):
        tgt = (tgt or "").strip()
        if tgt and tgt.lower() != src.lower():
            glossary[src] = tgt
    return glossary


def translate_word_list(words: list[str], target_lang: str) -> tuple[list[str], list[str], list[str], str]:
    if not words:
        return [], [], [], ""

    prompt = (
        "Translate each single word to "
        f"{TARGET_LANG_NAMES.get(target_lang, target_lang)}. Use the most common short meaning, "
        "1-3 words. For each word also give: 'pos' = part of speech in English "
        "(pronoun, noun, verb, adjective, adverb, article, preposition, conjunction, numeral, interjection); "
        "'lemma' = the dictionary/base form of the SOURCE word (e.g. plural/inflected -> base form). "
        "Return a JSON object where keys are the numeric indices and values are objects with 't', 'pos', 'lemma'. "
        "Example: {\"0\": {\"t\": \"olma\", \"pos\": \"noun\", \"lemma\": \"apple\"}}"
    )

    tr_list: list[str] = []
    pos_list: list[str] = []
    lemma_list: list[str] = []
    provider = ""

    providers = [
        ("openai", bool(os.getenv("OPENAI_API_KEY")), translate_openai),
        ("claude", bool(os.getenv("ANTHROPIC_API_KEY")), translate_claude),
        ("gemini", bool(os.getenv("GEMINI_API_KEY")), translate_gemini),
        ("groq", bool(os.getenv("GROQ_API_KEY")), translate_groq),
    ]
    if not any(enabled for _, enabled, _ in providers):
        return ([offline_translate_word(w) for w in words], [""] * len(words),
                [""] * len(words), "offline_dictionary")

    def translate_chunk(chunk: list[str]) -> tuple[list[str], list[str], list[str], str]:
        """Bitta to'plamni tarjima qiladi; ishlamasa ikkiga bo'lib qayta uradi."""
        payload = json.dumps({str(i): w for i, w in enumerate(chunk)}, ensure_ascii=False)
        for _attempt in range(3):
            for name, enabled, fn in providers:
                if not enabled:
                    continue
                try:
                    parsed = json_object_from_text(fn(prompt, payload))
                    c_tr, c_pos, c_lemma = indexed_values(
                        parsed, len(chunk), [offline_translate_word(w) for w in chunk]
                    )
                    matched = sum(
                        1 for i, tr in enumerate(c_tr)
                        if tr and tr.lower() != chunk[i].lower()
                        and tr != offline_translate_word(chunk[i])
                    )
                    # Model to'plamning bir qismiga javob bermasligi mumkin —
                    # o'shanda qolgan so'zlar o'z-o'ziga "tarjima" bo'lib
                    # qoladi va lug'atdan tushib ketadi (ekranda o'sha
                    # daqiqalarda kartochka chiqmaydi). Shuning uchun javob
                    # deyarli to'liq bo'lishini talab qilamiz; bo'lmasa
                    # to'plam ikkiga bo'linib qayta so'raladi.
                    need = max(1, int(len(chunk) * _env_float("VOCAB_MIN_COVERAGE", 0.8)))
                    if matched < need:
                        raise RuntimeError(
                            f"Lug'atda yetarli tarjima qilinmadi ({matched}/{len(chunk)})"
                        )
                    ai_throttle()
                    return c_tr, c_pos, c_lemma, name
                except Exception:
                    continue
            ai_retry_backoff()

        # Katta to'plam bir marta ishlamasligi ko'pincha vaqtinchalik. Ikkiga
        # bo'lib qayta urinamiz — aks holda butun bir bo'lak so'z tarjimasiz
        # qoladi va ular lug'atdan butunlay tushib qoladi (ekranda o'sha
        # daqiqalarda hech qanday so'z chiqmaydi).
        if len(chunk) > AI_MIN_SPLIT_BATCH:
            half = len(chunk) // 2
            l_tr, l_pos, l_lem, l_p = translate_chunk(chunk[:half])
            r_tr, r_pos, r_lem, r_p = translate_chunk(chunk[half:])
            best = l_p if l_p != "offline_dictionary" else r_p
            return l_tr + r_tr, l_pos + r_pos, l_lem + r_lem, best

        emit(
            "progress",
            message=f"Diqqat: {len(chunk)} so'z lug'atga tarjima qilinmadi",
            progress=0.58,
        )
        return ([offline_translate_word(w) for w in chunk], [""] * len(chunk),
                [""] * len(chunk), "offline_dictionary")

    batch_size = max(20, int(os.getenv("VOCAB_BATCH", "80")))
    for start in range(0, len(words), batch_size):
        chunk = words[start:start + batch_size]
        c_tr, c_pos, c_lemma, p = translate_chunk(chunk)
        tr_list.extend(c_tr)
        pos_list.extend(c_pos)
        lemma_list.extend(c_lemma)
        provider = p or provider

    return tr_list, pos_list, lemma_list, provider


def offline_translate_word(word: str) -> str:
    return COMMON_WORDS.get(normalize_word(word), word)
