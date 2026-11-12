"""Hujjatlar: TXT, DOCX, o'qish uchun PDF va Yordamchi sayti uchun MD."""
from __future__ import annotations

import bisect
import csv
import os
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .core import POS_ORDER, ReadingBlock, ReadingPair, Segment, _env_float, normalize_word, pos_label
from .media import seconds_to_srt_time
from .vocab import dedupe_by_lemma, is_translit_only
from .subtitles import FONTS_DIR
def write_txt_transcript(path: Path, original: list[Segment], translated: list[Segment] | None) -> None:
    lines: list[str] = ["MATN (1-format: Aralash)", "======================", ""]
    for i, seg in enumerate(original):
        lines.append(seg.text)
        if translated and i < len(translated):
            lines.append(f"    {translated[i].text}")
        lines.append("")

    if translated:
        lines += ["", "MATN (2-format: Alohida)", "========================", ""]
        lines += ["--- ORIGINAL ---", ""]
        for seg in original:
            lines.append(seg.text)

        lines += ["", "--- TARJIMA ---", ""]
        for seg in translated:
            lines.append(seg.text)

    path.write_text("\n".join(lines), encoding="utf-8-sig")


def _vocab_freq_note(e: dict[str, Any]) -> str:
    c = int(e.get("count", 1) or 1)
    return f"  (x{c})" if c > 1 else ""


def write_txt_vocab(path: Path, entries: list[dict[str, Any]]) -> None:
    # Bir xil o'zakli so'zlarni birlashtiramiz (kelgan/keldi -> kelmoq).
    merged = dedupe_by_lemma(entries)
    lines = ["LUG'AT (1-format: Chastota bo'yicha)", "=================================", ""]
    helpers = [e for e in merged if e.get("helper")]
    names = [e for e in merged if not e.get("helper") and is_translit_only(e)]
    main = [e for e in merged
            if not e.get("helper") and not is_translit_only(e)]
    lines.append(f"Asosiy so'zlar ({len(main)}) — eng ko'p uchraganlar tepada")
    lines.append("-" * 40)
    for e in main:
        lines.append(f"{e['word']} - {e['translation']}{_vocab_freq_note(e)}")
    if helpers:
        lines += ["", "Yordamchi so'zlar", "-" * 40]
        for e in helpers:
            lines.append(f"{e['word']} - {e['translation']} ({e['helper']}){_vocab_freq_note(e)}")
    if names:
        # Tarjimasi o'zi bilan bir xil — ism yoki o'zlashma.
        lines += ["", "Ismlar va o'zlashmalar", "-" * 40]
        for e in names:
            lines.append(f"{e['word']} - {e['translation']}{_vocab_freq_note(e)}")

    # Format 2
    lines += ["", "", "LUG'AT (2-format: So'z turkumlariga ajratilgan)", "===============================================", ""]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for e in merged:
        grouped.setdefault(pos_label(e), []).append(e)

    for cat in POS_ORDER:
        items = grouped.get(cat, [])
        if items:
            lines += [f"\n{cat} ({len(items)})", "-" * 40]
            for e in items:
                lines.append(f"{e['word']} - {e['translation']}{_vocab_freq_note(e)}")

    path.write_text("\n".join(lines), encoding="utf-8-sig")


def write_docx_transcript(path: Path, original: list[Segment], translated: list[Segment] | None) -> None:
    try:
        from docx import Document
    except Exception as exc:
        raise RuntimeError("DOCX uchun python-docx kerak: pip install python-docx") from exc
    doc = Document()
    doc.add_heading("Matn", level=1)
    for i, seg in enumerate(original):
        p = doc.add_paragraph()
        p.add_run(f"[{seconds_to_srt_time(seg.start)}] ").bold = True
        p.add_run(seg.text)
        if translated and i < len(translated):
            p2 = doc.add_paragraph(translated[i].text)
            p2.paragraph_format.left_indent = 240000
    doc.save(path)


def write_docx_vocab(path: Path, entries: list[dict[str, Any]]) -> None:
    try:
        from docx import Document
    except Exception as exc:
        raise RuntimeError("DOCX uchun python-docx kerak: pip install python-docx") from exc
    merged = dedupe_by_lemma(entries)
    doc = Document()
    doc.add_heading("Lug'at", level=1)
    table = doc.add_table(rows=1, cols=4)
    hdr = table.rows[0].cells
    hdr[0].text = "So'z"
    hdr[1].text = "Tarjima"
    hdr[2].text = "Turi"
    hdr[3].text = "Necha marta"
    for e in merged:
        row = table.add_row().cells
        row[0].text = str(e.get("word", ""))
        row[1].text = str(e.get("translation", ""))
        row[2].text = pos_label(e)
        row[3].text = str(int(e.get("count", 1) or 1))
    doc.save(path)


def write_csv_vocab(path: Path, entries: list[dict[str, Any]]) -> None:
    """Anki va Quizlet importi uchun sodda ustunli lug'at yozadi."""
    # Bitta lemma turli shakllarda takrorlansa, kartochkalar ham takrorlanib
    # ketadi va takrorlash navbati sun'iy uzayadi; shu sabab TXT/DOCX kabi
    # CSV ham birlashtirilgan ro'yxatdan tuziladi.
    merged = dedupe_by_lemma(entries)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["So'z", "Tarjima", "So'z turkumi", "Chastota"])
        for entry in merged:
            writer.writerow([
                str(entry.get("word", "")),
                str(entry.get("translation", "")),
                pos_label(entry),
                int(entry.get("count", 1) or 1),
            ])
