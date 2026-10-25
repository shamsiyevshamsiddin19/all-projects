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

AWS serverda ilova `/opt/train-shamsiyev-uz` ichida ishlaydi. `deploy/systemd/train-shamsiyev-uz.service` FastAPI jarayonini faqat ichki `8011` portida ishga tushiradi, `deploy/nginx/train.shamsiyev.uz.conf` esa domen so'rovlarini unga uzatadi. Nginx statik fayllarni to'g'ridan-to'g'ri beradi.

DNS'da `train.shamsiyev.uz` A yozuvi AWS server IP manziliga yo'naltirilgandan so'ng, Let's Encrypt sertifikati Nginx orqali olinadi. `.env` Git'dan chetda qoladi va faqat ish muhiti sozlamalarini saqlaydi.
