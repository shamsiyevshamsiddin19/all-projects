"""Talaba statistikasini (GPA, fan baholari, guruh/patok) LMS'dan olib
DB'ga saqlash — ro'yxatdan o'tgan foydalanuvchilar orasida reyting uchun."""
from __future__ import annotations

import re

from core import db

UNIVERSITY = "Muhammad al-Xorazmiy nomidagi TATU"


def patok_of(group: str) -> str:
    """Guruhdan patok: '315-24 DIoʻ' -> '315'."""
    g = (group or "").strip()
    if not g:
        return ""
    head = g.split("-")[0].strip()
    m = re.match(r"\d+", head)
    return m.group() if m else head


def norm_subject(subject: str) -> str:
    """Fan nomini solishtirish uchun normallashtirish (kredit/qavslarni olib tashlash)."""
    s = re.sub(r"\(.*?\)", "", subject or "")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


async def save_from(tg_id: int, prof, sp) -> dict:
    """Allaqachon olingan profil + study-plan ma'lumotidan saqlash (qayta so'rovsiz)."""
    group = prof.group
    await db.save_student_stats(
        tg_id=tg_id,
        full_name=prof.full_name,
        university=UNIVERSITY,
        speciality=prof.speciality,
        level=prof.level,
        patok=patok_of(group),
        groupname=group,
        gpa=sp.gpa,
    )
    rows = [(g.subject, norm_subject(g.subject), g.credit, g.grade, g.semester)
            for g in sp.grades if g.subject]
    await db.save_subject_grades(tg_id, rows)
    return {"gpa": sp.gpa, "subjects": len(rows)}


async def refresh(tg_id: int, client) -> dict:
    """Profil + study-plan ni olib, student_stats va subject_grades ni yangilaydi."""
    prof = await client.profile()
    sp = await client.study_plan()
    return await save_from(tg_id, prof, sp)
