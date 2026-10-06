# Subtitr Bot — MVP (Bosqich 1)

Telegram bot: video yuborasiz → tilni tanlaysiz → tayyor subtitrli videoni olasiz.

Bu MVP arxitektura hujjatining **1-bosqichi**:
aiogram + Groq Whisper + ffmpeg, toza kontur subtitr (5.5).

> Tarjima, ikki qatlam, to'lov, Mini App, admin sayt — keyingi bosqichlar.

## Talablar

- Python 3.11+
- **ffmpeg** tizimga o'rnatilgan va `PATH` da bo'lishi shart
  - Windows: https://www.gyan.dev/ffmpeg/builds/ → `ffmpeg.exe` ni PATH ga qo'shing
  - Tekshirish: `ffmpeg -version`
- Telegram bot tokeni (BotFather)
- Groq API kaliti (https://console.groq.com)

## O'rnatish

```powershell
cd "E:\Subtitle bot\subtitr_bot"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Sozlash

`.env.example` dan `.env` yarating va to'ldiring:

```powershell
Copy-Item .env.example .env
notepad .env
```

`BOT_TOKEN` va `GROQ_API_KEY` ni kiriting.

## Ishga tushirish

```powershell
python -m bot.main
```

Telegramda botga video yuboring → tilni tanlang → kuting.

## Tuzilma

```
subtitr_bot/
├── config.py            — sozlamalar (.env)
├── bot/
│   ├── main.py          — ishga tushirish
│   ├── keyboards.py     — til tanlash tugmalari
│   └── handlers/
│       ├── start.py     — /start, /help
│       └── video.py     — video → til → natija oqimi
└── worker/
    ├── pipeline.py      — to'liq zanjir (bloklamaydi)
    ├── transcribe.py    — Groq Whisper
    ├── subtitles.py     — sifatli .srt (maks 42 belgi, 2 qator)
    └── ffmpeg_utils.py  — audio ajratish + toza kontur burn
```

## Eslatmalar

- **Fayl hajmi:** oddiy Bot API faqat 20MB gacha yuklab oladi. Kattaroq
  uchun local Bot API server kerak (arxitektura K1) — keyingi bosqich.
- **Shrift:** standart `Arial`. Brendli ko'rinish uchun `Inter.ttf` o'rnatib
  `.env` da `SUB_FONT=Inter` qiling.
- **Bloklash yo'q:** og'ir ishlar `asyncio.to_thread` da. Ko'p foydalanuvchi
  uchun keyingi bosqichda Celery navbat qo'shiladi (arxitektura 8).
