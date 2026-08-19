"""Quiz/test bazalari: struktura, CRUD, savollar, progress (solved/flag)."""

from __future__ import annotations

import json

from fastapi import Request
from sqlalchemy import text

from .. import db
from ..errors import ApiError, success
from ..owner import owner_context
from .common import normalize_quiz_segment, parse_quiz_full_name, s, to_int
from . import activity, goals as goals_handlers


def _find_base(name) -> dict | None:
    parsed = parse_quiz_full_name(name)
    return db.fetch_one("SELECT * FROM quiz_bases WHERE full_name = :f LIMIT 1", {"f": parsed["full"]})


def _require_base(name) -> dict:
    base = _find_base(name)
    if not base:
        raise ApiError("Baza topilmadi.")
    return base


def _ensure_base(name) -> dict:
    parsed = parse_quiz_full_name(name)
    base = _find_base(parsed["full"])
    if base:
        return base
    db.execute(
        "INSERT INTO quiz_bases (full_name, subject_name, base_name) VALUES (:f, :s, :b)",
        {"f": parsed["full"], "s": parsed["subject"], "b": parsed["base"]},
    )
    return _require_base(parsed["full"])


def get_structure(request: Request, body: dict):
    rows = db.fetch_all(
        "SELECT qb.id, qb.full_name, qb.subject_name, qb.base_name, COUNT(qq.id) AS question_count "
        "FROM quiz_bases qb LEFT JOIN quiz_questions qq ON qq.base_id = qb.id "
        "GROUP BY qb.id, qb.full_name, qb.subject_name, qb.base_name "
        "ORDER BY qb.subject_name, qb.base_name"
    )
    structure = [
        {"subject": r["subject_name"], "name": r["base_name"], "full": r["full_name"], "count": int(r["question_count"])}
        for r in rows
    ]
    return success({"structure": structure})


def create_db(request: Request, body: dict):
    parsed = parse_quiz_full_name(body.get("name") or "")
    if parsed["full"] == "":
        raise ApiError("Baza nomi bo'sh.")
    db.execute(
        "INSERT INTO quiz_bases (full_name, subject_name, base_name) VALUES (:f, :s, :b) "
        "ON CONFLICT (full_name) DO UPDATE SET updated_at = CURRENT_TIMESTAMP",
        {"f": parsed["full"], "s": parsed["subject"], "b": parsed["base"]},
    )
    return success({"full": parsed["full"], "subject": parsed["subject"], "name": parsed["base"]})


def rename_fan(request: Request, body: dict):
    old_subject = normalize_quiz_segment(body.get("old") or "")
    new_subject = normalize_quiz_segment(body.get("new") or "")
    if old_subject == "" or new_subject == "":
        raise ApiError("Eski yoki yangi fan nomi bo'sh.")

    rows = db.fetch_all(
        "SELECT id, base_name FROM quiz_bases WHERE subject_name = :s ORDER BY id", {"s": old_subject}
    )
    if not rows:
        return success({"renamed": 0})

    for row in rows:
        new_full = f"{new_subject}__{row['base_name']}"
        clash = db.fetch_one(
            "SELECT id FROM quiz_bases WHERE full_name = :f AND id <> :id LIMIT 1",
            {"f": new_full, "id": row["id"]},
        )
        if clash:
            raise ApiError(f"Yangi fan nomi bilan to'qnashuv bor: {new_full}")

    with db.tx() as conn:
        for row in rows:
            conn.execute(
                text("UPDATE quiz_bases SET subject_name = :s, full_name = :f WHERE id = :id"),
                {"s": new_subject, "f": f"{new_subject}__{row['base_name']}", "id": row["id"]},
            )
    return success({"renamed": len(rows)})


def delete_fan(request: Request, body: dict):
    subject = normalize_quiz_segment(body.get("fan") or "")
    if subject == "":
        raise ApiError("Fan nomi bo'sh.")
    deleted = db.execute("DELETE FROM quiz_bases WHERE subject_name = :s", {"s": subject})
    return success({"deleted": deleted})


