"""Lug'at (dictionary), xatolar, English/Russian sozlamalari, save_state."""

from __future__ import annotations

import json

from fastapi import Request
from sqlalchemy import text

from .. import db
from ..errors import ApiError, success
from ..owner import global_context, owner_context
from .common import s, to_int


ALLOWED_DICT_LANGS = {"english", "russian"}


def _clean_dict_lang(value) -> str:
    lang = s(value).lower()
    return lang if lang in ALLOWED_DICT_LANGS else "russian"


def _get_dict_order(lang: str) -> list[str]:
    raw = db.storage_value("dict_category_order_" + lang, "[]", global_context())
    try:
        decoded = json.loads(raw or "[]")
    except (ValueError, TypeError):
        return []
    if not isinstance(decoded, list):
        return []
    return [x for x in decoded if isinstance(x, str) and x.strip() != ""]


def _save_dict_order(lang: str, order: list[str]) -> None:
    seen, clean = set(), []
    for item in order:
        if isinstance(item, str) and item.strip() != "" and item not in seen:
            seen.add(item)
            clean.append(item)
    db.storage_set(
        "dict_category_order_" + lang,
        json.dumps(clean, ensure_ascii=False),
        global_context(),
    )


def get_dict_data(request: Request, body: dict, lang: str):
    lang = _clean_dict_lang(lang)
    items = db.fetch_all(
        "SELECT category, word_ru, word_uz FROM dictionary_words WHERE lang = :l ORDER BY category, sort_order, id",
        {"l": lang},
    )
    order = _get_dict_order(lang)
    known: list[str] = []
    for item in items:
        if item["category"] not in known:
            known.append(item["category"])
    for category in known:
        if category not in order:
            order.append(category)
    return success({"items": items, "order": order})


def save_dict_cat(request: Request, body: dict):
    lang = _clean_dict_lang(body.get("lang"))
    category = s(body.get("category"))
    words = body.get("words") if isinstance(body.get("words"), list) else []
    if category == "":
        raise ApiError("Kategoriya nomi bo'sh.")

    saved = 0
    with db.tx() as conn:
        conn.execute(
            text("DELETE FROM dictionary_words WHERE lang = :l AND category = :c"), {"l": lang, "c": category}
        )
        for index, word in enumerate(words):
            if not isinstance(word, dict):
                continue
            ru = s(word.get("ru"))
            uz = s(word.get("uz"))
            if ru == "" and uz == "":
                continue
            conn.execute(
                text(
                    "INSERT INTO dictionary_words (lang, category, word_ru, word_uz, sort_order) "
                    "VALUES (:l, :c, :ru, :uz, :so)"
                ),
                {"l": lang, "c": category, "ru": ru, "uz": uz, "so": index},
            )
            saved += 1

    order = _get_dict_order(lang)
    if category not in order:
        order.append(category)
        _save_dict_order(lang, order)

    return success({"count": saved})


def rename_dict_cat(request: Request, body: dict):
    lang = _clean_dict_lang(body.get("lang"))
    old_name = s(body.get("old_name"))
    new_name = s(body.get("new_name"))
    if old_name == "" or new_name == "":
        raise ApiError("Kategoriya nomlari to'liq emas.")

    if old_name != new_name:
        clash = db.fetch_one(
            "SELECT id FROM dictionary_words WHERE lang = :l AND category = :c LIMIT 1", {"l": lang, "c": new_name}
        )
        if clash:
            raise ApiError("Bu nomdagi kategoriya allaqachon mavjud.")

    with db.tx() as conn:
        conn.execute(
            text("UPDATE dictionary_words SET category = :n WHERE lang = :l AND category = :o"),
            {"n": new_name, "l": lang, "o": old_name},
        )
        conn.execute(
            text("UPDATE dictionary_mistakes SET category = :n WHERE lang = :l AND category = :o"),
            {"n": new_name, "l": lang, "o": old_name},
        )

    order = _get_dict_order(lang)
    order = [new_name if name == old_name else name for name in order]
    _save_dict_order(lang, order)
    return success()


def delete_dict_cat(request: Request, body: dict):
    lang = _clean_dict_lang(body.get("lang"))
    category = s(body.get("category"))
    if category == "":
        raise ApiError("Kategoriya nomi kelmadi.")
    with db.tx() as conn:
        conn.execute(
            text("DELETE FROM dictionary_words WHERE lang = :l AND category = :c"), {"l": lang, "c": category}
        )
        conn.execute(
            text("DELETE FROM dictionary_mistakes WHERE lang = :l AND category = :c"), {"l": lang, "c": category}
        )
    _save_dict_order(lang, [n for n in _get_dict_order(lang) if n != category])
    return success()


def get_mistakes(request: Request, body: dict, lang: str, category: str):
    lang = _clean_dict_lang(lang)
    ctx = owner_context(request)
    category = category.strip()
    if category != "":
        rows = db.fetch_all(
            "SELECT category, word_ru, word_uz FROM dictionary_mistakes "
            "WHERE owner_type = :ot AND owner_key = :ok AND lang = :l AND category = :c ORDER BY updated_at DESC",
            {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang, "c": category},
        )
    else:
        rows = db.fetch_all(
            "SELECT category, word_ru, word_uz FROM dictionary_mistakes "
            "WHERE owner_type = :ot AND owner_key = :ok AND lang = :l ORDER BY updated_at DESC",
            {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang},
        )
    return success({"mistakes": rows})


