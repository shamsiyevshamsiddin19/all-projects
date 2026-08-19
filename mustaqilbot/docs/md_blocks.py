"""AI markdown matnini bloklarga ajratuvchi umumiy parser.

DOCX va PDF yasovchilar shu parserdan foydalanadi. Blok turlari:
  ("h1"|"h2"|"h3", matn)
  ("para", matn)          — oddiy xatboshi (**qalin** ichida saqlanadi)
  ("bold", matn)          — to'liq qalin qator
  ("bullet", matn)        — belgili ro'yxat elementi
  ("number", matn)        — raqamli ro'yxat elementi (raqami bilan)
  ("table", [[hujayralar]]) — birinchi qator sarlavha
  ("formula", matn)       — $$ ... $$ dan olingan formula
  ("chart", dict)         — ```chart JSON``` spetsifikatsiyasi
"""
from __future__ import annotations
import json
import re

_SEP_CELL = re.compile(r"^:?-{2,}:?$")
_NUM = re.compile(r"^(\d+[.)])\s+(.*)$")
_HR = re.compile(r"[\-*_—–=]{3,}")


_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean_ctrl(text: str) -> str:
    """XML'ga mos kelmaydigan nazorat belgilarini olib tashlaydi."""
    return _CTRL.sub("", text)


def strip_md(text: str) -> str:
    """Ichki markdown belgilarini olib tashlaydi (jadval hujayralari uchun)."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = text.replace("`", "")
    return clean_ctrl(text).strip()


def _parse_table(rows: list[str]) -> list[list[str]] | None:
    parsed: list[list[str]] = []
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        if cells and all(_SEP_CELL.fullmatch(c) for c in cells if c):
            continue  # |---|---| ajratkich qatori
        parsed.append(cells)
    if len(parsed) < 2:
        return None
    ncols = max(len(r) for r in parsed)
    if ncols < 2:
        return None
    return [r + [""] * (ncols - len(r)) for r in parsed]


def parse_blocks(markdown_text: str) -> list[tuple]:
    lines = markdown_text.split("\n")
    blocks: list[tuple] = []
    i = 0
    n = len(lines)

    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue

        # Gorizontal chiziq (--- *** ___) — hujjatga literal chiqmasin
        if _HR.fullmatch(s):
            i += 1
            continue

        # ```chart JSON``` bloki
        if s.startswith("```"):
            lang = s[3:].strip().lower()
            j = i + 1
            buf: list[str] = []
            while j < n and not lines[j].strip().startswith("```"):
                buf.append(lines[j])
                j += 1
            i = j + 1
            body = "\n".join(buf).strip()
            if lang == "chart" or (not lang and body.startswith("{") and '"type"' in body):
                try:
                    spec = json.loads(body)
                    if isinstance(spec, dict):
                        blocks.append(("chart", spec))
                        continue
                except (ValueError, TypeError):
                    pass
            # chart bo'lmagan/buzuq kod bloki — oddiy matn sifatida
            for l in buf:
                if l.strip():
                    blocks.append(("para", l.strip()))
            continue

        # Jadval: ketma-ket | bilan boshlanadigan qatorlar
        if s.startswith("|"):
            j = i
            rows = []
            while j < n and lines[j].strip().startswith("|"):
                rows.append(lines[j])
                j += 1
            i = j
            table = _parse_table(rows)
            if table:
                blocks.append(("table", table))
            else:
                for r in rows:
                    blocks.append(("para", strip_md(r.strip().strip("|"))))
            continue

        # Formula: $$ ... $$
        if s.startswith("$$"):
            if s.endswith("$$") and len(s) > 4:
                blocks.append(("formula", s[2:-2].strip()))
                i += 1
                continue
            buf = [s[2:].strip()]
            j = i + 1
            while j < n and "$$" not in lines[j]:
                buf.append(lines[j].strip())
                j += 1
            if j < n:
                buf.append(lines[j].split("$$")[0].strip())
                i = j + 1
            else:
                i = j
            blocks.append(("formula", " ".join(x for x in buf if x)))
            continue

        if s.startswith("### "):
            blocks.append(("h3", strip_md(s[4:])))
        elif s.startswith("## "):
            blocks.append(("h2", strip_md(s[3:])))
        elif s.startswith("# "):
            blocks.append(("h1", strip_md(s[2:])))
        elif s.startswith("- ") or s.startswith("* "):
            blocks.append(("bullet", s[2:].strip()))
        elif _NUM.match(s):
            m = _NUM.match(s)
            blocks.append(("number", m.group(2).strip()))
        elif s.startswith("**") and s.endswith("**") and s.count("**") == 2:
            blocks.append(("bold", s[2:-2].strip()))
        else:
            blocks.append(("para", s))
        i += 1

    return blocks


def split_bold_runs(text: str) -> list[tuple[str, bool]]:
    """Matnni (parcha, qalinmi) juftliklarga ajratadi — ichki **qalin** uchun."""
    parts: list[tuple[str, bool]] = []
    for i, seg in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if not seg:
            continue
        seg = re.sub(r"\*(.+?)\*", r"\1", seg)  # *kursiv* ni oddiy qilamiz
        parts.append((seg, i % 2 == 1))
    return parts or [(text, False)]
