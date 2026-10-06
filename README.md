# 🚀 Vibe Coding

**Shamsiddin Shamsiyev**ning shaxsiy loyihalar arxivi — Telegram botlar, web-platformalar va
desktop ilovalar. Har biri ishlab chiqarishda (production) sinovdan o'tgan, real
foydalanuvchilarga xizmat ko'rsatadigan tayyor mahsulotlar.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Aiogram](https://img.shields.io/badge/Aiogram-3-2CA5E0?logo=telegram&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Flutter](https://img.shields.io/badge/Flutter-02569B?logo=flutter&logoColor=white)

---

## 📂 Loyihalar

### 🤖 Telegram botlar

| Loyiha | Tavsif | Texnologiyalar |
| :--- | :--- | :--- |
| 🚀 **[01-boostday-productivity-bot](./01-boostday-productivity-bot)** | Kanalga avtomatik kunlik reja/TO-DO, challenge, eslatma va hisobotlar + Mini App. | `Python` `FastAPI` `PostgreSQL` |
| 📄 **[02-docforge-converter](./02-docforge-converter)** | Rasm/Fayl→PDF/ZIP, Matn→DOCX, PDF↔DOCX, Office→PDF, OCR, PDF birlashtirish/qirqish/watermark. | `Python` `Aiogram 3` `PostgreSQL` |
| 🏨 **[03-roomly-hotel-booking](./03-roomly-hotel-booking)** | Mehmonxona xonalarini bron qilish tizimi — Docker, Nginx, Django va bot. | `Django` `Aiogram 3` `Docker` |
| 🎬 **[04-cinehub-movie-bot](./04-cinehub-movie-bot)** | Kino va seriallarni qidirib topish va yuklab olish, inline qidiruv, web-admin panel. | `Python` `Aiogram 3` `PostgreSQL` |
| 📚 **[05-scholar-ai-assistant](./05-scholar-ai-assistant)** | Talabalar uchun mustaqil ish/referat/taqdimot tayyorlovchi AI yordamchi. | `Python` `Aiogram 3` `Claude/OpenAI API` |
| ❓ **[06-quizpulse-trivia-bot](./06-quizpulse-trivia-bot)** | `.txt` fayldan savol o'qib, Telegram quiz-poll turnirlariga aylantiradi. | `Python` `Aiogram 3` `PostgreSQL` |
| 🗓️ **[07-studyvault-exam-store](./07-studyvault-exam-store)** | Sessiyaga tayyorgarlik materiallari savdosi — Click to'lov, referal, HWID-aktivatsiya. | `Python` `Aiogram 3` `PostgreSQL` |
| 📝 **[08-captionflow-video-bot](./08-captionflow-video-bot)** | Videoga avtomatik subtitr (tarjima) yaratib qo'shib beradi. | `Python` `Aiogram 3` `FFmpeg` |
| 🎓 **[09-campusmate-lms-bot](./09-campusmate-lms-bot)** | TUIT LMS integratsiyasi — dars jadvali, baholar, deadline eslatmalari. | `Python` `Aiogram 3` `httpx/lxml` |

### 🌐 Web platformalar

