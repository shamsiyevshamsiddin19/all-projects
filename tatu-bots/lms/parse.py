"""LMS HTML/JSON parserlari. Tarmoqsiz — fixture'larda test qilinadi."""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from lxml import html as LH

from core.util import clean, parse_lms_deadline
from .models import (
    LESSON_TYPES,
    CalendarResource,
    Course,
    Final,
    MissedLesson,
    Profile,
    ScheduleItem,
    StudyGrade,
    StudyPlan,
    Task,
    TaskFile,
)

SEP = "###"


# ─────────────────────────── Semestrlar (HTML) ───────────────────────────
def parse_semesters(page_html: str) -> list[tuple[int, str]]:
    """my-courses sahifasidagi <select name='semester_id'> dan (id, nom)."""
    doc = LH.fromstring(page_html)
    out: list[tuple[int, str]] = []
    sel = doc.xpath("//select[@name='semester_id']")
    if not sel:
        return out
    for opt in sel[0].xpath(".//option"):
        val = (opt.get("value") or "").strip()
        if val.isdigit():
            out.append((int(val), clean(opt.text_content())))
    return out


def current_semester(semesters: list[tuple[int, str]]) -> int | None:
    """'qayta o'qish' bo'lmagan eng katta id — odatda joriy faol semestr."""
    if not semesters:
        return None
    normal = [s for s in semesters if "qayta" not in s[1].lower()]
    pool = normal or semesters
    return max(pool, key=lambda s: s[0])[0]


# ─────────────────────────── Fanlar (JSON) ───────────────────────────
def parse_courses(data: dict) -> list[Course]:
    out: list[Course] = []
    for row in (data or {}).get("data", []):
        teachers = [clean(t) for t in str(row.get("teachers", "")).split(SEP) if t.strip()]
        streams = [clean(s) for s in str(row.get("streams", "")).split(SEP) if s.strip()]
        parts = [clean(p) for p in str(row.get("part_ids", "")).split(SEP) if p.strip()]
        out.append(
            Course(
                id=int(row["id"]),
                subject=clean(row.get("subject")),
                subject_id=int(row.get("subject_id") or 0),
                semester_id=int(row.get("semester_id") or 0),
                streams=streams,
                teachers=teachers,
                part_ids=parts,
                attendance=int(row.get("attendance") or 0),
                failed=bool(row.get("failed")),
            )
        )
    return out


# ─────────────────────────── Jadval (JSON) ───────────────────────────
def parse_schedule(data: dict, tz=None) -> list[ScheduleItem]:
    items: list[ScheduleItem] = []
    for ev in (data or {}).get("json", []):
        title = clean(ev.get("title", "")).replace("\\n", "\n")
        raw_title = ev.get("title", "")
        room = ""
        body = raw_title
        # "(A-408)\nFan-STREAM"
        first, _, rest = raw_title.partition("\n")
        if first.strip().startswith("(") and first.strip().endswith(")"):
            room = clean(first).strip("()")
            body = rest
        body = clean(body)
        subject, stream = body, ""
        if "-" in body:
            subject, _, stream = body.rpartition("-")
            subject, stream = clean(subject), clean(stream)
        start = None
        if ev.get("start"):
            try:
                start = datetime.fromisoformat(ev["start"])
                if tz and start.tzinfo is None:
                    start = start.replace(tzinfo=tz)
            except ValueError:
                start = None
        code = int(ev.get("type") or 0)
        items.append(
            ScheduleItem(
                subject=subject or title,
                stream=stream,
                room=room,
                start=start,
                type_code=code,
                type_name=LESSON_TYPES.get(code, "Mashg'ulot"),
                color=clean(ev.get("className")),
            )
        )
    items.sort(key=lambda x: (x.start or datetime.max))
    return items


