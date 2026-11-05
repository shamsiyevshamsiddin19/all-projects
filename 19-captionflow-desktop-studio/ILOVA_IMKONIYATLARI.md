# CaptionFlow Desktop Studio (Subtitr Desktop)
## Dasturning Toʻliq Imkoniyatlari, Arxitekturasi va Barcha Rejimlari Qoʻllanmasi

> **CaptionFlow Desktop Studio** — xorijiy videolarni sunʼiy intellekt yordamida oʻzbek (yoki boshqa) tiliga professional tarjima qilish, subtitr yaratish, video kadriga kuydirish (hardsub), koʻp tilli CC treklari qoʻshish (softsub) hamda toza fon musiqasini saqlagan holda **kino darajasidagi AI dublyaj** qilishga moʻljallangan toʻliq siklli desktop studiyadir.

---

## 1. Texnologik Arxitektura

| Qatlam | Texnologiyalar | Vazifasi |
|---|---|---|
| **Frontend (UI)** | **Flutter Desktop (Linux x64)** | Material 3 zamonaviy Dark Cinema dizayn, video pleyer, real-vaqtli progress paneli va tahrirlagich |
| **Backend (Core)** | **Python 3.12 (JSON-RPC)** | Multi-threaded media pipeline, avtomatik kesh, audio/video tahlil, AI orkestratsiyasi |
| **Media Dvigateli** | **FFmpeg 6.1 + PyAV** | VA-API / NVENC apparat tezlatgichlari, Rubberband pitch-shifting, Mid-Side stereotools, Sidechain Compressor |
| **Transkripsiya** | **Groq Whisper Large v3 + Faster-Whisper** | Bulutda bir necha soniyada yoki offline CTranslate2 orqali 99% aniqlikdagi nutqni matnga aylantirish |
| **Tarjima va Dublyaj** | **Claude, GPT-4o, Gemini 2.5, Llama 3.3** | Kinematografik kontekstli tarjima, ismlar glossariysi, boʻgʻin va vaqtga moslashgan dialoglar |
| **AI Vokal Izolyatsiyasi** | **Demucs HTDemucs (PyTorch CPU)** | Musiqa va ovoz effektlarini 100% ajratib olib, original xorijiy nutqni batamom tozalash |
| **Ovoz Sintezi (TTS)** | **Microsoft Edge TTS Neural** | Sardor, Madina va 10 dan ortiq tildagi tabiiy inson ovozlari |

---

## 2. Kirish Manbalari (Input)

1. **Lokal Video Fayllar:**
   - Qoʻllab-quvvatlanadigan formatlar: `MP4`, `MKV`, `AVI`, `MOV`, `WebM`, `FLV`, `TS`.
   - Qulaylik: Fayllarni sudrab tashlash (**Drag-and-Drop**) yoki tizim fayl menejeridan tanlash.
2. **Internet Havolalari (URL):**
   - **YouTube** (Oddiy videolar, Shorts, uzun podkastlar, pleylistlar).
   - **Instagram** (Reels va post videolar).
   - **TikTok** (Suv belgisisiz toza videolar).
   - **Toʻgʻridan-toʻgʻri veb havolalar** (Har qanday veb sahifadagi MP4/HLS oqimlari).
   - Avtomatik yangilanuvchi `yt-dlp` dvigateli orqali maksimal sifatda (1080p, 4K) yuklab olish.
   - Tanlov: *"Faqat yuklash"* yoki *"Yuklab olish + AI qayta ishlash"*.

---

## 3. Asosiy Ishlash Rejimlari

Dastur 3 ta katta yoʻnalish va hujjatlar eksportini oʻz ichiga oladi:

```
                          ┌─ 1. Kuydirilgan Subtitr (Hardsub: dual_vocab, dual, original, translated)
                          │
[Video / URL Havola] ────┼─ 2. Yumshoq Subtitr (Softsub: 2 trek, dual CC, translated CC, original CC)
                          │
                          ├─ 3. Professional AI Dublyaj (Kino Avto, Sardor, Madina + Demucs BGM)
                          │
                          └─ 4. Hujjatlar va Matn (SRT, Transcript, Reading PDF/DOCX, Vocabulary)
```

---

### A. Kuydirilgan Subtitr (Hardsub — Kadrga Muhrlash)
Subtitr toʻgʻridan-toʻgʻri video tasviriga chiroyli shrift va soya bilan yoziladi. Har qanday televizor, telefon yoki eski pleyerda hech qanday sozlamasiz koʻrinadi:

1. **`dual_vocab` (Kino & Taʼlim — Dasturning eng kuchli rejimi):**
   - Ekranning pastida ikki qatorli subtitr: yuqori qatorda inglizcha asl matn, pastida oʻzbekcha tarjima.
   - Matndagi qiyin, yangi yoki nodir soʻzlar **sariq rangda yoritiladi**.
   - Ekranning yuqori qismida oʻsha soʻzning talaffuzi, soʻz turkumi, asosiy maʼnosi va kontekstdagi tarjimasi koʻrsatilgan **mini-lugʻat kartochkasi** chiqadi.
