"""SQLite ma'lumotlar bazasi (aiosqlite). Yengil — past RAM uchun."""
from __future__ import annotations

import json
import time
from typing import Any

import aiosqlite

from .config import settings
from . import crypto

_db: aiosqlite.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id       INTEGER PRIMARY KEY,
    service     TEXT NOT NULL DEFAULT 'lms',   -- 'lms' | 'hemis'
    login       TEXT,
    pwd_enc     TEXT,
    full_name   TEXT DEFAULT '',
    tg_username TEXT DEFAULT '',
    semester_id INTEGER DEFAULT 0,
    morning_on  INTEGER DEFAULT 1,
    deadline_on INTEGER DEFAULT 1,
    autosub_on  INTEGER DEFAULT 0,
    changes_on  INTEGER DEFAULT 1,
    settings    TEXT DEFAULT '{}',
    created_at  INTEGER,
    updated_at  INTEGER
);
CREATE TABLE IF NOT EXISTS sent_reminders (
    tg_id        INTEGER,
    task_uid     TEXT,
    threshold    INTEGER,
    sent_at      INTEGER,
    PRIMARY KEY (tg_id, task_uid, threshold)
);
CREATE TABLE IF NOT EXISTS autosubmit (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id       INTEGER,
    course_id   INTEGER,
    submit_id   TEXT,
    task_name   TEXT,
    deadline    INTEGER,
    file_id     TEXT,
    file_name   TEXT,
    status      TEXT DEFAULT 'pending',   -- pending | done | failed | cancelled
    created_at  INTEGER
);
CREATE TABLE IF NOT EXISTS student_stats (
    tg_id       INTEGER PRIMARY KEY,
    full_name   TEXT DEFAULT '',
    university  TEXT DEFAULT '',
    speciality  TEXT DEFAULT '',   -- yo'nalish (fakultet o'rnida)
    level       TEXT DEFAULT '',   -- kurs
    patok       TEXT DEFAULT '',
    groupname   TEXT DEFAULT '',
    gpa         REAL,
    updated_at  INTEGER
);
CREATE TABLE IF NOT EXISTS subject_grades (
    tg_id        INTEGER,
    subject      TEXT,
    norm_subject TEXT,
    credit       INTEGER DEFAULT 0,
    grade        REAL,
    semester     TEXT,
    PRIMARY KEY (tg_id, norm_subject, semester)
);
CREATE TABLE IF NOT EXISTS lms_snapshot (
    tg_id     INTEGER,
    kind      TEXT,       -- 'grade' | 'attendance' | 'resource'
    item_key  TEXT,
    value     TEXT,
    PRIMARY KEY (tg_id, kind, item_key)
);
"""


async def init() -> None:
    global _db
    _db = await aiosqlite.connect(settings.db_file)
    _db.row_factory = aiosqlite.Row
    await _db.executescript(SCHEMA)
    # migratsiya: eski bazaga yangi ustunlarni qo'shish
    for col, ddl in [
        ("tg_username", "ALTER TABLE users ADD COLUMN tg_username TEXT DEFAULT ''"),
        ("changes_on", "ALTER TABLE users ADD COLUMN changes_on INTEGER DEFAULT 1"),
    ]:
        try:
            await _db.execute(ddl)
        except Exception:  # noqa: BLE001
            pass  # allaqachon mavjud
    await _db.commit()


async def close() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None


def _conn() -> aiosqlite.Connection:
    if _db is None:
        raise RuntimeError("DB init() chaqirilmagan")
    return _db


# ─────────────────────────── Users ───────────────────────────
async def save_credentials(tg_id: int, login: str, password: str,
                           service: str = "lms", full_name: str = "",
                           tg_username: str = "") -> None:
    now = int(time.time())
    enc = crypto.encrypt(password)
    await _conn().execute(
        """INSERT INTO users (tg_id, service, login, pwd_enc, full_name, tg_username,
                              created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?)
           ON CONFLICT(tg_id) DO UPDATE SET
             service=excluded.service, login=excluded.login, pwd_enc=excluded.pwd_enc,
             full_name=CASE WHEN excluded.full_name<>'' THEN excluded.full_name ELSE users.full_name END,
             tg_username=CASE WHEN excluded.tg_username<>'' THEN excluded.tg_username ELSE users.tg_username END,
             updated_at=excluded.updated_at""",
        (tg_id, service, login, enc, full_name, tg_username, now, now),
    )
    await _conn().commit()


async def get_user(tg_id: int) -> dict | None:
    cur = await _conn().execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


async def get_credentials(tg_id: int) -> tuple[str, str] | None:
    u = await get_user(tg_id)
    if not u or not u["login"] or not u["pwd_enc"]:
        return None
    return u["login"], crypto.decrypt(u["pwd_enc"])


async def delete_user(tg_id: int) -> None:
    await _conn().execute("DELETE FROM users WHERE tg_id=?", (tg_id,))
    await _conn().execute("DELETE FROM autosubmit WHERE tg_id=?", (tg_id,))
    await _conn().commit()


async def set_field(tg_id: int, field: str, value: Any) -> None:
    if field not in {"semester_id", "morning_on", "deadline_on", "autosub_on",
                     "changes_on", "full_name"}:
        raise ValueError(f"ruxsat etilmagan maydon: {field}")
    await _conn().execute(f"UPDATE users SET {field}=?, updated_at=? WHERE tg_id=?",
                          (value, int(time.time()), tg_id))
    await _conn().commit()


async def all_users(service: str | None = None) -> list[dict]:
    if service:
        cur = await _conn().execute("SELECT * FROM users WHERE service=?", (service,))
    else:
        cur = await _conn().execute("SELECT * FROM users")
    return [dict(r) for r in await cur.fetchall()]


# ─────────────────────────── Reminders dedupe ───────────────────────────
async def reminder_already_sent(tg_id: int, task_uid: str, threshold: int) -> bool:
    cur = await _conn().execute(
        "SELECT 1 FROM sent_reminders WHERE tg_id=? AND task_uid=? AND threshold=?",
        (tg_id, task_uid, threshold))
    return await cur.fetchone() is not None


async def mark_reminder_sent(tg_id: int, task_uid: str, threshold: int) -> None:
    await _conn().execute(
        "INSERT OR IGNORE INTO sent_reminders VALUES (?,?,?,?)",
        (tg_id, task_uid, threshold, int(time.time())))
    await _conn().commit()


# ─────────────────────────── Auto-submit (halol) ───────────────────────────
async def add_autosubmit(tg_id: int, course_id: int, submit_id: str, task_name: str,
                         deadline: int, file_id: str, file_name: str) -> int:
    cur = await _conn().execute(
        """INSERT INTO autosubmit (tg_id, course_id, submit_id, task_name, deadline,
                                   file_id, file_name, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (tg_id, course_id, submit_id, task_name, deadline, file_id, file_name, int(time.time())))
    await _conn().commit()
    return cur.lastrowid


