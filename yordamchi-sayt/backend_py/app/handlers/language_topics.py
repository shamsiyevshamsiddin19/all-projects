"""Til mavzulari (Grammar va h.k.): Ingliz/Rus bo'limlari uchun mavzu ro'yxati + .md kontent."""

from __future__ import annotations

from fastapi import Request

from .. import db
from ..errors import ApiError, success
from ..owner import owner_context
from .common import s, to_int
from . import activity

# Har qanday til qiymati qabul qilinadi (english, russian, coding, lang_xxx va h.k.)

# MATERIALLAR bo'limlari (library.js). Bu jadval ikki xil kontentni saqlaydi:
#   · Grammar mavzulari  — lang = english/russian/coding/lang_xxx  -> section 'topic'
#   · Materiallar        — lang = quyidagi kalitlar                -> section 'material'
# Ikkalasi bir xil `section` bilan yozilsa, Reading/Listening materiallari
# "Grammatika" grafigiga tushib ketardi (topilgan nomutanosiblik).
# MUHIM: library.js dagi SECTIONS ro'yxatiga yangi bo'lim qo'shilsa —
# BU YERGA HAM qo'shish shart, aks holda statistika noto'g'ri bo'limga yoziladi.
LIBRARY_LANGS = {
    "en_reading", "en_listening", "en_writing", "en_speaking",
    "ru_listening", "ru_speaking", "ru_writing", "ru_shadowing",
}


def section_for_lang(lang: str) -> str:
    return "material" if lang in LIBRARY_LANGS else "topic"


def _clean_lang(value) -> str:
    lang = s(value).strip()
    if lang == "":
        raise ApiError("Til ko'rsatilmagan.", 422)
    return lang


def split_folder(raw: str) -> tuple[str, str]:
    """"Asosiy/Zamonlar/Present Simple" -> ("Asosiy/Zamonlar", "Present Simple").

    Ajratish FAQAT shu yerda (mavzu qo'shish/nomini o'zgartirishda) bajariladi
    va natija alohida ustunlarga yoziladi. Shuning uchun nomning ichidagi "/"
    (masalan "идти / ходить") keyinchalik papka deb talqin qilinmaydi.

    OXIRGI "/" bo'yicha ajratiladi (birinchi emas) — shunda ichma-ich papka
    yo'li ("A/B/Mavzu nomi") to'g'ri bo'linadi: folder="A/B", name="Mavzu nomi".
    """
    name = (raw or "").strip()
    i = name.rfind("/")
    if i < 0:
        return "", name
    folder = name[:i].strip()
    rest = name[i + 1:].strip()
    if not folder or not rest:
        return "", name          # "/x" yoki "x/" — papka emas, oddiy nom
    return folder, rest


def get_topics(request: Request, body: dict, lang: str):
    lang = _clean_lang(lang)
    ctx = owner_context(request)
    rows = db.fetch_all(
        "SELECT id, name, folder, (LENGTH(content) > 0) AS has_content FROM language_topics "
        "WHERE owner_type = :ot AND owner_key = :ok AND lang = :l "
        "ORDER BY sort_order, id",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang},
    )
    return success({"topics": [
        {"id": int(r["id"]), "name": r["name"], "folder": r["folder"] or "",
         "has_content": bool(r["has_content"])} for r in rows
    ]})


def get_topic(request: Request, body: dict, topic_id: int):
    ctx = owner_context(request)
    row = db.fetch_one(
        "SELECT id, lang, name, folder, content, test_content, game_content, game_type "
        "FROM language_topics "
        "WHERE id = :id AND owner_type = :ot AND owner_key = :ok LIMIT 1",
        {"id": topic_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    if not row:
        raise ApiError("Mavzu topilmadi.", 404)
    activity.record(ctx, section_for_lang(str(row["lang"])),
                    object_name=str(row["name"]), meta={"lang": row["lang"]})
    return success({
        "id": int(row["id"]), "lang": row["lang"], "name": row["name"],
        "folder": row["folder"] or "",
        "content": row["content"] or "",
        "test_content": row["test_content"] or "",
        "game_content": row["game_content"] or "",
        "game_type": row["game_type"] or "fill",
    })


def add_topic(request: Request, body: dict):
    lang = _clean_lang(body.get("lang"))
    raw = s(body.get("name"))
    if raw == "":
        raise ApiError("Mavzu nomi bo'sh.")
    # `folder` ANIQ berilgan bo'lsa (papka ichida turib qo'shilgan yoki
    # Materiallar bo'limidagi ichma-ich yo'l — "Level 1/Unit 2") — nomni
    # umuman bo'lmaymiz: nomning o'zida "/" bo'lishi mumkin va uni papkaga
    # ajratish nomni buzardi. Aks holda eskicha "Papka/Mavzu" ajratiladi.
    if body.get("folder") is not None:
        folder, name = s(body.get("folder")), raw
    else:
        folder, name = split_folder(raw)
    ctx = owner_context(request)
    sort_order = int(db.fetch_value(
        "SELECT COALESCE(MAX(sort_order), 0) + 1 FROM language_topics "
        "WHERE owner_type = :ot AND owner_key = :ok AND lang = :l",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang},
    ) or 0)
    new_id = db.execute_returning_id(
        "INSERT INTO language_topics (owner_type, owner_key, lang, name, folder, sort_order) "
        "VALUES (:ot, :ok, :l, :n, :f, :so)",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang,
         "n": name, "f": folder, "so": sort_order},
    )
    return success({"id": new_id})


