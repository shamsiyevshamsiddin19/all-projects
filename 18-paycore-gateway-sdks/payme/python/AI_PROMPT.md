# Payme to'lovini loyihaga ulash — AI uchun ko'rsatma

> **Foydalanuvchi uchun:** bu faylni o'zingiz o'qishingiz shart emas.
> AI'ga (Claude Code, Cursor, Copilot, ChatGPT...) shunday deng:
>
> ```
> payme_payment papkasidagi AI_PROMPT.md ni o'qi va Payme to'lovini
> loyihamga to'liq ulab ber.
> ```
>
> AI qolganini o'zi qiladi va oxirida sizdan nima talab qilinishini aytadi.

---

## Topshiriq

Sen shu loyihaga Payme (checkout.paycom.uz) to'lov tizimini **to'liq
ishlaydigan** holatda ulaysan. `payme_payment/` paketi tayyor — sen uni
loyihaning bazasi va framework'iga bog'laysan.

Ishni **taxmin qilib emas, loyihani o'qib** boshla.

Agar shu loyihada allaqachon [Click integratsiyasi](../../click/python)
ulangan bo'lsa, o'sha `click_orders.py` faylini ham o'qib chiq — Payme uchun
bir xil buyurtma jadvaliga ulanasan, tuzilishni takrorlama.

---

## 0-qadam: loyihani o'rgan

