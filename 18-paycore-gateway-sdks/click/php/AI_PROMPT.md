# Click to'lovini loyihaga ulash — AI uchun ko'rsatma (PHP)

> **Foydalanuvchi uchun:** bu faylni o'zingiz o'qishingiz shart emas.
> AI'ga (Claude Code, Cursor, Copilot, ChatGPT...) shunday deng:
>
> ```
> click/php papkasidagi AI_PROMPT.md ni o'qi va Click to'lovini
> loyihamga to'liq ulab ber.
> ```
>
> AI qolganini o'zi qiladi va oxirida sizdan nima talab qilinishini aytadi.

---

## Topshiriq

Sen shu loyihaga Click (my.click.uz) to'lov tizimini **to'liq ishlaydigan**
holatda ulaysan. `click/php/` papkasidagi fayllar tayyor — sen ularni
loyihaning bazasi va tuzilishiga bog'laysan.

Ishni **taxmin qilib emas, loyihani o'qib** boshla.

---

## 0-qadam: loyihani o'rgan

Quyidagilarni aniqla va o'zingga yozib ol:

1. **Loyiha turi** — oddiy PHP (har bir fayl alohida endpoint) yoki
   front-controller / framework (Laravel, Slim, CodeIgniter, Symfony)?
   Bu 5-qadamda qaysi usul tanlashni belgilaydi.
2. **PHP versiyasi** — `composer.json` yoki hosting sozlamasiga qara. Kod
   7.4+ uchun yozilgan; sen ham 8.0+ ga xos sintaksis qo'shma (`match`,
   `enum`, konstruktor promotion, `str_contains`) — hosting eski bo'lishi mumkin.
3. **Baza** — MySQL/PostgreSQL? Loyihada PDO qaytaradigan funksiya bormi
   (`db()`, `getPDO()`, `$pdo`)? Eloquent ishlatiladimi?
4. **Buyurtma jadvali** — to'lov qaysi jadvalga bog'lanadi? (`orders`,
   `payments`...). Narx qaysi ustunda? Holat (`status`) ustuni qanday
   qiymatlarni oladi (`new`, `pending_payment`, `paid`, `queue_waiting`...)?
5. **"Mahsulot berish" nima degani** — to'lov o'tgach nima bo'lishi kerak?
   (Telegram xabari, faylga ruxsat, buyurtmani navbatga qo'yish...) Loyihada
   shunga o'xshash **mavjud funksiya** bormi (`sendMessage`, `notifyAdmins`) —
   yangisini yozma, o'shani chaqir.
6. **Auth / CSRF** — loyihada global himoya bormi? (Bu muhim — 5-qadamga qara.)
7. **Logger** — loyihada o'z loggeri bormi (`logInfo`, `logError`, Monolog)?

Agar 4 yoki 5-band kodni o'qib aniqlanmasa — **foydalanuvchidan so'ra**, taxmin
qilma. Qolganini o'zing hal qil.

---

## 1-qadam: fayllarni joylashtir

`click/php/` papkasini loyihaga ko'chir (masalan `click/` yoki Laravel'da
`app/Click/`). Composer kerak emas — hamma narsa `require_once` bilan ishlaydi.

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
- `click_config.php` `.env` ni o'zi topib o'qiydi (shu papka → loyiha ildizi →
  bir daraja yuqori). Composer/dotenv kutubxonasi shart emas.
- Loyihada sozlama boshqacha saqlansa (Laravel `config/`, `config.php` massiv
  qaytaradi), `.env` o'rniga `clickSetConfig()` ni ishlat:

  ```php
  clickSetConfig([
      'service_id'       => $config['click']['service_id'],
      'merchant_id'      => $config['click']['merchant_id'],
      'secret_key'       => $config['click']['secret_key'],
      'merchant_user_id' => $config['click']['merchant_user_id'],
  ]);
  ```
  Buni endpoint'lardan **oldin** chaqir.
- `.env` `.gitignore` da borligini tekshir. Bo'lmasa — qo'sh.

---

## 3-qadam: bazaga ikkita ustun qo'sh

