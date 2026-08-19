"""Gamifikatsiya: daraja (XP), nishonlar, ball formulasi — sof yordamchi funksiyalar."""
from __future__ import annotations

# ─────────────────────────── darajalar (XP) ───────────────────────────
# Har daraja uchun kerakli XP progressiv oshadi. Darajalarga unvon beriladi.

_TITLES = [
    (1, "🌱 Yangi boshlovchi"),
    (3, "📗 O'quvchi"),
    (6, "📘 Bilimdon"),
    (10, "🎓 Talaba"),
    (15, "🧠 Bilag'on"),
    (22, "⭐ Ekspert"),
    (30, "🏅 Usta"),
    (45, "👑 Bilim sultoni"),
]


def level_for_xp(xp: int) -> dict:
    """XP'dan daraja hisoblaydi.

    Qaytadi: {level, title, into (shu darajaga to'plangan XP),
              need (keyingi darajagacha kerakli XP), progress (0..1)}
    """
    xp = max(0, int(xp or 0))
    level = 1
    need = 60
    into = xp
    while into >= need:
        into -= need
        level += 1
        need = int(need * 1.35)
    title = _TITLES[0][1]
    for lvl, ttl in _TITLES:
        if level >= lvl:
            title = ttl
    return {"level": level, "title": title, "into": into,
            "need": need, "progress": (into / need) if need else 0.0}


def xp_for_attempt(score: int, total: int, mode: str = "exam") -> int:
    """Bitta test uchun XP: har to'g'ri javob + yuqori foizga bonus.

    Imtihon rejimi mashqdan ko'proq beradi ( jiddiyroq).
    """
    if total <= 0:
        return 0
    pct = score / total
    base = score * (6 if mode == "exam" else 4)
    bonus = 0
    if pct >= 1.0:
        bonus = 25 if mode == "exam" else 15
    elif pct >= 0.9:
        bonus = 15 if mode == "exam" else 8
    elif pct >= 0.7:
        bonus = 6
    return int(base + bonus)


# ─────────────────────────── nishonlar ───────────────────────────
# code -> (emoji, sarlavha, tavsif)

ACHIEVEMENTS = {
    "first_quiz":  ("🎯", "Birinchi qadam", "Birinchi testni yakunlading"),
    "ten_quizzes": ("🔟", "Faol o'yinchi", "10 ta test yechding"),
    "fifty_quizzes": ("💪", "Chidamli", "50 ta test yechding"),
    "hundred_quizzes": ("🚀", "Marafonchi", "100 ta test yechding"),
    "perfect":     ("💯", "Benuqson", "Bir testda 100% to'plading"),
    "explorer":    ("🧭", "Kashfiyotchi", "5 xil testni sinab ko'rding"),
    "scholar":     ("📚", "Zabardast", "15 xil testni sinab ko'rding"),
    "streak3":     ("🔥", "Barqaror", "3 kun ketma-ket o'ynading"),
    "streak7":     ("🔥", "Olovli hafta", "7 kun ketma-ket o'ynading"),
    "streak30":    ("🏆", "Temir intizom", "30 kun ketma-ket o'ynading"),
    "centurion":   ("🎖", "Yuzboshi", "Jami 100 ta to'g'ri javob berding"),
    "sharpshooter": ("🎱", "Mergan", "Jami 500 ta to'g'ri javob berding"),
}


def achievement_line(code: str) -> str:
    emoji, title, desc = ACHIEVEMENTS.get(code, ("🏅", code, ""))
    return f"{emoji} <b>{title}</b> — {desc}"


def difficulty_from_accuracy(acc) -> str:
    """O'rtacha aniqlikdan avtomatik qiyinlik: past aniqlik = qiyin."""
    if acc is None:
        return "medium"
    if acc >= 0.8:
        return "easy"
    if acc >= 0.55:
        return "medium"
    return "hard"


DIFFICULTY_LABEL = {
    "easy": "🟢 Oson",
    "medium": "🟡 O'rta",
    "hard": "🔴 Qiyin",
}


def difficulty_label(diff) -> str:
    return DIFFICULTY_LABEL.get(diff or "", "")
