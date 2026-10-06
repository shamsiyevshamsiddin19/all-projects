"""Yuklab olingan materiallarni mavzu papkalariga ko'chiradi (bir martalik migratsiya).

Saqlangan kalendar HTML nusxalari asosida ishlaydi — LMS'ga kirish KERAK EMAS.

    .venv/bin/python -m scripts.organize_topics --dry-run   # faqat ko'rsatadi
    .venv/bin/python -m scripts.organize_topics             # ko'chiradi

Eski joylashuv:  <Fan>/Ma'ruza/01 - 1-maruza.pptx
Yangi joylashuv: <Fan>/Ma'ruza/2026:09:15 | Mavzu nomi…/1-maruza.pptx
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lms.parse import parse_calendar_resources  # noqa: E402
from scripts.fetch_materials import (  # noqa: E402
    ROOT, folders, kind_dir, safe, topic_folder, unique_path,
)

CAL = Path("/tmp/claude-1000/-home-shamsiddin/49f967aa-dbd7-4bea-ad3b-c3fddbfa6523/scratchpad/cal")


def replay(resources):
    """Resurslarni eski yuklovchidagi aynan o'sha tartibda qaytaradi."""
    seen: set[str] = set()
    out = []
    for r in resources:
        if r.is_external or r.url in seen:
            continue
        seen.add(r.url)
        num = (r.number or "").strip().rstrip(".")
        stem = f"{num.zfill(2)} - {r.title}" if num.isdigit() else r.title
        out.append((r, safe(stem, r.ext), safe(r.title, r.ext)))
    return out


def paths_for(base: Path, items):
    """Har bir resurs uchun (eski yo'l, yangi yo'l) juftligini hisoblaydi.

    Eski nomlar ham ' (2)' qo'shimchasi bilan qayta tiklanadi — aks holda bir xil
    nomli ikki fayl bitta manbaga ishora qilib, ko'chirish yarmida uzilib qoladi.
    """
    taken_old: set[Path] = set()
    taken_new: set[Path] = set()
    out = []
    for r, old_name, new_name in items:
        kd = kind_dir(base, r.kind)
        old = unique_path(kd / old_name, taken_old)
        new = unique_path(topic_folder(kd, r.date, r.topic, r.number) / new_name, taken_new)
        out.append((old, new))
    return out


def main():
    dry = "--dry-run" in sys.argv
    if not CAL.exists():
        print(f"Kalendar HTML nusxalari topilmadi: {CAL}\n"
              "Avval: .venv/bin/python -m scripts.dump_calendar")
        return

    fmap = folders()
    courses = {}
    for f in sorted(CAL.glob("*.html")):
        courses[f.stem] = replay(parse_calendar_resources(f.read_text(encoding="utf-8")))

    # Qaysi HTML qaysi fan papkasiga tegishli — mavjud fayl nomlari bo'yicha aniqlaymiz
    mapping = {}
    for cid, pairs in courses.items():
        if not pairs:
            continue
        best, best_hit = None, 0
        for base in fmap.values():
            # ko'chirilgani ham, ko'chirilmagani ham hisobga olinadi (qayta ishga tushirish uchun)
            hit = sum(1 for old, new in paths_for(base, pairs) if old.exists() or new.exists())
            if hit > best_hit:
                best, best_hit = base, hit
        if best is not None:
            mapping[cid] = (best, best_hit, len(pairs))

    print("=== Fan moslashtirish (fayl nomlari bo'yicha aniqlandi) ===")
    for cid, (base, hit, total) in sorted(mapping.items()):
        print(f"  {cid} → {base.name:42} {hit}/{total} fayl topildi")
    unmatched = [c for c, p in courses.items() if p and c not in mapping]
    if unmatched:
        print(f"  ⚠️ moslanmadi: {unmatched}")
    print()

    moves, missing, already = [], [], 0
    for cid, (base, _hit, _tot) in mapping.items():
        for old, new in paths_for(base, courses[cid]):
            if old.exists():
                moves.append((old, new))
            elif new.exists():
                already += 1          # oldingi ishga tushirishda ko'chirilgan
            else:
                missing.append(old)

    print(f"Ko'chiriladi: {len(moves)} | allaqachon joyida: {already} | topilmadi: {len(missing)}")
    topics = {m[1].parent for m in moves}
    print(f"Yaratiladigan mavzu papkalari: {len(topics)}")
    if missing:
        for p in missing[:5]:
            print(f"  ? {p.relative_to(ROOT)}")
        if len(missing) > 5:
            print(f"  …va yana {len(missing) - 5} ta")

    if dry:
        print("\n=== Namuna (birinchi 10) ===")
        for old, new in moves[:10]:
            print(f"  {old.name[:45]}")
            print(f"    → {new.parent.name}/{new.name[:45]}")
        return

    done = 0
    for old, new in moves:
        new.parent.mkdir(parents=True, exist_ok=True)
        old.rename(new)
        done += 1
    print(f"\n✅ Ko'chirildi: {done} ta fayl, {len(topics)} ta mavzu papkasiga.")


if __name__ == "__main__":
    main()