```sql
ALTER TABLE orders ADD COLUMN merchant_trans_id VARCHAR(64) NULL UNIQUE;
ALTER TABLE orders ADD COLUMN click_trans_id VARCHAR(64) NULL;
```

- `merchant_trans_id` **UNIQUE** bo'lishi shart.
- Loyihada migratsiya tizimi bo'lsa (Laravel migrations, Phinx) — migratsiya
  fayli yarat, qo'lda `ALTER TABLE` qilma.
- Mos ustunlar allaqachon bo'lsa — yangisini qo'shma, borini ishlat.

---

## 4-qadam: `click_orders.php` ni loyiha bazasiga bog'la

**Faqat shu faylni tahrirlaysan.** Ichidagi SQLite namunasini o'chirib
(`clickDemoDb`, `clickDemoCreateOrder` — demo qismi), 5 ta funksiyani loyihaning
bazasi bilan yoz. Faylning oxiridagi izohda MySQL va Laravel uchun namunalar bor.

Loyihada mavjud PDO bo'lsa — yangi ulanish yaratma, o'shani ishlat.

### `clickFindOrder($merchantTransId)` → `ClickOrder|null`

`ClickOrder` konstruktori: `new ClickOrder($id, $merchantTransId, $amount, $status, $extra)`

- `$id` — buyurtmaning raqamli id'si (Click'ga `merchant_prepare_id` bo'lib ketadi)
- `$amount` — kutilayotgan summa, so'mda
- `$status` — loyihaning holatini `CLICK_STATUS_PENDING` / `CLICK_STATUS_PAID` /
  `CLICK_STATUS_CANCELLED` ga **o'girib** ber:

  ```php
  $map = array(
      'new'             => CLICK_STATUS_PENDING,
      'pending_payment' => CLICK_STATUS_PENDING,
      'paid'            => CLICK_STATUS_PAID,
      'queue_waiting'   => CLICK_STATUS_PAID,   // allaqachon bajarilgan
      'done'            => CLICK_STATUS_PAID,
  );
  $status = isset($map[$row['status']]) ? $map[$row['status']] : CLICK_STATUS_CANCELLED;
  ```

  Diqqat: allaqachon bajarilgan buyurtma `CLICK_STATUS_PAID` bo'lishi kerak,
  aks holda ikkinchi marta to'lanib ketadi.
- `$extra` — `clickOnPaid()` da kerak bo'ladigan hamma narsa (`user_id`,
  `telegram_id`, `chat_id`...). Ikkinchi marta bazaga bormaslik uchun shu yerga sol.

### `clickMarkPaid(ClickOrder $order, $clickTransId)` → `bool`

**Bu yerda xato qilish — eng qimmat xato. Diqqat bilan o'qi.**

Shartni **SQL'ning o'ziga** qo'y va `rowCount()` ni qaytar:

```php
// TO'G'RI — atomar
$stmt = db()->prepare(
    "UPDATE orders SET status='paid', click_trans_id=?, paid_at=NOW()
      WHERE id=? AND status='pending_payment'"
);
$stmt->execute(array($clickTransId, $order->id));

return $stmt->rowCount() > 0;
```

```php
// NOTO'G'RI — poyga bor, mahsulot IKKI MARTA beriladi
if ($order->status === 'pending') {          // avval o'qish
    db()->exec("UPDATE orders SET status='paid' WHERE id={$order->id}");
    return true;                             // keyin yozish
}
```

Nega: Click javobni ololmasa `complete` so'rovini qayta yuboradi, ba'zan bir
vaqtda. `true` qaytgan chaqiruvda `clickOnPaid()` ishlaydi. Har safar `true`
qaytarsang — foydalanuvchi mahsulotni ikki marta oladi.

Laravel'da `->update()` atomar:
```php
return \App\Models\Order::where('id', $order->id)
    ->where('status', 'pending')
    ->update(['status' => 'paid']) > 0;
```

### `clickMarkCancelled(ClickOrder $order, $clickTransId)` → `void`

Buyurtmani bekor qilingan holatga o'tkaz (faqat u hali `pending` bo'lsa).

### `clickOnPaid(ClickOrder $order)` → `void`

