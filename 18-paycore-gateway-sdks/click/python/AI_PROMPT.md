# Click to'lovini loyihaga ulash — AI uchun ko'rsatma

> **Foydalanuvchi uchun:** bu faylni o'zingiz o'qishingiz shart emas.
> AI'ga (Claude Code, Cursor, Copilot, ChatGPT...) shunday deng:
>
> ```
> click_payment papkasidagi AI_PROMPT.md ni o'qi va Click to'lovini
> loyihamga to'liq ulab ber.
> ```
>
> AI qolganini o'zi qiladi va oxirida sizdan nima talab qilinishini aytadi.

---

## Topshiriq

Sen shu loyihaga Click (my.click.uz) to'lov tizimini **to'liq ishlaydigan**
holatda ulaysan. `click_payment/` paketi tayyor — sen uni loyihaning bazasi va
framework'iga bog'laysan.

Ishni **taxmin qilib emas, loyihani o'qib** boshla.

---

## 0-qadam: loyihani o'rgan

Quyidagilarni aniqla va o'zingga yozib ol:

1. **Framework** — FastAPI / Flask / Django / aiohttp / aiogram? (`requirements.txt`,
   `pyproject.toml`, `manage.py`, asosiy `app.py` ga qara)
2. **Baza** — PostgreSQL / MySQL / SQLite? Qaysi kutubxona orqali (psycopg,
   SQLAlchemy, Django ORM, xom SQL)?
3. **Buyurtma jadvali** — to'lov qaysi jadvalga bog'lanadi? (`orders`,
   `payments`, `purchases`...). Ustunlari qanday? Narx qaysi ustunda va qaysi
   turda (integer/decimal)? Holat (`status`) ustuni bor-yo'qmi, qanday
   qiymatlar ishlatiladi (`new`, `pending_payment`, `paid`...)?
4. **"Mahsulot berish" nima degani** — to'lov o'tgach nima bo'lishi kerak?
   (Telegram xabari, faylga ruxsat, obuna ochish, buyurtmani navbatga qo'yish...)
   Loyihada shunga o'xshash mavjud funksiya bormi — o'shani ishlat.
5. **Auth/middleware** — loyihada global autentifikatsiya yoki CSRF himoyasi
   bormi? (Bu muhim — 5-qadamga qara.)

Agar 3 yoki 4-band kodni o'qib aniqlanmasa — **foydalanuvchidan so'ra**, taxmin
qilma. Qolganini o'zing hal qil.

---

## 1-qadam: paketni joylashtir

`click_payment/` papkasini loyihaning import qilinadigan joyiga ko'chir
(odatda ildiz yoki `src/`). Django bo'lsa — app'lar yoniga.

`import click_payment` ishlashini tekshir.

---

## 2-qadam: `.env`

`.env.example` dagi o'zgaruvchilarni loyihaning `.env` fayliga qo'sh:

```
CLICK_SERVICE_ID=
CLICK_MERCHANT_ID=
CLICK_SECRET_KEY=
CLICK_MERCHANT_USER_ID=
CLICK_RETURN_URL=
```

- Qiymatlarni **sen to'ldirmaysan** — foydalanuvchi kabinetdan oladi. Bo'sh
  qoldir va oxirida unga ayt.
- `.env` `.gitignore` da borligini tekshir. Bo'lmasa — qo'sh.
- Loyihada `.env` boshqacha o'qilsa (Django `settings.py`, pydantic
  `Settings`...), o'sha yo'lni ishlat, lekin qiymatlar baribir muhit
  o'zgaruvchilari bo'lib qolsin (`click_config.py` `os.getenv` bilan o'qiydi).

---

## 3-qadam: bazaga ikkita ustun qo'sh

Buyurtma jadvaliga:

```sql
ALTER TABLE orders ADD COLUMN merchant_trans_id VARCHAR(64) UNIQUE;
ALTER TABLE orders ADD COLUMN click_trans_id VARCHAR(64);
```

- `merchant_trans_id` **UNIQUE** bo'lishi shart.
- Loyihada migratsiya tizimi bo'lsa (Alembic, Django migrations) — migratsiya
  fayli yarat, qo'lda `ALTER TABLE` qilma.
- Jadvalda mos ustunlar allaqachon bo'lsa — yangisini qo'shma, borini ishlat.

---

## 4-qadam: `click_orders.py` ni loyiha bazasiga bog'la

**Faqat shu faylni tahrirlaysan.** Ichidagi SQLite namunasini o'chirib
(`_db`, `_write`, `SCHEMA`, `create_order`, `reset_db_for_tests` — demo qismi),
5 ta funksiyani loyihaning bazasi bilan yoz. Faylning oxiridagi izohda
PostgreSQL / MySQL / Django ORM / SQLAlchemy uchun namunalar bor.

### `find_order(merchant_trans_id) -> Order | None`

Buyurtmani top va `Order` qilib qaytar:

- `id` — buyurtmaning raqamli id'si (Click'ga `merchant_prepare_id` bo'lib ketadi)
- `amount` — kutilayotgan summa, **Decimal**, so'mda
- `status` — loyihaning holatini `STATUS_PENDING` / `STATUS_PAID` /
  `STATUS_CANCELLED` ga **o'girib** ber. Masalan:

  ```python
  status={
      "new": STATUS_PENDING,
      "pending_payment": STATUS_PENDING,
      "paid": STATUS_PAID,
      "delivered": STATUS_PAID,
  }.get(row["status"], STATUS_CANCELLED)
  ```

  Diqqat: allaqachon bajarilgan buyurtma `STATUS_PAID` bo'lishi kerak, aks
  holda ikkinchi marta to'lanib ketadi.
- `extra` — `on_paid()` da kerak bo'ladigan hamma narsa (user_id, chat_id,
  product_id...). Ikkinchi marta bazaga bormaslik uchun shu yerga sol.

