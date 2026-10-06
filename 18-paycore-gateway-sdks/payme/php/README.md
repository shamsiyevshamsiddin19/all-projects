# Payme to'lov integratsiyasi — PHP

[Payme](https://payme.uz) (checkout.paycom.uz / business.payme.uz) to'lov
tizimining **Merchant API** integratsiyasi. Composer, `vendor/` — hech narsa
kerak emas.

- ✅ Oltita metod to'liq: `CheckPerformTransaction`, `CreateTransaction`,
  `PerformTransaction`, `CancelTransaction`, `CheckTransaction`, `GetStatement`
- ✅ HTTP Basic Auth tekshiruvi — `hash_equals` bilan timing-safe
- ✅ 12 soatlik avtomatik timeout
- ✅ To'langandan keyingi bekor qilish (refund) qo'llab-quvvatlanadi
- ✅ Takroriy so'rovlarga chidamli (idempotent)
- ✅ Bitta endpoint — oddiy hosting va framework rejimi
- ✅ 46 ta tekshiruv (PHPUnit kerak emas)

> **PHP 7.4+** (8.x da ham ishlaydi). Kerakli kengaytmalar: `pdo`, `json`.
> Namuna baza uchun `pdo_sqlite`.
>
> Bu repo'da [Click](../../click/php) integratsiyasi ham bor — ikkalasi bir
> xil naqshda, lekin protokollari tubdan farq qiladi (quyiga qarang).

---

## Payme Click'dan nimasi bilan farq qiladi

| | Click | Payme |
|---|---|---|
| Endpoint soni | 2 (`prepare`, `complete`) | **1** (hammasi `method` maydoniga qarab) |
| Autentifikatsiya | `sign_string` (md5 imzo) | **HTTP Basic Auth** (`Paycom:secret_key`) |
| Summa birligi | so'm | **tiyin** (1 so'm = 100 tiyin) |
| Metodlar soni | 2 | **6** |
| Muddat | yo'q | **12 soat** |
| To'langandan keyin bekor qilish | yo'q | **bor** (refund) |
| To'lov havolasi | query-string | **base64** kodlangan `key=value;...` |

---

## AI bilan ulash (eng tez yo'l)

[`AI_PROMPT.md`](AI_PROMPT.md) — AI'ga shunday deng:

```
payme/php papkasidagi AI_PROMPT.md ni o'qi va Payme to'lovini
loyihamga to'liq ulab ber.
```

---

## 3 qadamda ulash

### 1-qadam: fayllarni ko'chiring

`payme/php/` papkasini loyihangizga ko'chiring.

### 2-qadam: `.env` ni to'ldiring

| O'zgaruvchi | Majburiy | Nima bu |
|---|:---:|---|
| `PAYME_MERCHANT_ID` | ✅ | Kassa ID |
| `PAYME_SECRET_KEY` | ✅ | **Maxfiy kalit** |
| `PAYME_MERCHANT_LOGIN` | ➖ | Odatda `Paycom` |
| `PAYME_DB_PATH` | ➖ | SQLite fayli — faqat namuna uchun |

### 3-qadam: `payme_orders.php` ni o'z bazangizga moslang

**Ikki guruh funksiya bor:**

```php
// BIZNES — siz o'zgartirasiz
function paymeFindAccount(array $account)       // -> PaymeAccount|null
function paymeOnPaid(PaymeTransaction $tx)       // mahsulotni bering
function paymeOnCancelled(PaymeTransaction $tx)  // ixtiyoriy
function paymeCanRefund(PaymeTransaction $tx)    // ixtiyoriy, standart: true

// TRANZAKSIYA KUNDALIGI — Payme talab qiladi, demo SQLite tayyor
// (fayl oxirida MySQL namunasi bor)
```

---

## Endpoint (bitta manzil)

```php
require_once __DIR__ . '/payme/php/payme_methods.php';
require_once __DIR__ . '/payme/php/payme_utils.php';

// Oddiy hosting: payme.php faylini to'g'ridan-to'g'ri ochib qo'ying.
// Framework:
$response = paymeHandleRequest(paymeRequestData(), paymeAuthorizationHeader());
paymeSendJson($response);
```

Kabinetga yoziladigan manzil: `https://sizning-domen.uz/payme.php` (yoki
frameworkda o'zingiz belgilagan `/payme`).

> ⚠️ Bu manzil auth/CSRF middleware'dan **istisno** bo'lishi kerak — Payme
> login qila olmaydi. Namuna: [`examples/laravel_routes.php`](examples/laravel_routes.php).

## To'lov havolasi

```php
require_once __DIR__ . '/payme/php/payme_checkout.php';

$url = paymeCheckoutUrl(['order_id' => $order->id], paymeSomToTiyin($order->price));
```

`paymeSomToTiyin()` ni unutmang — Payme summani TIYINDA kutadi.

---

## Sinab ko'rish

```bash
php examples/create_payment.php
php -S localhost:8000
php tests/test_payme.php
# Jami: 46, xato: 0
```

---

## Xato kodlari

| Kod | Ma'nosi |
|---:|---|
| `-32700` | JSON parsing xatosi |
| `-32600` | Majburiy maydon yo'q |
| `-32601` | Metod topilmadi |
| `-32504` | Avtorizatsiya xato |
| `-31001` | Noto'g'ri summa |
| `-31003` | Tranzaksiya topilmadi |
| `-31007` | Bekor qilib bo'lmaydi |
| `-31008` | Amalni bajarib bo'lmaydi (holat/muddat) |
| `-31050` | Buyurtma topilmadi |
| `-31099` | Allaqachon to'langan / tranzaksiya bor |

## Fayllar

```
payme/php/
├── payme_orders.php      ← FAQAT SHUNI TAHRIRLAYSIZ
├── payme_methods.php     6 metod + JSON-RPC dispatcher
├── payme_auth.php        Basic Auth
├── payme_checkout.php    to'lov havolasi
├── payme_config.php      .env
├── payme_errors.php      xato kodlari
├── payme_utils.php       so'rov/javob yordamchilari
├── payme.php             yagona endpoint
├── examples/
├── tests/test_payme.php
└── AI_PROMPT.md
```

Python versiyasi: [`../python`](../python)

## Litsenziya

MIT