# ──────────────── Jadval — HAFTALIK GRID (qayta o'qish semestri) ────────────────
# Qayta o'qish semestrlari kalendar JSON emas, HTML haftalik jadval qaytaradi:
# ustunlar: Hafta | Juftlik | Dushanba..Shanba. Har hafta bloki 6 juftlik qatoridan iborat.
_PAIR_TIME = {1: (8, 30), 2: (10, 0), 3: (11, 30), 4: (13, 0), 5: (14, 30),
              6: (16, 0), 7: (17, 30), 8: (19, 0)}
_DATE_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


def parse_schedule_grid(view_html: str, tz=None) -> list[ScheduleItem]:
    """{"view": "<table>"} formatidagi haftalik jadvalni ScheduleItem'larga aylantiradi.
    Har mashg'ulotga hafta sanasi + juftlik vaqti bo'yicha aniq sana beriladi."""
    doc = LH.fromstring(view_html)
    items: list[ScheduleItem] = []
    week_start: datetime | None = None
    for tr in doc.xpath("//tbody/tr"):
        tds = tr.xpath("./td")
        if not tds:
            continue
        idx = 0
        if tds[0].get("rowspan"):  # hafta bloki boshi — sana oralig'i shu yerda
            m = _DATE_RE.search(tds[0].text_content())
            if m:
                d, mo, y = (int(x) for x in m.groups())
                week_start = datetime(y, mo, d)
            idx = 1
        if idx >= len(tds) or week_start is None:
            continue
        pm = re.search(r"\d+", tds[idx].text_content())
        pair = int(pm.group()) if pm else 0
        for wd, cell in enumerate(tds[idx + 1: idx + 7]):  # 6 kun: Dushanba..Shanba
            txt = clean(cell.text_content())
            if not txt:
                continue
            code_el = cell.xpath(".//span")
            room_el = cell.xpath(".//small[contains(@class,'text-info')]")
            code = clean(code_el[0].text_content()) if code_el else ""
            room = clean(room_el[0].text_content()) if room_el else ""
            subject = txt
            for extra in (code, room):
                if extra:
                    subject = subject.replace(extra, "")
            subject = clean(subject)
            hh, mm = _PAIR_TIME.get(pair, (8, 0))
            start = (week_start + timedelta(days=wd)).replace(hour=hh, minute=mm)
            if tz:
                start = start.replace(tzinfo=tz)
            items.append(ScheduleItem(
                subject=subject or code, stream=code, room=room, start=start,
                type_code=0, type_name="Mashg'ulot"))
    items.sort(key=lambda x: x.start or datetime.max)
    return items


# ─────────────────────────── Davomat (JSON) ───────────────────────────
def parse_attendance(data: dict) -> list[MissedLesson]:
    """Qoldirilgan darslar ro'yxati (barcha fanlar bo'yicha)."""
    out: list[MissedLesson] = []
    for row in (data or {}).get("data", []):
        out.append(MissedLesson(
            date=clean(row.get("date")),
            subject=clean(row.get("subject")),
            lesson_type=clean(row.get("type")),
            topic=clean(row.get("calendar")),
            excused=bool(row.get("has_reason")),
            theme_number=int(row.get("theme_number") or 0),
        ))
    return out


def group_missed(missed: list[MissedLesson]) -> dict[str, list[MissedLesson]]:
    out: dict[str, list[MissedLesson]] = {}
    for m in missed:
        out.setdefault(m.subject, []).append(m)
    return out


# ─────────────────────────── Yakuniy (JSON) ───────────────────────────
def parse_finals(data: dict) -> list[Final]:
    out: list[Final] = []
    for row in (data or {}).get("data", []):
        out.append(Final(
            subject=clean(row.get("subject")),
            stream=clean(row.get("stream")),
            date=clean(row.get("date")),
            start=clean(row.get("from")),
            room=clean(row.get("room")),
            grade=clean(str(row.get("f_grade") or "")),
        ))
    return out