async def pending_autosubmits() -> list[dict]:
    cur = await _conn().execute("SELECT * FROM autosubmit WHERE status='pending'")
    return [dict(r) for r in await cur.fetchall()]


async def set_autosubmit_status(rid: int, status: str) -> None:
    await _conn().execute("UPDATE autosubmit SET status=? WHERE id=?", (status, rid))
    await _conn().commit()


# ─────────────────────────── Reyting (student_stats) ───────────────────────────
async def save_student_stats(tg_id: int, full_name: str, university: str, speciality: str,
                             level: str, patok: str, groupname: str, gpa) -> None:
    await _conn().execute(
        """INSERT INTO student_stats
             (tg_id, full_name, university, speciality, level, patok, groupname, gpa, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?)
           ON CONFLICT(tg_id) DO UPDATE SET
             full_name=excluded.full_name, university=excluded.university,
             speciality=excluded.speciality, level=excluded.level, patok=excluded.patok,
             groupname=excluded.groupname, gpa=excluded.gpa, updated_at=excluded.updated_at""",
        (tg_id, full_name, university, speciality, level, patok, groupname, gpa, int(time.time())),
    )
    await _conn().commit()


async def save_subject_grades(tg_id: int, rows: list[tuple]) -> None:
    """rows: [(subject, norm_subject, credit, grade, semester), ...]"""
    await _conn().execute("DELETE FROM subject_grades WHERE tg_id=?", (tg_id,))
    await _conn().executemany(
        "INSERT OR REPLACE INTO subject_grades VALUES (?,?,?,?,?,?)",
        [(tg_id, s, n, c, g, sem) for (s, n, c, g, sem) in rows])
    await _conn().commit()


