"""LMS'dagi barcha ma'ruza va amaliyot materiallarini ~/Documents/TUIT ga yuklaydi.

Har bir fayl o'z fanining Ma'ruza/ yoki Amaliyot/ papkasiga tushadi.
Mavjud fayllar qayta yuklanmaydi (ustiga yozilmaydi).

Ishga tushirish:
    .venv/bin/python -m scripts.fetch_materials            # haqiqiy yuklash
    .venv/bin/python -m scripts.fetch_materials --dry-run  # faqat ro'yxat
"""
from __future__ import annotations

import asyncio
import getpass
import re
import sys
import unicodedata
from datetime import timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lms.client import LmsClient, LmsError, LoginError, OneIdSmsRequired  # noqa: E402

ROOT = Path.home() / "Documents" / "TUIT"
SKIP_DIRS = {"z_tools"}
BAD = re.compile(r'[\\/:*?"<>|\n\r\t]+')


def norm(s: str) -> str:
    """Taqqoslash uchun: kichik harf, diakritikasiz, faqat harf-raqam."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("'", "").replace("'", "").replace("`", "")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def safe(name: str, ext: str = "") -> str:
    name = BAD.sub("_", (name or "fayl")).strip().strip(".")[:90] or "fayl"
    if ext and not name.lower().endswith("." + ext.lower()):
        name = f"{name}.{ext}"
    return name


def safe_dir(name: str) -> str:
    """Papka nomi: ':' va '|' saqlanadi (Linux'da ruxsat), '/' esa almashtiriladi."""
    name = re.sub(r'[\\/\n\r\t\x00]+', "_", name or "").strip().strip(".")
    return name[:120] or "mavzu"


def iso_date(d: str) -> str:
    """'15.09.2026' → '2026:09:15' (nom bo'yicha saralanganda sana tartibida chiqadi)."""
    m = re.match(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", (d or "").strip())
    if not m:
        return "0000:00:00"
    dd, mm, yy = m.groups()
    return f"{yy}:{int(mm):02d}:{int(dd):02d}"


def topic_folder(kind_base: Path, date: str, topic: str, number: str) -> Path:
    """<Ma'ruza|Amaliyot>/YYYY:MM:DD | Mavzu nomi"""
    t = re.sub(r"\s+", " ", topic or "").strip()
    if len(t) > 70:
        t = t[:70].rsplit(" ", 1)[0].rstrip(" .,;:—-") + "…"
    t = t.rstrip(" .") or (f"{number}-mavzu" if number else "mavzu")
    return kind_base / safe_dir(f"{iso_date(date)} | {t}")


def folders() -> dict[str, Path]:
    """norm(fan nomi) -> papka"""
    out = {}
    for d in sorted(ROOT.iterdir()):
        if d.is_dir() and d.name not in SKIP_DIRS:
            out[norm(d.name)] = d
    return out


def match_folder(subject: str, fmap: dict[str, Path]) -> Path | None:
    """Fan nomini papkaga moslaydi: aniq moslik, so'ng ichki moslik.

    Taxminiy ("eng o'xshash") moslashtirish ataylab yo'q — noto'g'ri papkaga
    jimgina yozib qo'yishdan ko'ra, moslanmagan fanni ro'yxatga chiqargan afzal.
    """
    key = norm(re.sub(r"\(\s*\d+\s*kr\s*\)", "", subject))
    if key in fmap:
        return fmap[key]
    for k, p in fmap.items():
        if k and (k in key or key in k):
            return p
    return None


def unique_path(path: Path, taken: set[Path]) -> Path:
    """Bir xil nomli fayllar bir-birining ustiga yozilmasin.

    LMS'da bitta mavzuda bir xil nomli (masalan ikkita "1-maruza.docx") fayllar
    uchraydi — ularga " (2)", " (3)" qo'shamiz. Diskda allaqachon bor fayl ham
    band hisoblanadi, shunda qayta ishga tushirilganda tartib buzilmaydi.
    """
    if path not in taken:
        taken.add(path)
        return path
    i = 2
    while True:
        cand = path.with_name(f"{path.stem} ({i}){path.suffix}")
        if cand not in taken:
            taken.add(cand)
            return cand
        i += 1


def kind_dir(base: Path, kind: str) -> Path:
    """kind: lecture | practice → mavjud papka nomini topadi."""
    want = ["ma'ruza", "ma’ruza", "maruza"] if kind == "lecture" else ["amaliyot"]
    for d in base.iterdir():
        if d.is_dir() and norm(d.name) in {norm(w) for w in want}:
            return d
    d = base / ("Ma'ruza" if kind == "lecture" else "Amaliyot")
    d.mkdir(parents=True, exist_ok=True)
    return d


_CTRL = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|[\x00-\x1f\x7f]")


def clean_input(prompt: str) -> str:
    """input() + strelka/backspace tugmalaridan qolgan boshqaruv belgilarini tozalash.

    Terminalda yuqoriga strelka bosilsa input() ga \x1b[A kabi ketma-ketlik
    tushib qoladi va login buziladi — shuni olib tashlaymiz.
    """
    raw = input(prompt)
    out = _CTRL.sub("", raw).strip()
    if out != raw.strip():
        print(f"   (tozalandi → {out!r})")
    return out


async def ask_client() -> LmsClient:
    print("Kirish usuli:  1) OneID (id.egov.uz)   2) LMS login/parol")
    choice = (clean_input("Tanlang [1]: ") or "1")
    login = clean_input("Login: ")
    password = getpass.getpass("Parol (ko'rinmaydi): ")
    c = LmsClient()
    try:
        if choice == "1":
            try:
                await c.oneid_login(login, password)
            except OneIdSmsRequired:
                code = clean_input("SMS kod: ")
                await c.oneid_login_sms(login, code)
        else:
            await c.login(login, password)
    except Exception:
        await c.close()
        raise
    return c


async def main():
    dry = "--dry-run" in sys.argv
    if not ROOT.exists():
        print(f"Papka topilmadi: {ROOT}")
        return
    fmap = folders()
    print(f"Papkalar ({len(fmap)}): " + ", ".join(p.name for p in fmap.values()) + "\n")

    c = await ask_client()
    try:
        courses = await c.courses()
        print(f"\nLMS'da {len(courses)} ta fan topildi.\n")

        plan: list[tuple[Path, str, str]] = []   # (yo'l, url, tavsif)
        taken: set[Path] = set()
        missing_folder = []
        for co in courses:
            base = match_folder(co.subject, fmap)
            if base is None:
                missing_folder.append(co.subject)
                continue
            print(f"📘 {co.subject}  →  {base.name}")

            seen: set[str] = set()
            # 1) kalendar reja materiallari
            try:
                for r in await c.calendar_resources(co.id):
                    if r.is_external or r.url in seen:
                        continue
                    seen.add(r.url)
                    tdir = topic_folder(kind_dir(base, r.kind), r.date, r.topic, r.number)
                    dest = unique_path(tdir / safe(r.title, r.ext), taken)
                    plan.append((dest, r.url, r.title))
            except Exception as e:
                print(f"   ⚠️ kalendar o'qilmadi: {e}")
            # 2) topshiriqlarga biriktirilgan fayllar
            try:
                for t in await c.course_tasks(co.id, tz=timezone.utc):
                    k = "lecture" if t.is_lecture else "practice"
                    for f in t.files:
                        if f.url in seen:
                            continue
                        seen.add(f.url)
                        tag = "namuna" if f.kind == "sample" else "material"
                        stem = f"{t.name} - {f.name} ({tag})"
                        dest = unique_path(kind_dir(base, k) / safe(stem, f.ext), taken)
                        plan.append((dest, f.url, t.name))
            except Exception as e:
                print(f"   ⚠️ topshiriqlar o'qilmadi: {e}")

        if missing_folder:
            print("\n⚠️ Papkasi topilmagan fanlar: " + ", ".join(missing_folder))

        new = [(p, u, d) for p, u, d in plan if not p.exists()]
        print(f"\nJami fayl: {len(plan)} | yangi: {len(new)} | allaqachon bor: {len(plan) - len(new)}")
        if dry:
            for p, u, _ in new[:40]:
                print(f"  → {p.relative_to(ROOT)}")
            if len(new) > 40:
                print(f"  …va yana {len(new) - 40} ta")
            return

        ok, total = 0, 0
        dead: list[str] = []
        for p, url, desc in new:
            try:
                _, data = await c.download(url)
            except LmsError as e:
                dead.append(f"{p.name} — {e}")
                continue
            except Exception as e:
                code = getattr(getattr(e, "response", None), "status_code", None)
                dead.append(f"{p.name} — {'LMS serverida yo‘q (404)' if code == 404 else e}")
                continue
            p.parent.mkdir(parents=True, exist_ok=True)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            ok += 1
            total += len(data)
            print(f"  ✓ [{ok}/{len(new)}] {p.relative_to(ROOT)}  ({len(data)//1024} KB)")

        print(f"\n✅ Yuklandi: {ok} ta ({total/1048576:.1f} MB) | "
              f"o'tkazib yuborildi (bor edi): {len(plan) - len(new)}")
        if dead:
            print(f"⚠️ Olinmadi: {len(dead)}")
            for line in dead[:15]:
                print(f"   • {line}")
            if len(dead) > 15:
                print(f"   …va yana {len(dead) - 15} ta")
    finally:
        await c.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        pass
    except (LoginError, LmsError) as e:
        print(f"\n❌ {e}")