# ─────────────────────── Fan sahifasi vazifalari (HTML) ───────────────────────
def parse_course_tasks(page_html: str, tz=None) -> list[Task]:
    doc = LH.fromstring(page_html)
    tables = doc.xpath("//table[@id='simple-table1']")
    if not tables:
        tables = doc.xpath("//table[contains(@class,'sc-table')]")
    if not tables:
        return []
    table = tables[0]

    tasks: list[Task] = []
    last_task: Task | None = None
    for tr in table.xpath(".//tbody/tr"):
        classes = tr.get("class", "")
        if "criteria-row" in classes:
            if last_task is not None:
                last_task.criteria = _parse_criteria(tr)
            continue

        tds = tr.xpath("./td")
        if len(tds) < 6:
            continue

        task = Task()
        task.lesson_type = clean(tds[0].text_content())
        task.teacher = clean(tds[1].text_content())

        title_el = tds[2].xpath(".//*[contains(@class,'sc-activity-title')]")
        task.name = clean(title_el[0].text_content()) if title_el else clean(tds[2].text_content())

        # namuna fayllari (samples)
        for a in tds[2].xpath(".//a[@href]"):
            href = a.get("href", "")
            if "/uploads/" in href:
                task.files.append(TaskFile(name=clean(a.text_content()) or task.name,
                                           url=href, kind="sample"))

        task.deadline = parse_lms_deadline(tds[3].text_content(), tz=tz)

        score_el = tds[4].xpath(".//*[contains(@class,'sc-score')]")
        if score_el:
            task.score, task.max_score = _parse_score(score_el[0])

        # material fayllari (resources)
        for a in tds[5].xpath(".//a[@href]"):
            href = a.get("href", "")
            if "/uploads/" in href:
                task.files.append(TaskFile(name=clean(a.text_content()) or task.name,
                                           url=href, kind="resource"))

        # topshirish tugmasi bo'lsa (data-id)
        for btn in tr.xpath(".//*[@data-id]"):
            task.submit_id = btn.get("data-id")
            break

        tasks.append(task)
        last_task = task
    return tasks


def _parse_score(el) -> tuple[float | None, float | None]:
    full = clean(el.text_content())  # "8 / 8"
    max_el = el.xpath(".//*[contains(@class,'sc-max')]")
    mx = None
    if max_el:
        mtxt = clean(max_el[0].text_content()).lstrip("/ ").strip()
        mx = _to_num(mtxt)
        full = full.replace(clean(max_el[0].text_content()), "")
    sc = _to_num(full.strip())
    return sc, mx


def _parse_criteria(tr) -> list[tuple[str, str]]:
    out = []
    for item in tr.xpath(".//*[contains(@class,'sc-criteria-item')]"):
        strong = item.xpath(".//strong")
        val = clean(strong[0].text_content()) if strong else ""
        label = clean(item.text_content())
        if val and label.endswith(val):
            label = label[: -len(val)].strip()
        out.append((label, val))
    return out


def _to_num(s: str):
    s = (s or "").replace(",", ".").strip()
    try:
        f = float(s)
        return int(f) if f.is_integer() else f
    except (ValueError, TypeError):
        return None


