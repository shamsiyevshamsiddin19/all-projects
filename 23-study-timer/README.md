# ⏱ Zenith Study Timer

Minimalist orqaga sanash, pomodoro va fokus studiyasi. OLED ekranlar uchun toza qora fon,
nozik tipografiya va chalg'itmaydigan interfeys.

```
00      25      00
SOAT  DAQIQA  SONIYA
```

---

## ✨ Imkoniyatlar

### Beshta ish rejimi
| Rejim | Tavsif |
| :--- | :--- |
| 🎯 **Maqsadli sana** | Imtihon, taqdimot yoki yangi yilgacha kun/soat/daqiqa/soniya. Presetlar: ertaga, hafta oxiri, oy oxiri, +7 kun, +30 kun, yangi yil. |
| ⏳ **Davomiylik** | Kun/soat/daqiqa/soniya bo'yicha taymer. Presetlar: 5, 15, 25, 30, 45 daqiqa, 1 soat, 2 soat, 1 kun. `+1 / +5 / +15 / +1 soat / −5 daqiqa` tugmalari. |
| 🍅 **Pomodoro** | Dars, qisqa va uzun tanaffus — **davomiyliklari sozlanadi**. Sikl hisoblagichi (nolga qaytariladi) va "keyingi bosqichni avtomatik boshlash" tanlovi. |
| ⏱ **Sekundomer** | Yuzinchi ulushlargacha, bosqich (lap) yozib borish bilan. |
| 🕒 **Soat** | Hozirgi vaqt (sanani ko'rsatish ixtiyoriy). |

### Vaqt aniqligi
Taymer `setInterval` sanog'iga emas, **haqiqiy timestamp'ga** tayanadi. Natijada:

* boshqa tabga o'tganda brauzer taymerni sekinlashtirsa ham vaqt **to'g'ri** qoladi;
* sahifa yangilansa yoki yopilib ochilsa, **yurib turgan taymer davom etadi**;
* siz yo'q bo'lgan paytda taymer tugagan bo'lsa, qaytganingizda shu haqda xabar beriladi.

### Eslatmalar va statistika
* Oraliq eslatma: har 10 / 15 / 20 / 30 / 45 daqiqada.
* Tugashdan 1 daqiqa oldin ogohlantirish.
* Tizim bildirishnomalari (ruxsat **faqat** siz sozlamani yoqqaningizda so'raladi).
* Statistika: umumiy fokus vaqti, seanslar soni, bugungi natija. Fokus vaqti **haqiqatda yurgan**
  vaqt bo'yicha hisoblanadi — pauzalar qo'shilmaydi.
* JSON eksport / import va statistikani tozalash tugmalari.

### Ovoz (Web Audio, tashqi fayllarsiz)
* Signallar: Zen Singing Bowl, mayin billur qo'ng'iroq, Digital Chime, billur gong, o'chiq.
* Orqa fon: mayin yomg'ir, binaural (4 Hz farq — faqat naushnikda seziladi, ta'siri ilmiy
  isbotlanmagan), kosmik drone.
* Fon tabdan qaytganda audio konteksti uyqudan chiqariladi — signal yo'qolmaydi.

### Ko'rinish va qulaylik
* 6 ta mavzu (Pitch Black, Deep Navy, Matrix Emerald, Amber Luxury, Cyber Violet, Aurora).
* 5 ta shrift uslubi.
* 🇺🇿 O'zbekcha / 🇬🇧 inglizcha interfeys.
* To'liq ekran, 90° burish, Zen rejim (3,5 soniyadan keyin kursor yashirinadi), WakeLock.
* PWA: telefonga o'rnatiladi, birinchi yuklanishdan keyin **oflayn** ishlaydi.
* Accessibility: klaviatura bilan to'liq boshqariladi, `aria-live` bilan vaqt e'lon qilinadi,
  fokus halqasi panel ichida ushlanadi, `prefers-reduced-motion` hurmat qilinadi.

---

## ⌨️ Klaviatura

| Tugma | Vazifasi |
| :--- | :--- |
| `Space` | Boshlash / Pauza |
| `S` | Sozlamalar oynasi |
| `F` | To'liq ekran |
| `P` | Panelni qadash (pin) |
| `R` | Qayta o'rnatish |
| `L` | Bosqich (lap) — sekundomerda |
| `Esc` | Panelni yopish |

---

## 🚀 Ishga tushirish

```bash
python3 app.py
```

`http://localhost:5050` ochiladi. Yoki qisqa yo'l:

```bash
./run.sh
```

Foydali bayroqlar:

```bash
python3 app.py --port 8080 --no-browser --quiet
python3 app.py --host 0.0.0.0        # faqat ataylab: tarmoqqa ochadi
```

> **Nega `index.html` ni to'g'ridan-to'g'ri ochmaslik kerak?**
> `file://` da ES modullar, service worker, bildirishnomalar va JSON ombori ishlamaydi.
> Shu sabab `run.sh` mahalliy serverni ishga tushiradi.

---

## 🔐 Ma'lumotlar va maxfiylik

* Sozlamalar, taymer holati va statistika **brauzeringizning** `localStorage`'ida saqlanadi.
* Server ishlayotgan bo'lsa, nusxasi `data/timer_data.json` ga ham yoziladi va keyingi
  ochilishda o'qiladi (yangiroq nusxa ustun keladi).
* `data/` papkasi `.gitignore` da — shaxsiy statistika repoga tushmaydi.
* Server standart holatda **faqat `127.0.0.1`** ga bog'lanadi, `/api/data` da CORS yo'q va
  cross-site so'rovlar rad etiladi.

---

## 🧪 Testlar

```bash
pip install -r requirements.txt
python3 test_all.py
```

Bu: backend xavfsizligi va API, HTML ↔ JS ↔ CSS ↔ i18n mosligi, a11y, PWA fayllari va
Node mantiq testlarini ishga tushiradi (testlar vaqtinchalik papkada ishlaydi, `data/` ga tegmaydi).

Faqat mantiq testlari:

```bash
npm run test:unit        # node --test "tests/*.test.mjs"
```

Ixtiyoriy qatlamlar (tashqi paket talab qiladi):

```bash
npm run setup:e2e        # jsdom + Playwright o'rnatadi
npm run test:e2e         # haqiqiy brauzerda E2E (server ishlab turishi kerak)
npm run lint             # ESLint
```

---

## 📂 Fayllar strukturasi

```text
23-study-timer/
├── index.html                 # Yagona sahifa (semantik + a11y atributlari)
├── manifest.webmanifest       # PWA manifesti
├── sw.js                      # Service worker (oflayn kesh, shriftlar keshi)
├── app.py                     # Mahalliy server + JSON ombori (xavfsizlik cheklovlari bilan)
├── run.sh                     # Serverni ishga tushiruvchi skript
├── test_all.py                # To'liq test to'plami (orkestrator)
├── css/
│   └── style.css              # Dizayn tizimi, mavzular, responsiv va reduced-motion
├── js/
│   ├── app.js                 # Kontroller: hammasini bog'laydi
│   ├── ui.js                  # DOM keshi, chizish, panel, toast, statistika
│   ├── storage.js             # Sxema validatsiyasi, migratsiya, debounce, server sync
│   ├── audio.js               # Web Audio sintezatori
│   ├── platform.js            # Fullscreen, WakeLock, orientatsiya, bildirishnomalar
│   ├── i18n.js                # uz / en tarjimalari
│   ├── format.js              # Vaqtni formatlash (sof funksiyalar)
│   ├── constants.js           # Barcha konstantalar (sehrli raqamlar yo'q)
│   └── engine/
│       ├── countdown.js       # Timestamp asosidagi sanash yadrosi
│       └── timer-engine.js    # Rejimlar, hodisalar, saqlash/tiklash
├── tests/
│   ├── engine.test.mjs        # Taymer mantig'i (xulq-atvor testlari)
│   ├── storage.test.mjs       # Saqlash va validatsiya
│   ├── format-i18n.test.mjs   # Formatlash va tarjimalar
│   ├── dom.test.mjs           # jsdom integratsiyasi (ixtiyoriy)
│   └── e2e.spec.mjs           # Playwright (ixtiyoriy)
├── tools/
│   ├── make_icons.py          # PWA ikonalarini yasaydi (faqat stdlib)
│   └── vendor-fonts.sh        # Shriftlarni loyihaga ko'chirish (to'liq oflayn uchun)
└── icons/                     # PWA ikonalari
```

---

## 🔤 Shriftlar haqida

Shriftlar Google Fonts'dan yuklanadi va service worker ularni birinchi yuklanishdan keyin
keshlaydi — shundan so'ng internetsiz ham tipografiya saqlanadi. Umuman tarmoqqa chiqmasligini
xohlasangiz:

```bash
./tools/vendor-fonts.sh
```

so'ng `index.html` dagi Google Fonts `<link>` larini `fonts/fonts.css` bilan almashtiring.

---

## 📄 Litsenziya

[MIT](LICENSE) © Shamsiddin Shamsiyev
