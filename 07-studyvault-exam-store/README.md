# 🗓️ Sessiya Tayyorgarlik Bot

Talabalarga sessiyaga tayyorgarlik materiallarini sotuvchi Telegram bot. Eski PHP bot
(`baza_bot.php`) to'liq Python (aiogram 3 + PostgreSQL)'ga ko'chirildi. Click orqali to'lov,
referal tizimi (5 ta referal — bepul kirish) va HWID-asoslangan faollashtirish kaliti mavjud.

## Tuzilishi

```
sessiyabot/
├── main.py             # kirish nuqtasi (polling + Click ko'prik API + admin panel)
├── bot.py               # asosiy handlerlar (DB-asoslangan step/temp FSM)
├── config.py            # .env dan sozlamalar
├── db.py                # PostgreSQL (asyncpg)
├── click_api.py         # Click to'lov ko'prik API (webhook)
├── services.py          # aktivatsiya kaliti, HWID normalizatsiya, to'lov havolasi
├── keyboards.py         # klaviaturalar
├── admin_web.py         # web-admin panel (aiohttp, Basic Auth)
├── schema.sql           # PostgreSQL sxema
├── import_data.py       # eski PHP/MySQL bazadan ko'chirish
├── deploy.sh            # server o'rnatish (PostgreSQL + venv + systemd)
├── assets/               # yo'riqnoma rasmlari (HWID, faollashtirish)
└── .env.example
```

## Ishga tushirish

```bash
cd sessiyabot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN, DATABASE_URL, INTERNAL_SECRET va h.k. to'ldiring
python main.py
```

## Xususiyatlar

- Click orqali to'lov (eski server bilan `INTERNAL_SECRET` orqali ko'prik)
- Referal tizimi — 5 ta taklif qilingan foydalanuvchi uchun bepul kirish
- HWID-asoslangan faollashtirish kaliti (bir qurilmaga bog'lash)
- Web-admin panel: statistika, foydalanuvchilar, to'lovlar
- PostgreSQL — DB-asoslangan FSM (holat/vaqtinchalik ma'lumot bazada saqlanadi, xotirada emas)