2. **`original_vocab`:**
   - Faqat asl chet tili subtitri + tepada mini-lugʻat kartochkalari (tilni chuqur oʻrganuvchilar uchun).
3. **`dual`:**
   - Ikki qatorli toza kino subtitri (Asl matn + Tarjima), lugʻat kartochkalarisiz.
4. **`original`:**
   - Faqat asl tildagi subtitr (chet tilidagi nutqni eshitib tushunishni mashq qilish uchun).
5. **`translated`:**
   - Faqat oʻzbekcha tarjima subtitri.

---

### B. Yumshoq Subtitr (Softsub — CC Treklar, 0 Soniyada Tayyor)
Video kadri qayta render qilinmaydi (`-c:v copy`), shuning uchun video sifati 100% oʻzgarishsiz qoladi va ishlov berish **1–2 soniyada** tugaydi. Tomoshabin subtitrni pleyer menyusidan yoqishi yoki oʻchirib qoʻyishi mumkin:

1. **`softsub` (2 ta alohida trek — Tavsiya):**
   - 1-trek: Asl til subtitri (`eng`)
   - 2-trek: Oʻzbekcha tarjima subtitri (`uzb`)
   - Tomoshabin xohlagan tilini pleyerda almashtirib tomosha qiladi.
2. **`softsub_dual` (Ikki qatorli yagona trek):**
   - Bitta trek yoqilganda ham asl til, ham tarjima birgalikda ekranda chiqadi.
3. **`softsub_translated` (Faqat tarjima):**
   - Yagona oʻzbekcha CC yoʻlakchasi.
4. **`softsub_original` (Faqat asl matn):**
   - Yagona xorijiy til CC yoʻlakchasi.

---

### C. Professional AI Dublyaj (Cinema Studio Grade)
Oddiy robot ovozlaridan tubdan farq qiluvchi kino darajasidagi audio arxitektura:

1. **AI Vokal Izolyatsiyasi (Demucs HTDemucs):**
   - Videodagi audio ikki yoʻlakka ajratiladi:
     - `no_vocals.wav` — fon musiqasi, mashina tovushlari, portlashlar, qarsaklar va effektlar **100% toza saqlanadi**.
     - `vocals.wav` — asl inglizcha aktyor ovozi butunlay oʻchirib tashlanadi. Orqa fonda begona gʻoʻngʻillagan xorijiy nutq qolmaydi!
2. **Boʻgʻin va Vaqtga Moslashgan Tarjima (Cinematic Pacing):**
   - Tarjima AI ga har bir gapning millisekundigacha boʻlgan davomiyligi (`max_duration_sec`) beriladi.
   - AI kitobiy gaplarni emas, dublyaj qoidasi boʻyicha **ogʻzaki, qisqa va jarangdor** qilib oʻgiradi. Natijada gaplar 2x multfilmdek tezlashib ketmaydi.
3. **Kino Studiyasi Audio Mastering Zanjiri:**
   - TTS ovozi xom va quruq chiqmasligi uchun professional filtrlardan oʻtkaziladi:
     - **`highpass=f=80`**: Mikrofondagi past chastotali gupillash va shovqinlarni kesadi.
     - **`equalizer=f=250`**: Koʻkrak qafasi rezonansi va iliqlik bagʻishlaydi.
     - **`equalizer=f=3400` (De-esser)**: "s", "sh", "ch" tovushlaridagi noxush quloqni teshuvchi xirillashlarni tozalaydi.
     - **`acompressor`**: Sokin va baland jumlalarni kino standartiga tekislaydi.
     - **`alimiter`**: Raqamli qirqilish (clipping) va ovoz xirillashining oldini oladi.
4. **Multi-Voice (Koʻp Ovozli Aktyorlik):**
   - **`Kino (Avto)`**: Segmentdagi asl ovoz chastotasi ($F_0$) tahlil qilinadi. Erkak qahramon gapirsa — *Sardor*, ayol qahramon gapirsa — *Madina* avtomatik tanlanadi.
   - Qoʻlda tanlash: Istalgan vaqtda faqat *Sardor (Erkak)* yoki faqat *Madina (Ayol)* rejimiga oʻtish mumkin.
5. **Dinamik Sidechain Mikshing (Ducking):**
   - Dublyaj gapirayotgan paytda toza fon musiqasi mayin 3–4 dB pasayadi, gap tugashi bilan musiqa yana 100% jarangdorlikka qaytadi.
   - Sozlash imkoniyatlari: `18%` (Kino standarti), `10%` (Past fon), `0%` (Faqat dublyaj), `30%` (Baland fon).
6. **Multi-Track Audio Chiqishi:**
   - Tayyorlangan videoda **2 ta mustaqil audio trek** boʻladi:
     - 1-trek: Asl ovoz (Original)
     - 2-trek: Oʻzbekcha AI Dublyaj (Standart faol)

---

