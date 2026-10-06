# -*- coding: utf-8 -*-
"""Vaqt oralig'ini VAZIFADAN BO'LIMGA ko'chiradi.

Ilgari vaqt har bir vazifa MATNI ichida prefiks bo'lib turardi:

    "07:00 - 07:20 | Yugurish"

Endi u bo'limning o'z maydonida (`time`), chunki amalda bir bo'limdagi
ishlar bitta oraliqda bajariladi. Bu skript mavjud rejalarni yangi
shaklga o'tkazadi:

  * bo'lim vaqti = vazifalardagi ENG ERTA boshlanish -> ENG KECH tugash
  * vazifa matnlaridan prefiks olib tashlanadi

XAVFSIZLIK. Standart holatda QURUQ YURISH — hech narsa o'zgartirmaydi,
faqat nima bo'lishini ko'rsatadi. Haqiqiy o'zgartirish uchun:

    python group_time_migrate.py --apply

`--apply` bilan ishlaganda eski `tasks` qiymati ekranga to'liq
chiqariladi — kerak bo'lsa qo'lda qaytarish uchun.

ESLATMA: prefiksni olib tashlash Sport<->Boostday bog'lanishini
BUZMAYDI — u nomlarni solishtirishda prefiksni baribir olib tashlaydi
(sport.py::_TIME_PREFIX_SQL, core.js::normTaskName).
"""
from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "/opt/yordamchi/Boostdaybot/bot_py")

from app import db                                    # noqa: E402
from app.helpers import decode_task_groups, encode_task_groups   # noqa: E402

PREFIX = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*(?:[-–—]\s*(\d{1,2}):(\d{2}))?\s*\|\s*")


def hhmm(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"


def group_span(tasks: list) -> tuple[str, int]:
    """Bo'limdagi vazifalardan umumiy oraliqni hisoblaydi.

    Qaytaradi: ("07:00 - 07:45", nechta vazifada prefiks bor edi).
    """
    starts, ends, n = [], [], 0
    for t in tasks:
        m = PREFIX.match(str(t.get("text", "")))
        if not m:
            continue
        n += 1
        sh, sm = int(m.group(1)), int(m.group(2))
        starts.append(sh * 60 + sm)
        if m.group(3):
            ends.append(int(m.group(3)) * 60 + int(m.group(4)))
        else:
            ends.append(sh * 60 + sm)
    if not starts:
        return "", 0
    a, b = min(starts), max(ends)
    first = hhmm(a // 60, a % 60)
    if b <= a:
        return first, n
    return f"{first} - {hhmm(b // 60, b % 60)}", n


def main(apply: bool) -> int:
    rows = db.all_("SELECT id, tasks FROM plans ORDER BY id")
    changed = 0

    for r in rows:
        groups = decode_task_groups(r["tasks"])
        touched = False

        for g in groups:
            tasks = g.get("tasks") or []
            span, n = group_span(tasks)
            if not n:
                continue

            # Bo'lim vaqti allaqachon qo'yilgan bo'lsa tegmaymiz
            if not (g.get("time") or "").strip():
                g["time"] = span
            for t in tasks:
                t["text"] = PREFIX.sub("", str(t.get("text", "")))
            touched = True
            print(f"  reja {r['id']:<3} | {(g.get('name') or '(nomsiz)')[:18]:<18} | "
                  f"{n} ta vazifadan -> bo'lim vaqti {g['time']!r}")

        if not touched:
            continue
        changed += 1
        if apply:
            print(f"    ESKI qiymat (zaxira uchun): {r['tasks']}")
            db.run("UPDATE plans SET tasks = :t WHERE id = :i",
                   {"t": encode_task_groups(groups), "i": r["id"]})

    print()
    if not changed:
        print("Ko'chirishga narsa yo'q — hamma reja allaqachon yangi shaklda.")
        return 0
    if apply:
        print(f"BAJARILDI: {changed} ta reja yangilandi.")
    else:
        print(f"QURUQ YURISH: {changed} ta reja o'zgarardi. "
              f"Haqiqatan bajarish uchun --apply bilan ishga tushiring.")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
