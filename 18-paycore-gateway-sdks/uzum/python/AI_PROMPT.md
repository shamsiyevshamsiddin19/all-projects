# Uzum Bank to'lovini loyihaga ulash — AI uchun ko'rsatma (Python)

> **Foydalanuvchi uchun:** bu faylni o'zingiz o'qishingiz shart emas.
> AI'ga (Claude Code, Cursor, Copilot, ChatGPT...) shunday deng:
>
> ```
> uzum/python papkasidagi AI_PROMPT.md ni o'qi va Uzum Bank to'lovini
> loyihamga to'liq ulab ber.
> ```

---

## Topshiriq

Sen shu loyihaga Uzum Bank Merchant API'ni **to'liq ishlaydigan** holatda
ulaysan. `uzum_payment/` paketi tayyor — sen uni loyihaning bazasiga
bog'laysan.

**Uzum Bank Click/Payme'dan tubdan farq qiladi — bu farqni tushunmasdan
boshlama:**

1. **To'lov havolasi YO'Q.** Foydalanuvchi Uzum Bank ilovasida
   xizmatingizni `service_id` orqali topadi va to'lovni O'SHA YERDA
   boshlaydi. Sen `checkout_url()` kabi funksiya YOZMAYSAN — bunday narsa
   Uzum Bank protokolida umuman mavjud emas.
2. **Beshta ALOHIDA endpoint kerak** (`/check`, `/create`, `/confirm`,
   `/reverse`, `/status`), Payme'dagi bitta JSON-RPC endpoint emas.
