# Mustaqil Ish Bot 🎓

O'zbekiston talabalari uchun akademik hujjatlarni sun'iy intellekt yordamida
tayyorlab beruvchi Telegram bot ([@talabaxizmatlaribot](https://t.me/talabaxizmatlaribot)).

## Imkoniyatlari

- **8 hujjat turi**: referat, mustaqil ish, kurs ishi, diplom ishi, tezis,
  ilmiy maqola, taqdimot (slayd), krossvord
- **Professional formatlash**: haqiqiy Word jadvallari, LaTeX formulalar (OMML),
  grafik/diagrammalar (bar/line/pie), titul varag'i, ilmiy apparat
- **Fanga moslashuvchi**: iqtisodga statistika, matematikaga formulalar,
  huquqqa qonun havolalari va h.k.
- **Aniq hajm**: buyurtma qilingan bet soni bilan mos keladi (kalibrlangan)
- **Slaydlar**: 12 xil maket, 6 rang-mavzu, gradient fon, Pexels fon-fotolari
- **Haqiqiy manbalar**: web-search orqali real adabiyotlar va statistika
- **To'lov**: Click integratsiyasi, balans tizimi, referal, cashback

## Texnologiyalar

- **Bot**: [aiogram 3](https://docs.aiogram.dev/) (async Telegram)
- **AI**: Claude (asosiy) + OpenAI (zaxira)
- **DB**: PostgreSQL + SQLAlchemy (async)
- **Hujjatlar**: python-docx, python-pptx, reportlab, Pillow
- **Formulalar**: latex2mathml + mathml2omml
- **Web**: aiohttp (admin panel + Click webhook)

## Arxitektura

```
ai/           — AI promptlari va provayder qatlami (Claude + OpenAI)
bot/          — Telegram handlerlar, klaviaturalar, FSM holatlar
db/           — SQLAlchemy modellar va CRUD
docs/         — hujjat yasovchilar (docx, pdf, pptx, charts, crossword)
payment/      — Click to'lov integratsiyasi
services/     — generatsiya xizmati (navbat, bo'laklab yozish)
web/          — admin panel va Click webhook
config.py     — sozlamalar (env dan)
main.py       — kirish nuqtasi
```

## O'rnatish

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # va o'z qiymatlaringiz bilan to'ldiring
python main.py
```

`.env` faylida `BOT_TOKEN`, `ANTHROPIC_API_KEY`, `DATABASE_URL` va Click
sozlamalarini to'ldirish shart. Batafsil `.env.example` ga qarang.

## Litsenziya

Shaxsiy loyiha. Barcha huquqlar mualliflikда saqlanadi.