def add_mistake(request: Request, body: dict):
    lang = _clean_dict_lang(body.get("lang"))
    category = s(body.get("category"))
    ru = s(body.get("ru"))
    uz = s(body.get("uz"))
    if category == "" or ru == "":
        raise ApiError("Xato so'z uchun ma'lumot yetarli emas.")
    ctx = owner_context(request)
    db.execute(
        "INSERT INTO dictionary_mistakes (owner_type, owner_key, lang, category, word_ru, word_uz) "
        "VALUES (:ot, :ok, :l, :c, :ru, :uz) "
        "ON CONFLICT (owner_type, owner_key, category, word_ru) "
        "DO UPDATE SET word_uz = EXCLUDED.word_uz, lang = EXCLUDED.lang, updated_at = CURRENT_TIMESTAMP",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang, "c": category, "ru": ru, "uz": uz},
    )
    return success()


def remove_mistake(request: Request, body: dict):
    lang = _clean_dict_lang(body.get("lang"))
    category = s(body.get("category"))
    ru = s(body.get("ru"))
    if category == "" or ru == "":
        raise ApiError("O'chirish uchun so'z ma'lumoti kerak.")
    ctx = owner_context(request)
    db.execute(
        "DELETE FROM dictionary_mistakes WHERE owner_type = :ot AND owner_key = :ok AND lang = :l "
        "AND category = :c AND word_ru = :ru",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang, "c": category, "ru": ru},
    )
    return success()


# --- Xatolar versiya tarixi (GitHub'dagi kabi — har "yuklab olish" bir versiya) ---

def save_mistake_snapshot(request: Request, body: dict):
    lang = _clean_dict_lang(body.get("lang"))
    ctx = owner_context(request)
    rows = db.fetch_all(
        "SELECT category, word_ru, word_uz FROM dictionary_mistakes "
        "WHERE owner_type = :ot AND owner_key = :ok AND lang = :l ORDER BY updated_at DESC",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang},
    )
    if not rows:
        raise ApiError("Xato so'z yo'q — saqlash uchun hech narsa yo'q.")
    content = json.dumps(
        [{"ru": r["word_ru"], "uz": r["word_uz"], "cat": r["category"]} for r in rows],
        ensure_ascii=False,
    )
    new_id = db.execute_returning_id(
        "INSERT INTO dictionary_mistake_snapshots (owner_type, owner_key, lang, word_count, content) "
        "VALUES (:ot, :ok, :l, :n, :c)",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang, "n": len(rows), "c": content},
    )
    return success({"id": new_id, "word_count": len(rows)})


def list_mistake_snapshots(request: Request, body: dict, lang: str):
    lang = _clean_dict_lang(lang)
    ctx = owner_context(request)
    rows = db.fetch_all(
        "SELECT id, word_count, created_at FROM dictionary_mistake_snapshots "
        "WHERE owner_type = :ot AND owner_key = :ok AND lang = :l ORDER BY created_at DESC",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang},
    )
    return success({"snapshots": [
        {"id": int(r["id"]), "word_count": int(r["word_count"]), "created_at": str(r["created_at"])} for r in rows
    ]})


def get_mistake_snapshot(request: Request, body: dict, snapshot_id: int):
    ctx = owner_context(request)
    row = db.fetch_one(
        "SELECT id, lang, word_count, content, created_at FROM dictionary_mistake_snapshots "
        "WHERE id = :id AND owner_type = :ot AND owner_key = :ok",
        {"id": snapshot_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    if not row:
        raise ApiError("Versiya topilmadi.", 404)
    try:
        words = json.loads(row["content"])
    except (ValueError, TypeError):
        words = []
    return success({
        "id": int(row["id"]), "lang": row["lang"], "word_count": int(row["word_count"]),
        "created_at": str(row["created_at"]), "words": words,
    })


def delete_mistake_snapshot(request: Request, body: dict):
    snapshot_id = to_int(body.get("id"))
    if snapshot_id <= 0:
        raise ApiError("Versiya ID kelmadi.", 422)
    ctx = owner_context(request)
    db.execute(
        "DELETE FROM dictionary_mistake_snapshots WHERE id = :id AND owner_type = :ot AND owner_key = :ok",
        {"id": snapshot_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    return success()


def get_eng_settings(request: Request, body: dict):
    ctx = owner_context(request)
    items = db.storage_map(ctx)
    if "eng_names" not in items and "eng_settings_names" in items:
        items["eng_names"] = items["eng_settings_names"]
    if "eng_phones" not in items and "eng_settings_phones" in items:
        items["eng_phones"] = items["eng_settings_phones"]
    if "eng_settings_names" not in items and "eng_names" in items:
        items["eng_settings_names"] = items["eng_names"]
    if "eng_settings_phones" not in items and "eng_phones" in items:
        items["eng_settings_phones"] = items["eng_phones"]
    return success(items)


def save_eng_settings(request: Request, body: dict):
    ctx = owner_context(request)
    names = s(body.get("names"))
    phones = s(body.get("phones"))
    db.storage_set("eng_names", names, ctx)
    db.storage_set("eng_phones", phones, ctx)
    db.storage_set("eng_exam_date", s(body.get("exam_date")), ctx)
    db.storage_set("eng_settings_names", names, ctx)
    db.storage_set("eng_settings_phones", phones, ctx)
    return success()


def get_rus_settings(request: Request, body: dict):
    ctx = owner_context(request)
    return success(db.storage_map(ctx))


def save_rus_settings(request: Request, body: dict):
    ctx = owner_context(request)
    db.storage_set("rus_exam_date", s(body.get("exam_date")), ctx)
    db.storage_set("rus_settings_names", s(body.get("names")), ctx)
    db.storage_set("rus_settings_phones", s(body.get("phones")), ctx)
    return success()


def save_state(request: Request, body: dict):
    key = s(body.get("key"))
    if key == "":
        raise ApiError("Storage key bo'sh.")
    db.storage_set(key, str(body.get("value") or ""), owner_context(request))
    return success()
