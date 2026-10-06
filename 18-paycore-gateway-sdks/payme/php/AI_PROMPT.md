# Payme to'lovini loyihaga ulash — AI uchun ko'rsatma (PHP)

> **Foydalanuvchi uchun:** bu faylni o'zingiz o'qishingiz shart emas.
> AI'ga shunday deng:
>
> ```
> payme/php papkasidagi AI_PROMPT.md ni o'qi va Payme to'lovini
> loyihamga to'liq ulab ber.
> ```

---

## Topshiriq

Sen shu loyihaga Payme (checkout.paycom.uz) to'lov tizimini **to'liq
ishlaydigan** holatda ulaysan. `payme/php/` papkasidagi fayllar tayyor — sen
ularni loyihaning bazasi va tuzilishiga bog'laysan.

Ishni **taxmin qilib emas, loyihani o'qib** boshla. Agar loyihada
[Click integratsiyasi](../../click/php) allaqachon ulangan bo'lsa, o'sha
`click_orders.php` ni ham o'qi — bir xil buyurtma jadvaliga ulanasan.

---

## 0-qadam: loyihani o'rgan

1. Loyiha turi — oddiy PHP yoki front-controller/framework (Laravel, Slim)?
2. PHP versiyasi — kod 7.4+ uchun yozilgan, 8'ga xos sintaksis qo'shma.
3. Baza — MySQL/PostgreSQL? Loyihada PDO qaytaradigan funksiya bormi?
4. Buyurtma jadvali — narx qaysi ustunda, qaysi birlikda (so'm/tiyin)?
   **Payme summani TIYINDA kutadi** (1 so'm = 100 tiyin).
5. "Mahsulot berish" nima degani — mavjud funksiyani ishlat.
6. Auth/CSRF — global himoya bormi?
7. Logger — `paymeLog()` ni loyihaning logger'iga qarat.

Aniqlanmasa — foydalanuvchidan so'ra.

---

## 1-qadam: fayllarni joylashtir

`payme/php/` papkasini loyihaga ko'chir. Composer kerak emas.

---

## 2-qadam: `.env`

```
PAYME_MERCHANT_ID=
PAYME_SECRET_KEY=
```

Qiymatlarni **sen to'ldirmaysan** — foydalanuvchi business.payme.uz
kabinetidan oladi. `payme_config.php` `.env` ni o'zi topib o'qiydi (shu
papka → loyiha ildizi). Sozlamani loyiha config'idan bermoqchi bo'lsang:

```php
paymeSetConfig([
    'merchant_id' => $config['payme']['merchant_id'],
    'secret_key'  => $config['payme']['secret_key'],
]);
```

Buni endpoint'dan **oldin** chaqir.

---

## 3-qadam: tranzaksiya kundaligi jadvali qo'sh

Payme protokoli o'z bookkeeping'ini talab qiladi (Click'da bunday jadval
kerak emas edi):

```sql
CREATE TABLE payme_transactions (
    payme_id     VARCHAR(32) PRIMARY KEY,
    our_id       VARCHAR(32) NOT NULL,
    account_json TEXT NOT NULL,
    amount       BIGINT NOT NULL,      -- TIYINDA
    state        SMALLINT NOT NULL,
    payme_time   BIGINT NOT NULL,
    create_time  BIGINT NOT NULL,
    perform_time BIGINT NOT NULL DEFAULT 0,
    cancel_time  BIGINT NOT NULL DEFAULT 0,
    reason       SMALLINT NULL
);
CREATE INDEX idx_payme_tx_create_time ON payme_transactions(create_time);
```

Migratsiya tizimi bo'lsa — migratsiya fayli yarat.

---

## 4-qadam: `payme_orders.php` ni loyiha bazasiga bog'la

**Ikki guruh funksiya.**

### A) Biznes funksiyalar — albatta o'zgartirasan

`paymeFindAccount(array $account)` → `PaymeAccount|null`
- `$account` — Payme yuborgan `['order_id' => '42']`
- `amount` — **TIYINDA**! Bazada so'mda saqlangan bo'lsa `* 100` qil
- `payable=false` — buyurtma allaqachon to'langan/bekor bo'lsa
- Topilmasa `null`

`paymeOnPaid(PaymeTransaction $tx)` → mahsulotni ber. Uzoq ish qilma.

`paymeOnCancelled(PaymeTransaction $tx)` — `$tx->state ===
PAYME_STATE_CANCELLED_AFTER_PAID` bo'lsa bu QAYTARISH — ruxsatni bekor qil.

`paymeCanRefund(PaymeTransaction $tx)` → `bool` — to'langanni bekor qilish
(pul qaytarish) mumkinmi? Standart `true`.

### B) Tranzaksiya kundaligi — atomarlikni saqla

```php
// TO'G'RI — atomar (rowCount tekshiriladi)
function paymeMarkPerformed($paymeId)
{
    $stmt = db()->prepare(
        "UPDATE payme_transactions SET state=2, perform_time=?
          WHERE payme_id=? AND state=1"
    );
    $stmt->execute(array(paymeNowMs(), $paymeId));
    if ($stmt->rowCount() === 0) {
        return null;      // <- allaqachon to'langan, paymeOnPaid QAYTA chaqirilmaydi
    }
    return paymeGetTransaction($paymeId);
}
```

Bu — Click'dagi `clickMarkPaid` bilan bir xil qoida.

---

## 5-qadam: yagona endpoint qo'sh

Click'dagidek IKKITA emas, **BITTA** endpoint:

```php
require_once __DIR__ . '/payme/php/payme_methods.php';
require_once __DIR__ . '/payme/php/payme_utils.php';

$response = paymeHandleRequest(paymeRequestData(), paymeAuthorizationHeader());
paymeSendJson($response);
```

Kabinetga: `https://<domen>/payme.php` (yoki frameworkda o'zing belgilagan
`/payme`).

**Auth**: HTTP Basic Auth orqali (`payme_auth.php` avtomatik tekshiradi).
Global auth/CSRF middleware bo'lsa bu manzilni istisno qil (Laravel:
`VerifyCsrfToken::$except`, yoki route'ni `web` guruhidan chiqar).

---

## 6-qadam: to'lov havolasi

```php
require_once __DIR__ . '/payme/php/payme_checkout.php';

$url = paymeCheckoutUrl(['order_id' => $order->id], paymeSomToTiyin($order->price));
```

---

## 7-qadam: tekshir

1. `tests/test_payme.php` demo bazaga tayangan (`paymeDemoCreateOrder`) —
   loyiha bazasiga moslab yoz, keyin `php tests/test_payme.php`.
2. `paymeMarkPerformed` ikki marta `null` bo'lmagan natija qaytarmasligini tekshir.
3. Serverni ko'tarib, oltita metodni Basic Auth bilan qo'lda sina.
4. Auth/CSRF `/payme` ni bloklamayotganini tekshir.
5. Javobda faqat toza JSON borligini tekshir (PHP warning aralashmasin).

---

## Qat'iy qoidalar

1. Faqat `payme_orders.php` ni tahrirla.
2. Summa har doim TIYINDA.
3. `PAYME_SECRET_KEY` ni kodga yozma, git'ga qo'shma.
4. `create_time` — server vaqti, Payme yuborgan `time` emas.
5. Takroriy `CancelTransaction` — sababni yangilama, mavjud natijani qaytar.
6. PHP 8'ga xos sintaksis qo'shma.

---

## Yakunda foydalanuvchiga ayt

1. `.env` ga `PAYME_MERCHANT_ID` va `PAYME_SECRET_KEY`.
2. Kabinetga yoziladigan yagona manzil.
3. Bazaga qo'shilgan `payme_transactions` jadvali.
4. `paymeOnPaid()`/`paymeOnCancelled()` ichiga nima yozganing.
5. Sandbox (test.paycom.uz) bilan sinov o'tkazilmagani.
