"""LMS client jonli smoke-test. Serverda ishga tushiriladi:
   TEST_LOGIN=.. TEST_PASSWORD=.. python -m scripts.smoke_lms
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lms.client import LmsClient, LoginError  # noqa: E402


async def main():
    login = os.getenv("TEST_LOGIN") or (sys.argv[1] if len(sys.argv) > 1 else "")
    pwd = os.getenv("TEST_PASSWORD") or (sys.argv[2] if len(sys.argv) > 2 else "")
    if not login or not pwd:
        print("TEST_LOGIN / TEST_PASSWORD kerak")
        return

    async with LmsClient() as c:
        try:
            await c.login(login, pwd)
            print("[login] OK")
        except LoginError as e:
            print(f"[login] XATO: {e}")
            return

        sems = await c.semesters()
        print(f"[semesters] {len(sems)} ta:", sems[:4])
        from lms.parse import current_semester
        cur = current_semester(sems)
        print(f"[current_semester] {cur}")

        prof = await c.profile()
        print(f"[profile] {prof.full_name} | {prof.group} | {prof.level}-kurs | {prof.speciality}")

        for sem in [49, cur]:
            if not sem:
                continue
            courses = await c.courses(sem)
            print(f"[courses sem={sem}] {len(courses)} ta")
            if courses:
                for cc in courses:
                    print(f"    • [{cc.id}] {cc.subject} | {'/'.join(cc.streams)}")
                # birinchi fanning vazifalari
                tasks = await c.course_tasks(courses[0].id)
                print(f"[tasks {courses[0].subject}] {len(tasks)} ta topshiriq")
                for t in tasks[:4]:
                    print(f"    • [{t.lesson_type}] {t.name} | dl={t.deadline} "
                          f"| {t.score}/{t.max_score} | fayllar={len(t.files)}")
                # bitta faylni yuklab ko'rish (hajm)
                fileurls = [f.url for t in tasks for f in t.files]
                if fileurls:
                    try:
                        nm, data = await c.download(fileurls[0])
                        print(f"[download] {nm} = {len(data)} bayt")
                    except Exception as e:  # noqa: BLE001
                        print(f"[download] xato: {e}")
                break

        sch = await c.schedule(49)
        print(f"[schedule sem=49] {len(sch)} ta mashg'ulot")
        for it in sch[:5]:
            print(f"    • {it.start} {it.room} {it.type_name} {it.subject} ({it.stream})")


if __name__ == "__main__":
    asyncio.run(main())
