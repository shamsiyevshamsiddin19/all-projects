# train.shamsiyev.uz

Turli yo'nalishlarda qisqa, takrorlanuvchi mashqlar uchun FastAPI ilovasi. Hozirgi katalog uch yo'nalishni beradi: ruscha talaffuz, inglizcha sonlarni tinglab anglash va FastAPI/back-end bo'yicha tezkor savollar.

## Ishga tushirish

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/uvicorn app.main:app --reload
```

Ilova `http://127.0.0.1:8000` manzilida ochiladi. Testlar uchun:

```bash
.venv/bin/pytest
```

## Mashq qo'shish

`app/exercises/content.py` ichidagi `EXERCISES` ketma-ketligiga yangi `Exercise` obyektini qo'shish kifoya. Interfeys mashq turini avtomatik aniqlaydi:

- `pronunciation` — brauzer mikrofonidan nutqni matnga aylantiradi;
- `listening_number` — brauzer ovoz tizimi bilan sonni aytadi;
- `code_challenge` — tanlovli dasturlash savolini beradi.

Yangi, mutlaqo boshqa tur kerak bo'lsa `ExerciseKind` ga tur qo'shiladi va `static/js/app.js` dagi `practiceBody` funksiyasida uning interfeysi belgilanadi. Katalog javob kalitini API orqali yubormaydi.

## Production va AWS EC2

`deploy/Caddyfile` `train.shamsiyev.uz` uchun HTTPS sertifikatini avtomatik olishga tayyor. EC2 instansga Docker va Docker Compose o'rnatilgach, DNS'dagi `train.shamsiyev.uz` A yozuvini instansning ommaviy IP manziliga yo'naltiring, so'ng:

```bash
cp .env.example .env
docker compose -f docker-compose.production.yml up -d --build
```

Caddy 80 va 443 portlarini qabul qiladi, FastAPI esa faqat ichki Docker tarmog'ida `8000` portida ishlaydi. `.env` faylida maxfiy ma'lumot bo'lmaydi; u faqat ish muhiti sozlamalari uchun ajratilgan.
