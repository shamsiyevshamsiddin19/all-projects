"""LMS ma'lumot modellari."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Profile:
    full_name: str = ""
    student_id: str = ""
    faculty: str = ""
    group: str = ""
    level: str = ""          # kurs
    speciality: str = ""     # yo'nalish
    education_form: str = ""  # ta'lim shakli
    raw: dict = field(default_factory=dict)


@dataclass
class Course:
    id: int                  # course id (show/{id} uchun)
    subject: str
    subject_id: int
    semester_id: int
    streams: list[str] = field(default_factory=list)
    teachers: list[str] = field(default_factory=list)
    part_ids: list[str] = field(default_factory=list)
    attendance: int = 0
    failed: bool = False

    @property
    def teacher_line(self) -> str:
        return ", ".join(dict.fromkeys(self.teachers))


@dataclass
class TaskFile:
    name: str
    url: str
    kind: str = "resource"   # 'sample' (ustoz namunasi) | 'resource' (material)

    @property
    def ext(self) -> str:
        return self.url.rsplit(".", 1)[-1].lower() if "." in self.url else ""


@dataclass
class Task:
    lesson_type: str = ""    # Amaliyot / Ma'ruza / ...
    teacher: str = ""
    name: str = ""
    deadline: datetime | None = None
    score: float | None = None
    max_score: float | None = None
    criteria: list[tuple[str, str]] = field(default_factory=list)
    files: list[TaskFile] = field(default_factory=list)
    submit_id: str | None = None  # /upload uchun (mavjud bo'lsa)

    @property
    def is_lecture(self) -> bool:
        return self.lesson_type.lower().startswith("ma")  # Ma'ruza

    @property
    def is_practice(self) -> bool:
        return self.lesson_type.lower().startswith("am")  # Amaliyot

    @property
    def graded(self) -> bool:
        return self.score is not None


@dataclass
class ScheduleItem:
    subject: str = ""
    stream: str = ""
    room: str = ""
    start: datetime | None = None
    type_code: int = 0
    type_name: str = ""
    color: str = ""


@dataclass
class MissedLesson:
    date: str = ""
    subject: str = ""
    lesson_type: str = ""
    topic: str = ""
    excused: bool = False     # has_reason == 1
    theme_number: int = 0


@dataclass
class Final:
    subject: str = ""
    stream: str = ""          # patok
    date: str = ""
    start: str = ""           # boshlanish vaqti
    room: str = ""
    grade: str = ""           # f_grade


@dataclass
class StudyGrade:
    """Individual reja — fan bo'yicha yakuniy baho."""
    subject: str = ""
    credit: int = 0
    grade: float | None = None   # 5/4/3/2 yoki None
    semester: str = ""


@dataclass
class StudyPlan:
    gpa: float | None = None
    grades: list = field(default_factory=list)   # list[StudyGrade]

    @property
    def total_credits(self) -> int:
        return sum(g.credit for g in self.grades if g.grade)


@dataclass
class CalendarResource:
    """Kalendar reja resursi — ustoz mavzu bo'yicha yuklagan material."""
    topic: str = ""           # mavzu matni
    title: str = ""           # fayl/havola nomi
    url: str = ""             # dl.tuit.uz/... yoki tashqi havola
    date: str = ""            # mashg'ulot sanasi
    kind: str = "lecture"     # lecture | practice
    number: str = ""          # mavzu raqami

    @property
    def is_external(self) -> bool:
        return "dl.tuit.uz" not in self.url and "lms.tuit.uz" not in self.url

    @property
    def ext(self) -> str:
        tail = self.url.rsplit("/", 1)[-1]
        return tail.rsplit(".", 1)[-1].lower() if "." in tail else ""


LESSON_TYPES = {1: "Ma'ruza", 2: "Amaliyot", 3: "Laboratoriya", 4: "Seminar"}
