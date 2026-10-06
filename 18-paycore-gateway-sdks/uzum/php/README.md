# Uzum Bank to'lov integratsiyasi — PHP

[Uzum Bank](https://uzumbank.uz) Merchant API integratsiyasi — 5 webhook
(`check`, `create`, `confirm`, `reverse`, `status`). Composer, `vendor/`,
tashqi kutubxona yo'q.

> ⚠️ **Uzum Bank Click/Payme'dan tubdan farq qiladi**: bu yerda "to'lov
> havolasi" (checkout URL) YO'Q. Foydalanuvchi Uzum Bank ilovasida
> xizmatingizni `service_id` orqali qidirib topadi va to'lovni O'SHA YERDA
> boshlaydi. Sizning serveringiz faqat 5 ta webhook so'roviga javob beradi.

- ✅ 5 webhook to'liq — imzo o'rniga HTTP Basic Auth
- ✅ Uzum Bank'ning **idempotent-emas** protokoliga mos: takroriy
  `/create`/`/confirm` aniq xato qaytaradi (Click/Payme'dan farqli!)
- ✅ 30 daqiqalik avtomatik muddat tekshiruvi
- ✅ To'langandan keyin bekor qilish (refund) qo'llab-quvvatlanadi
- ✅ Oddiy hosting, Laravel
- ✅ 42 ta tekshiruv (PHPUnit kerak emas)

> **PHP 7.4+**. Kerakli kengaytmalar: `pdo`, `json`, `pdo_sqlite` (demo uchun).

---

## 1. Fayllarni ko'chiring

`uzum/php/` papkasini loyihangizga ko'chiring.

## 2. `.env` ni to'ldiring

```bash
cp .env.example .env
```

| O'zgaruvchi | Nima bu |
|---|---|
| `UZUM_SERVICE_ID` | Xizmat ID — foydalanuvchi sizni shu orqali topadi |
| `UZUM_WEBHOOK_LOGIN` | Webhook auth login (kabinetda o'zingiz belgilaysiz) |
| `UZUM_WEBHOOK_SECRET` | Webhook auth parol (kabinetda o'zingiz belgilaysiz) |

## 3. Kabinetga callback manzilini yozing

```
https://sizning-domen.uz/uzum
```

## 4. `uzum_orders.php` ni bazangizga bog'lang

**Faqat shu faylni tahrirlaysiz.** 4 ta funksiya: `uzumFindAccount()`,
`uzumOnConfirmed()`, `uzumOnReversed()`, `uzumCanReverse()`. Namuna SQLite
bilan ishlaydi, fayl oxirida MySQL namunasi bor.

---

## Endpoint'larni ulash

<details open>
<summary><b>Oddiy hosting / front-controller</b></summary>

```php
require_once __DIR__ . '/uzum/uzum_methods.php';

list($status, $body) = uzumHandleCheck($data, uzumAuthorizationHeader());
http_response_code($status);
header('Content-Type: application/json');
echo json_encode($body);
```

To'liq namuna: [`examples/router.php`](examples/router.php)
</details>

<details>
<summary><b>Laravel</b></summary>

To'liq namuna: [`examples/laravel_routes.php`](examples/laravel_routes.php)

⚠️ `web` va `auth` middleware'dan istisno qiling — so'rovlar Uzum Bank
serveridan keladi, CSRF token yo'q.
</details>

---

## Xato kodlari

| Kod | Ma'nosi | Qaysi metodda |
|---:|---|---|
| `10001` | Ruxsat yo'q (auth xato) | hammasi |
| `10005` | Majburiy maydon yo'q | hammasi |
| `10006` | Noto'g'ri `serviceId` | check, create |
| `10007` | Hisob topilmadi | check, create |
| `10008` | Allaqachon to'langan | check, create |
| `10009` | To'lov bekor qilingan | check, create |
| `10010` | Bu `transId` bilan tranzaksiya allaqachon bor | create |
| `10011` | Noto'g'ri summa | create |
| `10014` | Tranzaksiya topilmadi | confirm, reverse, status |
| `10015` | Tranzaksiya bekor qilingan | confirm |
| `10016` | Allaqachon tasdiqlangan | confirm |
| `10017` | Bekor qilib bo'lmaydi | reverse |
| `10018` | Allaqachon bekor qilingan | reverse |

To'liq ro'yxat: [`../python/README.md`](../python/README.md#xato-kodlari)

---

## ⚠️ Eng muhim farq: takroriy so'rov = XATO

Click/Payme'da takroriy so'rov "idempotent". **Uzum Bank'da EMAS** — takroriy
`/create` → `10010`, takroriy `/confirm` → `10016`. Kod buni to'g'ri
bajaradi — `tests/test_uzum.php` dagi tegishli testlarga qarang.

## 30 daqiqalik muddat

`/create` dan keyin 30 daqiqa ichida `/confirm` kelmasa — SIZ o'zingiz
tranzaksiyani bekor deb belgilaysiz (Uzum Bank alohida xabar bermaydi). Kod
buni `/confirm` va `/status` ichida avtomatik bajaradi.

---

## Sinab ko'rish

```bash
php tests/test_uzum.php
# Jami: 42, xato: 0
```

---

## Fayllar

```
uzum/php/
├── uzum_orders.php     ← FAQAT SHUNI TAHRIRLAYSIZ
├── uzum_methods.php     5 webhook handleri  (+ endpoint)
├── uzum_auth.php         Basic Auth tekshiruvi
├── uzum_config.php       .env
├── uzum_errors.php       xato kodlari
│
├── examples/
│   ├── router.php        front-controller'ga ulash
│   └── laravel_routes.php
│
├── tests/test_uzum.php   php tests/test_uzum.php
├── .env.example
└── AI_PROMPT.md
```

Boshqa tillar: [`../python`](../python) · [`../typescript`](../typescript)
Boshqa to'lov tizimlari: [`../../click`](../../click) · [`../../payme`](../../payme)

## Litsenziya

MIT
