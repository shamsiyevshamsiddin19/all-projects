"""AI tarjima — kontekstли, subtitr-maxsus (arxitektura 5.7).

Tartib: Gemini (bepul) -> Claude -> OpenAI. Tarjima bo'laklarga (batch)
bo'linadi va har bo'lakka atrofdagi qatorlar KONTEKST sifatida beriladi
(tarjima qilinmaydi) — olmosh, ohang, davomli gap saqlanib, tabiiy chiqadi.
Raqamli kalit (index) tizimi: qatorlar joyiga tushadi. Asl=javob (tarjima
qilinmagan) holati aniqlanadi (worker/_llm.py from_windowed_response).

Tezlik: bo'laklar PARALLEL yuboriladi (TRANSLATE_PARALLEL) — uzun kinoda
ketma-ket emas, bir vaqtning o'zida bir nechta bo'lak tarjima qilinadi.
Sifat: (1) GLOSSARIY — takroriy bosh-harfli nom/atamalar oldin bir marta
tarjima qilinib promptga kiritiladi (ismlar hamma joyda izchil bo'ladi);
(2) BO'SHLIQ-TO'LDIRISH — tarjima qilinmay qolgan qatorlar yana urinib
ko'riladi; (3) o'zbekcha tarjimada kirill sizib chiqsa lotinga o'giriladi.
"""
from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import settings
from worker import aiclient
from worker._llm import from_windowed_response, loads_lenient, to_windowed_payload

logger = logging.getLogger(__name__)

_LANG_NAME = {"uz": "o'zbek", "ru": "rus", "en": "ingliz"}

# Bir so'rovda tarjima qilinadigan qatorlar va atrofdagi kontekst qatorlari
_BATCH = 40
_CTX = 6
# Nechta bo'lak parallel yuborilsin (RPM limitiga urilib ketmaslik uchun me'yorli)
_PARALLEL = max(1, settings.translate_parallel)
# Glossariy faqat yetarli uzun matnda tuziladi (qisqa videoda ortiqcha AI chaqiruvi)
_GLOSSARY_MIN_LINES = 25
_GLOSSARY_MAX_TERMS = 40

# Til bo'yicha few-shot misol — og'zaki/lo'nda subtitr uslubini ko'rsatadi
_FEWSHOT = {
    "uz": (
        '{"0":"You know, this is gonna be huge.","1":"I mean, just trust me."}'
        ' -> {"0":"Bu juda katta voqea bo\'ladi.","1":"Menga ishoning."}'
    ),
    "ru": (
        '{"0":"You know, this is gonna be huge."}'
        ' -> {"0":"Это будет нечто грандиозное."}'
    ),
    "en": (
        '{"0":"Eshitdingmi, bu zo\'r bo\'ladi."}'
        ' -> {"0":"You won\'t believe how great this is."}'
    ),
}

# O'zbek KIRILL -> LOTIN (himoya to'ri): prompt aniq lotin so'rasa ham, ba'zi
# provayder kirill chiqarib yuborishi mumkin — bitta videoda alifbo aralashmasin.
_UZ_CYR2LAT = {
    "ў": "o‘", "қ": "q", "ғ": "g‘", "ҳ": "h", "ц": "ts", "щ": "sh",
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ч": "ch", "ш": "sh", "ъ": "’", "ы": "i", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
}


def _has_cyrillic(s: str) -> bool:
    return any("Ѐ" <= ch <= "ӿ" for ch in s)


def uz_to_latin(text: str) -> str:
    """O'zbekcha kirill matnni lotinga o'giradi (bosh harf holatini saqlab)."""
    out = []
    for ch in text:
        low = ch.lower()
        rep = _UZ_CYR2LAT.get(low)
        if rep is None:
            out.append(ch)
        elif ch == low:
            out.append(rep)
        else:  # bosh harf
            out.append(rep[:1].upper() + rep[1:])
    return "".join(out)


