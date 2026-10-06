#!/usr/bin/env python3
"""Subtitr Desktop protsessori — buyruq qatori kirish nuqtasi.

Kodning o'zi `subtitr/` paketida, qatlamlar bo'yicha bo'lingan:

    core        yo'llar, konstantalar, dataklasslar, matn yordamchilari
    media       video/audio, yuklab olish, subtitr fayllari, ffprobe
    clean       soxta matnni tozalash, bo'laklarni moslash
    cache       transkripsiya keshi va imzosi
    transcribe  Groq Whisper, lokal model, yutilgan nutqni tiklash
    translate   AI provayderlar, glossariy, so'z ro'yxati
    vocab       lug'at: chastota, lemma, yordamchi so'zlar
    subtitles   ASS yasash va videoga kuydirish
    documents   TXT/DOCX, o'qish uchun PDF, Yordamchi sayti uchun MD
    pipeline    bosqichlarni biriktiruvchi oqim
    cli         shu yerdagi `main()`

Bog'liqlik faqat yuqoridan pastga ketadi (`core` hech kimga bog'liq emas) —
halqa yo'q. Flutter ilovasi aynan shu faylni ishga tushiradi, shuning uchun
uning nomi va joyi o'zgarmaydi.
"""
from __future__ import annotations

import sys

from subtitr.cli import main

if __name__ == "__main__":
    sys.exit(main())
