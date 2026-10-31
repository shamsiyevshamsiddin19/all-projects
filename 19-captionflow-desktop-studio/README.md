# Subtitr Desktop

> Kod ikki joyda turadi: [`all-projects`](https://github.com/shamsiyevshamsiddin19/all-projects)
> monorepo'sida (`19-captionflow-desktop-studio/`) va shu alohida
> [`subtitle-desktop`](https://github.com/shamsiyevshamsiddin19/subtitle-desktop)
> repo'sida. Monorepo asosiy manba; bu repo `git subtree` bilan yangilanadi.

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
  - `translate.try_providers()` — AI chaqiruvlarining yagona qayta urinish
    joyi. Xato turkumlanadi (`core.error_kind()`): yaroqsiz kalit
    ("auth") provayderni butun ish davomiga o'chiradi, yaroqsiz so'rov
    ("bad_request") faqat shu chaqiruvda chetlab o'tiladi, qolgani
    (429/5xx) eksponensial kutish bilan qayta urinadi. Sozlash:
    `AI_MAX_ATTEMPTS` (3), `AI_RETRY_BACKOFF_SEC` (6),
    `AI_RETRY_MAX_SEC` (30)
  - `translate.translate_segments()` — to'plamlar PARALLEL yuboriladi.
    Kontekst manba matnidan olinadi (oldingi tarjimadan emas), shuning
    uchun to'plamlar bir-biriga bog'liq emas. Natija asl tartibda
    yig'iladi, kesh esa har to'plamdan keyin saqlanadi. Sozlash:
    `TRANSLATE_WORKERS` (3; `1` — eski ketma-ket xatti-harakat),
    `TRANSLATE_BATCH` (50)
- `desktop_requirements.txt` — Python paketlar ro'yxati. **Yagona manba**:
  `linux/build.sh` ham, ilovadagi "Paketlarni o'rnatish" tugmasi ham
  (`pipeline.required_packages()`) aynan shu fayldan o'qiydi.
- `tests/` — regressiya testlari (yangi bog'liqliksiz):
  `.venv/bin/python -m unittest discover -s tests`
- `subtitr_app/` — Flutter desktop GUI (Linux, Windows, macOS)
- `chrome-extension/` — "Subtitr Grabber" Chrome kengaytmasi
- `linux/`, `windows/`, `macos/` — har bir platforma uchun yig'ish va
  o'rnatish skriptlari hamda qo'llanma. **Kod umumiy** — platformalar
  bo'yicha nusxalanmaydi, faqat yig'ish tartibi farq qiladi.
- `ISHLATISH_LINUX.txt`, `ISHLATISH_DESKTOP.txt` — foydalanuvchi qo'llanmalari
  (ilova bilan birga yuboriladi)

## Xato hisoboti (log)

Har bir ish `logs/subtitr-YYYY-MM-DD.log` ga yoziladi (kesh papkasida;
**Sozlamalar → Xato hisoboti → Loglarni ochish**). Ekranda xatoning faqat
bitta qatori ko'rinadi, to'liq izi (traceback) esa shu faylda bo'ladi.

- API kalitlar logga **tushmaydi** — `core.redact()` ularni maskalaydi.
- Loglar 14 kundan keyin o'zi o'chadi, fayl 2 MB dan oshsa aylantiriladi.
- `SUBTITR_DEBUG=1` — batafsil (ishga tushgan buyruqlar ham).
- `SUBTITR_NO_LOG=1` — butunlay o'chiradi.

## To'xtatish (Bekor qilish)

"Bekor qilish" bosilganda ilova avval **SIGTERM** yuboradi: protsessor uni
`KeyboardInterrupt` ga aylantiradi, shuning uchun hamma `finally` bloki
ishlaydi — vaqtinchalik papka (uzun kinoda ~1 GB WAV) va yarim yozilgan
`.mp4` o'chadi. Faqat 4 soniyadan keyin ham tirik bo'lsa SIGKILL keladi.

Signal butun **process guruhiga** ketadi, shuning uchun `ffmpeg` va `yt-dlp`
ham to'xtaydi. Protsessor o'zini alohida guruhga faqat
`SUBTITR_OWN_PROCESS_GROUP=1` berilganda qo'yadi — buni Flutter ilovasi
qo'yadi; buyruq qatorida u yoqilmaydi, aks holda terminaldagi Ctrl+C
jarayonga yetib bormay qoladi.

Tugamay qolgan ishlardan qolgan papkalar har ishga tushishda tozalanadi
(12 soatdan eskilari — `core.clean_orphan_tmp()`).

## Disk keshi

Yuklab olingan videolar, ishchi fayllar, tayyor transkripsiyalar va Whisper
modellari ko'rinmas papkada (`SUBTITR_DATA_DIR`, Linux'da
`~/.cache/SubtitrDesktop`) saqlanadi.

Yuklamalar keshi **5 GB** dan oshsa, eng eski videolar o'zi o'chadi
(`SUBTITR_DL_CACHE_GB` bilan sozlanadi; `0` — cheklamaslik). Hajmni ko'rish
va qo'lda tozalash ilovadagi **Sozlamalar → Disk keshi** bo'limida, yoki
buyruq qatoridan:

```bash
.venv/bin/python desktop_processor.py cache-info
```

```bash
.venv/bin/python desktop_processor.py clear-cache --what downloads
```

`--what`: `downloads` (sukut), `work`, `models`, `transcripts`, `all`.
`all` ichiga `transcripts` **kirmaydi** — tayyor tarjimani o'chirish AI'ga
qaytadan pul turadi, shuning uchun uni faqat atayin so'raganda o'chiradi.

## Talablar (qisqacha)

| | |
|---|---|
| Flutter | 3.27+ |
| Python | 3.10+ |
| ffmpeg | Linux/macOS — tizimdan; Windows — `tools/` ga qo'lda |

Testlar (yangi bog'liqliksiz, standart `unittest`):

```bash
.venv/bin/python -m unittest discover -s tests   # 97 ta
cd subtitr_app && flutter test                   # 16 ta
```

## Eslatma

Bu papkada faqat manba kod bor. Katta binary fayllar (`ffmpeg.exe`, `ffprobe.exe`, `yt-dlp.exe`,
build/dist chiqishlari, o'rnatuvchi) reponing hajmini shishirmasligi uchun qo'shilmagan — build
qilishdan oldin ularni `tools/` papkasiga qo'lda qo'shish kerak. API kalitlar (`.env`) hech qachon
repoga qo'shilmaydi — faqat bo'sh namuna `.env.example` bor.
