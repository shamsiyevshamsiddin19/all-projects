# Uzum Bank to'lovini loyihaga ulash — AI uchun ko'rsatma (PHP)

> **Foydalanuvchi uchun:** bu faylni o'zingiz o'qishingiz shart emas.
> AI'ga shunday deng:
>
> ```
> uzum/php papkasidagi AI_PROMPT.md ni o'qi va Uzum Bank to'lovini
> loyihamga to'liq ulab ber.
> ```

---

## Topshiriq

Sen shu loyihaga Uzum Bank Merchant API'ni **to'liq ishlaydigan** holatda
ulaysan. `uzum/php/` dagi fayllar tayyor — sen ularni loyihaning bazasi va
tuzilishiga bog'laysan.

**Uzum Bank Click/Payme'dan tubdan farq qiladi — bu farqni tushunmasdan
boshlama:**

1. **To'lov havolasi YO'Q.** Foydalanuvchi Uzum Bank ilovasida
   xizmatingizni `service_id` orqali topadi va to'lovni O'SHA YERDA
   boshlaydi. `uzumPaymentUrl()` kabi funksiya YOZMA — bunday narsa
   protokolda umuman mavjud emas.
2. **Beshta ALOHIDA endpoint kerak** (`/check`, `/create`, `/confirm`,
   `/reverse`, `/status`).
3. **Xato holatida HTTP 400 qaytariladi** (Click/Payme'da har doim 200).
4. **Takroriy so'rov = XATO, muvaffaqiyat emas.** Agar Uzum Bank bir xil
   `transId` bilan `/create` yoki `/confirm` ni ikkinchi marta yuborsa,
   to'g'ri javob — mos xato kodi (`10010` / `10016`), oldingi
   muvaffaqiyatni QAYTA qaytarish EMAS. Kodda bu allaqachon to'g'ri
   qilingan — "tuzatib qo'ymang".

Ishni **taxmin qilib emas, loyihani o'qib** boshla.

---

## 0-qadam: loyihani o'rgan

1. **Loyiha turi** — oddiy PHP yoki framework (Laravel)?
2. **Baza** — MySQL/PostgreSQL? PDO qaytaradigan funksiya bormi (`db()`)?
3. **Buyurtma jadvali** — narx qaysi ustunda? Holat ustuni?
4. **"Mahsulot berish" nima degani** — `uzumOnConfirmed()` ichida nima
   qilinishi kerak?
5. **Auth middleware** — global himoya bormi?

Aniqlanmasa — foydalanuvchidan so'ra.

---

## 1-qadam: fayllarni joylashtir

`uzum/php/` ni loyihaga ko'chir. Composer kerak emas.

---

## 2-qadam: `.env`

```
UZUM_SERVICE_ID=
UZUM_WEBHOOK_LOGIN=
UZUM_WEBHOOK_SECRET=
```

Qiymatlarni **sen to'ldirmaysan**. `.env` `.gitignore` da borligini tekshir.

Loyihada sozlama boshqacha saqlansa, `.env` o'rniga:
```php
uzumSetConfig([
    'service_id'     => $config['uzum']['service_id'],
    'webhook_login'  => $config['uzum']['webhook_login'],
    'webhook_secret' => $config['uzum']['webhook_secret'],
]);
```

---

## 3-qadam: bazaga ustun qo'sh

```sql
ALTER TABLE orders ADD COLUMN uzum_trans_id VARCHAR(64) NULL;
```

Migratsiya tizimi bo'lsa — migratsiya fayli yarat.

---

## 4-qadam: `uzum_orders.php` ni loyiha bazasiga bog'la

**Faqat shu faylni tahrirlaysan.** Demo SQLite qismini (`uzumDemoDb`,
`uzumDemoCreateOrder`) o'chirib, quyidagilarni loyihaning PDO/ORM'i bilan yoz:

### `uzumFindAccount(array $params): ?UzumAccount`

`$params` — Uzum Bank yuborgan foydalanuvchi kiritgan maydonlar. `amount`
TIYINDA. `payable` — buyurtma hali to'lanmagan bo'lsa `true`.

### `uzumMarkConfirmed($transId): ?UzumTransaction`

**Bu yerda xato qilish — eng qimmat xato.** Shartni SQL'ning o'ziga qo'y:

```php
// TO'G'RI — atomar
$stmt = db()->prepare(
    "UPDATE uzum_transactions SET state='CONFIRMED', confirm_time=?
      WHERE trans_id=? AND state='CREATED'"
);
$stmt->execute(array(uzumNowMs(), $transId));
if ($stmt->rowCount() === 0) {
    return null;    // <- boshqa so'rov ulgurgan, on_confirmed chaqirilmaydi
}
return uzumGetTransaction($transId);
```

### `uzumMarkReversed($transId): ?UzumTransaction`

Xuddi shunday atomar, `state != 'REVERSED'` shart bilan.

### `uzumOnConfirmed($transaction)`

Mahsulotni ber. **DIQQAT:** pul ALLAQACHON yechilgan (Uzum Bank `/confirm`
dan oldin pulni yechadi). Xato bersa ham pul qaytarilmaydi.

### `uzumOnReversed($transaction)`

Ixtiyoriy.

---

## 5-qadam: BESHTA endpoint qo'sh

```php
require_once __DIR__ . '/uzum/uzum_methods.php';

list($status, $body) = uzumHandleCheck($data, uzumAuthorizationHeader());
http_response_code($status);
echo json_encode($body);
```

Namunalar: `examples/router.php`, `examples/laravel_routes.php`.

**Endpoint'lar ochiq bo'lishi kerak** — auth/CSRF'dan istisno qil.
Xavfsizlik `uzumHandle*()` ichidagi Basic Auth orqali ta'minlanadi.

Kabinetga bazaviy manzil: `https://<domen>/uzum`.

---

## 6-qadam: tekshir

1. **Testlarni moslab ishlatib ko'r** — `tests/test_uzum.php` demo SQLite'ga
   tayangan. `php tests/test_uzum.php` bilan ishga tushir.

2. **Takroriy so'rov haqiqatan xato qaytarishini tekshir:**
   ```php
   list($s1, $b1) = uzumHandleCreate($data, $auth);   // 200, CREATED
   list($s2, $b2) = uzumHandleCreate($data, $auth);   // 400, errorCode=10010 <- SHART
   ```

3. **Auth'ni tekshir** — noto'g'ri header bilan `400`/`10001` kelishini ko'r.

4. **Javobda ortiqcha narsa yo'qligini tekshir** — PHP warning/notice
   javobga aralashmasin.

---

## Qat'iy qoidalar

1. **Faqat `uzum_orders.php` ni tahrirla.**
2. **Checkout havolasi funksiyasini o'ylab topma.** Uzum Bank'da yo'q.
3. **Takroriy so'rovni idempotent qilib "tuzatma"** — ataylab xato qaytaradi.
4. **Summa TIYINDA.**
5. **Parolni kodga yozma, git'ga qo'shma.**

---

## Yakunda foydalanuvchiga ayt

1. `.env` ga qaysi 3 ta qiymatni kabinetdan olib qo'yish kerakligi.
2. Kabinetga yoziladigan callback manzil.
3. Bazaga qo'shilgan ustun.
4. `uzumOnConfirmed()` ichiga aniq nima yozganing.
5. Uzum Bank'da to'lov havolasi yo'qligini tushuntirganingni.
6. Nimani tekshira olmaganing (haqiqiy Uzum Bank kabineti bilan sinov
   o'tkazilmagan).
