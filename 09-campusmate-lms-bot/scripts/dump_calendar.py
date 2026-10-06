"""Kalendar reja sahifasining YANGI tuzilishini o'rganish uchun HTML'ni saqlaydi.

    .venv/bin/python -m scripts.dump_calendar

Parol getpass bilan so'raladi, hech qayerga yozilmaydi.
HTML nusxalari scratchpad'ga tushadi — parser shular asosida tuzatiladi.
"""
from __future__ import annotations

import asyncio
import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import lxml.html as LH  # noqa: E402

from scripts.fetch_materials import ask_client  # noqa: E402

OUT = Path("/tmp/claude-1000/-home-shamsiddin/49f967aa-dbd7-4bea-ad3b-c3fddbfa6523/scratchpad/cal")


def shape(href: str) -> str:
    """Havolani naqshga aylantiradi: raqam va hashlarni umumlashtiradi."""
    h = href.split("?")[0]
    h = re.sub(r"/[A-Za-z0-9_-]{20,}(\.[a-z0-9]+)?$", r"/{HASH}\1", h)
    return re.sub(r"/\d+", "/{N}", h)


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = await ask_client()
    try:
        courses = await c.courses()
        print(f"\n{len(courses)} ta fan\n")
        for co in courses:
            html = await c._get_html(f"/student/calendar/{co.id}")
            (OUT / f"{co.id}.html").write_text(html, encoding="utf-8")

            doc = LH.fromstring(html)
            tables = doc.xpath("//table")
            hrefs = [a.get("href") or "" for a in doc.xpath("//a[@href]")]
            yuklash = [a for a in doc.xpath("//a") if "yuklash" in (a.text_content() or "").lower()]
            pats = collections.Counter(shape(h) for h in hrefs if h and not h.startswith("#"))

            print(f"📘 {co.subject[:38]:40} id={co.id}")
            print(f"   HTML {len(html):>7} bayt | jadval {len(tables)} "
                  f"{[t.get('id') or '-' for t in tables]}")
            print(f"   havola {len(hrefs)} | 'Yuklash' tugmasi {len(yuklash)}")
            for pat, n in pats.most_common(6):
                print(f"      {n:4}  {pat[:95]}")
            if yuklash:
                print(f"      namuna Yuklash href: {yuklash[0].get('href')}")
            print()
        print(f"HTML nusxalari saqlandi: {OUT}")
        print("Endi Claude'ga 'tayyor' deng — parserni shular asosida tuzatadi.")
    finally:
        await c.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        pass