3. **Xato holatida HTTP 400 qaytariladi** (Click/Payme'da har doim 200).
4. **Takroriy so'rov = XATO, muvaffaqiyat emas.** Agar Uzum Bank bir xil
   `transId` bilan `/create` yoki `/confirm` ni ikkinchi marta yuborsa,
   to'g'ri javob — mos xato kodi (`10010` / `10016`), oldingi
   muvaffaqiyatni QAYTA qaytarish EMAS. Bu Click/Payme'dagi
   "idempotent — bir xil natijani qaytar" tamoyilidan TUBDAN farq qiladi.
   Kodda bu allaqachon to'g'ri qilingan — buni "tuzatib qo'ymang".

Ishni **taxmin qilib emas, loyihani o'qib** boshla.

---

## 0-qadam: loyihani o'rgan

1. **Framework** — FastAPI / Flask / Django / boshqa?
2. **Baza** — PostgreSQL / MySQL / SQLite? Qanday ORM?
3. **Buyurtma jadvali** — narx qaysi ustunda, qanday turda? Holat ustuni
   qanday qiymatlarni oladi?
4. **"Mahsulot berish" nima degani** — `on_confirmed()` ichida nima
   qilinishi kerak? Loyihada mavjud funksiya bormi?
5. **Auth middleware** — global himoya bormi? (5-qadamga qara.)

Aniqlanmasa — foydalanuvchidan so'ra, taxmin qilma.

---

## 1-qadam: paketni joylashtir

`uzum_payment/` papkasini loyihaga ko'chir. `import uzum_payment` ishlashini
tekshir.

---

## 2-qadam: `.env`

```
UZUM_SERVICE_ID=
UZUM_WEBHOOK_LOGIN=
UZUM_WEBHOOK_SECRET=
```

Qiymatlarni **sen to'ldirmaysan** — foydalanuvchi Uzum Bank kabinetidan
oladi. `.env` `.gitignore` da borligini tekshir.

---

## 3-qadam: bazaga ustun qo'sh

```sql
ALTER TABLE orders ADD COLUMN uzum_trans_id VARCHAR(64) NULL;
```

Bu ustun `uzum_orders.py` ichida sen yozadigan tranzaksiya kundaligi uchun
ishlatiladi (4-qadam).

---

## 4-qadam: `uzum_orders.py` ni loyiha bazasiga bog'la

**Faqat shu faylni tahrirlaysan.** Ichida:

### `find_account(params) -> UzumAccount | None`

`params` — Uzum Bank yuborgan foydalanuvchi kiritgan maydonlar (masalan
`{"account": "42"}`). Aniq qaysi maydon ishlatilishini foydalanuvchi Uzum
Bank kabinetida xizmatni sozlaganda belgilaydi (odatda buyurtma raqami yoki
lицевой счёt).

- `amount` — TIYINDA (1 so'm = 100 tiyin).
- `payable` — buyurtma hali to'lanmagan bo'lsa `True`.

### `on_confirmed(transaction)`

Mahsulotni shu yerda ber. **DIQQAT:** bu chaqirilganda pul ALLAQACHON
yechilgan (Uzum Bank `/confirm` dan oldin pulni yechadi). Xato bersa ham
pul qaytarilmaydi — faqat yetkazib berish jarayoni chalasi qoladi. Uzoq ish
qilma, navbatga uzat.

### `on_reversed(transaction)`

Bekor qilinganda (yoki qaytarilganda) chaqiriladi. Ixtiyoriy.

### Tranzaksiya kundaligi (`get_transaction`, `create_transaction`,
`mark_confirmed`, `mark_reversed`, `get_active_transaction_for_account`)

Bular Uzum Bank protokoli talab qiladigan bookkeeping — `/status` va
takroriy-so'rov-tekshiruvlari shularga tayanadi. Demo SQLite o'rniga o'z
bazangizni ulash namunasi fayl oxirida (PostgreSQL misolida).

**`mark_confirmed` va `mark_reversed` atomar bo'lishi SHART** —
`WHERE trans_id=? AND state=?` shartini SQL'ning o'ziga qo'y, `rowcount`
tekshir. Sabab Click/Payme'dagi bilan bir xil: parallel so'rovda mahsulot
ikki marta berilmasin.

---

## 5-qadam: BESHTA endpoint qo'sh

```python
from uzum_payment.uzum_methods import (
    handle_check, handle_create, handle_confirm, handle_reverse, handle_status,
)

# har biri (status_code, body_dict) qaytaradi — status_code AYNAN shu bilan javob bering
POST /uzum/check    -> handle_check(data, request.headers.get("Authorization"))
POST /uzum/create   -> handle_create(...)
POST /uzum/confirm  -> handle_confirm(...)
POST /uzum/reverse  -> handle_reverse(...)
POST /uzum/status   -> handle_status(...)
```

`examples/quickstart_fastapi.py` va `examples/flask_app.py` ga qarang.

**Endpoint'lar ochiq bo'lishi kerak** — so'rovlar Uzum Bank serveridan
keladi, foydalanuvchi brauzeridan emas. Global auth/CSRF bo'lsa, shu beshta
manzilni istisno qil. Xavfsizlik HTTP Basic Auth orqali ta'minlanadi —
`handle_*` funksiyalari ichida allaqachon tekshiriladi.

Kabinetga BITTA bazaviy manzil yoziladi:
```
https://<domen>/uzum
```
(Uzum Bank o'zi `/check`, `/create` va h.k. qo'shib chaqiradi — aniq shakl
kabinet interfeysiga qarab farq qilishi mumkin, foydalanuvchidan tasdiqlashini
so'ra.)

---

## 6-qadam: tekshir

1. **Testlarni moslab ishga tushir** — `tests/test_uzum.py` demo SQLite'ga
   tayangan. `uzum_orders.py` ni o'zgartirganingdan keyin moslab yoz, keyin
   `python -m pytest -v`.

2. **Takroriy so'rov haqiqatan xato qaytarishini tekshir** (bu eng ko'p
   noto'g'ri "tuzatiladigan" joy):
   ```python
   status, body = handle_create(data, auth)          # 200, CREATED
   status, body = handle_create(data, auth)           # 400, errorCode=10010 <- SHART
   ```
   Agar kimdir buni "idempotent qilib qo'yaman" deb o'zgartirsa — bu
   Uzum Bank hujjatiga zid, o'zgartirma.

3. **30 daqiqalik muddatni tekshir** — `/create` dan keyin vaqtni
   ilgari surib (`monkeypatch` yoki test uchun vaqtni qo'lda o'zgartirib)
   `/confirm` chaqirsang `10015` kelishi kerak.

4. **Auth'ni tekshir** — noto'g'ri `Authorization` header bilan so'rov
   yuborib, `400` va `10001` kelishini ko'r.

---

## Qat'iy qoidalar

1. **Faqat `uzum_orders.py` ni tahrirla.** `uzum_methods.py`, `uzum_auth.py`,
   `uzum_config.py`, `uzum_errors.py` — tegma.

2. **Checkout havolasi/URL FUNKSIYASINI O'YLAB TOPMA.** Uzum Bank'da bunday
   narsa yo'q. Agar foydalanuvchi "to'lov tugmasi" so'rasa, unga tushuntir:
   Uzum Bank'da foydalanuvchi ilova ichidan sizni topadi, sayt orqali emas.

3. **Takroriy so'rovni idempotent qilib "tuzatma"** — bu ataylab xato
   qaytaradi (yuqoriga qara).

4. **Summa TIYINDA** — Click ham, Uzum Bank ham tiyinda ishlaydi (Payme
   ham). So'm bilan aralashtirma: `amount_tiyin = amount_som * 100`.

5. **`secret_key`/parolni kodga yozma, git'ga qo'shma.**

---

## Yakunda foydalanuvchiga ayt

1. `.env` ga qaysi 3 ta qiymatni kabinetdan olib qo'yish kerakligi.
2. Kabinetga yoziladigan callback manzil.
3. Bazaga qo'shilgan ustun / migratsiya.
4. `on_confirmed()` ichiga aniq nima yozganing.
5. Uzum Bank'da to'lov havolasi yo'qligini, foydalanuvchi ilova ichidan
   to'lashini tushuntirganingni.
6. Nimani tekshirganing va nimani tekshira olmaganing (haqiqiy Uzum Bank
   kabineti/sandbox bilan sinov o'tkazilmagan).
