# Subtitr Desktop

Video subtitr/tarjima qiluvchi desktop ilova (Flutter GUI + Python backend). Windows va Linux.

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
- `subtitr_app/` — Flutter desktop GUI (Windows + Linux)
- `chrome-extension/` — "Subtitr Grabber" Chrome kengaytmasi
- `build_release.ps1` — Windows release (`.exe` + installer + zip) yig'ish skripti
- `installer.iss` — Inno Setup skripti (Windows)
- `build_release.sh` — Linux release (`dist/SubtitrDesktop` + tar.gz) yig'ish skripti
- `install.sh` — Linux o'rnatuvchi (menyu yorlig'i bilan, sudo shart emas)
- `ISHLATISH_LINUX.txt` — Linux uchun qo'llanma

## Eslatma

Bu papkada faqat manba kod bor. Katta binary fayllar (`ffmpeg.exe`, `ffprobe.exe`, `yt-dlp.exe`,
build/dist chiqishlari, o'rnatuvchi) reponing hajmini shishirmasligi uchun qo'shilmagan — build
qilishdan oldin ularni `tools/` papkasiga qo'lda qo'shish kerak. API kalitlar (`.env`) hech qachon
repoga qo'shilmaydi — faqat bo'sh namuna `.env.example` bor.
