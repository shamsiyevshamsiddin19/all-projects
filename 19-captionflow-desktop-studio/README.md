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
- Tahrirlashda jonli ko'rish: qatorni bosganda video o'sha joydan
  ovozi bilan o'ynaydi, subtitr esa aynan kuydiriladiganidek chiqadi
  (mpv ASS ni libass bilan chizadi — ffmpeg bilan bir xil kutubxona).
  libmpv bo'lmasa o'rniga kadr ko'rsatiladi
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
  - `vocab.build_vocabulary()` + `translate.translate_word_list()` —
    lug'at tarjimasiga so'z uchragan GAP ham yuboriladi. Kontekstsiz ko'p
    ma'noli so'z tasodifiy ma'noda tarjima bo'ladi; Groq bilan o'lchangan:
    `bank` → "bank" bo'lsa, kontekst bilan "qirg'oq"; `right` → "to'g'ri"
    bo'lsa, "o'ng"; `light` → "yorug'lik" bo'lsa, "yengil".
    Kesh `vocab_v3_*` — versiya oshirilmasa eski (kontekstsiz) lug'at
    qaytarilaverardi
  - `pipeline.preview_frame()` — tahrirlash oynasida qatorni bosganda
    o'sha soniyadan BITTA kadr chiqadi, ustida haqiqiy subtitr bilan.
    ASS `_render_data()` orqali renderning aynan o'zi bilan yasaladi,
    shuning uchun shrift, sariq quti, joylashuv va lug'at kartochkasi
    yakuniy videodagidek. `-copyts` SHART: usiz `-ss` vaqtlarni 0 ga
    qaytaradi va `ass` filtri subtitrni topa olmaydi
  - `core.dialogue_parts()` — "- Salom. - Salom." ko'rinishidagi dialog
    har so'zlovchi O'Z QATORIDAN boshlanadi. Shart: matn chiziqcha bilan
    boshlanishi va kamida ikkitasi bo'lishi — shunda "shunday - deb
    aytdi" yoki "o'z-o'zidan" xato aniqlanmaydi. **Haqiqiy diarization
    (kim gapirayotganini audiodan aniqlash) YO'Q** — u `pyannote`/`torch`
    (~2 GB) talab qiladi; bu faqat manbada mavjud belgilarni to'g'ri
    ko'rsatadi
  - `Segment.confidence` — model bo'lakka qanchalik ishonadi (0..1) yoki
    `None` (tayyor `.srt` da ishonch yo'q). Whisper `avg_logprob` dan
    `exp()` bilan olinadi. Ilgari bu qiymat faqat filtr uchun ishlatilib
    tashlanardi, Groq yo'lida esa umuman o'qilmas edi. Endi kesh va
    sessiya orqali tahrirlash oynasiga yetib boradi va u shubhali
    qatorlarni "tekshiring" deb belgilaydi (`SUBTITR_LOW_CONFIDENCE`,
    0.5). Birlashtirilgan bo'lak ENG PAST ishonchni oladi
  - `core.OFFLINE_WORDS` / `OFFLINE_PHRASES` — kalitsiz rejimdagi zaxira
    lug'at, **(manba, nishon)** juftligi bo'yicha kalitlangan:
    ingliz→o'zbek 98 so'z, rus→o'zbek 174 so'z. Juftlik yo'q bo'lsa bo'sh
    satr qaytadi — ilgari nishon til hisobga olinmas va rus tiliga
    so'ralganda ham o'zbekcha qaytarardi
  - `subtitles.write_ass()` lug'at kartochkalari — davomiylik
    (`SUBTITR_VOCAB_DURATION`, 4.0) minimal oraliqni ham belgilaydi:
    4.0 da sekundda ~3.2 kartochka sig'adi, 3.0 da ~4.2. Tez nutqda
    (4+ so'z/sek) sig'magan so'zlar bor bo'lsa, ularning soni aytiladi —
    ilgari jimgina tashlanardi
  - `clean.enforce_reading_speed()` — subtitr vaqtlari. Ustma-ust
    bo'laklar tuzatiladi (foydalanuvchi qo'ygan `.srt` ko'pincha ustma-ust
    bo'ladi va u yuqoridagi bosqichlardan o'tmaydi), ketma-ket bo'laklar
    orasiga tanaffus qo'yiladi. Qisqartirish o'qish vaqtidan past
    tushmaydi — matnni o'qib bo'lish tanaffus me'yoridan muhimroq.
    Sozlash: `SUB_MAX_CPS` (20), `SUB_MIN_DUR` (1.0),
    `SUB_MIN_GAP` (0.08), `SUB_MIN_VISIBLE` (0.3)
  - `translate.build_glossary()` — film bo'ylab ism izchilligi. Ism
    mezoni — token GAP O'RTASIDA bosh harf bilan kelishi (gap boshida
    har qanday so'z bosh harfli). Kelishik shakllari AI qaytargan
    lemma bo'yicha guruhlanadi, shuning uchun "Иван" ham, "Ивану" ham
    BITTA nishon shaklga ishora qiladi. Olmosh/fe'l/sifat `pos` bo'yicha
    chiqarib tashlanadi — ularni majburlash tarjimani buzadi
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
  - `transcribe.transcribe_with_groq()` — Groq hajm chegarasidan katta
    audio 20 daqiqalik bo'laklarga bo'linadi va ular ham parallel
    yuboriladi. Natija tugash tartibidan emas, BO'LAK INDEKSI bo'yicha
    yig'iladi (aks holda subtitr vaqtlari aralashadi). Sozlash:
    `GROQ_AUDIO_WORKERS` (2 — audio yuklash matndan og'ir),
    `GROQ_CHUNK_SECONDS` (1200)
  - `subtitles.audio_args_for()` — audio MP4 ga mos bo'lsa (aac, mp3,
    ac3, eac3, alac) qayta kodlanmaydi, `-c:a copy` bilan o'tadi.
    O'lchangan: 10 daqiqalik klipda 40.1s -> 15.1s. Yuklashda ham m4a
    (AAC) afzal ko'riladi, shuning uchun bu yo'l ko'pincha ishlaydi.
    Sozlash: `SUB_AUDIO` (auto|copy|aac), `SUB_AUDIO_BITRATE` (128k)
  - `pipeline.modes_for()` — "Hammasi" rejimi BITTA video beradi
    (`dual_vocab`) va qolgan hamma hujjatni. Render eng sekin bosqich,
    to'siq esa GPU kodlagichi: u ikki oqimni tezroq qila olmaydi
    (o'lchangan — bitta chiqish 6.1s, ikkitasi 12.2s; bir o'tishda ikki
    chiqish 11.3s, parallel ikki jarayon 10.7s, ya'ni 7-12%)
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

## API kalitlar qayerda saqlanadi

Kalitlar `api_keys.json` da, ilovaning ma'lumot papkasida, **faqat egasi
o'qiydigan** ruxsat bilan (`0600`). Model nomlari sir emas — ular
`SharedPreferences` da qoladi.

Ilgari kalitlar ham `SharedPreferences` da edi, uning fayli esa
`-rw-rw-r--` bilan yaratiladi: **kompyuterdagi har qanday foydalanuvchi
va jarayon** pullik API kalitni diskdan o'qiy olardi, zaxira va sinxron
dasturlar ham uni olib ketardi. Yangilangandan keyin birinchi ochilishda
eski kalitlar avtomatik ko'chiriladi va eskisidan o'chiriladi.

Bu **shifrlash emas**. Keyingi qadam — tizim kalit omboriga o'tish
(`flutter_secure_storage` → libsecret), lekin u Linux'da yana bitta
tizim sharti qo'shadi. `0600` esa bog'liqliksiz va ish stoli uchun
haqiqiy xavfni — boshqa hisoblar, tasodifiy zaxira, ulashib yuborilgan
sozlama papkasi — yopadi.

## Xato hisoboti (log)

Har bir ish `logs/subtitr-YYYY-MM-DD.log` ga yoziladi (kesh papkasida;
**Sozlamalar → Xato hisoboti → Loglarni ochish**). Ekranda xatoning faqat
bitta qatori ko'rinadi, to'liq izi (traceback) esa shu faylda bo'ladi.

- API kalitlar logga **tushmaydi** — `core.redact()` ularni maskalaydi.
- Loglar 14 kundan keyin o'zi o'chadi, fayl 2 MB dan oshsa aylantiriladi.
- `SUBTITR_DEBUG=1` — batafsil (ishga tushgan buyruqlar ham).
- `SUBTITR_NO_LOG=1` — butunlay o'chiradi.

## Apparat kodlash/dekodlash

Subtitr kuydirishda **kodlash** apparatda ketadi (NVENC / QSV / AMF /
VAAPI — `pick_video_encoder()` ishlaydiganini o'zi topadi, `SUB_ENCODER`
bilan majburlash mumkin).

**Dekodlash esa atayin CPU da.** Bu kompyuterda (AMD Lucienne iGPU)
o'lchangan, 60 soniyalik 1080p:

| manba | CPU dekod | GPU dekod (`-hwaccel vaapi`) |
|---|---|---|
| VP9 | 6.0–7.1 s | 13.2–13.4 s — **2× sekin** |
| AV1 | 11.7 s | **tushadi** (kod 69, AV1 qo'llanmaydi) |

Sababi: `ass` filtri CPU xotirasidagi kadrni talab qiladi, shuning uchun
har kadr GPU → CPU → GPU bo'ylab yuradi; umumiy xotirali iGPU da bu
ko'chirish dekodlashdan tejalgan vaqtdan qimmat. Ikkinchisi — bu iGPU
AV1 ni dekodlay olmaydi va ffmpeg CPU ga **qaytmaydi**, xato bilan
to'xtaydi (YouTube esa ko'pincha AV1 beradi).

Alohida videokartada foydali bo'lishi mumkin: `SUB_HWACCEL=vaapi`
(yoki `cuda`, `qsv`). **Yoqishdan oldin o'lchang.**

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
| libmpv | **Linux'da yig'ish uchun shart**: `sudo apt install libmpv-dev mpv`. Windows/macOS'da paket ichida keladi |

`libmpv` faqat tahrirlash oynasidagi **jonli pleyer** uchun kerak. U
bo'lmasa ilova ishlaydi, lekin pleyer o'rniga kadr ko'rsatiladi (kadr
faqat ffmpeg talab qiladi). Yig'ish paytida esa `libmpv-dev` shart —
`linux/build.sh` buni oldindan tekshiradi.

Testlar (yangi bog'liqliksiz, standart `unittest`):

```bash
.venv/bin/python -m unittest discover -s tests   # 171 ta
cd subtitr_app && flutter test                   # 31 ta
```

## Eslatma

Bu papkada faqat manba kod bor. Katta binary fayllar (`ffmpeg.exe`, `ffprobe.exe`, `yt-dlp.exe`,
build/dist chiqishlari, o'rnatuvchi) reponing hajmini shishirmasligi uchun qo'shilmagan — build
qilishdan oldin ularni `tools/` papkasiga qo'lda qo'shish kerak. API kalitlar (`.env`) hech qachon
repoga qo'shilmaydi — faqat bo'sh namuna `.env.example` bor.
