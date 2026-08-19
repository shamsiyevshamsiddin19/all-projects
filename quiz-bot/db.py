"""PostgreSQL (asyncpg) qatlami — sxema va so'rovlar."""
from __future__ import annotations

import datetime as _dt
import json

import asyncpg

from config import settings

_pool: asyncpg.Pool | None = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          BIGINT PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    is_blocked  BOOLEAN NOT NULL DEFAULT FALSE,
    xp          INT NOT NULL DEFAULT 0,
    streak      INT NOT NULL DEFAULT 0,
    best_streak INT NOT NULL DEFAULT 0,
    last_active DATE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    emoji       TEXT NOT NULL DEFAULT '📁',
    position    INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS quizzes (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    owner_id    BIGINT,
    category_id INT REFERENCES categories(id) ON DELETE SET NULL,
    difficulty  TEXT,
    description TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS questions (
    id            SERIAL PRIMARY KEY,
    quiz_id       INT NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    position      INT NOT NULL DEFAULT 0,
    text          TEXT NOT NULL,
    options       JSONB NOT NULL,
    correct       INT NOT NULL DEFAULT 0,
    explanation   TEXT,
    image_file_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_questions_quiz ON questions(quiz_id);

-- quiz_id: test o'chirilsa ham natijalar tarixi (leaderboard/CSV) saqlanib qolsin
-- deb SET NULL qilingan (quiz_name ustunida nom snapshoti bor).
CREATE TABLE IF NOT EXISTS attempts (
    id           SERIAL PRIMARY KEY,
    user_id      BIGINT,
    username     TEXT,
    quiz_id      INT REFERENCES quizzes(id) ON DELETE SET NULL,
    quiz_name    TEXT,
    score        INT NOT NULL DEFAULT 0,
    total        INT NOT NULL DEFAULT 0,
    mode         TEXT,
    duration_sec INT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_attempts_quiz ON attempts(quiz_id);
CREATE INDEX IF NOT EXISTS idx_attempts_created ON attempts(created_at);

-- Har bir savolga berilgan har bir javob — savol darajasidagi analitika uchun
-- (eng qiyin savollar, aniqlik foizi). question_text snapshoti savol
-- o'chirilgandan keyin ham tarixiy hisobotni tushunarli qoldiradi.
CREATE TABLE IF NOT EXISTS question_answers (
    id            SERIAL PRIMARY KEY,
    question_id   INT REFERENCES questions(id) ON DELETE SET NULL,
    quiz_id       INT REFERENCES quizzes(id) ON DELETE SET NULL,
    question_text TEXT,
    user_id       BIGINT,
    username      TEXT,
    chosen_index  INT,
    is_correct    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_qa_question ON question_answers(question_id);
CREATE INDEX IF NOT EXISTS idx_qa_quiz ON question_answers(quiz_id);

-- Sevimli testlar
CREATE TABLE IF NOT EXISTS favorites (
    user_id    BIGINT,
    quiz_id    INT REFERENCES quizzes(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, quiz_id)
);

-- Yutuqlar / nishonlar
CREATE TABLE IF NOT EXISTS user_achievements (
    user_id   BIGINT,
    code      TEXT,
    earned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, code)
);

CREATE TABLE IF NOT EXISTS settings (
    key    TEXT PRIMARY KEY,
    value  TEXT
);
"""


async def init() -> None:
    global _pool
    _pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=1, max_size=5)
    async with _pool.acquire() as con:
        await con.execute(SCHEMA)
        # ── migratsiyalar (eski bazalar uchun, idempotent) ──
        await con.execute("ALTER TABLE questions ADD COLUMN IF NOT EXISTS explanation TEXT")
        await con.execute("ALTER TABLE questions ADD COLUMN IF NOT EXISTS image_file_id TEXT")
        await con.execute("ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS category_id INT")
        await con.execute("ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS difficulty TEXT")
        await con.execute("ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS description TEXT")
        await con.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INT NOT NULL DEFAULT 0")
        await con.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INT NOT NULL DEFAULT 0")
        await con.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS best_streak INT NOT NULL DEFAULT 0")
        await con.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active DATE")
        await con.execute("ALTER TABLE attempts ADD COLUMN IF NOT EXISTS mode TEXT")
        await con.execute("ALTER TABLE attempts ADD COLUMN IF NOT EXISTS duration_sec INT")
        # quizzes.category_id FK (agar ustun eski migratsiyada FK'siz qo'shilgan bo'lsa)
        await con.execute("""
            DO $$
            BEGIN
                ALTER TABLE quizzes ADD CONSTRAINT quizzes_category_id_fkey
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL;
            EXCEPTION WHEN OTHERS THEN NULL;
            END $$;
        """)
        # eski bazalarda attempts.quiz_id CASCADE bo'lgan bo'lishi mumkin edi —
        # testni o'chirishda tarixni yo'qotmaslik uchun SET NULL'ga o'tkazamiz.
        await con.execute("""
            DO $$
            BEGIN
                ALTER TABLE attempts DROP CONSTRAINT IF EXISTS attempts_quiz_id_fkey;
                ALTER TABLE attempts ADD CONSTRAINT attempts_quiz_id_fkey
                    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE SET NULL;
            EXCEPTION WHEN OTHERS THEN NULL;
            END $$;
        """)


async def close() -> None:
    if _pool is not None:
        await _pool.close()


def pool() -> asyncpg.Pool:
    return _pool


# ─────────────────────────── users ───────────────────────────

async def ensure_user(user_id: int, username: str | None, first_name: str | None) -> None:
    await _pool.execute(
        """INSERT INTO users(id, username, first_name) VALUES($1,$2,$3)
           ON CONFLICT (id) DO UPDATE SET username=$2, first_name=$3""",
        user_id, username, first_name,
    )


async def is_blocked(user_id: int) -> bool:
    row = await _pool.fetchrow("SELECT is_blocked FROM users WHERE id=$1", user_id)
    return bool(row and row["is_blocked"])


async def mark_blocked(user_id: int) -> None:
    await _pool.execute("UPDATE users SET is_blocked=TRUE WHERE id=$1", user_id)


async def all_user_ids() -> list[int]:
    rows = await _pool.fetch("SELECT id FROM users WHERE NOT is_blocked")
    return [r["id"] for r in rows]


async def count_users(search: str = "") -> int:
    if search:
        return await _pool.fetchval(
            "SELECT COUNT(*) FROM users WHERE username ILIKE $1 OR first_name ILIKE $1",
            f"%{search}%") or 0
    return await _pool.fetchval("SELECT COUNT(*) FROM users") or 0


async def list_users(search: str = "", limit: int = 50, offset: int = 0) -> list[dict]:
    where = "WHERE u.username ILIKE $1 OR u.first_name ILIKE $1" if search else ""
    args = [f"%{search}%"] if search else []
    args += [limit, offset]
    ph = f"${len(args)-1}", f"${len(args)}"
    rows = await _pool.fetch(
        f"""SELECT u.id, u.username, u.first_name, u.is_blocked, u.created_at,
                   u.xp, u.streak, u.best_streak,
                   COUNT(a.id) AS attempts
            FROM users u LEFT JOIN attempts a ON a.user_id=u.id
            {where}
            GROUP BY u.id ORDER BY u.created_at DESC LIMIT {ph[0]} OFFSET {ph[1]}""",
        *args,
    )
    return [dict(r) for r in rows]


# ─────────────────────── gamifikatsiya (xp / streak) ───────────────────────

async def add_xp(user_id: int, amount: int) -> int:
    """XP qo'shadi va yangi umumiy XP'ni qaytaradi."""
    if amount <= 0:
        row = await _pool.fetchrow("SELECT xp FROM users WHERE id=$1", user_id)
        return int(row["xp"]) if row else 0
    row = await _pool.fetchrow(
        "UPDATE users SET xp = xp + $2 WHERE id=$1 RETURNING xp", user_id, amount)
    return int(row["xp"]) if row else 0


async def touch_streak(user_id: int) -> dict:
    """Kunlik faollik streak'ini yangilaydi. {streak, best_streak, changed} qaytaradi."""
    row = await _pool.fetchrow(
        "SELECT streak, best_streak, last_active FROM users WHERE id=$1", user_id)
    if not row:
        return {"streak": 0, "best_streak": 0, "changed": False}
    today = _dt.date.today()
    last = row["last_active"]
    streak = int(row["streak"] or 0)
    best = int(row["best_streak"] or 0)
    changed = False
    if last == today:
        pass  # bugun allaqachon hisoblangan
    elif last == today - _dt.timedelta(days=1):
        streak += 1
        changed = True
    else:
        streak = 1
        changed = True
    if streak > best:
        best = streak
    if changed or last != today:
        await _pool.execute(
            "UPDATE users SET streak=$2, best_streak=$3, last_active=$4 WHERE id=$1",
            user_id, streak, best, today)
    return {"streak": streak, "best_streak": best, "changed": changed}


async def user_profile(user_id: int) -> dict:
    """Profil uchun yig'ma statistika."""
    u = await _pool.fetchrow(
        "SELECT xp, streak, best_streak, created_at FROM users WHERE id=$1", user_id)
    agg = await _pool.fetchrow(
        """SELECT COUNT(*) AS attempts,
                  COALESCE(SUM(score),0) AS total_score,
                  COALESCE(SUM(total),0) AS total_q,
                  AVG(score::float/NULLIF(total,0)) AS avg_pct,
                  MAX(score::float/NULLIF(total,0)) AS best_pct,
                  COUNT(DISTINCT quiz_id) FILTER (WHERE quiz_id IS NOT NULL) AS quizzes,
                  COUNT(*) FILTER (WHERE total>0 AND score=total) AS perfect
           FROM attempts WHERE user_id=$1""",
        user_id)
    # umumiy reytingdagi o'rin (o'rtacha foiz bo'yicha)
    rank = await _pool.fetchval(
        """WITH avg_by_user AS (
              SELECT user_id, AVG(score::float/NULLIF(total,0)) a
              FROM attempts WHERE total>0 GROUP BY user_id)
           SELECT COUNT(*)+1 FROM avg_by_user
           WHERE a > (SELECT a FROM avg_by_user WHERE user_id=$1)""",
        user_id)
    d = dict(agg) if agg else {}
    d.update(dict(u) if u else {})
    d["rank"] = rank
    return d


# ─────────────────────────── achievements ───────────────────────────

async def user_achievement_codes(user_id: int) -> set:
    rows = await _pool.fetch("SELECT code FROM user_achievements WHERE user_id=$1", user_id)
    return {r["code"] for r in rows}


async def grant_achievement(user_id: int, code: str) -> bool:
    """Nishon beradi. Yangi bo'lsa True qaytaradi (bildirishnoma uchun)."""
    row = await _pool.fetchrow(
        """INSERT INTO user_achievements(user_id, code) VALUES($1,$2)
           ON CONFLICT (user_id, code) DO NOTHING RETURNING code""",
        user_id, code)
    return row is not None


async def correct_answers_total(user_id: int) -> int:
    return await _pool.fetchval(
        "SELECT COUNT(*) FROM question_answers WHERE user_id=$1 AND is_correct", user_id) or 0


# ─────────────────────────── categories ───────────────────────────

async def list_categories() -> list[dict]:
    rows = await _pool.fetch(
        """SELECT c.id, c.name, c.emoji, c.position,
                  COUNT(q.id) FILTER (WHERE q.is_active) AS q_count
           FROM categories c
           LEFT JOIN quizzes q ON q.category_id=c.id
           GROUP BY c.id ORDER BY c.position, c.name""")
    return [dict(r) for r in rows]


async def get_category(cat_id: int):
    return await _pool.fetchrow("SELECT * FROM categories WHERE id=$1", cat_id)


async def create_category(name: str, emoji: str = "📁", position: int = 0) -> int:
    return await _pool.fetchval(
        "INSERT INTO categories(name, emoji, position) VALUES($1,$2,$3) RETURNING id",
        name, emoji or "📁", position)


async def update_category(cat_id: int, name: str, emoji: str, position: int) -> None:
    await _pool.execute(
        "UPDATE categories SET name=$2, emoji=$3, position=$4 WHERE id=$1",
        cat_id, name, emoji or "📁", position)


async def delete_category(cat_id: int) -> None:
    await _pool.execute("DELETE FROM categories WHERE id=$1", cat_id)


async def set_quiz_category(quiz_id: int, category_id) -> None:
    await _pool.execute("UPDATE quizzes SET category_id=$2 WHERE id=$1", quiz_id, category_id)


async def uncategorized_count(active_only: bool = True) -> int:
    cond = " AND is_active" if active_only else ""
    return await _pool.fetchval(
        f"SELECT COUNT(*) FROM quizzes WHERE category_id IS NULL{cond}") or 0


# ─────────────────────────── quizzes ───────────────────────────

async def create_quiz(name: str, owner_id: int, questions: list[dict],
                      category_id=None, difficulty=None) -> int:
    """Test + savollarni bitta tranzaksiyada saqlaydi. quiz_id qaytaradi."""
    async with _pool.acquire() as con:
        async with con.transaction():
            qid = await con.fetchval(
                """INSERT INTO quizzes(name, owner_id, category_id, difficulty)
                   VALUES($1,$2,$3,$4) RETURNING id""",
                name, owner_id, category_id, difficulty,
            )
            for pos, q in enumerate(questions):
                await con.execute(
                    """INSERT INTO questions(quiz_id, position, text, options, correct,
                                             explanation, image_file_id)
                       VALUES($1,$2,$3,$4,$5,$6,$7)""",
                    qid, pos, q["text"], json.dumps(q["options"], ensure_ascii=False),
                    q["correct"], q.get("explanation"), q.get("image_file_id"),
                )
    return qid


async def get_quiz(quiz_id: int):
    return await _pool.fetchrow(
        """SELECT q.*, c.name AS category_name, c.emoji AS category_emoji
           FROM quizzes q LEFT JOIN categories c ON c.id=q.category_id
           WHERE q.id=$1""", quiz_id)


def _row_to_q(r) -> dict:
    opts = r["options"]
    if isinstance(opts, str):
        opts = json.loads(opts)
    d = {"id": r["id"], "text": r["text"], "options": opts,
         "correct": r["correct"], "explanation": r["explanation"]}
    try:
        d["image_file_id"] = r["image_file_id"]
    except (KeyError, ValueError):
        d["image_file_id"] = None
    return d


async def get_questions(quiz_id: int) -> list[dict]:
    rows = await _pool.fetch(
        "SELECT id, text, options, correct, explanation, image_file_id FROM questions "
        "WHERE quiz_id=$1 ORDER BY position, id",
        quiz_id,
    )
    return [_row_to_q(r) for r in rows]


async def get_question(qid: int):
    r = await _pool.fetchrow(
        "SELECT id, quiz_id, text, options, correct, explanation, image_file_id "
        "FROM questions WHERE id=$1", qid)
    if not r:
        return None
    d = _row_to_q(r)
    d["quiz_id"] = r["quiz_id"]
    return d


async def update_question(qid, text, options, correct, explanation) -> None:
    await _pool.execute(
        """UPDATE questions SET text=$2, options=$3, correct=$4, explanation=$5 WHERE id=$1""",
        qid, text, json.dumps(options, ensure_ascii=False), correct, explanation or None,
    )


async def delete_question(qid: int) -> None:
    await _pool.execute("DELETE FROM questions WHERE id=$1", qid)


async def add_questions(quiz_id: int, questions: list[dict]) -> None:
    base = await _pool.fetchval(
        "SELECT COALESCE(MAX(position),0)+1 FROM questions WHERE quiz_id=$1", quiz_id) or 0
    async with _pool.acquire() as con:
        async with con.transaction():
            for i, q in enumerate(questions):
                await con.execute(
                    """INSERT INTO questions(quiz_id, position, text, options, correct,
                                             explanation, image_file_id)
                       VALUES($1,$2,$3,$4,$5,$6,$7)""",
                    quiz_id, base + i, q["text"],
                    json.dumps(q["options"], ensure_ascii=False),
                    q["correct"], q.get("explanation"), q.get("image_file_id"),
                )


async def count_quizzes(active_only: bool = False, search: str = "", category_id="__all__") -> int:
    conds = []
    args = []
    if active_only:
        conds.append("is_active")
    if search:
        args.append(f"%{search}%")
        conds.append(f"name ILIKE ${len(args)}")
    if category_id != "__all__":
        if category_id is None:
            conds.append("category_id IS NULL")
        else:
            args.append(category_id)
            conds.append(f"category_id = ${len(args)}")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    return await _pool.fetchval(f"SELECT COUNT(*) FROM quizzes {where}", *args) or 0


async def list_quizzes(active_only: bool = True, search: str = "", category_id="__all__",
                       limit: int = 100, offset: int = 0) -> list[dict]:
    conds = []
    args = []
    if active_only:
        conds.append("q.is_active")
    if search:
        args.append(f"%{search}%")
        conds.append(f"q.name ILIKE ${len(args)}")
    if category_id != "__all__":
        if category_id is None:
            conds.append("q.category_id IS NULL")
        else:
            args.append(category_id)
            conds.append(f"q.category_id = ${len(args)}")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    args += [limit, offset]
    rows = await _pool.fetch(
        f"""SELECT q.*, c.name AS category_name, c.emoji AS category_emoji,
                   COUNT(qs.id) AS q_count
            FROM quizzes q
            LEFT JOIN questions qs ON qs.quiz_id=q.id
            LEFT JOIN categories c ON c.id=q.category_id
            {where}
            GROUP BY q.id, c.name, c.emoji
            ORDER BY q.created_at DESC LIMIT ${len(args)-1} OFFSET ${len(args)}""",
        *args,
    )
    return [dict(r) for r in rows]


async def count_questions(quiz_id: int) -> int:
    return await _pool.fetchval("SELECT COUNT(*) FROM questions WHERE quiz_id=$1", quiz_id) or 0


async def set_quiz_active(quiz_id: int, active: bool) -> None:
    await _pool.execute("UPDATE quizzes SET is_active=$2 WHERE id=$1", quiz_id, active)


async def set_quiz_difficulty(quiz_id: int, difficulty) -> None:
    await _pool.execute("UPDATE quizzes SET difficulty=$2 WHERE id=$1", quiz_id, difficulty)


async def delete_quiz(quiz_id: int) -> None:
    await _pool.execute("DELETE FROM quizzes WHERE id=$1", quiz_id)


async def rename_quiz(quiz_id: int, name: str) -> None:
    await _pool.execute("UPDATE quizzes SET name=$2 WHERE id=$1", quiz_id, name)


# ─────────────────────────── favorites ───────────────────────────

async def add_favorite(user_id: int, quiz_id: int) -> None:
    await _pool.execute(
        """INSERT INTO favorites(user_id, quiz_id) VALUES($1,$2)
           ON CONFLICT DO NOTHING""", user_id, quiz_id)


async def remove_favorite(user_id: int, quiz_id: int) -> None:
    await _pool.execute("DELETE FROM favorites WHERE user_id=$1 AND quiz_id=$2",
                        user_id, quiz_id)


async def is_favorite(user_id: int, quiz_id: int) -> bool:
    return bool(await _pool.fetchval(
        "SELECT 1 FROM favorites WHERE user_id=$1 AND quiz_id=$2", user_id, quiz_id))


async def list_favorites(user_id: int, limit: int = 50) -> list[dict]:
    rows = await _pool.fetch(
        """SELECT q.id, q.name, q.is_active, COUNT(qs.id) AS q_count
           FROM favorites f
           JOIN quizzes q ON q.id=f.quiz_id
           LEFT JOIN questions qs ON qs.quiz_id=q.id
           WHERE f.user_id=$1 AND q.is_active
           GROUP BY q.id ORDER BY MAX(f.created_at) DESC LIMIT $2""",
        user_id, limit)
    return [dict(r) for r in rows]


async def recent_quizzes(user_id: int, limit: int = 5) -> list[dict]:
    """Foydalanuvchi so'nggi o'ynagan (mavjud) testlar."""
    rows = await _pool.fetch(
        """SELECT q.id, q.name, MAX(a.created_at) AS last_played,
                  COUNT(qs.id) AS q_count
           FROM attempts a
           JOIN quizzes q ON q.id=a.quiz_id
           LEFT JOIN questions qs ON qs.quiz_id=q.id
           WHERE a.user_id=$1 AND q.is_active
           GROUP BY q.id ORDER BY last_played DESC LIMIT $2""",
        user_id, limit)
    return [dict(r) for r in rows]


# ───────────────────────── attempts / leaderboard ─────────────────────────

async def save_attempt(user_id, username, quiz_id, quiz_name, score, total,
                       mode=None, duration_sec=None) -> None:
    await _pool.execute(
        """INSERT INTO attempts(user_id, username, quiz_id, quiz_name, score, total,
                                mode, duration_sec)
           VALUES($1,$2,$3,$4,$5,$6,$7,$8)""",
        user_id, username, quiz_id, quiz_name, score, total, mode, duration_sec,
    )


async def leaderboard(quiz_id: int | None = None, limit: int = 10,
                      period: str = "all") -> list[dict]:
    """Eng yaxshi natijalar. period: 'all' | 'week'."""
    since = ""
    if period == "week":
        since = " AND created_at > now() - interval '7 days'"
    if quiz_id:
        rows = await _pool.fetch(
            f"""SELECT user_id, MAX(username) AS username,
                       MAX(score::float / NULLIF(total,0)) AS best,
                       COUNT(*) AS tries
                FROM attempts WHERE quiz_id=$1 AND total>0{since}
                GROUP BY user_id ORDER BY best DESC, tries ASC LIMIT $2""",
            quiz_id, limit,
        )
    else:
        rows = await _pool.fetch(
            f"""SELECT user_id, MAX(username) AS username,
                       AVG(score::float / NULLIF(total,0)) AS best,
                       COUNT(*) AS tries
                FROM attempts WHERE total>0{since}
                GROUP BY user_id ORDER BY best DESC, tries DESC LIMIT $1""",
            limit,
        )
    return [dict(r) for r in rows]


async def user_history(user_id: int, limit: int = 10) -> list[dict]:
    rows = await _pool.fetch(
        """SELECT quiz_name, score, total, mode, duration_sec, created_at FROM attempts
           WHERE user_id=$1 ORDER BY created_at DESC LIMIT $2""",
        user_id, limit,
    )
    return [dict(r) for r in rows]


async def count_results(search: str = "") -> int:
    if search:
        return await _pool.fetchval(
            "SELECT COUNT(*) FROM attempts WHERE quiz_name ILIKE $1 OR username ILIKE $1",
            f"%{search}%") or 0
    return await _pool.fetchval("SELECT COUNT(*) FROM attempts") or 0


async def list_results(search: str = "", limit: int = 50, offset: int = 0) -> list[dict]:
    where = "WHERE quiz_name ILIKE $1 OR username ILIKE $1" if search else ""
    args = [f"%{search}%"] if search else []
    args += [limit, offset]
    rows = await _pool.fetch(
        f"""SELECT username, user_id, quiz_name, score, total, mode, duration_sec, created_at
            FROM attempts {where}
            ORDER BY created_at DESC LIMIT ${len(args)-1} OFFSET ${len(args)}""",
        *args,
    )
    return [dict(r) for r in rows]


async def quiz_attempt_stats(quiz_id: int) -> dict:
    row = await _pool.fetchrow(
        """SELECT COUNT(*) AS attempts,
                  AVG(score::float/NULLIF(total,0)) AS avg_pct
           FROM attempts WHERE quiz_id=$1""",
        quiz_id,
    )
    return dict(row) if row else {"attempts": 0, "avg_pct": None}


# ─────────────────────── savol darajasidagi analitika ───────────────────────

async def log_answer(question_id, quiz_id, question_text, user_id, username,
                     chosen_index, is_correct) -> None:
    await _pool.execute(
        """INSERT INTO question_answers
               (question_id, quiz_id, question_text, user_id, username, chosen_index, is_correct)
           VALUES($1,$2,$3,$4,$5,$6,$7)""",
        question_id, quiz_id, question_text, user_id, username, chosen_index, bool(is_correct),
    )


async def question_stats(quiz_id: int) -> list[dict]:
    """Har savol bo'yicha: jami javob, to'g'ri javob soni (pozitsiya tartibida)."""
    rows = await _pool.fetch(
        """SELECT q.id, q.position, q.text,
                  COUNT(qa.id) AS total,
                  COUNT(qa.id) FILTER (WHERE qa.is_correct) AS correct
           FROM questions q
           LEFT JOIN question_answers qa ON qa.question_id = q.id
           WHERE q.quiz_id = $1
           GROUP BY q.id ORDER BY q.position, q.id""",
        quiz_id,
    )
    return [dict(r) for r in rows]


async def quiz_accuracy(quiz_id: int):
    """Test bo'yicha umumiy aniqlik foizi (avtomatik qiyinlik uchun)."""
    return await _pool.fetchval(
        """SELECT AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END)
           FROM question_answers WHERE quiz_id=$1""", quiz_id)


# ─────────────────────────── settings kv ───────────────────────────

async def get_setting(key: str, default: str = "") -> str:
    row = await _pool.fetchrow("SELECT value FROM settings WHERE key=$1", key)
    return row["value"] if row else default


async def set_setting(key: str, value: str) -> None:
    await _pool.execute(
        """INSERT INTO settings(key,value) VALUES($1,$2)
           ON CONFLICT (key) DO UPDATE SET value=$2""",
        key, value,
    )