def rename_db(request: Request, body: dict):
    old_parsed = parse_quiz_full_name(body.get("old") or "")
    new_parsed = parse_quiz_full_name(body.get("new") or "")

    base = _find_base(old_parsed["full"])
    if not base:
        raise ApiError("Baza topilmadi.")

    if old_parsed["full"] == new_parsed["full"]:
        return success({"full": new_parsed["full"]})

    clash = db.fetch_one(
        "SELECT id FROM quiz_bases WHERE full_name = :f AND id <> :id LIMIT 1",
        {"f": new_parsed["full"], "id": base["id"]},
    )
    if clash:
        raise ApiError("Bu nomdagi baza allaqachon mavjud.")

    db.execute(
        "UPDATE quiz_bases SET full_name = :f, subject_name = :s, base_name = :b WHERE id = :id",
        {"f": new_parsed["full"], "s": new_parsed["subject"], "b": new_parsed["base"], "id": base["id"]},
    )
    return success({"full": new_parsed["full"]})


def delete_db(request: Request, body: dict):
    parsed = parse_quiz_full_name(body.get("name") or "")
    deleted = db.execute("DELETE FROM quiz_bases WHERE full_name = :f", {"f": parsed["full"]})
    return success({"deleted": deleted})


def upload_base(request: Request, body: dict, db_name: str):
    if db_name.strip() == "":
        raise ApiError("Baza nomi kelmadi.")

    questions = body.get("questions") if isinstance(body.get("questions"), list) else []
    base = _ensure_base(db_name)

    saved = 0
    with db.tx() as conn:
        conn.execute(text("DELETE FROM quiz_progress WHERE base_id = :b"), {"b": base["id"]})
        conn.execute(text("DELETE FROM quiz_questions WHERE base_id = :b"), {"b": base["id"]})
        for index, question in enumerate(questions):
            if not isinstance(question, dict):
                continue
            text_val = s(question.get("text"))
            if text_val == "":
                continue
            options = question.get("options") if isinstance(question.get("options"), (dict, list)) else {}
            correct = s(question.get("correct"))
            # Izoh ixtiyoriy — kelmasa bo'sh satr saqlanadi
            explanation = s(question.get("explanation"))
            conn.execute(
                text(
                    "INSERT INTO quiz_questions "
                    "(base_id, question_text, options_json, correct_answer, explanation, sort_order) "
                    "VALUES (:b, :t, :o, :c, :e, :so)"
                ),
                {
                    "b": base["id"],
                    "t": text_val,
                    "o": json.dumps(options, ensure_ascii=False),
                    "c": correct,
                    "e": explanation,
                    "so": index,
                },
            )
            saved += 1
    return success({"count": saved})