# ─────────────────────────── Profil (HTML) ───────────────────────────
def parse_profile(page_html: str) -> Profile:
    doc = LH.fromstring(page_html)
    p = Profile()
    pairs: dict[str, str] = {}

    # LMS: <span class="si-field-label">Kurs</span><span class="si-field-value">2</span>
    for label in doc.xpath("//*[contains(@class,'si-field-label')]"):
        k = clean(label.text_content()).rstrip(":").lower()
        val = ""
        sib = label.getnext()
        while sib is not None:
            cls = sib.get("class", "")
            if "si-field-value" in cls:
                val = clean(sib.text_content())
                break
            sib = sib.getnext()
        if k and val:
            pairs[k] = val

    # umumiy zaxira: th/td jadval juftliklari
    if not pairs:
        for row in doc.xpath("//tr[count(td)>=2 or (td and th)]"):
            cells = row.xpath("./th|./td")
            if len(cells) >= 2:
                k = clean(cells[0].text_content()).rstrip(":").lower()
                v = clean(cells[1].text_content())
                if k and v:
                    pairs[k] = v

    def _norm(s: str) -> str:
        for ch in "'’ʻ`‘":
            s = s.replace(ch, "")
        return s.lower()

    npairs = {_norm(k): v for k, v in pairs.items()}

    def pick(*keys):
        for kk in keys:
            kk = _norm(kk)
            for label, val in npairs.items():
                if kk in label:
                    return val
        return ""

    name_el = doc.xpath("//*[contains(@class,'si-student-name') or contains(@class,'si-profile-name')]")
    p.full_name = clean(name_el[0].text_content()) if name_el else pick("f.i.o", "familiya")
    p.faculty = pick("fakultet")
    p.group = pick("guruh")
    p.level = pick("kurs", "bosqich", "daraja")
    p.speciality = pick("yo'nalish", "yo nalish", "yonalish", "mutaxassis")
    p.education_form = pick("ta'lim shakli", "ta lim shakli", "talim shakli")
    p.raw = pairs
    return p


# ─────────────────── Individual reja / GPA (HTML) ───────────────────
def parse_study_plan(page_html: str) -> StudyPlan:
    """/student/study-plan — rasmiy GPA + har fan bo'yicha yakuniy baho + kredit."""
    doc = LH.fromstring(page_html)
    sp = StudyPlan()
    g = doc.xpath("//*[contains(@class,'gpa-badge')]")
    if g:
        m = re.search(r"\d+(?:[.,]\d+)?", clean(g[0].text_content()))
        if m:
            sp.gpa = float(m.group().replace(",", "."))

    for card in doc.xpath("//*[contains(@class,'semester-card')]"):
        sem_el = card.xpath(".//*[contains(@class,'semester-num')]")
        sem = clean(sem_el[0].text_content()) if sem_el else ""
        for tr in card.xpath(".//table//tbody/tr"):
            tds = tr.xpath("./td")
            if len(tds) < 3:
                continue
            name = clean(tds[0].text_content())
            credit = _to_num(clean(tds[1].text_content())) or 0
            grade = _to_num(clean(tds[2].text_content()))
            if name:
                sp.grades.append(StudyGrade(subject=name, credit=int(credit),
                                            grade=grade, semester=sem))
    return sp


# ─────────────────── Kalendar reja resurslari (HTML) ───────────────────
def parse_calendar_resources(page_html: str) -> list[CalendarResource]:
    """/student/calendar/{id} — ustoz mavzu bo'yicha yuklagan ma'ruza/amaliyot
    resurslari (dl.tuit.uz/subject-resources/...) va tashqi havolalar."""
    doc = LH.fromstring(page_html)
    out: list[CalendarResource] = []
    for table_id, kind in (("simple-table-1", "lecture"), ("simple-table-2", "practice")):
        tables = doc.xpath(f"//table[@id='{table_id}']")
        if not tables:
            continue
        for tr in tables[0].xpath(".//tbody/tr"):
            tds = tr.xpath("./td")
            if len(tds) < 2:
                continue
            number = clean(tds[0].text_content())
            p_el = tds[1].xpath(".//p")
            topic = clean(p_el[0].text_content()) if p_el else clean(tds[1].text_content())
            date = clean(tds[2].text_content()) if len(tds) >= 3 else ""
            for a in tds[1].xpath(".//a[@href]"):
                href = (a.get("href") or "").strip()
                if not href or href.startswith("#") or href.startswith("javascript"):
                    continue
                title = clean(a.text_content()) or (topic[:40] if topic else f"{number}-mavzu")
                out.append(CalendarResource(
                    topic=topic, title=title, url=href, date=date,
                    kind=kind, number=number))
    return out
