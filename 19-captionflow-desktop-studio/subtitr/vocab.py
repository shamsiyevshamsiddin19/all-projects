"""Lug'at tuzish: chastota, lemma, yordamchi so'zlar."""
from __future__ import annotations

import bisect
from typing import Any

from .core import HELPERS, Segment, Word, normalize_word
from .translate import translate_word_list


def sentence_for(word: Word, segments: list[Segment], starts: list[float]) -> str:
    """So'z uchragan subtitr bo'lagining matni (topilmasa bo'sh satr).

    So'z vaqti bo'yicha qidiradi: bo'laklar tartiblangan, shuning uchun
    ikkilik qidiruv yetarli."""
    if not segments:
        return ""
    i = bisect.bisect_right(starts, word.start) - 1
    if i < 0:
        i = 0
    # So'z chegarada bo'lsa qo'shni bo'lakka tushib qolishi mumkin.
    for j in (i, i + 1):
        if 0 <= j < len(segments) and segments[j].start - 0.2 <= word.start <= segments[j].end + 0.2:
            return segments[j].text
    return segments[i].text if 0 <= i < len(segments) else ""


def build_vocabulary(
    words: list[Word],
    source_lang: str,
    target_lang: str,
    segments: list[Segment] | None = None,
) -> list[dict[str, Any]]:
    # Chastota (#4) — har bir so'z necha marta uchraydi.
    freq: dict[str, int] = {}
    first: dict[str, Word] = {}
    for item in words:
        key = normalize_word(item.word)
        if len(key) < 2 or key.isdigit():
            continue
        freq[key] = freq.get(key, 0) + 1
        first.setdefault(key, item)
    keys = list(first.keys())
    # Har so'z BIRINCHI uchragan gapini olib beramiz — kontekstsiz ko'p
    # ma'noli so'z tasodifiy ma'noda tarjima bo'ladi ("bank" — qirg'oqmi
    # yoki bankmi, "коса" — soch o'rimimi yoki o'roqmi).
    contexts: list[str] | None = None
    if segments:
        ordered = sorted(segments, key=lambda x: x.start)
        starts = [x.start for x in ordered]
        contexts = [sentence_for(first[k], ordered, starts) for k in keys]
    translations, pos_list, lemma_list, provider = translate_word_list(
        keys, target_lang, contexts=contexts, source_lang=source_lang
    )
    entries: list[dict[str, Any]] = []
    for key, tr, pos, lemma in zip(keys, translations, pos_list, lemma_list):
        # Tarjima topilmagan so'z ("brought - brought") lug'atda ham, ekrandagi
        # animatsiyada ham foyda bermaydi — tashlab yuboramiz.
        if not tr or normalize_word(tr) == normalize_word(key):
            continue
        lemma_norm = (lemma or "").strip().lower()
        entries.append(
            {
                "word": key,
                "translation": tr,
                "pos": pos,
                "lemma": lemma_norm,
                "count": freq.get(key, 1),
                # Lemma ham qaraladi: "тобой" ro'yxatda yo'q, lemmasi "ты".
                "helper": (helper_category(key, source_lang)
                           or helper_category(lemma_norm, source_lang)),
                "provider": provider,
            }
        )
    # Eng ko'p uchraganlar tepada.
    entries.sort(key=lambda e: -int(e.get("count", 1)))
    return entries


def dedupe_by_lemma(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """So'zning turli shakllarini (kelgan/kelmoqda -> kelmoq) bitta yozuvга
    birlashtiradi va chastotalarni qo'shadi. Lemma bo'lmasa — so'zning o'zi."""
    groups: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for e in entries:
        lemma = (e.get("lemma") or e.get("word") or "").strip().lower() or str(e.get("word", ""))
        if lemma not in groups:
            groups[lemma] = {**e, "word": lemma, "count": int(e.get("count", 1)), "forms": {str(e.get("word", ""))}}
            order.append(lemma)
        else:
            g = groups[lemma]
            g["count"] = int(g.get("count", 1)) + int(e.get("count", 1))
            g["forms"].add(str(e.get("word", "")))
            if not g.get("translation") and e.get("translation"):
                g["translation"] = e["translation"]
    out = [groups[k] for k in order]
    out.sort(key=lambda e: -int(e.get("count", 1)))
    return out


def is_translit_only(entry: dict[str, Any]) -> bool:
    """Tarjimasi so'zning transliteratsiyasidan iborat yozuvlar.

    "Чебурашка -> Cheburashka", "радио -> radio" — bular hech narsa
    o'rgatmaydi: foydalanuvchi so'zni ko'rganda allaqachon tushunadi.
    Lug'at ro'yxatida ham, ekrandagi kartochkada ham joy egallamasin."""
    word = normalize_word(str(entry.get("word") or ""))
    tr = normalize_word(str(entry.get("translation") or ""))
    return bool(word) and bool(tr) and translit_ru_basic(word) == tr


def entry_helper(entry: dict[str, Any], source_lang: str) -> str:
    """Yozuv yordamchi so'zmi — matndagi shakli, keyin lug'at shakli bo'yicha.

    Lemma ham tekshiriladi, chunki ro'yxatga har bir kelishik shaklini
    yozib chiqish mumkin emas: "тобой" ro'yxatda yo'q, lekin uning lemmasi
    "ты" — olmosh. Lemma qaralmasa, u lug'at tepasida qolib ketadi."""
    label = helper_category(str(entry.get("word") or ""), source_lang)
    if label:
        return label
    return helper_category(str(entry.get("lemma") or ""), source_lang)


def helper_category(word: str, source_lang: str) -> str:
    lang = (source_lang or "").lower()
    groups = HELPERS.get(lang, {})
    key = normalize_word(word)
    if lang == "ru":
        key = translit_ru_basic(key)
    for label, items in groups.items():
        if key in items:
            return label
    return ""


def translit_ru_basic(text: str) -> str:
    table = str.maketrans(
        {
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
            "ё": "e", "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k",
            "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
            "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
            "ч": "ch", "ш": "sh", "щ": "sh", "ы": "i", "э": "e", "ю": "yu",
            "я": "ya", "ь": "", "ъ": "",
        }
    )
    return text.translate(table)