def _system_prompt(target_name: str, target_lang: str, glossary: dict | None = None) -> str:
    example = _FEWSHOT.get(target_lang, "")
    script_rule = {
        "uz": (
            "- MUHIM: FAQAT O'ZBEK LOTIN alifbosida yoz (o', g', sh, ch, ng bilan). "
            "HECH QACHON kirill harflardan foydalanma (dunyo, emas дунё).\n"
        ),
        "ru": "- Rus KIRILL alifbosida yoz.\n",
        "en": "- Standart lotin ingliz alifbosida yoz.\n",
    }.get(target_lang, "")
    gloss = ""
    if glossary:
        pairs = ", ".join(f"{k} = {v}" for k, v in list(glossary.items())[:_GLOSSARY_MAX_TERMS])
        gloss = (
            "- IZCHILLIK — quyidagi nom/atamalarni HAMMA JOYDA aynan shunday "
            f"tarjima qil: {pairs}.\n"
        )
    return (
        f"Sen professional SUBTITR tarjimonisan. Senga JSON obyekt beriladi: "
        f"uchta qism — \"context_before\", \"translate\", \"context_after\".\n"
        f"context_before va context_after — videoning oldingi/keyingi qatorlari, "
        f"FAQAT ma'noni (olmosh, davomli gap, ohang) tushunish uchun. Ularni "
        f"TARJIMA QILMA va javobga QO'SHMA.\n"
        f"FAQAT \"translate\" ichidagi qiymatlarni TABIIY va RAVON {target_name} "
        f"tiliga tarjima qil. Qoidalar:\n"
        f"- QISQA va OG'ZAKI yoz (kitobiy emas) — ekranda tez o'qilsin, AMMO "
        f"mazmunni tashlama.\n"
        f"- Asl OHANGNI saqla: savol — savol, undov — undov bo'lsin.\n"
        f"- Ma'nosiz to'ldiruvchilarni (well, you know, I mean, ну вот) tashlab yubor.\n"
        f"- Slang/og'zaki iborani {target_name} og'zaki muqobili bilan ber "
        f"(so'zma-so'z emas).\n"
        f"- Ismlar, brend va atamalarni IZCHIL (hamma joyda bir xil) tarjima qil.\n"
        + script_rule
        + gloss
        + (f"Misol: {example}\n" if example else "")
        + f"QAT'IY: AYNAN o'sha raqamli kalitlar bilan TEKIS (flat) JSON obyekt "
        f"qaytar — faqat \"translate\" kalitlari (kalit qo'shma, o'chirma, "
        f"o'zgartirma). Izoh yo'q. Faqat JSON."
    )


def _gemini_raw(payload: str, system_prompt: str) -> str:
    return aiclient.gemini_generate(
        payload, system_prompt, model=settings.gemini_model, temperature=0.2,
    )


def _openai_raw(payload: str, system_prompt: str) -> str:
    return aiclient.openai_generate(payload, system_prompt, temperature=0.2)


def _providers():
    # Gemini ASOSIY — billing yoqilgan (Tier 1), flash-lite eng arzon (~10x
    # Claude'dan arzon). Claude ishonchli zaxira (kredit bilan), OpenAI oxirgi chora.
    return [
        ("gemini", aiclient.gemini_available(), _gemini_raw),
        ("claude", aiclient.claude_available(), aiclient.claude_generate),
        ("openai", aiclient.openai_available(), _openai_raw),
    ]


def _raw_any(payload: str, system_prompt: str) -> str:
    """Birinchi ishlaydigan provayder javobini qaytaradi (glossariy uchun)."""
    last_exc: Exception | None = None
    for name, available, raw_fn in _providers():
        if not available:
            continue
        try:
            return raw_fn(payload, system_prompt)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            continue
    raise RuntimeError(f"Provayder ishlamadi: {last_exc}")


# ---------------------------------------------------------------- Glossariy (izchillik)

_NAME_RE = re.compile(r"\b[A-ZА-ЯЁ][A-Za-zА-Яа-яЁё''\-]{2,}")


def _build_glossary(texts: list[str], target_name: str, target_lang: str) -> dict:
    """Takroriy bosh-harfli so'zlarni (ism/atama) bir marta tarjima qiladi.

    Bu tarjima batchlar orasida izchillikni ta'minlaydi — masalan "John" hamma
    joyda "Jon" bo'ladi. Xato bo'lsa bo'sh lug'at (jim o'tadi)."""
    if len(texts) < _GLOSSARY_MIN_LINES:
        return {}
    from collections import Counter

    cnt: Counter[str] = Counter()
    for t in texts:
        # Gap boshidagi so'zni tashlaymiz (u har doim bosh harfli — ism emas)
        words = _NAME_RE.findall(t or "")
        for w in words:
            cnt[w] += 1
    # Kamida 2 marta uchragan, uzunligi yetarli nomlar (chindan ism/atama)
    names = [w for w, c in cnt.most_common(_GLOSSARY_MAX_TERMS) if c >= 2 and len(w) >= 3]
    if not names:
        return {}
    payload = json.dumps({str(i): n for i, n in enumerate(names)}, ensure_ascii=False)
    prompt = (
        f"Quyidagi JSON — filmdagi ism, joy va atamalar. Har birini {target_name} "
        f"tiliga TABIIY transliteratsiya/tarjima qil (odamlar ismi odatda "
        f"tovushiga mos yoziladi). AYNAN o'sha kalitlar bilan TEKIS JSON qaytar, "
        f"izohsiz.\n" + (
            "O'zbekcha lotin alifbosida yoz.\n" if target_lang == "uz" else ""
        )
    )
    try:
        content = _raw_any(payload, prompt)
        data = loads_lenient(content)
        gloss: dict[str, str] = {}
        for i, name in enumerate(names):
            v = data.get(str(i)) if isinstance(data, dict) else None
            if isinstance(v, str) and v.strip() and v.strip() != name:
                gloss[name] = v.strip()
        logger.info("Glossariy: %d ta nom/atama izchil tarjima qilindi", len(gloss))
        return gloss
    except Exception as exc:  # noqa: BLE001
        logger.warning("Glossariy tuzilmadi (o'tkazib yuboriladi): %s", exc)
        return {}


