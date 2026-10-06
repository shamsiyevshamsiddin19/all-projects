# Subtitr Desktop

Video subtitr/tarjima qiluvchi desktop ilova (Flutter GUI + Python backend).

## O'rnatish

Platformangizni tanlang — har birida to'liq qo'llanma bor:

| Platforma | Qo'llanma | Holati |
|---|---|---|
| **Linux** | [`linux/README.md`](linux/README.md) | sinalgan (Ubuntu 24.04) |
| **Windows** | [`windows/README.md`](windows/README.md) | sinalgan (Win 10/11) |
| **macOS** | [`macos/README.md`](macos/README.md) | **sinalmagan** — skriptlar bor, Mac'da tekshirilmagan |

Qisqacha (Linux):

```bash
git clone https://github.com/shamsiyevshamsiddin19/vibe-coding.git
cd vibe-coding/subtitr-desktop
./linux/build.sh && ./dist/SubtitrDesktop/install.sh
```

Uchala platformada ham ilova **manbadan yig'iladi**: Flutter GUI va Python
protsessor bir papkaga yig'ilib, keyin o'rnatiladi. Tayyor o'rnatuvchi
fayllar repoda saqlanmaydi (Linux arxivi ~220 MB, GitHub chegarasi 100 MB) —
ular bo'lsa [Releases](https://github.com/shamsiyevshamsiddin19/vibe-coding/releases)
sahifasida bo'ladi.

## Nima qila oladi

- Video/audio transkripsiya (Groq Whisper / faster-whisper)
- Tarjima (OpenAI / Anthropic Claude / Google Gemini / Groq)
- Lug'at (lemma + chastota) va o'quv uchun so'z animatsiyasi
- "O'qish uchun matn": videoni qayta ko'rmasdan o'qish uchun A4 PDF (3 xil
  maket), TXT va Yordamchi sayti uchun `.md` (gap + so'z tarjimalari ichida)
- Subtitr kuydirish (ffmpeg, apparat kodlash: NVENC/QSV/AMF) — asl matn,
  ikki qator, yoki faqat tarjima
- YouTube/Instagram va boshqa saytlardan video yuklash (yt-dlp)
- Chrome kengaytmasi (`chrome-extension/`) — sahifadagi video oqim havolasini topib beradi

## Tuzilma

- `desktop_processor.py` — kirish nuqtasi (PyInstaller bilan `.exe`ga qotiriladi)
- `subtitr/` — backend kodi, qatlamlar bo'yicha. Bog'liqlik faqat yuqoridan
  pastga ketadi (`core` hech kimga bog'liq emas) — halqa yo'q:

  | modul | mas'uliyati |
  |---|---|
  | `core` | yo'llar, konstantalar, dataklasslar, matn yordamchilari |
  | `media` | video/audio, yuklab olish, subtitr fayllari, ffprobe |
  | `clean` | soxta matnni tozalash, bo'laklarni moslash |
  | `cache` | transkripsiya keshi va imzosi |
  | `transcribe` | Groq Whisper, lokal model, yutilgan nutqni tiklash |
  | `translate` | AI provayderlar, glossariy, so'z ro'yxati |
  | `vocab` | lug'at: chastota, lemma, yordamchi so'zlar |
  | `subtitles` | ASS yasash va videoga kuydirish |
  | `documents` | TXT/DOCX, o'qish uchun PDF, Yordamchi sayti uchun MD |
  | `pipeline` | bosqichlarni biriktiruvchi oqim |
  | `cli` | buyruq qatori |

  Diqqat qilinadigan joylar:
  - `transcribe.swallowed_gap_ranges()` — transkripsiya butunlay o'tkazib
    yuborgan parchalarni topadi (lokal VAD bilan tekshirib, qayta o'qitadi)
  - `documents.build_reading_blocks()` — subtitr bo'laklaridan o'qiladigan
    abzatslar (tushib qolgan gap nuqtalarini tiklaydi)
  - `documents.write_pdf_reading()` — A4 o'qish maketi (plain/parallel/split)
  - `documents.build_sentence_pairs()` + `write_md_reading()` — Yordamchi
    saytining "O'qish" formati (`:: tarjima`, `{so'z|tarjima}`)
- `tests/` — regressiya testlari (yangi bog'liqliksiz):
  `.venv/bin/python -m unittest discover -s tests`
- `subtitr_app/` — Flutter desktop GUI (Linux, Windows, macOS)
- `chrome-extension/` — "Subtitr Grabber" Chrome kengaytmasi
- `linux/`, `windows/`, `macos/` — har bir platforma uchun yig'ish va
  o'rnatish skriptlari hamda qo'llanma. **Kod umumiy** — platformalar
  bo'yicha nusxalanmaydi, faqat yig'ish tartibi farq qiladi.
- `ISHLATISH_LINUX.txt`, `ISHLATISH_DESKTOP.txt` — foydalanuvchi qo'llanmalari
  (ilova bilan birga yuboriladi)

## Talablar (qisqacha)

| | |
|---|---|
| Flutter | 3.27+ |
| Python | 3.10+ |
| ffmpeg | Linux/macOS — tizimdan; Windows — `tools/` ga qo'lda |

Testlar (yangi bog'liqliksiz, standart `unittest`):

```bash
.venv/bin/python -m unittest discover -s tests   # 56 ta
cd subtitr_app && flutter test                   # 10 ta
```

## Eslatma

Bu papkada faqat manba kod bor. Katta binary fayllar (`ffmpeg.exe`, `ffprobe.exe`, `yt-dlp.exe`,
build/dist chiqishlari, o'rnatuvchi) reponing hajmini shishirmasligi uchun qo'shilmagan — build
qilishdan oldin ularni `tools/` papkasiga qo'lda qo'shish kerak. API kalitlar (`.env`) hech qachon
repoga qo'shilmaydi — faqat bo'sh namuna `.env.example` bor.
