# Payme to'lov integratsiyasi — Python

[Payme](https://payme.uz) (checkout.paycom.uz / business.payme.uz) to'lov
tizimining **Merchant API** integratsiyasi. Sof Python — hech qanday tashqi
paket kerak emas.

- ✅ Oltita metod to'liq: `CheckPerformTransaction`, `CreateTransaction`,
  `PerformTransaction`, `CancelTransaction`, `CheckTransaction`, `GetStatement`
- ✅ HTTP Basic Auth tekshiruvi — timing-safe
- ✅ 12 soatlik avtomatik timeout (tranzaksiya muddati)
- ✅ To'langandan keyingi bekor qilish (qaytarish/refund) qo'llab-quvvatlanadi
- ✅ Takroriy so'rovlarga chidamli (idempotent — mahsulot ikki marta berilmaydi)
- ✅ FastAPI, Flask, Django uchun tayyor endpoint
- ✅ Tayyor SQLite saqlagich + o'z bazangizni ulash imkoni
- ✅ 31 ta test

> Bu repo'da [Click](../../click/python) integratsiyasi ham bor — ikkalasi
> bir xil naqshda qurilgan, lekin protokollari TUBDAN farq qiladi (quyiga
> qarang).

---

## Payme Click'dan nimasi bilan farq qiladi

| | Click | Payme |
|---|---|---|
| Endpoint soni | 2 (`prepare`, `complete`) | **1** (hammasi `method` maydoniga qarab) |
| Autentifikatsiya | `sign_string` (md5 imzo) | **HTTP Basic Auth** (`Paycom:secret_key`) |
| Summa birligi | so'm | **tiyin** (1 so'm = 100 tiyin) |
| Metodlar soni | 2 | **6** |
| Muddat | yo'q | **12 soat** — shundan keyin avtomatik bekor bo'ladi |
| To'langandan keyin bekor qilish | yo'q | **bor** (`CancelTransaction`, qaytarish) |
| To'lov havolasi | query-string | **base64** kodlangan `key=value;...` |

---

## 1. O'rnatish

```bash
pip install -r requirements.txt
```

## 2. `.env` sozlash

```bash
cp .env.example .env           # Windows: copy .env.example .env
```

Qiymatlarni [business.payme.uz](https://business.payme.uz) kabinetidan olasiz:

| O'zgaruvchi | Majburiy | Nima bu |
|---|---|---|
| `PAYME_MERCHANT_ID` | ✅ | Kassa ID — to'lov havolasida ishlatiladi |
| `PAYME_SECRET_KEY` | ✅ | **Maxfiy kalit** — har bir so'rov shu bilan tasdiqlanadi |
| `PAYME_MERCHANT_LOGIN` | ➖ | Odatda `Paycom` (standart qiymat) |
| `PAYME_CHECKOUT_BASE_URL` | ➖ | Odatda o'zgartirilmaydi |
| `PAYME_DB_PATH` | ➖ | SQLite fayli (demo tranzaksiya kundaligi uchun) |

> **`PAYME_SECRET_KEY` — eng muhim qiymat.** Click'dagi kabi imzo emas,
> to'g'ridan-to'g'ri parol sifatida ishlatiladi. Kodga yozmang, git'ga
> qo'shmang. Bir marta ochilib qolsa kabinetdan darhol yangilang.

## 3. Yagona endpoint'ni Payme kabinetiga yozing

```
https://sizning-domen.uz/payme
```

Payme boshqa to'lov tizimlaridan farqli — hamma metod (`CheckPerformTransaction`,
`CreateTransaction`, ...) shu **bitta** manzilga POST qiladi, `method` maydoni
orqali farqlanadi.

---

## Kodda ishlatish

```python
from payme_payment import handle_request, checkout_url, som_to_tiyin
from payme_payment import payme_orders as orders

# 1) Buyurtma yaratamiz va to'lov havolasini yasaymiz
url = checkout_url({"order_id": order.id}, som_to_tiyin(order.price_som))
# foydalanuvchini shu havolaga yuboring

# 2) Yagona endpoint (FastAPI namunasi)
@app.post("/payme")
async def payme_webhook(request: Request, authorization: str = Header(None)):
    body = await request.json()
    return handle_request(body, authorization)
```

`payme_orders.py` dagi `on_paid()` funksiyasi to'lov tasdiqlangach chaqiriladi
— mahsulotni shu yerda berasiz.

---

## To'lov oqimi

```
  Foydalanuvchi          Sizning serveringiz              Payme serveri
       │                         │                              │
       │  checkout_url() havolasi│                              │
       ├────────────────────────>│                              │
       │   pay_url                                              │
       │<────────────────────────┤                              │
       │                                                        │
       │  Payme sahifasida kartani tasdiqlaydi                  │
       ├───────────────────────────────────────────────────────>│
       │                         │                              │
       │                         │ POST /payme                  │
       │                         │  method: CheckPerformTransaction
       │                         │<─────────────────────────────┤
       │                         │  order bor, summa mos, allow:true
       │                         ├─────────────────────────────>│
       │                         │                              │
       │                         │ POST /payme                  │
       │                         │  method: CreateTransaction   │
       │                         │<─────────────────────────────┤
       │                         │  state: 1 (pending)          │
       │                         ├─────────────────────────────>│
       │                         │                              │
       │                         │        💰 pul yechiladi       │
       │                         │                              │
       │                         │ POST /payme                  │
       │                         │  method: PerformTransaction  │
       │                         │<─────────────────────────────┤
       │                         │  on_paid() -> mahsulot!      │
       │                         │  state: 2 (paid)              │
       │                         ├─────────────────────────────>│
```

