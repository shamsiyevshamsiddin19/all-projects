"""Modellardan Telegram (HTML) xabarlarini shakllantirish."""
from __future__ import annotations

from datetime import datetime

from core.util import esc, fmt_dt, time_left
from lms.models import Course, Final, MissedLesson, Profile, ScheduleItem, Task

WEEKDAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
TYPE_EMOJI = {"Ma'ruza": "📖", "Amaliyot": "✍️", "Laboratoriya": "🔬", "Seminar": "💬"}


def fmt_profile(p: Profile, gpa=None) -> str:
    lines = [f"👤 <b>{esc(p.full_name)}</b>", ""]
    if gpa is not None:
        lines.append(f"⭐️ <b>GPA: {gpa}</b>")
        lines.append("")
    fields = [
        ("🎓 Yo'nalish", p.speciality),
        ("📚 Kurs", p.level),
        ("👥 Guruh", p.group),
    ]
    extra = {
        "Daraja": p.raw.get("darajasi", ""),
        "Ta'lim shakli": p.raw.get("ta’lim shakli", "") or p.raw.get("ta'lim shakli", ""),
        "O'qish tili": p.raw.get("o’qish tili", "") or p.raw.get("o'qish tili", ""),
        "Murabbiy": p.raw.get("murabbiy", ""),
        "Tug'ilgan sana": p.raw.get("tug’ilgan sanasi", ""),
        "Stipendiya": p.raw.get("stipendiya", ""),
    }
    for label, val in fields:
        if val:
            lines.append(f"{label}: <b>{esc(val)}</b>")
    for label, val in extra.items():
        if val:
            lines.append(f"• {label}: {esc(val)}")
    return "\n".join(lines)


def fmt_courses(courses: list[Course], sem_name: str = "") -> str:
    head = f"📚 <b>Fanlarim</b>{(' — ' + esc(sem_name)) if sem_name else ''}\n"
    if not courses:
        return head + "\nHozircha faol fan topilmadi (ta'til davri bo'lishi mumkin)."
    body = []
    for i, c in enumerate(courses, 1):
        body.append(f"{i}. <b>{esc(c.subject)}</b>\n     👨‍🏫 {esc(c.teacher_line)}")
    return head + "\n" + "\n".join(body) + "\n\nBatafsil ko'rish uchun pastdan tanlang 👇"


def _group_by_day(items: list[ScheduleItem]) -> dict[str, list[ScheduleItem]]:
    out: dict[str, list[ScheduleItem]] = {}
    for it in items:
        key = it.start.strftime("%Y-%m-%d") if it.start else "?"
        out.setdefault(key, []).append(it)
    return out


def _day_title(date_str: str) -> str:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{WEEKDAYS[d.weekday()]}, {d.strftime('%d.%m.%Y')}"
    except ValueError:
        return date_str


def fmt_one_day(items: list[ScheduleItem], date_str: str) -> str:
    todays = [i for i in items if i.start and i.start.strftime("%Y-%m-%d") == date_str]
    head = f"📅 <b>{_day_title(date_str)}</b>\n"
    if not todays:
        return head + "\n🎉 Bugun dars yo'q!"
    todays.sort(key=lambda x: x.start or datetime.max)
    rows = []
    for it in todays:
        emoji = TYPE_EMOJI.get(it.type_name, "📌")
        t = it.start.strftime("%H:%M") if it.start else "--:--"
        room = f" · {esc(it.room)}" if it.room else ""
        rows.append(f"🕐 <b>{t}</b>{room}\n   {emoji} {esc(it.subject)} "
                    f"<i>({esc(it.type_name)})</i>")
    return head + "\n" + "\n\n".join(rows)


def fmt_week(items: list[ScheduleItem]) -> str:
    if not items:
        return "🗓 <b>Haftalik jadval</b>\n\nMa'lumot topilmadi."
    out = ["🗓 <b>Jadval</b>"]
    for day, day_items in sorted(_group_by_day(items).items()):
        out.append(f"\n<b>━ {_day_title(day)} ━</b>")
        day_items.sort(key=lambda x: x.start or datetime.max)
        for it in day_items:
            emoji = TYPE_EMOJI.get(it.type_name, "📌")
            t = it.start.strftime("%H:%M") if it.start else "--:--"
            room = f" {esc(it.room)}" if it.room else ""
            out.append(f"  {t}{room} {emoji} {esc(it.subject)}")
    return "\n".join(out)