| Loyiha | Tavsif | Texnologiyalar |
| :--- | :--- | :--- |
| ☁️ **[10-cloudnexus-hosting-platform](./10-cloudnexus-hosting-platform)** | Bulutli hosting va IT xizmatlari platformasi dizayni. | `HTML` `CSS` `JavaScript` |
| 🧮 **[11-mathcraft-web-calc](./11-mathcraft-web-calc)** | Django asosida yaratilgan interaktiv kalkulyator veb-ilovasi. | `Python` `Django` |
| 🎵 **[12-scarpion-music-streaming](./12-scarpion-music-streaming)** | Django asosidagi musiqa streaming va audio pleer platformasi. | `Python` `Django` `JavaScript` |
| 🌐 **[13-shamsiyev-portfolio-hub](./13-shamsiyev-portfolio-hub)** | Shaxsiy portfolio veb-sayti va server sozlamalari. | `HTML` `CSS` `JavaScript` `Nginx` |
| 🎮 **[14-tictactoe-minimax-pro](./14-tictactoe-minimax-pro)** | Django asosidagi Tic-Tac-Toe (X va O) o'yini veb-ilovasi. | `Python` `Django` |
| 🛒 **[15-wstore-digital-marketplace](./15-wstore-digital-marketplace)** | Raqamli mahsulotlar sotish marketpleysi (Django 5 & Next.js 15 variantlari). | `Django 5` `Next.js 15` `TypeScript` `PostgreSQL` |
| 📚 **[16-yordamchi-productivity-suite](./16-yordamchi-productivity-suite)** | Shaxsiy o'quv platformasi — sayt, desktop app va mobil ilova. | `FastAPI` `PostgreSQL` `Vanilla JS` |
| 🎨 **[17-craftsite-web-templates](./17-craftsite-web-templates)** | Turli sohalar uchun tayyor statik sayt shablonlari (7 ta namuna). | `HTML` `CSS` `JavaScript` |

### 🛠️ Integratsiyalar va Kutubxonalar

| Loyiha | Tavsif | Texnologiyalar |
| :--- | :--- | :--- |
| 💳 **[18-paycore-gateway-sdks](./18-paycore-gateway-sdks)** | Click, Payme va Uzum to'lov tizimlari integratsiyalari to'plami. | `Python` `TypeScript` `PHP` |

### 💻 Desktop & Ilovalar

| Loyiha | Tavsif | Texnologiyalar |
| :--- | :--- | :--- |
| 💻 **[19-captionflow-desktop-studio](./19-captionflow-desktop-studio)** | Video subtitr/tarjima qiluvchi Windows desktop ilova (GUI + backend). | `Flutter` `Python` |
| 📱 **[20-momentum-habit-tracker](./20-momentum-habit-tracker)** | Odatlar va faoliyat kuzatuvchi mobil hamda backend ilovasi. | `Flutter` `Backend` |
| 🃏 **[21-gamecraft-kotlin-app](./21-gamecraft-kotlin-app)** | Kotlin/Compose o'yin va yordamchi ilovasi. | `Kotlin` `Gradle` |

---

## 🏗️ Umumiy arxitektura

Bot loyihalari bir xil andozaga amal qiladi — bu ularni tez tushunish va texnik xizmat
ko'rsatishni osonlashtiradi:

- **aiogram 3** (async, router-asoslangan handlerlar) + **PostgreSQL** (`asyncpg`)
- Har bir botda ichki **web-admin panel** (`aiohttp`) — statistika, foydalanuvchilar,
  sozlamalar; ko'pchiligi umumiy master-domen dropdown uslubida
- `.env` / `.env.example` orqali sozlamalar — maxfiy qiymatlar kodda emas
- `deploy.sh` — Hetzner/Ubuntu serverga bir buyruq bilan o'rnatish (venv, systemd, PostgreSQL)
- Eski PHP botlarning aksariyati **Python'ga to'liq ko'chirilgan** (tarixiy ma'lumotlar
  migratsiya skriptlari bilan)

## ⚙️ Ishga tushirish

Har bir loyihaning batafsil qo'llanmasi o'z papkasidagi `README.md`da. Umumiy tartib:

```bash
cd <loyiha-nomi>
python3 -m venv venv && source venv/bin/activate   # Python loyihalari uchun
pip install -r requirements.txt
cp .env.example .env        # va o'z qiymatlaringiz bilan to'ldiring
python run.py                # yoki bot.py / main.py — loyiha ichidagi README'ga qarang
```

`wstore` (Next.js) uchun: `npm install` → `.env` sozlash → `npm run dev`.

## 👨‍💻 Muallif

**Shamsiddin Shamsiyev** — Backend Developer (Python, Django, FastAPI, PostgreSQL, Docker)

[![GitHub](https://img.shields.io/badge/GitHub-@shamsiyevshamsiddin19-181717?logo=github&logoColor=white)](https://github.com/shamsiyevshamsiddin19)
