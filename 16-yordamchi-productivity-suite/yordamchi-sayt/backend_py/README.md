# Yordamchi — Python (FastAPI) backend

Bu papka eski PHP backend'ini (`api.php`, `config/database.php`) to'liq almashtiradi.
Frontend'ni **o'zgartirish shart emas** — u `api.php?action=...` ni chaqiradi, FastAPI ham
aynan shu manzilda javob beradi.

## Nima o'zgardi (PHP → Python) va qanday kamchiliklar tuzatildi

| Muammo (PHP) | Yechim (Python) |
|---|---|
| Baza paroli kodda va git'da | Barcha maxfiy ma'lumot `.env` da (`app/config.py`), git'ga tushmaydi |
| Xato xabari SQL/baza tuzilishini oshkor qilardi | Markaziy handler faqat log'ga yozadi, foydalanuvchiga umumiy xabar (`errors.py`) |
| Schema har so'rovda `ALTER`/`SHOW` bilan tekshirilardi | Faqat startup'da bir marta (`db.init_schema`) |
| Xavfsizlik sarlavhalari qisman | Har javobga `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` |
| Log fayli cheksiz o'sardi | `RotatingFileHandler` (5MB × 3) |
| `health` host/port'ni oshkor qilardi | Faqat `APP_DEBUG=true` bo'lganda ko'rsatadi |

Barcha SQL prepared statement (named params) — SQL-injection yo'q.

## Login talab qilinmaydi
Bu ilova **login talab qilmaydi** — barcha foydalanuvchilar bitta umumiy ma'lumot fazosida
ishlaydi (`REQUIRE_AUTH=false`, `owner.owner_context` doim `('global','shared')`). Ro'yxatdan
o'tish/kirish UI'si ixtiyoriy bo'lib qoladi, ammo ma'lumotni saqlash uchun kirish shart emas.

## Talablar
- Python 3.10+
- PostgreSQL 12+ (jadvallar `database/schema.sql` dan startup'da avtomatik yaratiladi)

## Lokal ishga tushirish (Windows/Linux)

```bash
cd backend_py
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # va qiymatlarni to'ldiring
# SESSION_SECRET yarating:  python -c "import secrets;print(secrets.token_hex(32))"

uvicorn app.main:app --reload --port 8000
```

Frontend'ni ham shu app tarqatishini xohlasangiz `.env` da `SERVE_STATIC=true` qo'ying —
`http://localhost:8000/` sizga `index.html` ni beradi. Aks holda frontend'ni alohida
(nginx yoki `python -m http.server`) tarqating va `api.php` so'rovlarini 8000-portga yo'naltiring.

## VPS (shamsiyev) ga o'rnatish

```bash
# 1. Kod
sudo mkdir -p /var/www/yordamchi
# butun loyiha (index.html, assets/, backend_py/ ...) ni shu yerga ko'chiring

# 2. Virtualenv + kutubxonalar
cd /var/www/yordamchi/backend_py
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Sozlama
cp .env.example .env
python3 -c "import secrets;print('SESSION_SECRET='+secrets.token_hex(32))" >> .env
nano .env        # DB_* va qolganlarini to'ldiring

# 4. Baza (PostgreSQL) — foydalanuvchi va baza yarating (jadvallar startup'da avtomatik yaratiladi)
#    sudo -u postgres psql -c "CREATE USER yordamchi WITH PASSWORD 'CHANGE_ME';"
#    sudo -u postgres psql -c "CREATE DATABASE yordamchi OWNER yordamchi;"
#    Eski MySQL ma'lumotini ko'chirish uchun pgloader ishlating:  pgloader mysql://... postgresql://...

# 5. systemd
sudo cp deploy/yordamchi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now yordamchi
sudo systemctl status yordamchi

# 6. nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/yordamchi
sudo ln -s /etc/nginx/sites-available/yordamchi /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 7. HTTPS
sudo certbot --nginx -d yordamchi.example.com
```

## Migratsiya tarixi
Loyiha avval PHP'da edi — endi to'liq Python/FastAPI backend + build-siz JS frontend
(`assets/js/app2/`). Eski PHP fayllar (`api.php`, `config/database.php`, `router.php`,
`sozlamalar.php`) va eski frontend (`index.js`, sahifa-boshiga-sahifa `.html`/`.css`) o'chirilgan.