**CheckPerformTransaction** — "bu to'lovni qabul qila olasanmi?" Pul hali
yechilmagan.
**CreateTransaction** — Payme tranzaksiya ochadi (bizning "prepare"imiz).
**PerformTransaction** — pul yechildi, tasdiqla (bizning "complete"imiz).
`on_paid()` shu yerda ishlaydi.

Qo'shimcha ikkita metod har doim ham ishlatilmaydi, lekin protokol talab
qiladi: **CheckTransaction** (Payme holatni so'rasa) va **GetStatement**
(Payme kabinetidagi hisobot uchun tranzaksiyalar ro'yxatini so'rasa).

---

## Autentifikatsiya (Basic Auth)

Click imzo bilan ishlagan bo'lsa, Payme oddiy HTTP Basic Auth ishlatadi:

```
Authorization: Basic base64("Paycom:MAXFIY_KALIT")
```

Login har doim `Paycom` (kabinetda boshqacha ko'rsatilmagan bo'lsa). Bu
`payme_auth.py` da avtomatik tekshiriladi — sizga tegishli emas.

## Summa — TIYINDA

Payme summani **tiyinda** kutadi (1 so'm = 100 tiyin), Click esa so'mda edi.
`som_to_tiyin()` yordamchisi bor:

```python
som_to_tiyin(5000)   # -> 500000
```

`payme_orders.py` dagi `PaymeAccount.amount` ham TIYIN bo'lishi kerak.

## 12 soatlik muddat

Agar foydalanuvchi `CreateTransaction` dan keyin 12 soat ichida to'lamasa,
tranzaksiya avtomatik bekor qilinadi (`state=-1`, `reason=4`). Bu kutubxona
ichida avtomatik amalga oshadi — sizga hech narsa qilish kerak emas.

## To'langandan keyin bekor qilish (refund)

Click'da bunday imkoniyat yo'q edi. Payme'da `CancelTransaction` to'langan
(`state=2`) tranzaksiyani ham bekor qila oladi — natijada `state=-2` bo'ladi.
Bu — pul qaytarish. `payme_orders.py` dagi `can_refund()` orqali buni
taqiqlashingiz mumkin (masalan darhol yuklab olinadigan fayl uchun).

## Xato kodlari

| Kod | Ma'nosi | Qachon |
|---:|---|---|
| `-32700` | JSON parsing xatosi | So'rov JSON emas |
| `-32600` | Majburiy maydon yo'q | `method`/`params` shakli noto'g'ri |
| `-32601` | Metod topilmadi | Noma'lum `method` |
| `-32504` | Avtorizatsiya xato | Basic Auth login/parol mos emas |
| `-32400` | Ichki xato | Kutilmagan server xatosi |
| `-31001` | Noto'g'ri summa | Bazadagi narx bilan mos emas |
| `-31003` | Tranzaksiya topilmadi | Noma'lum `id` |
| `-31007` | Bekor qilib bo'lmaydi | `can_refund()` `False` qaytardi |
| `-31008` | Amalni bajarib bo'lmaydi | Holat nomos yoki muddat o'tgan |
| `-31050` | Buyurtma topilmadi | `find_account()` `None` qaytardi |
| `-31099` | Allaqachon to'langan / tranzaksiya bor | Ikkinchi urinish |

---

## O'z bazangizni ulash

`payme_orders.py` dagi 4 ta biznes funksiyani (`find_account`, `on_paid`,
`on_cancelled`, `can_refund`) o'zgartirasiz. Tranzaksiya kundaligi (Payme
talab qiladigan CheckTransaction/GetStatement uchun) demo SQLite bilan keladi
— fayl oxirida PostgreSQL namunasi bor.

---

## Xavfsizlik — e'tibor bering

1. **`PAYME_SECRET_KEY` faqat `.env` da.** Click'dagidan farqli, bu to'g'ridan
   to'g'ri parol — sizib chiqsa, xohlagan odam soxta to'lov yubora oladi.
2. **Har bir metodda `mark_performed`/`mark_cancelled` atomar.** Parallel
   kelgan takroriy so'rov `on_paid()` ni qayta chaqirmasligi shart —
   `payme_orders.py` dagi `rowcount` tekshiruviga qarang.
3. **Summani har doim bazadan tekshiring** — `CheckPerformTransaction` va
   `CreateTransaction` buni avtomatik qiladi.
4. **`can_refund()` orqali qaytarib bo'lmaydigan mahsulotlarni himoya qiling.**

---

## Testlar

```bash
pip install pytest
python -m pytest -v
# 31 passed
```

## Tuzilishi

```
payme/python/
├── .env.example
├── requirements.txt
├── payme_payment/
│   ├── payme_config.py       # .env dan o'qish
│   ├── payme_auth.py         # Basic Auth tekshiruvi
│   ├── payme_checkout.py     # to'lov havolasi (base64)
│   ├── payme_errors.py       # Payme xato kodlari
│   ├── payme_orders.py       # ← SIZ TAHRIRLAYSIZ (bazangizga ulanish)
│   └── payme_methods.py      # 6 metod + JSON-RPC dispatcher
├── examples/
│   ├── quickstart_fastapi.py
│   ├── flask_app.py
│   └── django_views.py
└── tests/
    └── test_payme.py
```