def rename_topic(request: Request, body: dict):
    topic_id = to_int(body.get("id"))
    raw = s(body.get("name"))
    if topic_id <= 0 or raw == "":
        raise ApiError("Mavzuni tahrirlash uchun ma'lumot yetarli emas.", 422)
    # `folder` aniq berilsa — nom bo'linmaydi (add_topic bilan bir xil qoida).
    if body.get("folder") is not None:
        folder, name = s(body.get("folder")), raw
    else:
        folder, name = split_folder(raw)
    ctx = owner_context(request)
    db.execute(
        "UPDATE language_topics SET name = :n, folder = :f, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = :id AND owner_type = :ot AND owner_key = :ok",
        {"n": name, "f": folder, "id": topic_id,
         "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    return success()


ALLOWED_GAME_TYPES = {"fill", "sort", "match", "order"}
_PART_COLUMN = {"content": "content", "test": "test_content", "game": "game_content"}


def upload_topic_content(request: Request, body: dict):
    """Mavzuning bir qismini saqlaydi: `part` = content (matn) | test | game."""
    topic_id = to_int(body.get("id"))
    content = "" if body.get("content") is None else str(body.get("content"))
    part = s(body.get("part")) or "content"
    if topic_id <= 0:
        raise ApiError("Mavzu ID kelmadi.", 422)
    column = _PART_COLUMN.get(part)
    if column is None:
        raise ApiError("Noma'lum bo'lim.", 422)

    ctx = owner_context(request)
    params = {"c": content, "id": topic_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]}
    extra = ""
    if part == "game":
        game_type = s(body.get("game_type")).lower()
        if game_type not in ALLOWED_GAME_TYPES:
            game_type = "fill"
        params["gt"] = game_type
        extra = ", game_type = :gt"

    # `column` faqat yuqoridagi qat'iy lug'atdan olinadi (injection'siz).
    db.execute(
        f"UPDATE language_topics SET {column} = :c{extra}, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = :id AND owner_type = :ot AND owner_key = :ok",
        params,
    )
    return success()


def delete_lang_topics(request: Request, body: dict):
    """Butun tilning mavzularini o'chiradi (maxsus til o'chirilganda).

    Frontend (languages.js::langDelete) buni allaqachon chaqirardi, lekin
    action ro'yxatda yo'q edi — so'rov 400 bilan qaytib, `.catch()` da jimgina
    yutilardi va o'chirilgan tilning mavzulari bazada abadiy qolib ketardi.
    """
    lang = _clean_lang(body.get("lang"))
    ctx = owner_context(request)
    n = db.fetch_value(
        "SELECT COUNT(*) FROM language_topics "
        "WHERE owner_type = :ot AND owner_key = :ok AND lang = :l",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang},
    ) or 0
    db.execute(
        "DELETE FROM language_topics WHERE owner_type = :ot AND owner_key = :ok AND lang = :l",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "l": lang},
    )
    return success({"deleted": int(n)})


def delete_topic(request: Request, body: dict):
    topic_id = to_int(body.get("id"))
    if topic_id <= 0:
        raise ApiError("Mavzu ID kelmadi.", 422)
    ctx = owner_context(request)
    db.execute(
        "DELETE FROM language_topics WHERE id = :id AND owner_type = :ot AND owner_key = :ok",
        {"id": topic_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    return success()
