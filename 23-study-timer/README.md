# ⏱ Zenith Study Timer — Ultra Minimalist Countdown & Focus Studio

<p align="center">
  <b>05 &nbsp;&nbsp; 22 &nbsp;&nbsp; 05 &nbsp;&nbsp; 01</b><br>
  <i>DAYS &nbsp;&nbsp;&nbsp;&nbsp; HOURS &nbsp;&nbsp;&nbsp;&nbsp; MINUTES &nbsp;&nbsp;&nbsp;&nbsp; SECONDS</i>
</p>

Zamonaviy, o'ta nafis va chalg'itmaydigan (distraction-free) minimalist taymer va diqqatni jamlash (focus & study) veb-platformasi. Foydalanuvchi taqdim etgan dizayn andozasi asosida yaratilgan bo'lib, OLED ekranlar uchun toza qora (`#000000`) fon va o'ta nozik zamonaviy tipografiyadan iborat.

---

## ✨ Asosiy Imkoniyatlari

### 1. 🎛 Chap Chetki Interaktiv Sozlamalar Paneli (Slide-out Drawer)
- Kursorni ekranning chap chetiga olib borganingizda (edge-hover) shaffof glassmorphic sozlamalar paneli silliq ochiladi.
- Kursorni paneldan uzoqlashtirganda panel avtomatik tarzda yopilib, ekranda faqat toza taymer qoladi.
- **Qadash (Pin) imkoniyati:** `📌` tugmasi (yoki klaviaturadagi `P`) orqali panelni ekranda doimiy ochiq qoldirish mumkin.

### 2. 🎯 5 Xil Ish Rejimi
- **🎯 Maqsadli Sana (Target Date):** Muayyan kelajakdagi sana yoki voqeaga (masalan: Yangi Yil, Imtihon, Loyiha taqdimoti) aniq kun, soat, daqiqa va soniyalarda orqaga sanash.
  - Tezkor presetlar: Ertaga 00:00, Hafta oxiri, Oy oxiri, +7 kun, +30 kun, Yangi Yil 2027 va Asl Rasm ko'rinishi (5d 22h 5m 1s).
- **⏳ Davomiylik (Duration Timer):** Kun, soat, daqiqa va soniyalarni belgilab vaqt sanash.
  - Tezkor presetlar: 5m, 15m, 25m, 45m, 1h, 2h va `+1m`, `+5m`, `+15m`, `+1h` tugmalari.
- **🍅 Pomodoro Rejimi:** Dars va diqqat seanslari (25 daqiqa fokus, 5 daqiqa qisqa tanaffus, 15 daqiqa uzun tanaffus va sikllar hisoblagichi).
- **⏱ Sekundomer (Stopwatch):** Vaqtni noldan boshlab to'g'ri sanash.
- **🕒 Jonli Soat (Clock):** Hozirgi real vaqtni xuddi shu o'ta nafis tipografiyada ko'rsatish.

### 3. 🎨 Dizayn, Mavzular va Tipografiya
- **Kulrang va oq premium ikonalar:** Hech qanday bachkana rangli emojilar ishlatilmagan — barcha elementlar yuqori sifatli vektorli SVG gliflar bilan bezatilgan.
- **Mavzular:**
  - *Pitch Black (Obsidian)* — Asl rasmdek toza qora fon.
  - *Deep Navy (Midnight)* — Chuqur quyuq ko'k.
  - *Matrix Emerald* — Yashil minimalist texno.
  - *Amber Luxury* — Issiq tilla nur.
  - *Cyber Violet* — Neon binafsharang.
  - *Aurora Gradient* — Yumshoq kosmik gradient.
- **Shriftlar:** Urbanist UltraLight, Inter Thin, Montserrat Light, JetBrains Mono, Cormorant Garamond.

### 4. 🔔 Ovoz, Eslatmalar va Ambient Fokus Tizimi (Web Audio API)
Tashqi audio fayllarsiz, to'liq toza Web Audio sintezatori:
- **Tugash signallari:** Zen Singing Bowl (meditatsiya qo'ng'irog'i), Mayin billur qo'ng'iroq, Zamonaviy Digital Chime, Billur Gong.
- **Ovozni testlash:** Sozlamalar menyusida tanlangan signalni darhol oldindan eshitib ko'rish tugmasi.
- **Oraliq eslatmalar:** Har 10, 15, 20, 30 yoki 45 daqiqada diqqatni saqlash uchun mayin oraliq eslatma chalinadi.
- **Tugashdan 1 daqiqa oldin ogohlantirish:** Yakuniy xulosa uchun maxsus signal.
- **Orqa fon shovqinlari (White Noise):** Mayin yomg'ir, 432Hz Binaural Focus (alfa/teta to'lqinlari), Chuqur kosmik drone.

### 5. 👁 Zen Rejimi va Tejamkorlik
- **Kursor yashirish:** 3.5 soniya harakatsizlikdan so'ng sichqoncha kursori va yordamchi matnlar avtomatik yashirinadi.
- **WakeLock API:** Dars paytida ekran o'chib qolmaydi.
- **To'liq Ekran:** `F` yoki `F11` orqali to'liq ekranga o'tish.

---

## ⌨️ Tezkor Klaviaturadagi Tugmalar

| Tugma | Vazifasi |
| :--- | :--- |
| `Space` | Boshlash / Pauza (Play / Pause) |
| `F` | To'liq ekranga o'tish / chiqish (Fullscreen) |
| `P` | Sozlamalar panelini qadash (Pin / Unpin) |
| `R` | Taymerni qayta o'rnatish (Reset) |
| `Esc` | Sozlamalar panelini yopish |

---

## 🚀 Ishga Tushirish

### Usul 1: Brauzer orqali darhol ochish
```bash
./run.sh
```
yoki `index.html` faylini istalgan brauzerda oching.

### Usul 2: Mahalliy server orqali ishga tushirish
```bash
python3 app.py
```
Bu `http://localhost:5050` manzilida serverni ishga tushiradi va brauzerda avtomatik ochadi.

---

## 📂 Fayllar Strukturasi
```text
23-study-timer/
├── index.html            # Asosiy HTML sahifa
├── css/
│   └── style.css         # Ultra minimalist dizayn va mavzular
├── js/
│   ├── audio.js          # Web Audio API sintezatori (chime & ambient)
│   └── app.js            # Taymer mantig'i, rejimlari va kursor harakati
├── run.sh                # Linux tezkor launcher skripti
├── app.py                # Python lokal server
└── README.md             # Qo'llanma
```