def fmt_deadlines(pairs: list[tuple[str, Task]], now: datetime | None = None) -> str:
    """pairs = [(subject, task), ...] faqat kelajakdagi deadline'lar."""
    head = "⏰ <b>Yaqin deadline'lar</b>\n"
    if not pairs:
        return head + "\n✅ Yaqin orada topshiriq muddati yo'q."
    pairs = sorted(pairs, key=lambda p: p[1].deadline or datetime.max)
    rows = []
    for subj, t in pairs:
        left = time_left(t.deadline, now)
        warn = "🔴" if (t.deadline and (t.deadline - (now or datetime.now(t.deadline.tzinfo))).days < 1) else "🟡"
        rows.append(f"{warn} <b>{esc(t.name)}</b>\n   📘 {esc(subj)} · {esc(t.lesson_type)}\n"
                    f"   📆 {fmt_dt(t.deadline)} · <i>{left}</i> qoldi")
    return head + "\n" + "\n\n".join(rows)


def fmt_attendance(courses: list[Course], missed: list[MissedLesson]) -> str:
    head = "📋 <b>Davomat — qoldirilgan darslar (NB)</b>\n"
    by_subj: dict[str, list[MissedLesson]] = {}
    for m in missed:
        by_subj.setdefault(m.subject, []).append(m)
    rows, total, total_unexcused = [], 0, 0
    # courses tartibida
    names = [c.subject for c in courses] or list(by_subj.keys())
    for name in names:
        lst = by_subj.get(name, [])
        cnt = len(lst)
        if cnt == 0:
            # courses dagi attendance soni (detalsiz)
            c = next((x for x in courses if x.subject == name), None)
            cnt = c.attendance if c else 0
            if cnt == 0:
                rows.append(f"✅ {esc(name)} — toza")
                continue
            rows.append(f"⚠️ {esc(name)} — <b>{cnt}</b> ta")
            total += cnt
            continue
        unexcused = sum(1 for m in lst if not m.excused)
        total += cnt
        total_unexcused += unexcused
        mark = "🔴" if unexcused else "🟡"
        extra = f" ({unexcused} sababsiz)" if unexcused else " (sababli)"
        rows.append(f"{mark} {esc(name)} — <b>{cnt}</b> ta{extra}")
    foot = f"\n\n🧮 Jami: <b>{total}</b> ta qoldirilgan dars"
    if total_unexcused:
        foot += f", shundan <b>{total_unexcused}</b> ta sababsiz ❗️"
    foot += "\n\n<i>Tafsilot uchun fanni tanlang 👇</i>" if missed else ""
    return head + "\n" + "\n".join(rows) + foot


def fmt_missed_detail(subject: str, lessons: list[MissedLesson]) -> str:
    head = f"📋 <b>{esc(subject)}</b> — qoldirilgan darslar\n"
    if not lessons:
        return head + "\n✅ Qoldirilgan dars yo'q."
    rows = []
    for m in lessons:
        mark = "✅ sababli" if m.excused else "🔴 sababsiz"
        emoji = TYPE_EMOJI.get(m.lesson_type, "📌")
        topic = m.topic[:90] + "…" if len(m.topic) > 90 else m.topic
        rows.append(f"{emoji} <b>{esc(m.date)}</b> · {esc(m.lesson_type)} · {mark}\n"
                    f"   <i>{esc(topic)}</i>")
    return head + "\n" + "\n\n".join(rows)


def fmt_finals(finals: list[Final]) -> str:
    head = "🏆 <b>Yakuniy imtihonlar</b>\n"
    if not finals:
        return head + "\nHozircha imtihon jadvali e'lon qilinmagan."
    rows = []
    for f in finals:
        line = f"📘 <b>{esc(f.subject)}</b>"
        if f.stream:
            line += f" · {esc(f.stream)}"
        meta = []
        if f.date:
            meta.append(f"📆 {esc(f.date)}")
        if f.start:
            meta.append(f"🕐 {esc(f.start)}")
        if f.room:
            meta.append(f"🚪 {esc(f.room)}")
        if meta:
            line += "\n   " + " · ".join(meta)
        if f.grade and f.grade not in ("0", "None", ""):
            line += f"\n   📊 Ball: <b>{esc(f.grade)}</b>"
        rows.append(line)
    return head + "\n" + "\n\n".join(rows)