async def get_student_stats(tg_id: int) -> dict | None:
    cur = await _conn().execute("SELECT * FROM student_stats WHERE tg_id=?", (tg_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


async def all_student_stats() -> dict[int, dict]:
    cur = await _conn().execute("SELECT * FROM student_stats")
    return {r["tg_id"]: dict(r) for r in await cur.fetchall()}


_SCOPES = {
    "university": ("1=1", lambda me: []),
    "speciality": ("speciality=?", lambda me: [me["speciality"]]),
    "level": ("level=?", lambda me: [me["level"]]),
    "patok": ("patok=?", lambda me: [me["patok"]]),
    "group": ("groupname=?", lambda me: [me["groupname"]]),
}


async def ranking(tg_id: int, scope: str, top_n: int = 10) -> dict | None:
    me = await get_student_stats(tg_id)
    if not me or me.get("gpa") is None:
        return None
    where, argf = _SCOPES.get(scope, _SCOPES["university"])
    args = argf(me)
    cur = await _conn().execute(
        f"SELECT tg_id, full_name, gpa FROM student_stats "
        f"WHERE gpa IS NOT NULL AND {where} ORDER BY gpa DESC, full_name ASC", args)
    rows = [dict(r) for r in await cur.fetchall()]
    my_gpa = me["gpa"]
    position = 1 + sum(1 for r in rows if r["gpa"] > my_gpa)
    top = [{"name": r["full_name"], "gpa": r["gpa"], "is_me": r["tg_id"] == tg_id}
           for r in rows[:top_n]]
    return {"position": position, "total": len(rows), "gpa": my_gpa,
            "top": top, "scope": scope}


async def subject_ranking(tg_id: int) -> list[dict]:
    cur = await _conn().execute(
        "SELECT subject, norm_subject, grade FROM subject_grades "
        "WHERE tg_id=? AND grade IS NOT NULL ORDER BY subject", (tg_id,))
    mine = [dict(r) for r in await cur.fetchall()]
    out = []
    for r in mine:
        cur2 = await _conn().execute(
            "SELECT grade FROM subject_grades WHERE norm_subject=? AND grade IS NOT NULL",
            (r["norm_subject"],))
        peers = [g[0] for g in await cur2.fetchall()]
        pos = 1 + sum(1 for g in peers if g > r["grade"])
        out.append({"subject": r["subject"], "grade": r["grade"],
                    "position": pos, "total": len(peers), "norm": r["norm_subject"]})
    return out


async def leaderboard() -> list[dict]:
    """GPA bo'yicha reytingga kirgan BARCHA talabalar (yuqoridan pastga).
    Web reyting sahifasi uchun — guruhlash handlerda qilinadi."""
    cur = await _conn().execute(
        "SELECT * FROM student_stats WHERE gpa IS NOT NULL "
        "ORDER BY gpa DESC, full_name ASC")
    return [dict(r) for r in await cur.fetchall()]


async def subject_leaderboards() -> list[dict]:
    """Har fan bo'yicha to'liq reyting.
    [{'subject': nom, 'students': [{'name','group','grade'}, ...]}, ...]"""
    cur = await _conn().execute(
        "SELECT sg.norm_subject AS norm, sg.subject AS subject, "
        "       s.full_name AS name, s.groupname AS grp, sg.grade AS grade "
        "FROM subject_grades sg JOIN student_stats s ON s.tg_id=sg.tg_id "
        "WHERE sg.grade IS NOT NULL "
        "ORDER BY sg.grade DESC, s.full_name ASC")
    groups: dict[str, dict] = {}
    for r in await cur.fetchall():
        g = groups.setdefault(r["norm"], {"subject": r["subject"], "students": []})
        g["students"].append({"name": r["name"], "group": r["grp"], "grade": r["grade"]})
    return sorted(groups.values(), key=lambda x: (x["subject"] or "").lower())


async def subject_top(norm_subject: str, top_n: int = 10) -> list[dict]:
    cur = await _conn().execute(
        "SELECT s.full_name, sg.grade FROM subject_grades sg "
        "JOIN student_stats s ON s.tg_id=sg.tg_id "
        "WHERE sg.norm_subject=? AND sg.grade IS NOT NULL "
        "ORDER BY sg.grade DESC, s.full_name ASC LIMIT ?", (norm_subject, top_n))
    return [{"name": r[0], "grade": r[1]} for r in await cur.fetchall()]


# ─────────────────────── LMS o'zgarish snapshot ───────────────────────
async def snapshot_get(tg_id: int, kind: str) -> dict[str, str]:
    """Oldingi holat: {item_key: value}."""
    cur = await _conn().execute(
        "SELECT item_key, value FROM lms_snapshot WHERE tg_id=? AND kind=?",
        (tg_id, kind))
    return {r[0]: r[1] for r in await cur.fetchall()}


async def snapshot_clear(tg_id: int) -> None:
    """Foydalanuvchining barcha o'zgarish-snapshotlarini o'chiradi (semestr
    almashganda — yangi semestr ma'lumoti 'yangi' deb flood bo'lmasligi uchun)."""
    await _conn().execute("DELETE FROM lms_snapshot WHERE tg_id=?", (tg_id,))
    await _conn().commit()


async def snapshot_set(tg_id: int, kind: str, items: dict[str, str]) -> None:
    """Holatni to'liq almashtiradi."""
    c = _conn()
    await c.execute("DELETE FROM lms_snapshot WHERE tg_id=? AND kind=?", (tg_id, kind))
    if items:
        await c.executemany(
            "INSERT OR REPLACE INTO lms_snapshot (tg_id, kind, item_key, value) "
            "VALUES (?,?,?,?)",
            [(tg_id, kind, k, str(v)) for k, v in items.items()])
    await c.commit()


async def stats() -> dict:
    c = _conn()
    out: dict[str, int] = {}
    q = [
        ("users", "SELECT COUNT(*) FROM users"),
        ("morning_on", "SELECT COUNT(*) FROM users WHERE morning_on=1"),
        ("deadline_on", "SELECT COUNT(*) FROM users WHERE deadline_on=1"),
        ("autosub_on", "SELECT COUNT(*) FROM users WHERE autosub_on=1"),
        ("reminders_sent", "SELECT COUNT(*) FROM sent_reminders"),
        ("autosub_pending", "SELECT COUNT(*) FROM autosubmit WHERE status='pending'"),
        ("autosub_done", "SELECT COUNT(*) FROM autosubmit WHERE status='done'"),
    ]
    for key, sql in q:
        cur = await c.execute(sql)
        row = await cur.fetchone()
        out[key] = row[0] if row else 0
    return out


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)
