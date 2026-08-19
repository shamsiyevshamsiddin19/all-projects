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
| 📄 **[document-convertor](./document-convertor)** | Rasm/Fayl→PDF/ZIP, Matn→DOCX, PDF↔DOCX, Office→PDF, OCR, PDF birlashtirish/qirqish/watermark. | `Python` `Aiogram 3` `PostgreSQL` |
| 🎬 **[kino-bot](./kino-bot)** | Kino va seriallarni qidirib topish va yuklab olish, inline qidiruv, web-admin panel. | `Python` `Aiogram 3` `PostgreSQL` |
| 📚 **[mustaqilbot](./mustaqilbot)** | Talabalar uchun mustaqil ish/referat/taqdimot tayyorlovchi AI yordamchi. | `Python` `Aiogram 3` `Claude/OpenAI API` |
| ❓ **[quiz-bot](./quiz-bot)** | `.txt` fayldan savol o'qib, Telegram quiz-poll turnirlariga aylantiradi. | `Python` `Aiogram 3` `PostgreSQL` |
| 🗓️ **[sessiyabot](./sessiyabot)** | Sessiyaga tayyorgarlik materiallari savdosi — Click to'lov, referal, HWID-aktivatsiya. | `Python` `Aiogram 3` `PostgreSQL` |
| 📝 **[subtitr-bot](./subtitr-bot)** | Videoga avtomatik subtitr (tarjima) yaratib qo'shib beradi. | `Python` `Aiogram 3` `FFmpeg` |
| 🎓 **[tatu-bots](./tatu-bots)** | TUIT LMS integratsiyasi — dars jadvali, baholar, deadline eslatmalari. | `Python` `Aiogram 3` `httpx/lxml` |
| 🚀 **[boostday-bot](./boostday-bot)** | Kanalga avtomatik kunlik reja/TO-DO, challenge, eslatma va hisobotlar + Mini App. | `Python` `FastAPI` `PostgreSQL` |

### 🌐 Web platformalar

| Loyiha | Tavsif | Texnologiyalar |
| :--- | :--- | :--- |
| 🛒 **[wstore](./wstore)** | Raqamli mahsulotlar (kod loyihalari, botlar, saytlar) sotish marketpleysi — wstore.uz. | `Next.js 15` `TypeScript` `Prisma` `PostgreSQL` |
| 🎨 **[web-site](./web-site)** | Turli sohalar uchun tayyor statik sayt shablonlari (7 ta namuna). | `HTML` `CSS` `JavaScript` |
| 📚 **[yordamchi-sayt](./yordamchi-sayt)** | Shaxsiy o'quv platformasi — testlar, lug'at (SRS), sport, dars jadvali, maqsadlar. | `FastAPI` `PostgreSQL` `Vanilla JS` |

### 💻 Desktop

| Loyiha | Tavsif | Texnologiyalar |
| :--- | :--- | :--- |
| 💻 **[subtitr-desktop](./subtitr-desktop)** | Video subtitr/tarjima qiluvchi Windows desktop ilova (GUI + backend). | `Flutter` `Python` |

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
