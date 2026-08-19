# Boostday bot — Python (FastAPI)

Telegram bot (@boostdaybot) — webhook + cron + Telegram Mini App. Yordamchi sayt bilan
**bitta PostgreSQL bazani** (`yordamchi`) ulashadi.

## Tarkib
- `app/main.py` — webhook (`POST /boost/webhook`), Mini App API (`/boost/api`), fayl yuklash (`/boost/upload`), Mini App sahifasi (`GET /boost/app` → `miniapp.html`)
- `app/handlers.py` + `app/callbacks.py` — bot suhbat oqimi (matn buyruqlar, inline tugmalar)
- `app/tg.py` + `app/helpers.py` — Telegram API klienti, vazifa/bo'lim guruhlash mantig'i
- `app/scheduler.py` (`run_cron.py` orqali) — rejalashtirilgan yuborishlar, hisobotlar
- `app/db.py` — PostgreSQL (SQLAlchemy Core)
- `app/config.py` (`.env`) — sozlamalar
- `app/media.py` — Mini App'dan yuklangan fayllarni Telegram orqali saqlash
- `miniapp.html` — Telegram-native Mini App (bosh sahifa, rejalar, statistika, kanallar)

## Lokal ishga tushirish
```bash
cd bot_py
python -m venv .venv
# Windows: .venv\Scripts\activate   Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # BOT_TOKEN, DB_*, WEB_APP_URL ni to'ldiring
uvicorn app.main:app --port 8090
```

## VPS'ga o'rnatish
```bash
cd /opt/yordamchi/Boostdaybot/bot_py
python3.9 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env      # DB_* Yordamchisayt/backend_py/.env bilan bir xil bo'lsin

sudo cp deploy/boostday-bot.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now boostday-bot

sudo cp deploy/boostday-cron.service deploy/boostday-cron.timer /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now boostday-cron.timer

# nginx: /boost/webhook, /boost/api, /boost/app, /boost/upload — asosiy sayt nginx konfiguratsiyasida

.venv/bin/python set_webhook.py set https://domeningiz.uz/boost/webhook
.venv/bin/python set_webhook.py info
```

## Muhim
- `WEB_APP_URL` — Mini App manzili (`https://domeningiz.uz/boost/app`)
- `DB_*` — sayt bilan bir xil PostgreSQL baza (`Yordamchisayt/backend_py/.env` bilan mos)
- Jadvallar (`users`, `plans`, ...) startup'da avtomatik yaratiladi
- Vazifalar (TO-DO/Har kungi reja) ixtiyoriy ravishda bo'limlarga guruhlanishi mumkin (`helpers.py`: `decode_task_groups`/`encode_task_groups`)