Mahsulotni shu yerda ber — 0-qadamning 5-bandida aniqlagan ishni qil. Mavjud
funksiyalarni chaqir, yangisini yozma.

- Uzoq ish qilma — Click javobni kutib turadi.
- Bu funksiya xato bersa, to'lov baribir `paid` bo'lib qoladi va xato logga
  yoziladi — bu ataylab shunday.

### `clickOnCancelled(ClickOrder $order)` → `void`

Ixtiyoriy.

### Logger

Loyihada o'z loggeri bo'lsa, `click_utils.php` dagi `clickLog()` ni o'shanga
qarat:

```php
function clickLog($level, $message, array $context = array())
{
    logYozish($level, $message, $context, 'click');
}
```

---

## 5-qadam: endpoint'larni ula

`click_prepare.php` va `click_complete.php` **ikki xil ishlaydi** — loyihaga
mos keladiganini tanla:

### A) Oddiy hosting (har bir fayl alohida URL)

Hech narsa qilish shart emas — fayllar to'g'ridan-to'g'ri chaqirilganda o'zi
javob beradi. Kabinetga yoziladigan manzil:
```
https://domen.uz/click/click_prepare.php
https://domen.uz/click/click_complete.php
```

### B) Framework / front-controller

`require` qilganda fayllar **hech narsa chiqarmaydi** — faqat funksiyalarni
e'lon qiladi:

```php
require_once __DIR__ . '/click/click_prepare.php';
require_once __DIR__ . '/click/click_complete.php';

// route: POST /click/prepare
clickSendJson(clickHandlePrepare(clickRequestData()));

// route: POST /click/complete
clickSendJson(clickHandleComplete(clickRequestData()));
```

Laravel'da `response()->json(clickHandlePrepare($request->all()))`.
Namunalar: `examples/router.php`, `examples/laravel_routes.php`.

### Eng ko'p unutiladigan narsa — endpoint'lar ochiq bo'lishi kerak

- So'rovlar **Click serveridan** keladi, foydalanuvchi brauzeridan emas. Click
  login qila olmaydi va CSRF token yubormaydi.
- Global auth middleware / `.htaccess` paroli / API-key tekshiruvi bo'lsa — bu
  ikkita manzilni **istisno** qil, aks holda Click 403 oladi va to'lovlar
  ishlamaydi.
- Laravel: `web` guruhiga qo'yma yoki `VerifyCsrfToken::$except` ga qo'sh.
- Rate-limit bo'lsa, bu manzillarni chiqarib tashla.

Xavfsizlik imzo (`sign_string`) orqali ta'minlanadi — `clickHandlePrepare()` va
`clickHandleComplete()` ichida tekshiriladi. Qo'shimcha auth kerak emas.

---

## 6-qadam: to'lov havolasi

Foydalanuvchi "sotib olaman" bosganda:

```php
require_once __DIR__ . '/click/click_config.php';

// buyurtmaga unikal merchant_trans_id ber (bir marta)
if (empty($order['merchant_trans_id'])) {
    $merchantTransId = 'ORD' . $order['id'];
    $stmt = db()->prepare('UPDATE orders SET merchant_trans_id = ? WHERE id = ?');
    $stmt->execute(array($merchantTransId, $order['id']));
} else {
    $merchantTransId = $order['merchant_trans_id'];
}

$url = clickPaymentUrl($merchantTransId, $order['price']);
header('Location: ' . $url);
```

Telegram botda — tugma sifatida: `array('text' => "To'lash", 'url' => $url)`.

Bir nechta to'lov turi bo'lsa prefiks bilan ajrat: `ORD42` (xarid), `SUB7`
(obuna) — `clickFindOrder()` ichida prefiksga qarab kerakli jadvalni topasan.

---

## 7-qadam: tekshir — bu qadamni o'tkazib yuborma

1. **Testlarni moslab ishlatib ko'r.**

   `tests/test_click.php` demo SQLite bazasiga tayangan
   (`clickDemoCreateOrder`). Sen `click_orders.php` ni o'zgartirganingdan keyin
   ular ishlamaydi — testlarni loyihaning test bazasiga moslab yoz, keyin:

   ```
   php tests/test_click.php
   ```

   Bu testlar imzo, summa, takroriy callback va bekor qilishni tekshiradi —
   o'chirib tashlama, moslab qo'y.