# ---------------------------------------------------------------- Bo'lak tarjimasi

def _translate_window(
    texts: list[str], start: int, end: int, system_prompt: str
) -> tuple[dict[int, str], str]:
    """Bitta bo'lak (range(start,end)) ni kontekst bilan tarjima qiladi."""
    payload = to_windowed_payload(texts, start, end, _CTX)
    expected = end - start

    for name, available, raw_fn in _providers():
        if not available:
            continue
        try:
            content = raw_fn(payload, system_prompt)
            out, matched = from_windowed_response(content, texts, start, end)
            if matched < max(1, expected // 2):
                raise ValueError(f"kam tarjima ({matched}/{expected})")
            logger.info(
                "Tarjima '%s' [%d:%d] (%d/%d qator)", name, start, end, matched, expected
            )
            return out, name
        except Exception as exc:
            logger.warning(
                "'%s' tarjima xatosi [%d:%d] (%s) — keyingi provayder",
                name, start, end, exc,
            )
            continue

    raise RuntimeError("Tarjima qilinmadi (AI provayderlar ishlamadi)")


def translate_texts(texts: list[str], target_lang: str) -> tuple[list[str], str]:
    """Matnlarni target_lang tiliga kontekstли tarjima qiladi. (tarjimalar, provayder)."""
    if not texts:
        return texts, ""
    target_name = _LANG_NAME.get(target_lang, target_lang)

    # (Task 7) Nom/atama izchilligi uchun glossariy
    glossary = _build_glossary(texts, target_name, target_lang)
    system_prompt = _system_prompt(target_name, target_lang, glossary)

    out = list(texts)  # natija (topilmaganlar asl matn bilan qoladi)
    provider_used = ""

    # (Task 1) Bo'laklarni PARALLEL tarjima qilamiz — uzun kinoda ancha tezroq.
    batches = [
        (s, min(s + _BATCH, len(texts))) for s in range(0, len(texts), _BATCH)
    ]
    if len(batches) == 1 or _PARALLEL <= 1:
        for s, e in batches:
            try:
                chunk, provider_used = _translate_window(texts, s, e, system_prompt)
                for i, t in chunk.items():
                    out[i] = t
            except Exception as exc:  # noqa: BLE001
                logger.warning("Bo'lak [%d:%d] tarjima qilinmadi: %s", s, e, exc)
    else:
        with ThreadPoolExecutor(max_workers=_PARALLEL) as ex:
            futures = {
                ex.submit(_translate_window, texts, s, e, system_prompt): (s, e)
                for s, e in batches
            }
            for fut in as_completed(futures):
                s, e = futures[fut]
                try:
                    chunk, prov = fut.result()
                    provider_used = prov or provider_used
                    for i, t in chunk.items():
                        out[i] = t
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Bo'lak [%d:%d] tarjima qilinmadi: %s", s, e, exc)

    # (Task 9) Bo'shliq-to'ldirish: partiya "yarmi tarjima bo'lsa" qabul qilingani
    # uchun ayrim qatorlar asl (tarjima qilinmagan) holicha qolishi mumkin.
    # Shularni yig'ib, kichik oynada YANA tarjima qilamiz.
    gap_idx = [
        i for i, (o, s) in enumerate(zip(out, texts))
        if s.strip() and o.strip() == s.strip()
    ]
    if gap_idx:
        logger.info("Bo'shliq to'ldirish: %d qator qayta tarjima qilinmoqda", len(gap_idx))
        runs: list[list[int]] = []
        for i in gap_idx:
            if runs and i - runs[-1][-1] <= 2 and (i - runs[-1][0]) < _BATCH:
                runs[-1].append(i)
            else:
                runs.append([i])
        for run in runs:
            lo, hi = run[0], run[-1] + 1
            try:
                chunk, _ = _translate_window(texts, lo, hi, system_prompt)
                for i in run:
                    if i in chunk and chunk[i].strip() != texts[i].strip():
                        out[i] = chunk[i]
            except Exception as exc:  # noqa: BLE001
                logger.warning("Bo'shliq to'ldirish qismi ishlamadi: %s", exc)

    # (Task 9) Alifbo izchilligi: o'zbekcha tarjimada kirill sizib chiqsa lotinga
    # o'giramiz (asl/tarjima qilinmagan qatorlarga tegmaymiz).
    if target_lang == "uz":
        for i in range(len(out)):
            if out[i] != texts[i] and _has_cyrillic(out[i]):
                out[i] = uz_to_latin(out[i])

    return out, provider_used