1. **Framework** — FastAPI / Flask / Django / aiohttp?
2. **Baza** — PostgreSQL / MySQL / SQLite? Qaysi kutubxona orqali?
3. **Buyurtma jadvali** — narx qaysi ustunda, qaysi turda (integer/decimal)?
   Payme summani **TIYINDA** kutadi (1 so'm = 100 tiyin) — bazangizda so'mda
   saqlangan bo'lsa, `find_account()` ichida `* 100` qilishni unutma.
4. **"Mahsulot berish" nima degani** — mavjud funksiyani ishlat, yangisini yozma.
5. **Auth/middleware** — global auth bo'lsa, `/payme` manzilini istisno qil.
6. **Click integratsiyasi bormi?** — bo'lsa, bitta `orders`/`payments`
   jadvalidan ikkalasi ham foydalanishi mumkin (Click `merchant_trans_id`,
   Payme `order_id` orqali).

Aniqlanmasa — **foydalanuvchidan so'ra**, taxmin qilma.

---

## 1-qadam: paketni joylashtir

`payme_payment/` papkasini loyihaga ko'chir. `import payme_payment`
ishlashini tekshir.

---

## 2-qadam: `.env`

```
PAYME_MERCHANT_ID=
PAYME_SECRET_KEY=
```

- Qiymatlarni **sen to'ldirmaysan** — foydalanuvchi business.payme.uz
  kabinetidan oladi.
- `PAYME_MERCHANT_LOGIN` odatda "Paycom" — o'zgartirmang, faqat kabinetda
  aniq boshqacha ko'rsatilgan bo'lsa.
- `.env` `.gitignore` da borligini tekshir.

---

## 3-qadam: bazaga tranzaksiya kundaligi jadvali qo'sh

Payme protokoli (Click'dan farqli) o'z tranzaksiya kundaligini talab qiladi
— bu ixtiyoriy emas, `CheckTransaction`/`GetStatement` shunga tayanadi:

```sql
CREATE TABLE payme_transactions (
    payme_id     VARCHAR(32) PRIMARY KEY,
    our_id       VARCHAR(32) NOT NULL,
    account_json TEXT NOT NULL,
    amount       BIGINT NOT NULL,      -- TIYINDA
    state        SMALLINT NOT NULL,    -- 1/2/-1/-2
    payme_time   BIGINT NOT NULL,      -- ms
    create_time  BIGINT NOT NULL,      -- ms
    perform_time BIGINT NOT NULL DEFAULT 0,
    cancel_time  BIGINT NOT NULL DEFAULT 0,
    reason       SMALLINT
);
CREATE INDEX idx_payme_tx_create_time ON payme_transactions(create_time);
```

Loyihada migratsiya tizimi bo'lsa (Alembic, Django migrations) — migratsiya
fayli yarat.

---

## 4-qadam: `payme_orders.py` ni loyiha bazasiga bog'la

**Ikki guruh funksiya bor.**

### A) Biznes funksiyalar — bularni albatta o'zgartirasan

`find_account(account: dict) -> PaymeAccount | None`
- `account` — Payme yuborgan `{"order_id": "42"}` kabi dict
- Buyurtmani top, `PaymeAccount(id, amount, payable, extra)` qaytar
- `amount` — TIYINDA! Bazangizda so'mda saqlangan bo'lsa `* 100` qil
- `payable=False` qo'y — agar buyurtma allaqachon to'langan/bekor bo'lsa
- Topilmasa `None`

`on_paid(transaction: PaymeTransaction) -> None`
- Mahsulotni ber. `transaction.account["order_id"]` orqali buyurtmani top
- Uzoq ish qilma — Payme javobni kutib turadi

`on_cancelled(transaction: PaymeTransaction) -> None`
- `transaction.state == STATE_CANCELLED_AFTER_PAID` bo'lsa — bu QAYTARISH
  (pul allaqachon berilgan edi). Mahsulotga ruxsatni bekor qil.

`can_refund(transaction: PaymeTransaction) -> bool`
- To'langan tranzaksiyani bekor qilish (pul qaytarish) mumkinmi?
- Standart: har doim `True`. Qaytarib bo'lmaydigan mahsulot bo'lsa `False`.

### B) Tranzaksiya kundaligi — Payme'ning o'zi talab qiladi

`get_transaction`, `get_active_transaction_for_account`, `create_transaction`,
`mark_performed`, `mark_cancelled`, `list_transactions` — bular ledger CRUD.
Demo SQLite ishlatadi. O'z bazangizga o'tkazganda **atomarlikni saqla**:

```python
# TO'G'RI — atomar (rowcount tekshiriladi)
def mark_performed(payme_id):
    cur = db.execute(
        "UPDATE payme_transactions SET state=2, perform_time=%s "
        "WHERE payme_id=%s AND state=1",
        (now_ms(), payme_id),
    )
    if cur.rowcount == 0:
        return None      # <- allaqachon to'langan, on_paid QAYTA chaqirilmaydi
    return get_transaction(payme_id)
```

Bu — Click'dagi `mark_paid` bilan bir xil qoida: shartni SQL'ning o'ziga
qo'y, avval o'qib keyin yozma.

---

## 5-qadam: yagona endpoint qo'sh

Payme'da Click'dagidek IKKITA emas, **BITTA** endpoint bor — hamma metod
`method` maydoni orqali farqlanadi:

```python
from payme_payment import handle_request

@app.post("/payme")
async def payme_webhook(request: Request, authorization: str = Header(None)):
    body = await request.json()
    return handle_request(body, authorization)
```

Kabinetga yoziladigan yagona manzil: `https://<domen>/payme`

### Auth haqida

- So'rov Payme serveridan keladi, login qila olmaydi.
- Xavfsizlik **HTTP Basic Auth** orqali (`payme_auth.py` avtomatik
  tekshiradi) — Click'dagi imzo emas.
- Global auth middleware bo'lsa `/payme` ni istisno qil, aks holda ikki xil
  auth to'qnashib, Payme har doim 401/403 oladi.

---

## 6-qadam: to'lov havolasi

```python
from payme_payment import checkout_url, som_to_tiyin

url = checkout_url({"order_id": order.id}, som_to_tiyin(order.price_som))
```

`som_to_tiyin()` ni unutma — Payme summani so'mda emas, TIYINDA kutadi.

---

## 7-qadam: tekshir — bu qadamni o'tkazib yuborma

1. **Testlarni moslab ishlatib ko'r.**

   `tests/test_payme.py` demo SQLite bazasiga tayangan (`demo_create_order`,
   `reset_db_for_tests`). `payme_orders.py` ni o'zgartirganingdan keyin ular
   ishlamaydi — testlarni loyihaning test bazasiga moslab yoz, keyin:

   ```
   python -m pytest -v
   ```

2. **`mark_performed` ikki marta `None` bo'lmagan natija qaytarmasligini tekshir:**

   ```python
   assert mark_performed(payme_id) is not None
   assert mark_performed(payme_id) is None   # <- shu SHART
   ```

3. **Barcha oltita metodni qo'lda sinab ko'r** (Basic Auth bilan):

   ```bash
   AUTH=$(echo -n "Paycom:SIZNING_KALIT" | base64)
   curl -X POST http://localhost:8000/payme \
     -H "Authorization: Basic $AUTH" \
     -H "Content-Type: application/json" \
     -d '{"method":"CheckPerformTransaction","params":{"amount":500000,"account":{"order_id":"42"}},"id":1}'
   ```

   Tekshir:
   - to'g'ri auth -> natija, noto'g'ri auth -> `-32504`
   - `CreateTransaction` -> `state: 1`
   - `PerformTransaction` -> `state: 2`, `on_paid()` chaqirilgani
   - takroriy `PerformTransaction` -> bir xil natija, `on_paid()` QAYTA chaqirilmagani
   - `CancelTransaction` to'langandan keyin -> `state: -2` (refund)

4. **12 soatlik muddatni sinash uchun** `payme_time` ni o'tmishga qo'yib
   `CreateTransaction`/`PerformTransaction` chaqir — `-31008` kelishi kerak.

---

## Qat'iy qoidalar

1. **Faqat `payme_orders.py` ni tahrirla.** `payme_methods.py`,
   `payme_auth.py`, `payme_checkout.py`, `payme_config.py`, `payme_errors.py`
   — tegma.
2. **Summa har doim TIYINDA.** So'm bilan aralashtirma.
3. **`PAYME_SECRET_KEY` ni kodga yozma, git'ga qo'shma.**
4. **`create_time` — server vaqti, Payme yuborgan `time` emas.** Kutubxona
   buni to'g'ri qiladi (`payme_orders.py`dagi `create_transaction`ga qara).
5. **Ikkinchi marta `CancelTransaction` chaqirilsa — sababni yangilama**,
   mavjud natijani qaytar (idempotentlik).

---

## Yakunda foydalanuvchiga ayt

1. `.env` ga `PAYME_MERCHANT_ID` va `PAYME_SECRET_KEY` ni kabinetdan olib
   qo'yish kerakligi.
2. Kabinetga yoziladigan **yagona** manzil: `https://<domen>/payme`.
3. Bazaga qo'shilgan `payme_transactions` jadvali / migratsiya.
4. `on_paid()` va `on_cancelled()` ichiga aniq nima yozganing.
5. Haqiqiy Payme kabineti (sandbox: test.paycom.uz) bilan sinov
   o'tkazilmagani.