2. **`clickMarkPaid` ikki marta `true` qaytarmasligini alohida tekshir:**

   ```php
   var_dump(clickMarkPaid($order, '123'));   // true
   var_dump(clickMarkPaid($order, '123'));   // false  <- shu SHART
   ```

3. **Serverni ko'tarib, prepare/complete ni imitatsiya qil** — imzoni qo'lda
   hisoblab, form-encoded POST yubor:

   ```bash
   php -S localhost:8000
   curl -X POST http://localhost:8000/click/click_prepare.php \
     -d "click_trans_id=123" -d "service_id=..." -d "merchant_trans_id=ORD1" \
     -d "amount=5000" -d "sign_time=2026-01-01 00:00:00" -d "sign_string=<md5>"
   ```

   prepare imzosi:
   `md5(click_trans_id + service_id + secret_key + merchant_trans_id + amount + "0" + sign_time)`

   Quyidagilarni ko'r:
   - to'g'ri imzo → `error: 0`
   - soxta imzo → `error: -1`
   - noto'g'ri summa → `error: -2`
   - complete'dan keyin bazada holat `paid`
   - complete'ni takror yuborganda → `error: 0`, lekin mahsulot **qayta
     berilmaydi**

4. **Auth/CSRF bu endpoint'larni bloklamayotganini tekshir** (login qilmasdan
   POST yuborib ko'r — 403 kelmasligi kerak).

5. **Javobda ortiqcha narsa yo'qligini tekshir** — endpoint faqat toza JSON
   qaytarishi kerak. PHP warning/notice yoki `echo` javobga aralashsa, Click
   uni o'qiy olmaydi. `display_errors` o'chirilganini tekshir.

---

## Qat'iy qoidalar

1. **Faqat `click_orders.php` ni tahrirla.** `click_prepare.php`,
   `click_complete.php`, `click_signature.php`, `click_config.php`,
   `click_errors.php`, `click_utils.php` — tegma. Ularda Click protokoli va
   xavfsizlik mantiqi bor.

2. **`amount` ni imzo uchun qayta formatlama.** Click `"5000.00"` yuborsa,
   `(float)` ga o'girib qaytarsang `"5000"` bo'ladi va imzo buziladi. Kod buni
   to'g'ri qiladi — aralashma.

3. **`secret_key` ni kodga yozma, loglarga chiqarma, git'ga qo'shma.**

4. **`return_url` ga tushishni "to'landi" deb hisoblama.** U brauzerdan keladi
   va soxtalashtirilishi mumkin. Holatni **bazadan** o'qi.

5. **Click'ning `error` maydonini `sign_string` bilan aralashtirma.** U
   complete'da "foydalanuvchi bekor qildi" degani va imzoga kirmaydi.

6. **To'lov holatini faqat `complete` tasdiqlaydi**, `prepare` emas. `prepare`
   da mahsulot berma.

7. **PHP 8 ga xos sintaksis qo'shma** — hosting 7.4 bo'lishi mumkin.

---

## Yakunda foydalanuvchiga ayt

1. `.env` ga qaysi 4 ta qiymatni kabinetdan olib qo'yish kerakligi
   (`CLICK_SERVICE_ID`, `CLICK_MERCHANT_ID`, `CLICK_SECRET_KEY`,
   `CLICK_MERCHANT_USER_ID`).
2. Click kabinetiga yozilishi kerak bo'lgan **aniq** manzillar (qaysi usulni
   tanlaganingga qarab):
   ```
   https://<domen>/click/click_prepare.php     (oddiy hosting)
   yoki
   https://<domen>/click/prepare               (framework)
   ```
   Domen HTTPS va tashqaridan ochiq bo'lishi shart (lokal sinash uchun ngrok).
3. Bazaga qo'shilgan ustunlar / migratsiya ishga tushirilishi kerakligi.
4. `clickOnPaid()` ichiga aniq nima yozganing.
5. Nimani tekshirganing va nimani tekshira olmaganing (masalan: haqiqiy Click
   kabineti bilan sinov o'tkazilmagan).
