# Click to'lov integratsiyasi — PHP

[Click](https://click.uz) (my.click.uz) to'lov tizimini **o'z loyihangizga**
qo'shish uchun tayyor fayllar. Merchant API — `prepare` / `complete`.

- 📁 **Papkani ko'chirasiz** — Composer, `vendor/`, tashqi kutubxona yo'q
- 🗄️ **O'z bazangiz bilan ishlaydi** — bizning jadvalimiz yo'q, sizning
  `orders` jadvalingizga ulanadi
- ✏️ **Bitta fayl tahrirlanadi** — `click_orders.php`
- 🔌 **Ikki xil ishlatiladi** — oddiy hosting'da fayl o'zi endpoint bo'ladi,
  framework'da `require` qilib chaqirasiz
- 🔒 Imzo tekshiruvi, takroriy callback himoyasi, atomar to'lov belgilash
- 🧪 42 ta tekshiruv (PHPUnit kerak emas)

> **PHP 7.4+** (8.x da ham ishlaydi). Kerakli kengaytmalar: `pdo`, `json`.
> Namuna baza uchun `pdo_sqlite`; o'z bazangizda `pdo_mysql` yetarli.

---

## AI bilan ulash (eng tez yo'l)

Loyihangizda AI ishlatasizmi (Claude Code, Cursor, Copilot, ChatGPT)? Repoda
[`AI_PROMPT.md`](AI_PROMPT.md) bor — AI uchun to'liq ko'rsatma. AI'ga shunday
deng:

```
click/php papkasidagi AI_PROMPT.md ni o'qi va Click to'lovini
loyihamga to'liq ulab ber.
```

Qo'lda ulamoqchi bo'lsangiz — quyidagi 3 qadam.

---

## 3 qadamda ulash

### 1-qadam: fayllarni ko'chiring

`click/php/` papkasini loyihangizga ko'chiring, masalan `click/` deb:

```
sizning_loyihangiz/
├── click/                  ← shu papkani ko'chiring
│   ├── click_prepare.php
│   ├── click_complete.php
│   ├── click_orders.php
│   └── ...
├── index.php
└── .env
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

`.env` fayli `click/php/` da ham, loyiha ildizida ham bo'lishi mumkin — ikkalasi
ham topiladi. Composer'siz o'qiladi.

Sozlamani framework config'idan bermoqchi bo'lsangiz:

```php
clickSetConfig([
    'service_id'       => config('services.click.service_id'),
    'merchant_id'      => config('services.click.merchant_id'),
    'secret_key'       => config('services.click.secret_key'),
    'merchant_user_id' => config('services.click.merchant_user_id'),
]);
```

> **`CLICK_SECRET_KEY`** — eng muhim qiymat. Uni bilgan odam soxta "to'landi"
> so'rovini yubora oladi. Kodga yozmang, loglarga chiqarmang, git'ga qo'shmang.

### 3-qadam: `click_orders.php` ni o'z bazangizga moslang

**Faqat shu faylni tahrirlaysiz.** Ichida 5 ta funksiya bor:

```php
// BAZA
function clickFindOrder($merchantTransId)          // -> ClickOrder|null
function clickMarkPaid(ClickOrder $o, $ctid)       // -> bool (atomar!)
function clickMarkCancelled(ClickOrder $o, $ctid)  // -> void

// HODISALAR
function clickOnPaid(ClickOrder $o)                // mahsulotni shu yerda bering
function clickOnCancelled(ClickOrder $o)           // ixtiyoriy
```

Fayl ichida SQLite bilan ishlaydigan namuna turibdi — klon qilib darrov sinab
ko'rasiz. Fayl **oxirida** MySQL va Laravel (Eloquent) uchun tayyor namunalar
bor.

Buyurtma jadvalingizga ikkita ustun qo'shasiz:

```sql
ALTER TABLE orders ADD COLUMN merchant_trans_id VARCHAR(64) NULL UNIQUE;
ALTER TABLE orders ADD COLUMN click_trans_id VARCHAR(64) NULL;
```

---

## Endpoint'larni ulash

Click ikkita manzilga so'rov yuboradi. Loyihangizga qarab ikki xil usul bor:

<details open>
<summary><b>1. Oddiy hosting</b> (fayl o'zi endpoint)</summary>

Hech narsa qilish shart emas — fayllar o'zi javob beradi. Click kabinetiga
shunchaki manzillarini yozasiz:

```
Prepare URL:   https://sizning-domen.uz/click/click_prepare.php
Complete URL:  https://sizning-domen.uz/click/click_complete.php
```
</details>

<details>
<summary><b>2. Framework</b> (Laravel, Slim, o'z routeringiz)</summary>

Fayllarni `require` qilganingizda ular o'zi hech narsa chiqarmaydi — faqat
funksiyalarni e'lon qiladi:

```php
require_once __DIR__ . '/click/click_prepare.php';
require_once __DIR__ . '/click/click_complete.php';

// o'z routeringizda:
$javob = clickHandlePrepare(clickRequestData());   // massiv qaytaradi
clickSendJson($javob);
```

Laravel: [`examples/laravel_routes.php`](examples/laravel_routes.php)
Front-controller: [`examples/router.php`](examples/router.php)

Kabinetga o'z manzillaringizni yozasiz:
```
Prepare URL:   https://sizning-domen.uz/click/prepare
Complete URL:  https://sizning-domen.uz/click/complete
```
</details>

> ⚠️ **Bu ikkala manzil ochiq bo'lishi kerak.** So'rov Click serveridan keladi —
> u sizning tizimingizga login qila olmaydi va CSRF token yubormaydi. Global
> auth / CSRF middleware bo'lsa, shu ikkitasini **istisno** qiling, aks holda
> Click 403 oladi va to'lovlar ishlamaydi. Xavfsizlik imzo orqali ta'minlanadi.

Domen **HTTPS** bo'lishi shart. Lokal sinash uchun [ngrok](https://ngrok.com).

## To'lov havolasini yasash

```php
require_once __DIR__ . '/click/click_config.php';

// buyurtmaga unikal merchant_trans_id bering (bir marta)
$merchantTransId = 'ORD' . $order['id'];

$url = clickPaymentUrl($merchantTransId, $order['price']);
header('Location: ' . $url);
```

`merchant_trans_id` bazangizda **unikal** bo'lishi shart — Click uni
prepare/complete so'rovlarida qaytarib yuboradi va siz shu orqali buyurtmani
topasiz. Bir nechta to'lov turi bo'lsa prefiks bilan ajrating: `ORD42` (xarid),
`SUB7` (obuna).

To'liq namuna: [`examples/create_payment.php`](examples/create_payment.php)

---

## Sinab ko'rish

```bash
cp .env.example .env
php examples/create_payment.php        # havola yasaydi
php -S localhost:8000                  # click_prepare.php ochiladi
```

Testlar:

```bash
php tests/test_click.php
# Jami: 42, xato: 0
```

---

## To'lov qanday o'tadi

```
  Foydalanuvchi          Sizning serveringiz              Click serveri
       │                         │                              │
       │  "sotib olaman"         │                              │
       ├────────────────────────>│                              │
       │                         │  clickPaymentUrl(...)        │
       │      pay_url            │  (bazada: pending)           │
       │<────────────────────────┤                              │
       │                                                        │
       │  Click sahifasida kartasini tasdiqlaydi                │
       ├───────────────────────────────────────────────────────>│
       │                         │                              │
       │                         │   POST click_prepare.php     │
       │                         │<─────────────────────────────┤
       │                         │  imzo + summa tekshiriladi   │
       │                         │  clickFindOrder()            │
       │                         │  error: 0, prepare_id: 42    │
       │                         ├─────────────────────────────>│
       │                         │                              │
       │                         │           💰 pul yechiladi    │
       │                         │                              │
       │                         │   POST click_complete.php    │
       │                         │<─────────────────────────────┤
       │                         │  clickMarkPaid()  -> true    │
       │                         │  clickOnPaid()    -> mahsulot│
       │                         │  error: 0                    │
       │                         ├─────────────────────────────>│
       │  return_url ga qaytadi  │                              │
       │<───────────────────────────────────────────────────────┤
```

**prepare** — "bu to'lovni qabul qila olasanmi?" Pul hali yechilmagan.
**complete** — "pul yechildi, mahsulotni ber." `clickOnPaid()` shu yerda ishlaydi.

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
> holida kirishi kerak. Click `"5000.00"` yuborsa, `(float)` ga o'girib
> qaytarsangiz `"5000"` bo'lib qoladi va imzo mos kelmaydi. Bu kod `amount` ga
> tegmaydi.

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

2. **`clickMarkPaid()` atomar bo'lsin.** Click javobni ololmasa complete'ni
   qayta yuboradi (ba'zan bir vaqtda). Shartni SQL'ning o'ziga qo'ying —
   `WHERE id=? AND status='pending'` — va `rowCount() > 0` qaytaring. Aks holda
   mahsulot ikki marta beriladi.

3. **`action` so'rovdan olinmaydi.** Imzo tekshirilganda endpoint qaysi bo'lsa,
   o'shanikini (`0` yoki `1`) ishlatamiz. Aks holda prepare uchun olingan imzoni
   complete so'roviga qo'yib yuborish mumkin bo'lardi.

4. **Summa har doim bazadan tekshiriladi** — so'rovdagi `amount` ga ishonmaymiz.

5. **`clickOnPaid()` ichida uzoq ish qilmang.** Click javobni kutib turadi.

6. **Endpoint'larni auth bilan yopmang** — yuqoriga qarang.

---

## Fayllar

```
click/php/
├── click_orders.php        ← FAQAT SHUNI TAHRIRLAYSIZ (bazangizga ulanish)
├── click_prepare.php       prepare so'rovi  (+ endpoint)
├── click_complete.php      complete so'rovi (+ endpoint)
├── click_signature.php     imzo qurish/tekshirish
├── click_config.php        .env + to'lov havolasi
├── click_errors.php        Click xato kodlari
├── click_utils.php         kichik yordamchilar
│
├── examples/
│   ├── create_payment.php  to'lov havolasini yasash
│   ├── laravel_routes.php  Laravel'ga ulash
│   └── router.php          front-controller'ga ulash
│
├── tests/test_click.php    php tests/test_click.php
├── .env.example            ← sozlamalar
└── AI_PROMPT.md            ← AI'ga beriladigan ko'rsatma
```

Python versiyasi: [`../python`](../python)

## Litsenziya

MIT
