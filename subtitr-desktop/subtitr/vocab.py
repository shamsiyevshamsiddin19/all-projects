"""Lug'at tuzish: chastota, lemma, yordamchi so'zlar."""
from __future__ import annotations

from typing import Any

from .core import HELPERS, Word, normalize_word
from .translate import translate_word_list


def build_vocabulary(words: list[Word], source_lang: str, target_lang: str) -> list[dict[str, Any]]:
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
    translations, pos_list, lemma_list, provider = translate_word_list(keys, target_lang)
    entries: list[dict[str, Any]] = []
    for key, tr, pos, lemma in zip(keys, translations, pos_list, lemma_list):
        # Tarjima topilmagan so'z ("brought - brought") lug'atda ham, ekrandagi
        # animatsiyada ham foyda bermaydi — tashlab yuboramiz.
        if not tr or normalize_word(tr) == normalize_word(key):
            continue
        entries.append(
            {
                "word": key,
                "translation": tr,
                "pos": pos,
                "lemma": (lemma or "").strip().lower(),
                "count": freq.get(key, 1),
                "helper": helper_category(key, source_lang),
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