def fmt_overall(items: list[tuple[str, float, float]], gpa=None) -> str:
    """items = [(subject, total, max), ...]"""
    head = "📈 <b>Umumiy o'zlashtirish</b>\n"
    if gpa is not None:
        head += f"\n⭐️ <b>GPA: {gpa}</b>  <i>(barcha semestrlar)</i>\n"
    head += "\n<b>Joriy semestr fanlari:</b>"
    if not items:
        return head + "\nMa'lumot yo'q."
    rows, g_total, g_max = [], 0.0, 0.0
    for subj, total, mx in items:
        g_total += total
        g_max += mx
        pct = f" · {total / mx * 100:.0f}%" if mx else ""
        rows.append(f"📘 {esc(subj)} — <b>{total:g}</b>/{mx:g}{pct}")
    avg = (g_total / g_max * 100) if g_max else 0
    foot = (f"\n\n🧮 Jami: <b>{g_total:g}</b> / {g_max:g}\n"
            f"📊 O'rtacha o'zlashtirish: <b>{avg:.1f}%</b>")
    return head + "\n" + "\n".join(rows) + foot


def fmt_grades(course: Course, tasks: list[Task]) -> str:
    head = f"📊 <b>{esc(course.subject)}</b> — baholar\n"
    if not tasks:
        return head + "\nMa'lumot yo'q."
    rows, total, total_max = [], 0.0, 0.0
    for t in tasks:
        emoji = TYPE_EMOJI.get(t.lesson_type, "📌")
        if t.score is not None:
            sc = f"<b>{t.score}</b>/{t.max_score if t.max_score is not None else '?'}"
            total += float(t.score)
            if t.max_score:
                total_max += float(t.max_score)
        else:
            sc = "—"
        rows.append(f"{emoji} {esc(t.name)} — {sc}")
    foot = f"\n\n🧮 Jami: <b>{total:g}</b>"
    if total_max:
        foot += f" / {total_max:g}"
    return head + "\n" + "\n".join(rows) + foot


SCOPE_TITLES = {
    "university": "🎓 Universitet bo'yicha",
    "speciality": "🧭 Yo'nalish bo'yicha",
    "level": "📚 Kurs bo'yicha",
    "patok": "👥 Potok bo'yicha",
    "group": "🏠 Guruh bo'yicha",
}
_MEDAL = {1: "🥇", 2: "🥈", 3: "🥉"}


def _rank_name(name: str, is_me: bool) -> str:
    if is_me:
        return f"<b>{esc(name)} (siz)</b>"
    return esc(name)


def fmt_rank(res: dict, scope_extra: str = "") -> str:
    title = SCOPE_TITLES.get(res["scope"], "🏅 Reyting")
    head = f"{title} reyting\n"
    if scope_extra:
        head += f"<i>{esc(scope_extra)}</i>\n"
    head += (f"\n⭐️ Sizning GPA: <b>{res['gpa']}</b>\n"
             f"📍 O'rningiz: <b>{res['position']}</b> / {res['total']} talaba\n")
    if res["total"] <= 1:
        head += ("\n<i>Hozircha siz yagona ro'yxatdan o'tgan talabasiz. "
                 "Do'stlaringiz botga qo'shilgan sari reyting aniqroq bo'ladi.</i>")
        return head
    rows = ["\n🏆 <b>Top 10:</b>"]
    for i, t in enumerate(res["top"], 1):
        mark = _MEDAL.get(i, f"{i}.")
        rows.append(f"{mark} {_rank_name(t['name'], t['is_me'])} — GPA {t['gpa']}")
    return head + "\n" + "\n".join(rows)


def fmt_subject_ranks(ranks: list[dict]) -> str:
    head = "📖 <b>Fanlar bo'yicha reyting</b>\n"
    if not ranks:
        return head + "\nMa'lumot yo'q (study-plan'da baholar topilmadi)."
    rows = []
    for r in sorted(ranks, key=lambda x: x["position"]):
        medal = _MEDAL.get(r["position"], "")
        rows.append(f"📘 {esc(r['subject'])}\n   {medal} <b>{r['position']}</b>/{r['total']} "
                    f"· bahoyingiz: <b>{r['grade']:g}</b>")
    return head + "\n" + "\n\n".join(rows)


def fmt_subject_top(subject: str, top: list[dict]) -> str:
    head = f"📘 <b>{esc(subject)}</b> — top talabalar\n"
    if not top:
        return head + "\nMa'lumot yo'q."
    rows = []
    for i, t in enumerate(top, 1):
        mark = _MEDAL.get(i, f"{i}.")
        rows.append(f"{mark} {esc(t['name'])} — baho {t['grade']:g}")
    return head + "\n" + "\n".join(rows)
