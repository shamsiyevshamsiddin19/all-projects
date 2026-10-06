# 🎓 TUIT LMS Bot (@tatulmsbot)

TATU (TUIT) talabalari uchun LMS (lms.tuit.uz) bilan integratsiyalashgan Telegram yordamchi
bot. Talaba LMS login/parolini bir marta kiritadi (shifrlangan holda saqlanadi), so'ng bot
orqali dars jadvali, baholar, deadline'lar va materiallarni to'g'ridan-to'g'ri Telegram'da
ko'radi — saytga kirib o'tirishga hojat qolmaydi.

## Tuzilishi

```
tatu-bots/
├── run.py                   # kirish nuqtasi (polling + admin web)
├── core/
│   ├── config.py             # .env dan sozlamalar
│   ├── db.py                 # SQLite (aiosqlite) — foydalanuvchi/sessiya saqlash
│   ├── crypto.py             # Fernet — LMS login/parolni shifrlab saqlash
│   └── util.py               # yordamchi funksiyalar (HTML escape, fayl limiti)
├── bots/
│   ├── lms_bot.py            # @tatulmsbot handlerlari (start, login, menyu, jadval)
│   ├── inline.py             # inline rejim
│   ├── keyboards.py          # klaviaturalar
│   ├── texts.py              # matnlar
│   ├── admin_web.py          # web-admin panel (aiohttp)
│   └── scheduler.py          # ertalabki push va deadline eslatmalari (APScheduler)
├── lms/
│   ├── client.py             # lms.tuit.uz bilan httpx orqali sessiya-cookie klient
│   ├── parse.py              # HTML parsing (lxml)
│   ├── models.py             # Profile, Course, ScheduleItem, Final va h.k.
│   ├── session.py            # login/sessiya boshqaruvi
│   └── stats.py              # baholar/statistika hisoblash
├── deploy/                   # systemd xizmat + watchdog fayllari
├── scripts/smoke_lms.py      # LMS klientini qo'lda tekshirish skripti
└── requirements.txt
```

## Ishga tushirish

```bash
cd tatu-bots
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# .env yarating: LMS_BOT_TOKEN, FERNET_KEY (Fernet.generate_key()), ADMIN_IDS va h.k.
python run.py
```

## Xususiyatlar

- LMS login/parolni **Fernet bilan shifrlab** saqlash (ochiq matnda emas)
- Dars jadvali, baholar, final imtihonlar, o'tkazib yuborilgan darslar
- Ertalabki avtomatik push (`MORNING_PUSH`) va deadline eslatmalari (APScheduler)
- Web-admin panel (aiohttp) — master domen orqali proksi qilinadi
- systemd xizmati zaif server (498MB RAM) uchun maxsus sozlangan: `MemoryHigh`/`MemoryMax`,
  `CPUQuota`, watchdog timer bilan avtomatik tiklanish
