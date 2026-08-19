"""lms.tuit.uz jonli klient (httpx, sessiya-cookie). Faqat serverdan ishlaydi
(sandbox tuit.uz'ni bloklaydi)."""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta

import httpx

from core.config import settings
from core.util import TG_FILE_LIMIT
from . import parse
from .models import (
    CalendarResource,
    Course,
    Final,
    MissedLesson,
    Profile,
    ScheduleItem,
    StudyPlan,
    Task,
)

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

_TOKEN_RE = re.compile(r'name="_token"\s+value="([^"]+)"')
_META_CSRF_RE = re.compile(r'name="csrf-token"\s+content="([^"]+)"')

# O'qish so'rovlari uchun kesh muddati (soniya). Bir talaba menyular bo'ylab
# tez yurganda LMS'ni qayta-qayta urmaslik uchun.
CACHE_TTL = 180.0


class LoginError(Exception):
    pass


class LmsError(Exception):
    pass


class LmsClient:
    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        self.base = (base_url or settings.lms_base_url).rstrip("/")
        self.c = httpx.AsyncClient(
            base_url=self.base,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": UA, "Accept-Language": "uz,ru;q=0.9,en;q=0.8"},
        )
        self._authed = False
        self._csrf: str | None = None
        # foydalanuvchi Sozlamalarda tanlagan semestr (0/None = avto-aniqlash)
        self.semester_id: int | None = None
        # key -> (fetched_ts, value)
        self._cache: dict[str, tuple[float, object]] = {}

    async def _cached(self, key: str, factory, ttl: float = CACHE_TTL):
        """factory() natijasini ttl davomida keshdan qaytaradi."""
        now = time.time()
        hit = self._cache.get(key)
        if hit and now - hit[0] < ttl:
            return hit[1]
        val = await factory()
        self._cache[key] = (now, val)
        return val

    def invalidate(self, prefix: str = "") -> None:
        """Keshni tozalash (ma'lumot o'zgargach). prefix bo'lsa — faqat o'sha."""
        if not prefix:
            self._cache.clear()
        else:
            for k in [k for k in self._cache if k.startswith(prefix)]:
                self._cache.pop(k, None)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.c.aclose()

    async def close(self):
        await self.c.aclose()

    # ─────────────────── auth ───────────────────
    async def login(self, login: str, password: str) -> None:
        r = await self.c.get("/auth/login")
        m = _TOKEN_RE.search(r.text)
        if not m:
            raise LmsError("Login sahifasidan CSRF token topilmadi")
        data = {
            "_token": m.group(1),
            "login": login.strip(),
            "password": password,
            "g-recaptcha-response": "",
        }
        r2 = await self.c.post("/auth/login", data=data)
        if "/auth/login" in str(r2.url) or "/login" in str(r2.url):
            raise LoginError("Login yoki parol xato")
        self._authed = True
        cm = _META_CSRF_RE.search(r2.text)
        if cm:
            self._csrf = cm.group(1)

    def _check(self, r: httpx.Response):
        if "/auth/login" in str(r.url):
            self._authed = False
            raise LoginError("Sessiya tugadi — qayta kirish kerak")

    async def _get_html(self, path: str) -> str:
        r = await self.c.get(path)
        self._check(r)
        cm = _META_CSRF_RE.search(r.text)
        if cm:
            self._csrf = cm.group(1)
        return r.text

    async def _get_json(self, path: str) -> dict:
        r = await self.c.get(path, headers={"X-Requested-With": "XMLHttpRequest",
                                            "Accept": "application/json"})
        self._check(r)
        try:
            return r.json()
        except Exception as e:  # noqa: BLE001
            raise LmsError(f"JSON kutilgandi: {path} ({e})")

    # ─────────────────── data ───────────────────
    async def semesters(self) -> list[tuple[int, str]]:
        return await self._cached(
            "semesters",
            lambda: self._semesters_fetch())

    async def _semesters_fetch(self) -> list[tuple[int, str]]:
        return parse.parse_semesters(await self._get_html("/student/my-courses"))

    async def resolve_semester(self, semester_id: int | None) -> int:
        if semester_id:
            return semester_id
        # foydalanuvchi Sozlamalarda aniq semestr tanlagan bo'lsa — o'shani
        if self.semester_id:
            return self.semester_id
        sems = await self.semesters()
        cur = parse.current_semester(sems)
        if not cur:
            raise LmsError("Semestr aniqlanmadi")
        return cur

    async def _semester_name(self, sid: int) -> str:
        for s_id, name in await self.semesters():
            if s_id == sid:
                return name
        return ""

    async def courses(self, semester_id: int | None = None) -> list[Course]:
        sem = await self.resolve_semester(semester_id)

        async def f():
            data = await self._get_json(f"/student/my-courses/data?semester_id={sem}")
            return parse.parse_courses(data)
        return await self._cached(f"courses:{sem}", f)

    async def course_tasks(self, course_id: int, tz=None) -> list[Task]:
        return await self._cached(
            f"tasks:{course_id}",
            lambda: self._course_tasks_fetch(course_id, tz))

    async def _course_tasks_fetch(self, course_id: int, tz) -> list[Task]:
        return parse.parse_course_tasks(
            await self._get_html(f"/student/my-courses/show/{course_id}"), tz=tz)

    async def schedule(self, semester_id: int | None = None, tz=None) -> list[ScheduleItem]:
        sem = await self.resolve_semester(semester_id)
        return await self._cached(
            f"schedule:{sem}",
            lambda: self._schedule_fetch(sem, tz))

    async def _schedule_fetch(self, sem: int, tz) -> list[ScheduleItem]:
        data = await self._get_json(f"/student/schedule/load/{sem}")
        if data.get("json"):
            return parse.parse_schedule(data, tz=tz)
        # qayta o'qish semestri — HTML haftalik grid qaytaradi
        if data.get("view"):
            items = parse.parse_schedule_grid(data["view"], tz=tz)
            # butun semestr emas — joriy hafta atrofidagi oynani qoldiramiz
            now = datetime.now(tz) if tz else datetime.now()
            lo, hi = now - timedelta(days=2), now + timedelta(days=9)
            return [i for i in items if i.start and lo <= i.start <= hi]
        return []

    async def schedule_active(self, tz=None) -> tuple[list[ScheduleItem], int | None, str]:
        """Haqiqatan FAOL semestr jadvalini qaytaradi: (items, sem_id, sem_name).

        Odatdagi joriy semestrni afzal ko'radi. Agar u tugagan bo'lsa
        (bugundan boshlab dars yo'q), 'qayta o'qish' (retake) semestriga o'tadi.
        Hech qaysi faol bo'lmasa — ([], None, "") qaytadi (ta'til/semestr tugagan)."""
        # foydalanuvchi aniq semestr tanlagan bo'lsa — o'shaning jadvalini beramiz
        if self.semester_id:
            items = await self.schedule(semester_id=self.semester_id, tz=tz)
            return items, self.semester_id, await self._semester_name(self.semester_id)
        sems = await self.semesters()
        if not sems:
            return [], None, ""
        normal = [s for s in sems if "qayta" not in s[1].lower()]
        retake = [s for s in sems if "qayta" in s[1].lower()]
        candidates: list[tuple[int, str]] = []
        if normal:
            candidates.append(max(normal, key=lambda s: s[0]))
        candidates += sorted(retake, key=lambda s: s[0], reverse=True)

        today = (datetime.now(tz) if tz else datetime.now()).date()
        for sem_id, sem_name in candidates:
            items = await self.schedule(semester_id=sem_id, tz=tz)
            # bugundan keyin (yoki bugun) dars bo'lsa — semestr faol
            if any(i.start and i.start.date() >= today for i in items):
                return items, sem_id, sem_name
        # hech qaysida kelajak dars yo'q — hammasi tugagan
        return [], None, ""

    async def profile(self) -> Profile:
        return await self._cached(
            "profile",
            lambda: self._profile_fetch())

    async def _profile_fetch(self) -> Profile:
        return parse.parse_profile(await self._get_html("/student/info"))

    async def study_plan(self) -> StudyPlan:
        return await self._cached(
            "study_plan",
            lambda: self._study_plan_fetch())

    async def _study_plan_fetch(self) -> StudyPlan:
        return parse.parse_study_plan(await self._get_html("/student/study-plan"))

    async def finals(self) -> dict:
        return await self._get_json("/student/finals/data")

    async def finals_list(self) -> list[Final]:
        return parse.parse_finals(await self.finals())

    async def attendance(self, semester_id: int | None = None,
                         subject_id: int | None = None) -> list[MissedLesson]:
        """Qoldirilgan darslar (barcha fanlar bo'yicha — subject_id e'tiborga olinmaydi)."""
        sem = await self.resolve_semester(semester_id)
        sid = subject_id or 0
        data = await self._get_json(
            f"/student/attendance/data?subject_id={sid}&semester_id={sem}")
        return parse.parse_attendance(data)

    async def calendar_resources(self, course_id: int) -> list[CalendarResource]:
        """Kalendar reja resurslari (ustoz yuklagan ma'ruza/amaliyot materiallari)."""
        return await self._cached(
            f"calendar:{course_id}",
            lambda: self._calendar_fetch(course_id))

    async def _calendar_fetch(self, course_id: int) -> list[CalendarResource]:
        return parse.parse_calendar_resources(
            await self._get_html(f"/student/calendar/{course_id}"))

    # ─────────────────── fayllar ───────────────────
    async def download(self, url: str, limit: int = TG_FILE_LIMIT) -> tuple[str, bytes]:
        if url.startswith("/"):
            url = self.base + url
        name = url.rsplit("/", 1)[-1].split("?")[0] or "fayl"
        async with self.c.stream("GET", url) as r:
            self._check(r)
            r.raise_for_status()
            chunks, total = [], 0
            async for chunk in r.aiter_bytes():
                total += len(chunk)
                if total > limit:
                    raise LmsError(f"Fayl juda katta (> {limit // (1024*1024)} MB): {name}")
                chunks.append(chunk)
        return name, b"".join(chunks)

    # ─────────────────── topshirish (halol auto-submit) ───────────────────
    async def submit(self, submit_id: str, file_bytes: bytes, filename: str) -> dict:
        if not self._csrf:
            await self._get_html("/dashboard/news")  # csrf olish uchun
        files = {"file": (filename, file_bytes)}
        data = {"id": submit_id, "_token": self._csrf or ""}
        r = await self.c.post(
            "/student/my-courses/upload", data=data, files=files,
            headers={"X-Requested-With": "XMLHttpRequest", "X-CSRF-TOKEN": self._csrf or ""},
        )
        self._check(r)
        # topshirilgach fan vazifalari o'zgaradi — keshni tozalaymiz
        self.invalidate("tasks:")
        try:
            return r.json()
        except Exception:  # noqa: BLE001
            return {"status": r.status_code, "ok": r.is_success}