### D. Hujjatlar va Matnli Eksportlar
1. **`srt`**: Universal subtitr fayli (barcha pleyerlar va YouTube uchun).
2. **`transcript`**: Vaqtlari koʻrsatilgan toʻliq ikki tilli dialog transkripti (`.txt`).
3. **`reading`**: Videoni kitobdek oʻqish uchun tayyorlangan formatli chiroyli kitobcha (`.pdf` / `.docx`).
4. **`vocabulary`**: Videodagi barcha yangi soʻzlar roʻyxati, ularning maʼnosi, transkripsiyasi va videodagi kontekst misollari (`.txt` / `.json`).

---

## 4. Interaktiv Subtitr Muharriri (Translation Editor)

Videoni render qilishdan oldin uni koʻrib chiqish va tahrirlash imkoniyati:
- **Noaniq satrlarni aniqlash:** Whisper AI ishonchlilik bali (Confidence score) past boʻlgan satrlarni sariq va qizil rang bilan belgilab beradi.
- **Matn va Vaqtni Tahrirlash:** Har bir qatordagi asl matnni ham, tarjimani ham, gapning boshlanish (`start`) va tugash (`end`) vaqtini ham toʻgʻridan-toʻgʻri oʻzgartirish mumkin.
- **Bitta Tugma bilan Qayta Tarjima:** Agar biror satr tarjimasi yoqmasa, ustidagi tugmani bosish orqali faqat shu satrni AI yordamida qaytadan oʻgirish mumkin.
- **Kesh bilan sinxronizatsiya:** Muharrirda kiritilgan har bir oʻzgarish diskdagi keshga bir zumda yoziladi va yakuniy render aynan tahrirlangan variant asosida chiqadi.

---

## 5. Tashqi Koʻrinish va Subtitr Stilizatsiyasi

Kuydirilgan (Hardsub) va Yumshoq (Softsub) rejimlar uchun maxsus vizual sozlamalar:
- **Shrift hajmi (Font Scale):** `0.8x`, `0.9x`, `1.0x` (Tavsiya), `1.15x`, `1.3x`.
- **Ekrandagi oʻrni:** Pastda (Bottom), Oʻrtada (Center), Tepada (Top).
- **Tarjima rangi:**
  -  Neon Yashil (`#39FF14`) — qorongʻu va yorugʻ sahnalarda eng yaxshi oʻqiladi.
  -  Oltin Sariq (`#FFD700`) — kino va hujjatli filmlar standarti.
  - ⚪ Sof Oq (`#FFFFFF`) — klassik minimalizm.
  - 🔵 Moviy Neon (`#00D2FF`) — zamonaviy texnologik uslub.
  - 🔴 Pushti Neon (`#FF3366`) — dinamik blog uslubi.
- **Asl matn uslubi:**
  - `Plain` — oddiy aniq matn.
  - `Dimmed` — tarjimadan chalgʻitmaslik uchun biroz shaffof qilingan.
  - `Brackets` — qavs ichida.
- **Video Sifati:** `720p`, `1080p Full HD`, `1440p 2K`, `2160p 4K UHD`.
- **AI Upscaling:** Kichik oʻlchamdagi videolarni sifatini yoʻqotmasdan yuqori piksellarga koʻtarish.

---

## 6. Xavfsizlik, Kesh va Ishonchlilik

1. **Avtomatik Kesh Tizimi (Checkpoint Restoration):**
   - Transkripsiya, tarjima, lugʻat va dublyajning har bir qadami `~/.cache/SubtitrDesktop` papkasida JSON holida saqlanadi.
   - Agar internet uzilsa yoki jarayon toʻxtatilsa, dastur qayta yoqilganda avvalgi tayyor qismlarni noldan boshlamaydi — vaqt va API soʻrovlari tejaladi.
2. **Maxfiy Kalitlar Xavfsizligi:**
   - OpenAI, Anthropic, Gemini, Groq kalitlari operatsion tizimning maxfiy xotirasida (`shared_preferences` / Linux secret service) saqlanadi.
   - Kalitlar hech qachon ochiq muhit oʻzgaruvchisi (env) orqali boshqa dasturlarga sizib chiqmaydi.
3. **Xatoliklarga Chidamlilik:**
   - Biror AI provayderi (masalan Groq) vaqtincha limitga tushsa, dastur avtomatik ravishda boshqa kalitga (Gemini, Claude, OpenAI) yoki offline lugʻatga oʻtadi.
   - Demucs ishlamasa, dastur toʻxtab qolmaydi — FFmpeg Mid-Side filtri orqali baribir toza ovoz chiqarib beradi.

---

## 7. Xulosa

**CaptionFlow Desktop Studio** — shaxsiy foydalanish uchun yaratilgan, biroq imkoniyatlari va arxitekturasi boʻyicha eng qimmat pullik xalqaro servislar (Descript, ElevenLabs, CapCut) darajasida mustahkam, offline va xavfsiz ishlaydigan mukammal desktop vositadir.

