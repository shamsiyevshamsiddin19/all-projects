# Uzum Bank to'lov integratsiyasi — Python

[Uzum Bank](https://uzumbank.uz) Merchant API integratsiyasi — 5 webhook
(`check`, `create`, `confirm`, `reverse`, `status`). Sof Python — asosiy
kutubxona uchun hech qanday tashqi paket kerak emas.

> ⚠️ **Uzum Bank Click/Payme'dan tubdan farq qiladi**: bu yerda "to'lov
> havolasi" (checkout URL) YO'Q. Foydalanuvchi Uzum Bank ilovasida
> xizmatingizni `service_id` orqali qidirib topadi va to'lovni O'SHA YERDA
> boshlaydi. Sizning serveringiz faqat 5 ta webhook so'roviga javob beradi —
> pastga qarang.

- ✅ 5 webhook to'liq — imzo o'rniga HTTP Basic Auth
- ✅ Uzum Bank'ning **idempotent-emas** protokoliga mos: takroriy
  `/create`/`/confirm` aniq xato qaytaradi (Click/Payme'dan farqli!)
- ✅ 30 daqiqalik avtomatik muddat tekshiruvi
- ✅ To'langandan keyin bekor qilish (refund) qo'llab-quvvatlanadi
- ✅ FastAPI va Flask uchun tayyor endpoint'lar
- ✅ 27 test

---

## 1. O'rnatish

```bash
pip install -r requirements.txt
cp .env.example .env
```

## 2. `.env` sozlash

| O'zgaruvchi | Nima bu | Qayerdan olinadi |
|---|---|---|
| `UZUM_SERVICE_ID` | Xizmat ID — foydalanuvchi sizni shu orqali topadi | Kabinet |
| `UZUM_WEBHOOK_LOGIN` | Webhook so'rovlarini tasdiqlash uchun login | Kabinetda o'zingiz belgilaysiz |
| `UZUM_WEBHOOK_SECRET` | Webhook so'rovlarini tasdiqlash uchun parol | Kabinetda o'zingiz belgilaysiz |

> Payme'dan farqli — login "Paycom" kabi qat'iy belgilanmagan, ikkalasini
> ham (login va parol) kabinetda O'ZINGIZ o'rnatasiz.

## 3. Kabinetga callback manzilini yozish

Kabinetda BITTA bazaviy manzil so'raladi:

```
https://sizning-domen.uz/uzum
```

Uzum Bank shu manzilga `/check`, `/create`, `/confirm`, `/reverse`, `/status`
qo'shib so'rov yuboradi. Domen **HTTPS** bo'lishi shart.

## 4. Ishga tushirish

```bash
uvicorn examples.quickstart_fastapi:app --port 8000
```

---

## To'lov qanday o'tadi

Click/Payme'da foydalanuvchi SIZNING saytingizdan boshlaydi. Uzum Bank'da —
**teskarisi**: foydalanuvchi Uzum Bank ilovasida sizni qidiradi.

```
  Foydalanuvchi          Uzum Bank ilovasi         Sizning serveringiz
       │                         │                          │
       │  xizmatni qidiradi      │                          │
       │  (service_id orqali)    │                          │
       ├────────────────────────>│                          │
       │  "account" kiritadi     │                          │
       │  (masalan buyurtma №)   │                          │
       ├────────────────────────>│                          │
       │                         │      POST /check          │
       │                         │─────────────────────────>│
       │                         │      status: OK           │
       │                         │<─────────────────────────┤
       │                         │                          │
       │                         │      POST /create         │
       │                         │─────────────────────────>│
       │                         │      status: CREATED      │
       │                         │<─────────────────────────┤
       │                         │                          │
       │                         │   💰 pul yechiladi         │
       │                         │                          │
       │                         │      POST /confirm        │
       │                         │─────────────────────────>│
       │                         │   (mahsulot shu yerda     │
       │                         │    beriladi — on_confirmed)│
       │                         │      status: CONFIRMED    │
       │                         │<─────────────────────────┤
       │   "To'landi" ko'radi    │                          │
       │<────────────────────────┤                          │
```

**`/confirm` kelganda pul ALLAQACHON yechilgan** (Click/Payme'da esa
`complete`/`perform` — bu deduksiya signalining o'zi). Shuning uchun
`on_confirmed()` xato bersa ham to'lov qaytarilmaydi — faqat mahsulot berish
jarayoni chalasi qoladi va buni logdan kuzatasiz.

Agar `/confirm` javob bermasa (server xatosi, timeout), Uzum Bank **`/status`
bilan 10 martagacha so'raydi**, siz `CONFIRMED` yoki `FAILED` qaytarguningizcha.

---

## ⚠️ Eng muhim farq: takroriy so'rov = XATO, muvaffaqiyat emas

Click va Payme'da takroriy `complete`/`PerformTransaction` "idempotent" —
bir xil muvaffaqiyat natijasini qaytarasiz. **Uzum Bank'da BUNDAY EMAS.**
Rasmiy hujjat aniq yozgan:

> "Верните этот код (`10010`) при повторном создании транзакции с тем же
> `transId`" — ya'ni takroriy `/create` uchun **xato qaytaring**.

Xuddi shunday: takroriy `/confirm` → `10016`, takroriy `/reverse` → `10018`.
Kod buni to'g'ri bajaradi — `test_create_duplicate_returns_error_not_idempotent`
va `test_confirm_duplicate_returns_error_not_idempotent` testlariga qarang.

## 30 daqiqalik muddat

Agar `/create` dan keyin 30 daqiqa ichida `/confirm` kelmasa, tranzaksiya
"muvaffaqiyatsiz" hisoblanadi — **buni Uzum Bank alohida xabar bermaydi,
buni SIZ o'zingiz kuzatishingiz kerak** (Payme'da esa 12 soatlik muddat ham
xuddi shu tarzda o'zingiz kuzatiladigan tamoyilda). Kod bu tekshiruvni
`/confirm` va `/status` ichida avtomatik bajaradi.

---

## Xato kodlari

| Kod | Ma'nosi | Qaysi metodda |
|---:|---|---|
| `10001` | Ruxsat yo'q (auth xato) | hammasi |
| `10002` | JSON parse xato | hammasi |
| `10003` | Noto'g'ri HTTP metod | hammasi |
| `10005` | Majburiy maydon yo'q | hammasi |
| `10006` | Noto'g'ri `serviceId` | check, create |
| `10007` | Hisob (buyurtma) topilmadi | check, create |
| `10008` | Allaqachon to'langan | check, create |
| `10009` | To'lov bekor qilingan | check, create |
| `10010` | Bu `transId` bilan tranzaksiya allaqachon bor | create |
| `10011` | Noto'g'ri summa | create |
| `10012` | Summa minimaldan kam | create |
| `10013` | Summa maksimaldan ko'p | create |
| `10014` | Tranzaksiya topilmadi | confirm, reverse, status |
| `10015` | Tranzaksiya bekor qilingan | confirm |
| `10016` | Allaqachon tasdiqlangan | confirm |
| `10017` | Bekor qilib bo'lmaydi | reverse |
| `10018` | Allaqachon bekor qilingan | reverse |
| `99999` | Ichki server xatosi | hammasi |

---

## Sinab ko'rish

```bash
python -m pytest -v
# 27 passed
```

---

## Fayllar

```
uzum_payment/
├── uzum_orders.py     ← FAQAT SHUNI TAHRIRLAYSIZ (bazangizga ulanish)
├── uzum_methods.py     5 webhook handleri
├── uzum_auth.py         Basic Auth tekshiruvi
├── uzum_config.py       .env
├── uzum_errors.py       xato kodlari
└── __init__.py

examples/
├── quickstart_fastapi.py
└── flask_app.py

tests/test_uzum.py
.env.example
AI_PROMPT.md            ← AI'ga beriladigan ko'rsatma
```

Boshqa tillar: [`../php`](../php) · [`../typescript`](../typescript)
Boshqa to'lov tizimlari: [`../../click`](../../click) · [`../../payme`](../../payme)

## Litsenziya

MIT