def get_data(request: Request, body: dict, db_name: str):
    name = db_name.strip()
    if name == "" or name == "Global_Data":
        return goals_handlers.get_global_data(request, body)

    base = _find_base(name)
    if not base:
        return success({"questions": [], "solved": [], "flags": []})

    q_rows = db.fetch_all(
        "SELECT id, question_text, options_json, correct_answer, explanation FROM quiz_questions "
        "WHERE base_id = :b ORDER BY sort_order, id",
        {"b": base["id"]},
    )
    questions = []
    for row in q_rows:
        try:
            options = json.loads(row["options_json"] or "null")
        except (ValueError, TypeError):
            options = None
        questions.append({
            "id": int(row["id"]),
            "text": row["question_text"],
            "options": options if isinstance(options, (dict, list)) else {},
            "correct": row["correct_answer"],
            "explanation": row["explanation"] or "",
        })

    ctx = owner_context(request)
    p_rows = db.fetch_all(
        "SELECT question_id, is_solved, flag_type, wrong_count FROM quiz_progress "
        "WHERE base_id = :b AND owner_type = :ot AND owner_key = :ok",
        {"b": base["id"], "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    solved, flags, wrong = [], {}, {}
    for row in p_rows:
        if int(row["is_solved"]) == 1:
            solved.append(int(row["question_id"]))
        if row["flag_type"]:
            flags[int(row["question_id"])] = row["flag_type"]
        wc = int(row.get("wrong_count") or 0)
        if wc > 0:
            wrong[int(row["question_id"])] = wc

    return success({"questions": questions, "solved": solved, "flags": flags, "wrong": wrong})


def mark_solved(request: Request, body: dict, db_name: str):
    base = _require_base(db_name)
    question_id = to_int(body.get("id"))
    if question_id <= 0:
        raise ApiError("Savol ID kelmadi.")

    ctx = owner_context(request)
    db.execute(
        "INSERT INTO quiz_progress (base_id, question_id, owner_type, owner_key, is_solved, flag_type) "
        "VALUES (:b, :q, :ot, :ok, 1, '') "
        "ON CONFLICT (base_id, question_id, owner_type, owner_key) "
        "DO UPDATE SET is_solved = 1, updated_at = CURRENT_TIMESTAMP",
        {"b": base["id"], "q": question_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    return success()


def set_flag(request: Request, body: dict, db_name: str):
    base = _require_base(db_name)
    question_id = to_int(body.get("id"))
    flag_type = s(body.get("type"))
    if question_id <= 0:
        raise ApiError("Savol ID kelmadi.")

    ctx = owner_context(request)
    existing = db.fetch_one(
        "SELECT id, is_solved FROM quiz_progress "
        "WHERE base_id = :b AND question_id = :q AND owner_type = :ot AND owner_key = :ok LIMIT 1",
        {"b": base["id"], "q": question_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )

    if flag_type == "" or flag_type == "none":
        if existing:
            if int(existing["is_solved"]) == 1:
                db.execute("UPDATE quiz_progress SET flag_type = '' WHERE id = :id", {"id": existing["id"]})
            else:
                db.execute("DELETE FROM quiz_progress WHERE id = :id", {"id": existing["id"]})
        return success()

    db.execute(
        "INSERT INTO quiz_progress (base_id, question_id, owner_type, owner_key, is_solved, flag_type) "
        "VALUES (:b, :q, :ot, :ok, 0, :ft) "
        "ON CONFLICT (base_id, question_id, owner_type, owner_key) "
        "DO UPDATE SET flag_type = EXCLUDED.flag_type, updated_at = CURRENT_TIMESTAMP",
        {"b": base["id"], "q": question_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"], "ft": flag_type},
    )
    return success()


def _question_of_base(base_id, question_id: int) -> dict | None:
    return db.fetch_one(
        "SELECT id FROM quiz_questions WHERE id = :q AND base_id = :b LIMIT 1",
        {"q": question_id, "b": base_id},
    )


def add_question(request: Request, body: dict, db_name: str):
    """Bazaga bitta savol qo'shadi (butun bazani qayta yuklamasdan)."""
    base = _ensure_base(db_name)
    text_val = s(body.get("text"))
    if text_val == "":
        raise ApiError("Savol matni bo'sh.")
    options = body.get("options") if isinstance(body.get("options"), dict) else {}
    if len(options) < 2:
        raise ApiError("Kamida 2 ta variant kerak.")
    correct = s(body.get("correct")) or sorted(options.keys())[0]
    explanation = s(body.get("explanation"))

    order = db.fetch_value(
        "SELECT COALESCE(MAX(sort_order), 0) + 1 FROM quiz_questions WHERE base_id = :b",
        {"b": base["id"]},
    )
    new_id = db.execute_returning_id(
        "INSERT INTO quiz_questions "
        "(base_id, question_text, options_json, correct_answer, explanation, sort_order) "
        "VALUES (:b, :t, :o, :c, :e, :so)",
        {"b": base["id"], "t": text_val, "o": json.dumps(options, ensure_ascii=False),
         "c": correct, "e": explanation, "so": int(order or 0)},
    )
    return success({"id": new_id})


def edit_question(request: Request, body: dict, db_name: str):
    base = _require_base(db_name)
    question_id = to_int(body.get("id"))
    if question_id <= 0 or not _question_of_base(base["id"], question_id):
        raise ApiError("Savol topilmadi.", 404)

    text_val = s(body.get("text"))
    if text_val == "":
        raise ApiError("Savol matni bo'sh.")
    options = body.get("options") if isinstance(body.get("options"), dict) else {}
    if len(options) < 2:
        raise ApiError("Kamida 2 ta variant kerak.")
    correct = s(body.get("correct")) or sorted(options.keys())[0]
    explanation = s(body.get("explanation"))

    db.execute(
        "UPDATE quiz_questions SET question_text = :t, options_json = :o, correct_answer = :c, "
        "explanation = :e, updated_at = CURRENT_TIMESTAMP WHERE id = :id AND base_id = :b",
        {"t": text_val, "o": json.dumps(options, ensure_ascii=False), "c": correct,
         "e": explanation, "id": question_id, "b": base["id"]},
    )
    return success()


def delete_question(request: Request, body: dict, db_name: str):
    base = _require_base(db_name)
    question_id = to_int(body.get("id"))
    if question_id <= 0:
        raise ApiError("Savol ID kelmadi.")
    deleted = db.execute(
        "DELETE FROM quiz_questions WHERE id = :id AND base_id = :b",
        {"id": question_id, "b": base["id"]},
    )
    return success({"deleted": deleted})


def mark_wrong(request: Request, body: dict, db_name: str):
    """Xato javob berilgan savolni belgilaydi (wrong_count oshadi).

    `flag_type` ('saved') dan alohida ustun — foydalanuvchi saqlagan savol bilan
    xato qilingan savol bir-birini o'chirib yubormasligi uchun.
    """
    base = _require_base(db_name)
    question_id = to_int(body.get("id"))
    if question_id <= 0:
        raise ApiError("Savol ID kelmadi.")

    ctx = owner_context(request)
    db.execute(
        "INSERT INTO quiz_progress (base_id, question_id, owner_type, owner_key, is_solved, flag_type, wrong_count) "
        "VALUES (:b, :q, :ot, :ok, 0, '', 1) "
        "ON CONFLICT (base_id, question_id, owner_type, owner_key) "
        "DO UPDATE SET wrong_count = quiz_progress.wrong_count + 1, updated_at = CURRENT_TIMESTAMP",
        {"b": base["id"], "q": question_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    return success()


def clear_wrong(request: Request, body: dict, db_name: str):
    """Savol o'zlashtirildi — xatolar ro'yxatidan chiqariladi."""
    base = _require_base(db_name)
    question_id = to_int(body.get("id"))
    if question_id <= 0:
        raise ApiError("Savol ID kelmadi.")

    ctx = owner_context(request)
    db.execute(
        "UPDATE quiz_progress SET wrong_count = 0, updated_at = CURRENT_TIMESTAMP "
        "WHERE base_id = :b AND question_id = :q AND owner_type = :ot AND owner_key = :ok",
        {"b": base["id"], "q": question_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    return success()


# --- Xato savollarning versiya tarixi (lug'atdagi bilan bir xil g'oya) ---

def save_wrong_snapshot(request: Request, body: dict, db_name: str):
    """Joriy xato savollarni bir versiya qilib saqlaydi.

    Savol MATNI va variantlari ham nusxaga yoziladi — savol keyinroq
    tahrirlansa yoki o'chirilsa ham eski versiya o'sha paytdagi holatni
    ko'rsataveradi (lug'atdagi snapshot bilan bir xil qoida).
    """
    base = _require_base(db_name)
    ctx = owner_context(request)
    rows = db.fetch_all(
        "SELECT qq.id, qq.question_text, qq.options_json, qq.correct_answer, qq.explanation, qp.wrong_count "
        "FROM quiz_progress qp JOIN quiz_questions qq ON qq.id = qp.question_id "
        "WHERE qp.base_id = :b AND qp.owner_type = :ot AND qp.owner_key = :ok AND qp.wrong_count > 0 "
        "ORDER BY qp.wrong_count DESC, qq.id",
        {"b": base["id"], "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    if not rows:
        raise ApiError("Xato savol yo'q — saqlash uchun hech narsa yo'q.")

    items = []
    for r in rows:
        try:
            options = json.loads(r["options_json"] or "null")
        except (ValueError, TypeError):
            options = None
        items.append({
            "id": int(r["id"]),
            "text": r["question_text"],
            "options": options if isinstance(options, (dict, list)) else {},
            "correct": r["correct_answer"],
            "explanation": r["explanation"] or "",
            "wrong_count": int(r["wrong_count"] or 0),
        })

    new_id = db.execute_returning_id(
        "INSERT INTO quiz_wrong_snapshots (owner_type, owner_key, base_full_name, question_count, content) "
        "VALUES (:ot, :ok, :f, :n, :c)",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "f": base["full_name"],
         "n": len(items), "c": json.dumps(items, ensure_ascii=False)},
    )
    return success({"id": new_id, "question_count": len(items)})


def list_wrong_snapshots(request: Request, body: dict, db_name: str):
    base = _require_base(db_name)
    ctx = owner_context(request)
    rows = db.fetch_all(
        "SELECT id, question_count, created_at FROM quiz_wrong_snapshots "
        "WHERE owner_type = :ot AND owner_key = :ok AND base_full_name = :f ORDER BY created_at DESC",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "f": base["full_name"]},
    )
    return success({"snapshots": [
        {"id": int(r["id"]), "question_count": int(r["question_count"]), "created_at": str(r["created_at"])}
        for r in rows
    ]})


def get_wrong_snapshot(request: Request, body: dict, snapshot_id: int):
    ctx = owner_context(request)
    row = db.fetch_one(
        "SELECT id, base_full_name, question_count, content, created_at FROM quiz_wrong_snapshots "
        "WHERE id = :id AND owner_type = :ot AND owner_key = :ok",
        {"id": snapshot_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    if not row:
        raise ApiError("Versiya topilmadi.", 404)
    try:
        questions = json.loads(row["content"])
    except (ValueError, TypeError):
        questions = []
    return success({
        "id": int(row["id"]), "db": row["base_full_name"],
        "question_count": int(row["question_count"]),
        "created_at": str(row["created_at"]), "questions": questions,
    })


def delete_wrong_snapshot(request: Request, body: dict):
    snapshot_id = to_int(body.get("id"))
    if snapshot_id <= 0:
        raise ApiError("Versiya ID kelmadi.", 422)
    ctx = owner_context(request)
    db.execute(
        "DELETE FROM quiz_wrong_snapshots WHERE id = :id AND owner_type = :ot AND owner_key = :ok",
        {"id": snapshot_id, "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    return success()


def save_quiz_result(request: Request, body: dict):
    """Yakunlangan test sessiyasini tarixga yozadi."""
    base_full = s(body.get("db"))
    if base_full == "":
        raise ApiError("Baza nomi kelmadi.")
    total = max(0, to_int(body.get("total")))
    correct = max(0, to_int(body.get("correct")))
    wrong = max(0, to_int(body.get("wrong")))
    if total <= 0:
        return success({"skipped": True})
    percent = int(round(correct * 100.0 / total))

    ctx = owner_context(request)
    mode = s(body.get("mode"))[:32]
    db.execute(
        "INSERT INTO quiz_results (owner_type, owner_key, base_full, mode, total, correct, wrong, percent) "
        "VALUES (:ot, :ok, :bf, :m, :t, :c, :w, :p)",
        {
            "ot": ctx["owner_type"], "ok": ctx["owner_key"], "bf": base_full,
            "m": mode, "t": total, "c": correct, "w": wrong, "p": percent,
        },
    )
    duration = to_int(body.get("duration")) or None
    activity.record(
        ctx, "quiz", object_name=base_full, amount=total, unit="savol", duration=duration,
        meta={"correct": correct, "wrong": wrong, "percent": percent, "mode": mode},
    )
    return success({"percent": percent})


def get_quiz_results(request: Request, body: dict, db_name: str):
    """Tarix: agar db berilsa shu baza bo'yicha, aks holda hammasi.

    IKKI XIL cheklov ATAYLAB:
      * `db` berilgan  — bu bitta baza uchun "oxirgi sessiyalar" paneli
        (quiz.js::renderQuizHistory), 50 ta yetarli.
      * `db` berilmagan — bu Statistika DINAMIKA grafigi (stats.js) va
        Sozlamalardagi ma'lumot eksporti. Grafik endi ~400 kunlik tarixni
        ko'rsatadi, shuning uchun 50 ta cheklov eski kunlarni JIMGINA
        yo'qotib, grafikda soxta 0 chizardi.
    """
    ctx = owner_context(request)
    name = db_name.strip()
    if name:
        rows = db.fetch_all(
            "SELECT base_full, mode, total, correct, wrong, percent, created_at FROM quiz_results "
            "WHERE owner_type = :ot AND owner_key = :ok AND base_full = :bf "
            "ORDER BY created_at DESC LIMIT 50",
            {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "bf": name},
        )
    else:
        rows = db.fetch_all(
            "SELECT base_full, mode, total, correct, wrong, percent, created_at FROM quiz_results "
            "WHERE owner_type = :ot AND owner_key = :ok ORDER BY created_at DESC LIMIT 3000",
            {"ot": ctx["owner_type"], "ok": ctx["owner_key"]},
        )
    results = [
        {
            "db": r["base_full"], "mode": r["mode"], "total": int(r["total"]),
            "correct": int(r["correct"]), "wrong": int(r["wrong"]), "percent": int(r["percent"]),
            "at": r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else "",
        }
        for r in rows
    ]
    return success({"results": results})


def reset_history(request: Request, body: dict, db_name: str):
    base = _require_base(db_name)
    ctx = owner_context(request)
    db.execute(
        "DELETE FROM quiz_progress WHERE base_id = :b AND owner_type = :ot AND owner_key = :ok",
        {"b": base["id"], "ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    return success()
