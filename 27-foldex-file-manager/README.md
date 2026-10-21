# 📂 Foldex — Telegram File Manager Bot + Web Admin Panel

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=flat&logo=telegram&logoColor=white)](https://aiogram.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat)](https://www.sqlalchemy.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com)

**Foldex** — Telegram Bot va zamonaviy Veb-Admin Panel (SPA) orqali shaxsiy bulutli fayllar va cheksiz ierarxik papkalarni boshqarish, ko'rish, qidirish hamda to'g'ridan-to'g'ri Telegram chatlarida ulashish imkonini beruvchi to'liq asinxron tizim.

- 🌐 **Ishlab chiqarish domeni:** `https://foldex.shamsiyev.uz`
- 👤 **Yagona administrator:** `TELEGRAM_ADMIN_ID = 7883409434`
- 🖥️ **Ishlab chiqarish serveri:** `yordamchi` (`82.70.41.85`, port `8027`)
- 🔗 **GitHub Repozitoriyasi:** [shamsiyevshamsiddin19/Foldexs](https://github.com/shamsiyevshamsiddin19/Foldexs)

---

## 📑 Mundarija
1. [Loyiha Imkoniyatlari](#-loyiha-imkoniyatlari)
2. [Arxitektura va Texnologiyalar](#-arxitektura-va-texnologiyalar)
3. [Qat'iy Xavfsizlik Modeli](#-qatiy-xavfsizlik-modeli)
4. [Reply Keyboard Navigatsiyasi](#-reply-keyboard-navigatsiyasi)
5. [Telegram Inline Mode](#-telegram-inline-mode)
6. [Veb-Admin Panel Xususiyatlari](#-veb-admin-panel-xususiyatlari)
7. [Ma'lumotlar Bazasi va Atomik Tahlil](#-malumotlar-bazasi-va-atomik-tahlil)
8. [O'rnatish va Ishga Tushirish (Mahalliy)](#-ornatish-va-ishga-tushirish-mahalliy)
9. [Serverga Joylashtirish (Docker & Nginx & SSL)](#-serverga-joylashtirish-docker--nginx--ssl)
10. [Telegram Webhook va BotFather Sozlamalari](#-telegram-webhook-va-botfather-sozlamalari)

---

## 🌟 Loyiha Imkoniyatlari

- **Cheksiz Ierarxik Papkalar:** Papka ichida yana cheksiz darajagacha ichki papkalar (subfolders) ochish va navigatsiya qilish.
- **Tezkor Reply Keyboard:** Botda papkalar dinamik Reply tugmalar orqali ko'rinadi (`⬅️ Orqaga`, `🏠 Bosh menyu`, `📤 Hammasini yuborish`).
- **Kuchli Inline Mode:** Istalgan chatda `@bot_username` orqali papkalarni ko'rish, ichki papkalarni ochish va fayllarni zudlik bilan jo'natish.
- **Veb-Admin Panel (SPA):**
  - Zamonaviy Glassmorphism qora mavzu (Dark mode, neon aksentlar, Google Fonts *Plus Jakarta Sans*).
  - Drag-and-drop orqali bir vaqtda ko'plab fayllarni yuklash (Batch upload).
  - Real vaqtli yuklash indikatori (0% -> 100% progress bar).
  - Papka va fayllarni qayta nomlash, boshqa papkalarga ko'chirish va xavfsiz o'chirish.
  - Jonli qidiruv (Debounce filtrlash bilan).
  - Breadcrumbs yo'li orqali qulay navigatsiya.
- **Telegram Kesh Integratsiyasi:** Fayllar Telegram `file_id` orqali keshlanadi, bu esa bot orqali jo'natishda server kanalini ortiqcha yuklamasdan lahzalik yetkazishni ta'minlaydi.

---

## 🏗️ Arxitektura va Texnologiyalar

```text
27-foldex-file-manager/
├── alembic/                      # PostgreSQL migratsiyalari
│   ├── env.py
│   └── versions/001_initial_schema.py
├── app/
│   ├── api/                      # FastAPI REST endpointlari
│   │   ├── auth.py               # WebApp va /login autentifikatsiyasi
│   │   ├── folders.py            # Papkalar CRUD va daraxti
│   │   ├── files.py              # Fayllar yuklash, ko'chirish, yuklab olish
│   │   ├── stats.py              # Dashboard ko'rsatkichlari
│   │   └── webhook.py            # Telegram updates qabul qilish
│   ├── bot/                      # aiogram 3.x Telegram boti
│   │   ├── loader.py             # Bot & Dispatcher
│   │   ├── middlewares/auth.py   # Qat'iy 7883409434 avtorizatsiyasi
│   │   ├── keyboards/            # Reply va Inline klaviaturalar
│   │   └── handlers/             # Bot komandalari va Inline query
│   ├── core/                     # Konfiguratsiya, xavfsizlik va DB
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/                   # SQLAlchemy 2.0 asinxron modellari
│   │   ├── folder.py
│   │   ├── file_item.py
│   │   └── auth_token.py
│   ├── schemas/                  # Pydantic v2 sxemalari
│   ├── services/                 # Biznes mantiq (Fayl va Papka xizmatlari)
│   ├── static/                   # CSS va JavaScript (Vanilla SPA)
│   │   ├── css/style.css
│   │   └── js/app.js, auth.js
│   ├── templates/                # Jinja2 HTML shablonlari (index.html, login.html)
│   └── main.py                   # FastAPI + aiogram lifespan ilovasi
├── uploads/                      # Diskdagi fayllar ombori
├── nginx/                        # foldex.shamsiyev.uz Nginx konfiguratsiyasi
├── Dockerfile                    # Ko'p bosqichli ishlab chiqarish konteyneri
├── docker-compose.yml            # FastAPI + PostgreSQL orkestratsiyasi
├── requirements.txt              # Python kutubxonalari
└── .env.example                  # Muhit o'zgaruvchilari namunasi
```

---

## 🔒 Qat'iy Xavfsizlik Modeli

Loyiha talabiga binoan, tizim faqat **bitta** administratorga xizmat qiladi:
`TELEGRAM_ADMIN_ID = 7883409434`

| Qatlam | Tekshiruv Mexanizmi | Natija (Agar ID != 7883409434 bo'lsa) |
| :--- | :--- | :--- |
| **Bot Xabarlar** | `AdminAuthMiddleware` | `⛔ Kirish taqiqlangan! Faqat administrator uchun.` xabari |
| **Bot Tugmalar** | `AdminAuthMiddleware` | `⛔ Ruxsat berilmagan!` alert bildirishnomasi |
| **Inline Rejim** | `AdminAuthMiddleware` & `inline.py` | `⛔ Kirish huquqi mavjud emas` yagona natijasi |
| **Veb API lar** | `get_current_admin` Dependency | `HTTP 401 Unauthorized` yoki `HTTP 403 Forbidden` |
| **VebApp Kirish** | HMAC-SHA256 rasmiy Telegram imzosi | Imzo noto'g'ri bo'lsa sessiya berilmaydi |
| **Brauzer Kirish** | Botdagi `/login` bir martalik kriptografik token | Token faqat 1 marta va 15 daqiqa ishlaydi |

---

## ⌨️ Reply Keyboard Navigatsiyasi

`/start` yuborilganda foydalanuvchiga asosiy papkalar Reply Keyboard tugmalari sifatida ko'rsatiladi:
- 🇷🇺 Rus tili
- 💻 Dasturlash
- 📚 Kitoblar
- 📁 Boshqa fayllar

Papka bosilganda bot uning ichiga kiradi va quyidagilarni ko'rsatadi:
1. **Navigatsiya zanjiri (Breadcrumbs):** Masalan: `Bosh sahifa / Rus tili / Grammatika / Padejlar`.
2. **Fayllar ro'yxati:** Nomi va hajmi bilan.
3. **Klaviatura tugmalari:**
   - Ichki subfolderlar (2 tadan);
   - Fayl tugmalari (`📄 darslik.pdf` — bosilganda darhol jo'natiladi);
   - `📤 Hammasini yuborish` (barcha fayllarni bir zumda ketma-ket yuboradi);
   - `⬅️ Orqaga` (bir pog'ona yuqoriga qaytadi);
   - `🏠 Bosh menyu` (Ildiz katalogiga qaytadi);
   - `🌐 Admin Panel` (`https://foldex.shamsiyev.uz` tugmasi).

---

## ⚡ Telegram Inline Mode

Botfather orqali `@bot_username` uchun Inline rejim yoqilgandan so'ng, istalgan chatda quyidagicha chaqiriladi:

1. `@bot_username` (bo'sh so'rov):
   - Asosiy papkalar ro'yxati chiqadi. Har bir papka ostida `📂 Ochish` tugmasi bo'ladi.
2. `@bot_username folder:<ID>`:
   - Tanlangan papka ichidagi barcha subfolderlar va fayllar chiqadi.
   - Eng boshida `⬅️ Orqaga` tugmasi joylashadi.
   - Agar fayllar bo'lsa: `📤 Hammasini yuborish` natijasi chiqadi.
   - Fayllar Telegramning `CachedDocument`, `CachedPhoto`, `CachedVideo` turlarida lahzada uzatiladi.
3. `@bot_username <qidiruv matni>`:
   - Barcha papkalar bo'yicha global tezkor qidiruv natijalari taqdim etiladi.

---

## 💻 Veb-Admin Panel Xususiyatlari

- **To'liq SPA (Single Page Application):** Sahifani qayta yuklamasdan lahzalik navigatsiya.
- **Drag-and-Drop:** Fayllarni brauzer oynasiga tashlash orqali yuklash.
- **Hajm va Formatlar:** 500 MB gacha bo'lgan barcha turdagi fayllarni (PDF, Word, Excel, Video, Audio, Arxiv, Kod) qabul qilish.
- **Katta Fayllar Yuklash Xavfsizligi:** Bo'laklab (chunked) xotiraga yuklanmasdan to'g'ridan-to'g'ri diskka yoziladi.
- **Path Traversal Himoyasi:** Fayl nomlari qat'iy tozalanadi (`sanitize_filename`).

---

## 🗄️ Ma'lumotlar Bazasi va Atomik Tahlil

### SQLAlchemy Modellari Tuzilishi

| Model | Jadval | Maydonlar | Bog'liqliklar |
| :--- | :--- | :--- | :--- |
| `Folder` | `folders` | `id, name, parent_id, icon, color, description, order_index, created_at, updated_at` | `children` (self-referential, cascade delete), `files` |
| `FileItem` | `files` | `id, folder_id, name, stored_filename, file_path, file_size, mime_type, file_type, telegram_file_id, description` | `folder` (Many-to-One) |
| `AdminAuthToken` | `admin_auth_tokens` | `id, token, telegram_user_id, is_used, expires_at, created_at` | One-time token verification |

### FastAPI Qatlamlari va Xotira Boshqaruvi Taqqoslashi

```
[Mijoz (Browser / Telegram)]
            │
            ▼
    [Nginx Reverse Proxy] (SSL TLSv1.3, 500M max_body, gzip)
            │
            ▼
     [FastAPI Server] (Uvicorn ASGI)
     ├── [Security & Auth Middleware] ──> TELEGRAM_ADMIN_ID == 7883409434
     ├── [API Routers] (Folders, Files, Stats, Webhook)
     └── [aiogram 3.x Dispatcher] ──> Telegram Bot API
            │
    ┌───────┴───────┐
    ▼               ▼
[PostgreSQL DB]  [Fizik Disk: uploads/]
(asyncpg pool)   (UUID fayllar oqimli yoziladi)
```

---

## 🚀 O'rnatish va Ishga Tushirish (Mahalliy)

### 1. Repozitoriy va Muhit
```bash
cd 27-foldex-file-manager
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Sozlamalarni kiritish
`.env.example` dan nusxa olib `.env` yarating:
```bash
cp .env.example .env
nano .env
```
Quyidagi qiymatlarni kiriting:
```ini
BOT_TOKEN="sizning_bot_tokeningiz"
TELEGRAM_ADMIN_ID=7883409434
DATABASE_URL="postgresql+asyncpg://foldex_user:secure_password@localhost:5432/foldex_db"
USE_WEBHOOK=false # Mahalliyda polling uchun
```

### 3. Serverni ishga tushirish
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Brauzerda: `http://localhost:8000`

---

## 🌐 Serverga Joylashtirish (Docker & Nginx & SSL)

Asosiy server: **shamsiyev.uz** (`79.76.49.83`, Oracle Cloud Stockholm).

### 1. Docker Compose orqali ishga tushirish
```bash
docker compose up -d --build
```
PostgreSQL va FastAPI konteynerlari avtomatik ishga tushadi.

### 2. Nginx va SSL ni sozlash
1. Nginx konfiguratsiyasini nusxalang:
   ```bash
   sudo cp nginx/foldex.shamsiyev.uz.conf /etc/nginx/sites-available/foldex.shamsiyev.uz.conf
   sudo ln -s /etc/nginx/sites-available/foldex.shamsiyev.uz.conf /etc/nginx/sites-enabled/
   ```
2. Certbot orqali bepul SSL sertifikat oling:
   ```bash
   sudo certbot --nginx -d foldex.shamsiyev.uz
   ```
3. Nginx ni qayta ishga tushiring:
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

---

## 🤖 Telegram Webhook va BotFather Sozlamalari

### 1. BotFather sozlamalari
1. Telegramda `@BotFather` ga kiring.
2. `/setinline` buyrug'ini yuboring va botingizni tanlang. Qidiruv maydoni tavsifiga `Fayllarni qidirish...` deb yozing.
3. `/setinlinefeedback` buyrug'ini yoqing (`Enabled`).
4. `/setmenubutton` buyrug'i orqali WebApp tugmasini qo'shing:
   - URL: `https://foldex.shamsiyev.uz`
   - Nomi: `🌐 Fayllarni boshqarish`

### 2. Webhook holatini tekshirish
FastAPI ishga tushgach, webhook avtomatik tarzda o'rnatiladi:
```bash
curl -F "url=https://foldex.shamsiyev.uz/api/webhook/telegram" \
     -F "secret_token=foldex_super_secret_webhook_key_2026" \
     https://api.telegram.org/bot<BOT_TOKEN>/setWebhook
```
Tekshirish:
```bash
curl https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo
```

---

## 👨‍💻 Muallif
- **Dasturchi:** Shamsiddin Shamsiyev
- **Ta'lim dargohi:** TATU (Toshkent axborot texnologiyalari universiteti)
- **Yo'nalish:** Backend dasturlash (FastAPI, PostgreSQL, aiogram 3.x, Linux avtomatlashtirish)