### `mark_paid(order, click_trans_id) -> bool`

**Bu yerda xato qilish — eng qimmat xato. Diqqat bilan o'qi.**

Shartni **SQL'ning o'ziga** qo'y va o'zgargan qatorlar sonini qaytar:

```python
# TO'G'RI — atomar
cur.execute(
    "UPDATE orders SET status='paid', click_trans_id=%s, paid_at=NOW() "
    "WHERE id=%s AND status='pending_payment'",
    (click_trans_id, order.id),
)
return cur.rowcount > 0
```

```python
# NOTO'G'RI — poyga bor, mahsulot IKKI MARTA beriladi
if order.status == "pending":       # avval o'qish
    cur.execute("UPDATE orders SET status='paid' WHERE id=%s", (order.id,))
    return True                     # keyin yozish
```

Nega: Click javobni ololmasa `complete` so'rovini qayta yuboradi, ba'zan bir
vaqtda. `True` qaytgan chaqiruvda `on_paid()` ishlaydi. Har safar `True`
qaytarsang — foydalanuvchi mahsulotni ikki marta oladi.

Django ORM'da `.update()` atomar:
```python
return Order.objects.filter(id=order.id, status="pending").update(status="paid") > 0
```

### `mark_cancelled(order, click_trans_id) -> None`

Buyurtmani bekor qilingan holatga o'tkaz (faqat u hali `pending` bo'lsa).

### `on_paid(order) -> None`

Mahsulotni shu yerda ber — 0-qadamning 4-bandida aniqlagan ishni qil.
Loyihada tayyor funksiya bo'lsa (`send_message`, `grant_access`,
`notify_admins`...), yangisini yozma, o'shani chaqir.

- Uzoq davom etadigan ish qilma — Click javobni kutib turadi. Loyihada
  navbat (Celery/RQ/asyncio task) bo'lsa, og'ir ishni o'shanga uzat.
- Bu funksiya xato bersa, to'lov baribir `paid` bo'lib qoladi va xato logga
  yoziladi — bu ataylab shunday.

### `on_cancelled(order) -> None`

Ixtiyoriy. Kerak bo'lmasa `pass` qoldir yoki log yoz.

---

## 5-qadam: ikkita endpoint qo'sh

Loyiha framework'iga mos ravishda (`examples/` da namunalar bor):

```python
from click_payment import handle_prepare, handle_complete

POST /click/prepare   ->  handle_prepare(request_data)   # dict qaytaradi -> JSON
POST /click/complete  ->  handle_complete(request_data)  # dict qaytaradi -> JSON
```

`request_data` — so'rovdagi maydonlar dict holida. Click odatda
**form-encoded POST** yuboradi; JSON ham kelishi mumkin — ikkalasini ham qabul
qil (`examples/fastapi_app.py` dagi `_request_data` ga qara).

**Eng ko'p unutiladigan narsa — bu ikkala endpoint ochiq bo'lishi kerak:**

- Bu so'rovlar **Click serveridan** keladi, foydalanuvchi brauzeridan emas.
  Click sizning tizimingizga login qila olmaydi.
- Loyihada global auth middleware / `@login_required` / API-key tekshiruvi
  bo'lsa — bu ikkita manzilni **istisno** qilib qo'y, aks holda Click 403 oladi
  va to'lovlar ishlamaydi.
- Django'da `@csrf_exempt` shart.
- Rate-limit bo'lsa, bu manzillarni chiqarib tashla.

Xavfsizlik imzo (`sign_string`) orqali ta'minlanadi — `handle_prepare` va
`handle_complete` ichida allaqachon tekshiriladi. Qo'shimcha auth kerak emas.

