# 🎬 Kino Bot (Python / aiogram 3 + PostgreSQL)

Eski PHP bot to'liq Python'ga ko'chirildi. Qo'shildi: **inline qidiruv**, **web-admin panel**
(master domen dropdown'iga mos uslubda), tasodifiy kino, kengaytirilgan statistika.

## Tuzilishi

```
kino/
├── bot.py                 # kirish nuqtasi (polling + web-admin)
├── config.py              # .env dan sozlamalar
├── db.py                  # PostgreSQL (asyncpg) + sxema
├── utils.py               # caption, obuna tekshiruvi, matn
├── tmdb.py                # TMDB qidiruv
├── keyboards.py           # klaviaturalar
├── states.py              # FSM holatlari
├── handlers/
│   ├── user.py            # start, kod, menyular, qidiruv, reyting, tasodifiy
│   ├── admin.py           # Telegram admin panel (kontent qo'shish)
│   ├── inline.py          # inline rejim
│   └── callbacks.py       # obuna tasdiqlash, guruhga so'rov
├── web/
│   ├── admin.py           # web-admin sahifalari
│   ├── theme.py           # master bilan bir xil dizayn + bot dropdown
│   └── server.py          # aiohttp runner
├── migrate_mysql_to_pg.py # eski MySQL bazadan ko'chirish
├── requirements.txt
└── .env.example
```

## O'rnatish (Hetzner / Ubuntu)

```bash
sudo apt update && sudo apt install -y python3-venv postgresql
sudo -u postgres psql -c "CREATE USER kino WITH PASSWORD '190919';"
sudo -u postgres psql -c "CREATE DATABASE kino OWNER kino;"

cd /opt/kino
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # va qiymatlarni to'ldiring
python bot.py
```

## Eski MySQL bazani ko'chirish

```bash
pip install pymysql
export MYSQL_HOST=localhost MYSQL_USER=... MYSQL_PASS=... MYSQL_DB=692b3496c861f_kino
python migrate_mysql_to_pg.py
```
> MySQL dump faylini bersangiz, uni to'g'ridan-to'g'ri import qilib ko'rsatib beraman.

## Web-admin

- To'g'ridan: `http://SERVER_IP:8080/admin` (`WEB_ADMIN_USER`/`WEB_ADMIN_PASSWORD`)
- Master domen dropdown orqali: `https://DOMEN/kino/admin`
  - Master `.env`: `KINO_ORIGIN=http://178.104.25.218:8080`, `KINO_BRIDGE_SECRET=<sir>`
  - Kino `.env`: `WEB_BRIDGE_SECRET=<xuddi shu sir>`
  - Master `web/admin.py` dropdown va `/kino` proxy allaqachon qo'shilgan.

## systemd (avto-ishga tushirish)

```ini
# /etc/systemd/system/kinobot.service
[Unit]
Description=Kino Bot
After=network.target postgresql.service

[Service]
WorkingDirectory=/opt/kino
ExecStart=/opt/kino/.venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable --now kinobot
```

## Inline rejim
1. @BotFather → `/setinline` → botni tanlab, placeholder yozing (masalan: `Kino nomi...`).
2. Istalgan chatda: `@Tarjimakinolarubot spider` → natijani bosing → bot orqali ochiladi.
