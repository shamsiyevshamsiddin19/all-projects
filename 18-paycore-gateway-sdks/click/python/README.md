# Click to'lov integratsiyasi — Python

[Click](https://click.uz) (my.click.uz) to'lov tizimini **o'z loyihangizga**
qo'shish uchun tayyor fayllar. Merchant API — `prepare` / `complete`.

- 📁 **Papkani ko'chirasiz** — kutubxona o'rnatish, `pip install` yo'q
- 🗄️ **O'z bazangiz bilan ishlaydi** — bizning jadvalimiz yo'q, sizning
  `orders` jadvalingizga ulanadi
- ✏️ **Bitta fayl tahrirlanadi** — `click_orders.py`
- 🔒 Imzo tekshiruvi, takroriy callback himoyasi, atomar to'lov belgilash
- 🧪 21 ta test
- ⚙️ FastAPI, Flask, Django uchun namunalar

> `click_payment/` paketi faqat standart Python bilan ishlaydi (3.10+).
> Hech qanday tashqi paket kerak emas.

---

## AI bilan ulash (eng tez yo'l)

Loyihangizda AI ishlatasizmi (Claude Code, Cursor, Copilot, ChatGPT)? Repoda
[`AI_PROMPT.md`](AI_PROMPT.md) bor — AI uchun to'liq ko'rsatma. AI'ga shunday
deng:

```
click_payment papkasidagi AI_PROMPT.md ni o'qi va Click to'lovini
loyihamga to'liq ulab ber.
```

AI loyihangizni o'rganadi, `click_orders.py` ni bazangizga bog'laydi,
endpoint'larni qo'shadi, migratsiya yozadi va tekshiradi. Oxirida sizdan faqat
`.env` ga kabinetdan olingan 4 ta qiymatni qo'yish va Click kabinetiga
manzillarni yozish talab qilinadi.

Qo'lda ulamoqchi bo'lsangiz — quyidagi 3 qadam.

---

## 3 qadamda ulash

### 1-qadam: papkani ko'chiring

`click_payment/` papkasini o'z loyihangizga ko'chiring:

```
sizning_loyihangiz/
├── click_payment/          ← shu papkani ko'chiring
├── app.py
└── ...
```

### 2-qadam: `.env` ni to'ldiring

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Qiymatlarni [merchant.click.uz](https://merchant.click.uz) kabinetidan olasiz:

| O'zgaruvchi | Majburiy | Nima bu |
|---|:---:|---|
| `CLICK_SERVICE_ID` | ✅ | Xizmat (servis) ID — kabinet → Mening xizmatlarim |
| `CLICK_MERCHANT_ID` | ✅ | Savdogar raqamingiz — kabinet → Profil |
| `CLICK_SECRET_KEY` | ✅ | **Maxfiy kalit** — imzo shu bilan tekshiriladi |
| `CLICK_MERCHANT_USER_ID` | ✅ | Foydalanuvchi raqamingiz — kabinet → Profil |
| `CLICK_RETURN_URL` | ➖ | To'lovdan keyin qaytariladigan sahifangiz |
| `CLICK_PAY_BASE_URL` | ➖ | To'lov sahifasi manzili (odatda o'zgartirilmaydi) |
| `CLICK_DB_PATH` | ➖ | SQLite fayli — faqat namuna baza uchun |

> **`CLICK_SECRET_KEY`** — eng muhim qiymat. Uni bilgan odam soxta "to'landi"
> so'rovini yubora oladi. Kodga yozmang, loglarga chiqarmang, git'ga qo'shmang.
> `.env` allaqachon `.gitignore` da.

### 3-qadam: `click_orders.py` ni o'z bazangizga moslang

**Faqat shu faylni tahrirlaysiz.** Ichida 5 ta funksiya bor:

```python
# BAZA
def find_order(merchant_trans_id) -> Order | None:
    """Buyurtmani bazangizdan toping."""

def mark_paid(order, click_trans_id) -> bool:
    """UPDATE ... SET status='paid' WHERE id=? AND status='pending'
       va rowcount > 0 qaytaring."""

def mark_cancelled(order, click_trans_id) -> None:
    """Bekor qilingan deb belgilang."""

# HODISALAR
def on_paid(order) -> None:
    """To'lov o'tgach BIR MARTA chaqiriladi — mahsulotni shu yerda bering."""

def on_cancelled(order) -> None:
    """To'lov bekor bo'lganda (ixtiyoriy)."""
```

Fayl ichida SQLite bilan ishlaydigan namuna turibdi — klon qilib darrov sinab
ko'rasiz. Fayl **oxirida** PostgreSQL, MySQL, Django ORM va SQLAlchemy uchun
tayyor namunalar bor.

Buyurtmangizga bitta ustun qo'shishingiz kerak bo'ladi:

```sql
ALTER TABLE orders ADD COLUMN merchant_trans_id VARCHAR(64) UNIQUE;
ALTER TABLE orders ADD COLUMN click_trans_id VARCHAR(64);
```

---

## Endpoint'larni qo'shish

Click ikkita manzilga so'rov yuboradi. Loyihangizga shu ikkitasini qo'shasiz:

<details open>
<summary><b>FastAPI</b></summary>

```python
from fastapi import FastAPI, Request
from click_payment import handle_prepare, handle_complete

app = FastAPI()

@app.post("/click/prepare")
async def click_prepare(request: Request):
    return handle_prepare(dict(await request.form()))

@app.post("/click/complete")
async def click_complete(request: Request):
    return handle_complete(dict(await request.form()))
```

To'liq namuna: [`examples/fastapi_app.py`](examples/fastapi_app.py)
</details>

<details>
<summary><b>Flask</b></summary>

```python
from flask import Flask, jsonify, request
from click_payment import handle_prepare, handle_complete

app = Flask(__name__)

@app.post("/click/prepare")
def click_prepare():
    return jsonify(handle_prepare(request.form.to_dict()))

@app.post("/click/complete")
def click_complete():
    return jsonify(handle_complete(request.form.to_dict()))
```

To'liq namuna: [`examples/flask_app.py`](examples/flask_app.py)
</details>

<details>
<summary><b>Django</b></summary>

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from click_payment import handle_prepare, handle_complete

@csrf_exempt
def click_prepare_view(request):
    return JsonResponse(handle_prepare(request.POST.dict()))

@csrf_exempt
def click_complete_view(request):
    return JsonResponse(handle_complete(request.POST.dict()))
```

`@csrf_exempt` shart — so'rov Click serveridan keladi, brauzerdan emas.

To'liq namuna: [`examples/django_views.py`](examples/django_views.py)
</details>

Keyin Click kabinetiga shu manzillarni yozasiz:

```
Prepare URL:   https://sizning-domen.uz/click/prepare
Complete URL:  https://sizning-domen.uz/click/complete
```

Domen **HTTPS** bo'lishi shart. Lokal sinash uchun [ngrok](https://ngrok.com)
kabi tunnel ishlating.

## To'lov havolasini yasash

```python
from click_payment import payment_url

url = payment_url("ORD42", 5000)      # merchant_trans_id, summa (so'mda)
# foydalanuvchini `url` ga yuboring
```

`merchant_trans_id` ("ORD42") — sizning to'lov identifikatoringiz. Bazangizda
**unikal** bo'lishi shart; Click uni prepare/complete so'rovlarida qaytarib
yuboradi va siz shu orqali buyurtmani topasiz.

---

## Sinab ko'rish

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn examples.fastapi_app:app --port 8000
```

```bash
curl -X POST "http://localhost:8000/orders?product=Kitob&amount=5000"
# {"merchant_trans_id":"ORD1","amount":5000,"pay_url":"https://my.click.uz/services/pay?..."}
```

`pay_url` ni brauzerda oching.

Testlar:

```bash
pip install pytest
python -m pytest -v
```

---

## To'lov qanday o'tadi

```
  Foydalanuvchi          Sizning serveringiz              Click serveri
       │                         │                              │
       │  "sotib olaman"         │                              │
       ├────────────────────────>│                              │
       │                         │  payment_url(...)            │
       │      pay_url            │  (bazada: pending)           │
       │<────────────────────────┤                              │
       │                                                        │
       │  Click sahifasida kartasini tasdiqlaydi                │
       ├───────────────────────────────────────────────────────>│
       │                         │                              │
       │                         │   POST /click/prepare        │
       │                         │<─────────────────────────────┤
       │                         │  imzo + summa tekshiriladi   │
       │                         │  find_order()                │
       │                         │  error: 0, prepare_id: 42    │
       │                         ├─────────────────────────────>│
       │                         │                              │
       │                         │           💰 pul yechiladi    │
       │                         │                              │
       │                         │   POST /click/complete       │
       │                         │<─────────────────────────────┤
       │                         │  mark_paid()  -> True        │
       │                         │  on_paid()    -> mahsulot!   │
       │                         │  error: 0                    │
       │                         ├─────────────────────────────>│
       │  return_url ga qaytadi  │                              │
       │<───────────────────────────────────────────────────────┤
```

**prepare** — "bu to'lovni qabul qila olasanmi?" Pul hali yechilmagan.
**complete** — "pul yechildi, mahsulotni ber." `on_paid()` shu yerda ishlaydi.

---

## Imzo (sign_string)

Click har bir so'rovni md5 imzo bilan yuboradi:

```
prepare  (action=0):
    md5(click_trans_id + service_id + secret_key + merchant_trans_id
        + amount + action + sign_time)

complete (action=1):
    md5(click_trans_id + service_id + secret_key + merchant_trans_id
        + merchant_prepare_id + amount + action + sign_time)
```

Yagona farq — complete'da `merchant_trans_id` bilan `amount` orasiga
`merchant_prepare_id` qo'shiladi.

> ⚠️ **Eng ko'p uchraydigan xato:** `amount` imzoga Click yuborgan **xom satr**
> holida kirishi kerak. Click `"5000.00"` yuborsa, uni `float` ga o'girib
> qaytadan satrga aylantirsangiz `"5000.0"` bo'lib qoladi va imzo mos kelmaydi.
> Bu kod `amount` ga tegmaydi.

## Xato kodlari

| Kod | Ma'nosi | Qachon |
|---:|---|---|
| `0` | Success | Hammasi joyida |
| `-1` | SIGN CHECK FAILED | Imzo yoki `service_id` mos kelmadi |
| `-2` | Incorrect parameter amount | Summa bazadagidan farq qiladi |
| `-3` | Action not found | — |
| `-4` | Already paid | Allaqachon to'langan |
| `-5` | User does not exist | `merchant_trans_id` topilmadi |
| `-6` | Transaction does not exist | `merchant_prepare_id` mos emas |
| `-7` | Failed to update user | — |
| `-8` | Error in request from click | Majburiy maydon yetishmayapti |
| `-9` | Transaction cancelled | To'lov bekor qilingan |

---

## Xavfsizlik — e'tibor bering

1. **`return_url` ga tushish "to'landi" degani EMAS.** U foydalanuvchi
   brauzeridan keladi va uni qo'lda yozib qo'yish mumkin. To'lovni faqat Click
   serveridan kelgan `complete` so'rovi tasdiqlaydi. Natija sahifasida holatni
   **bazangizdan** o'qing.

2. **`mark_paid()` atomar bo'lsin.** Click javobni ololmasa complete'ni qayta
   yuboradi (ba'zan bir vaqtda). Shartni SQL'ning o'ziga qo'ying —
   `WHERE id=? AND status='pending'` — va `rowcount > 0` qaytaring. Aks holda
   mahsulot ikki marta beriladi.

3. **`action` so'rovdan olinmaydi.** Imzo tekshirilganda endpoint qaysi bo'lsa,
   o'shanikini (`0` yoki `1`) ishlatamiz. Aks holda prepare uchun olingan imzoni
   complete so'roviga qo'yib yuborish mumkin bo'lardi.

4. **Summa har doim bazadan tekshiriladi** — so'rovdagi `amount` ga ishonmaymiz.

5. **`on_paid()` ichida uzoq ish qilmang.** Click javobni kutib turadi. Og'ir
   ishni navbatga (queue/celery) qo'ying.

---

## Fayllar

```
click_payment/              ← loyihangizga shu papkani ko'chiring
├── click_orders.py         ← FAQAT SHUNI TAHRIRLAYSIZ (bazangizga ulanish)
├── click_prepare.py        prepare so'rovi
├── click_complete.py       complete so'rovi
├── click_signature.py      imzo qurish/tekshirish
├── click_config.py         .env + to'lov havolasi
├── click_errors.py         Click xato kodlari
└── click_utils.py          kichik yordamchilar

examples/                   loyihangizga qanday ulashning namunalari
├── fastapi_app.py
├── flask_app.py
└── django_views.py

tests/test_click.py
.env.example                ← sozlamalar
AI_PROMPT.md                ← AI'ga beriladigan ko'rsatma
```

## Litsenziya

MIT