---

## 6-qadam: to'lov havolasi

Foydalanuvchi "sotib olaman" bosganda:

```python
from click_payment import payment_url

# buyurtmaga unikal merchant_trans_id ber (bir marta)
if not order.merchant_trans_id:
    order.merchant_trans_id = f"ORD{order.id}"
    order.save()

url = payment_url(order.merchant_trans_id, order.price)
# foydalanuvchini shu havolaga yubor (redirect / Telegram tugmasi / link)
```

Loyihada bir nechta to'lov turi bo'lsa, prefiks bilan ajrat: `ORD42` (xarid),
`SUB7` (obuna) — `find_order` ichida prefiksga qarab kerakli jadvalni topasan.

---

## 7-qadam: tekshir — bu qadamni o'tkazib yuborma

1. **Testlarni moslab ishlatib ko'r.**

   `tests/test_click.py` demo SQLite bazasiga tayangan (`create_order`,
   `reset_db_for_tests`). Sen `click_orders.py` ni o'zgartirganingdan keyin ular
   ishlamaydi — testlarni loyihaning test bazasiga moslab yoz (fixture
   buyurtma yaratsin), keyin ishga tushir:

   ```
   python -m pytest -v
   ```

   Bu testlar imzo, summa, takroriy callback va bekor qilishni tekshiradi —
   ularni o'chirib tashlama, moslab qo'y.

2. **`mark_paid` ikki marta `True` qaytarmasligini alohida tekshir:**

   ```python
   assert mark_paid(order, "123") is True
   assert mark_paid(order, "123") is False   # <- shu SHART
   ```

3. **Serverni ko'tarib, prepare/complete ni imitatsiya qil** (imzoni qo'lda
   hisoblab, form-encoded POST yubor) va quyidagilarni ko'r:
   - to'g'ri imzo -> `error: 0`
   - soxta imzo -> `error: -1`
   - noto'g'ri summa -> `error: -2`
   - complete'dan keyin bazada holat `paid`
   - complete'ni takror yuborganda -> `error: 0`, lekin mahsulot **qayta
     berilmaydi**

   Namuna imzo (prepare uchun):
   `md5(click_trans_id + service_id + secret_key + merchant_trans_id + amount + "0" + sign_time)`

4. Auth middleware bu endpoint'larni bloklamayotganini tekshir (login qilmasdan
   POST yuborib ko'r — 403 kelmasligi kerak).

---

## Qat'iy qoidalar

1. **Faqat `click_orders.py` ni tahrirla.** `click_prepare.py`,
   `click_complete.py`, `click_signature.py`, `click_config.py`,
   `click_errors.py`, `click_utils.py` — tegma. Ularda Click protokoli va
   xavfsizlik mantiqi bor; "yaxshilash" mumkin emas.

2. **`amount` ni imzo uchun qayta formatlama.** Click `"5000.00"` yuborsa,
   `float` ga o'girib qaytarsang `"5000.0"` bo'ladi va imzo buziladi. Kod buni
   to'g'ri qiladi — aralashma.

3. **`secret_key` ni kodga yozma, loglarga chiqarma, git'ga qo'shma.** Faqat
   `.env` da.

4. **`return_url` ga tushishni "to'landi" deb hisoblama.** U brauzerdan keladi
   va soxtalashtirilishi mumkin. Natija sahifasida holatni **bazadan** o'qi.

5. **`error` maydonini `sign_string` bilan aralashtirma.** Click'ning `error`
   maydoni complete'da "foydalanuvchi bekor qildi" degani — u imzoga kirmaydi.

6. **To'lov holatini faqat `complete` tasdiqlaydi**, `prepare` emas. `prepare`
   da mahsulot berma.

---

## Yakunda foydalanuvchiga ayt

1. `.env` ga qaysi 4 ta qiymatni kabinetdan olib qo'yish kerakligi
   (`CLICK_SERVICE_ID`, `CLICK_MERCHANT_ID`, `CLICK_SECRET_KEY`,
   `CLICK_MERCHANT_USER_ID`).
2. Click kabinetiga yozilishi kerak bo'lgan **aniq** manzillar:
   ```
   Prepare URL:   https://<domen>/click/prepare
   Complete URL:  https://<domen>/click/complete
   ```
   Domen HTTPS va tashqaridan ochiq bo'lishi shart (lokal sinash uchun ngrok).
3. Bazaga qo'shilgan ustunlar / migratsiya ishga tushirilishi kerakligi.
4. `on_paid()` ichiga aniq nima yozganing.
5. Nimani tekshirganing va nimani tekshira olmaganing (masalan: haqiqiy Click
   kabineti bilan sinov o'tkazilmagan).
