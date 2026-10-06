# Click to'lov integratsiyasi — TypeScript

[Click](https://click.uz) (my.click.uz) to'lov tizimini **o'z loyihangizga**
qo'shish uchun tayyor fayllar. Merchant API — `prepare` / `complete`.

- 📁 **Papkani ko'chirasiz** — kutubxona o'rnatish shart emas
- 📦 **Nol bog'liqlik** — faqat `node:crypto` (Node'ning o'zida bor)
- 🗄️ **O'z bazangiz bilan ishlaydi** — bizning jadvalimiz yo'q, sizning
  `orders` jadvalingizga ulanadi
- ✏️ **Bitta fayl tahrirlanadi** — `click-orders.ts`
- 🧩 **Tipli shartnoma** — `ClickOrdersAdapter` interfeysi, xatoni TypeScript
  o'zi tutadi
- 🔒 Imzo tekshiruvi, takroriy callback himoyasi, atomar to'lov belgilash
- 🧪 26 ta test
- ⚙️ Next.js (App Router), Express, Hono/Bun/Deno

> **Node 18+**. Next.js, Express, Hono, Bun, Deno — hammasida ishlaydi.

---

## ⚠️ Next.js uchun eng muhim ikkita qator

Boshqa hamma narsani to'g'ri qilib, shu ikkitasida qoqilib qolish oson:

```ts
// app/api/click/prepare/route.ts
export const runtime = "nodejs";        // Edge'da md5 YO'Q — imzo ishlamaydi
export const dynamic = "force-dynamic"; // callback keshlanmasin
```

Click imzosi `md5` bilan hisoblanadi, Web Crypto API esa md5 ni umuman
qo'llab-quvvatlamaydi — shuning uchun Node runtime shart.

---

## AI bilan ulash (eng tez yo'l)

Loyihangizda AI ishlatasizmi (Claude Code, Cursor, Copilot, ChatGPT)? Repoda
[`AI_PROMPT.md`](AI_PROMPT.md) bor — AI uchun to'liq ko'rsatma. AI'ga shunday
deng:

```
click/typescript papkasidagi AI_PROMPT.md ni o'qi va Click to'lovini
loyihamga to'liq ulab ber.
```

Qo'lda ulamoqchi bo'lsangiz — quyidagi 3 qadam.

---

## 3 qadamda ulash

### 1-qadam: papkani ko'chiring

`click-payment/` papkasini loyihangizga ko'chiring:

```
sizning_loyihangiz/
├── src/
│   ├── click-payment/      ← shu papkani ko'chiring
│   └── app/
└── .env
```

### 2-qadam: `.env` ni to'ldiring

| O'zgaruvchi | Majburiy | Nima bu |
|---|:---:|---|
| `CLICK_SERVICE_ID` | ✅ | Xizmat (servis) ID — kabinet → Mening xizmatlarim |
| `CLICK_MERCHANT_ID` | ✅ | Savdogar raqamingiz — kabinet → Profil |
| `CLICK_SECRET_KEY` | ✅ | **Maxfiy kalit** — imzo shu bilan tekshiriladi |
| `CLICK_MERCHANT_USER_ID` | ✅ | Foydalanuvchi raqamingiz — kabinet → Profil |
| `CLICK_RETURN_URL` | ➖ | To'lovdan keyin qaytariladigan sahifangiz |
| `CLICK_PAY_BASE_URL` | ➖ | To'lov sahifasi manzili (odatda o'zgartirilmaydi) |

> **`CLICK_SECRET_KEY`** — nomiga hech qachon `NEXT_PUBLIC_` qo'shmang, u
> brauzerga chiqib ketadi. Kodga yozmang, git'ga qo'shmang.

Sozlamani `.env` dan emas, o'z config'ingizdan bermoqchi bo'lsangiz:

```ts
import { setConfig } from "@/click-payment";

setConfig({
  serviceId: myConfig.click.serviceId,
  merchantId: myConfig.click.merchantId,
  secretKey: myConfig.click.secretKey,
  merchantUserId: myConfig.click.merchantUserId,
});
```

### 3-qadam: `click-orders.ts` ni o'z bazangizga moslang

**Faqat shu faylni tahrirlaysiz.** U `ClickOrdersAdapter` interfeysini
bajaradi — 5 ta metod:

```ts
export const orders: ClickOrdersAdapter = {
  async findOrder(merchantTransId) { /* buyurtmani toping */ },
  async markPaid(order, clickTransId) { /* -> boolean (atomar!) */ },
  async markCancelled(order, clickTransId) { /* bekor qiling */ },
  async onPaid(order) { /* mahsulotni shu yerda bering */ },
  async onCancelled(order) { /* ixtiyoriy */ },
};
```

Hozir u yerda xotirada ishlaydigan namuna turibdi (klon qilib darrov sinaysiz,
lekin ishlab chiqarishga yaroqsiz). Fayl **oxirida** Prisma, Drizzle va xom SQL
uchun tayyor namunalar bor.

Buyurtma jadvalingizga ikkita ustun qo'shasiz. Prisma bo'lsa:

```prisma
model Order {
  // ...
  merchantTransId String?  @unique   // <- @unique SHART
  clickTransId    String?
  paidAt          DateTime?
}
```

---

## Endpoint'larni qo'shish

<details open>
<summary><b>Next.js (App Router)</b></summary>

```ts
// src/app/api/click/prepare/route.ts
import { NextResponse } from "next/server";
import { handlePrepare, readRequestData } from "@/click-payment";

export const runtime = "nodejs";          // MAJBURIY (yuqoriga qarang)
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  return NextResponse.json(await handlePrepare(await readRequestData(req)));
}
```

```ts
// src/app/api/click/complete/route.ts
import { NextResponse } from "next/server";
import { handleComplete, readRequestData } from "@/click-payment";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  return NextResponse.json(await handleComplete(await readRequestData(req)));
}
```

`middleware.ts` da auth bo'lsa — `/api/click/*` ni istisno qiling:

```ts
export const config = {
  matcher: ["/((?!api/click|_next/static|_next/image).*)"],
};
```

To'liq namuna: [`examples/nextjs-route-handlers.ts`](examples/nextjs-route-handlers.ts)
</details>

<details>
<summary><b>Express</b></summary>

```ts
import express from "express";
import { handlePrepare, handleComplete } from "./click-payment/index.js";

const app = express();

// ⚠️ SHU QATORSIZ hamma so'rov "-8" oladi — Click form-encoded yuboradi
app.use(express.urlencoded({ extended: false }));

app.post("/click/prepare", async (req, res) => {
  res.json(await handlePrepare(req.body));
});

app.post("/click/complete", async (req, res) => {
  res.json(await handleComplete(req.body));
});
```

To'liq namuna: [`examples/express-app.ts`](examples/express-app.ts)
</details>

<details>
<summary><b>Hono / Bun / Deno</b></summary>

```ts
app.post("/click/prepare", async (c) => {
  return c.json(await handlePrepare(await readRequestData(c.req.raw)));
});
```
</details>

Keyin Click kabinetiga manzillarni yozasiz:

```
Prepare URL:   https://sizning-domen.uz/api/click/prepare
Complete URL:  https://sizning-domen.uz/api/click/complete
```

> ⚠️ **Bu ikkala manzil ochiq bo'lishi kerak.** So'rov Click serveridan keladi —
> u login qila olmaydi va cookie/CSRF token yubormaydi. Auth middleware bo'lsa
> shu ikkitasini istisno qiling, aks holda Click 307/401 oladi va to'lovlar
> ishlamaydi. Xavfsizlik imzo orqali ta'minlanadi.

Domen **HTTPS** bo'lishi shart. Lokal sinash uchun [ngrok](https://ngrok.com).

## To'lov havolasini yasash

```ts
import { paymentUrl } from "@/click-payment";

// buyurtmaga unikal merchantTransId bering (bir marta)
const merchantTransId = `ORD${order.id}`;
await prisma.order.update({
  where: { id: order.id },
  data: { merchantTransId },
});

const url = paymentUrl(merchantTransId, order.price);
redirect(url);
```

`merchantTransId` bazangizda **unikal** bo'lishi shart — Click uni
prepare/complete so'rovlarida qaytarib yuboradi va siz shu orqali buyurtmani
topasiz. Bir nechta to'lov turi bo'lsa prefiks bilan ajrating: `ORD42` (xarid),
`SUB7` (obuna).

---

## Sinab ko'rish

```bash
npm install
npm test           # 26 ta test
npm run typecheck  # tsc --noEmit
```

Express namunasini haydash:

```bash
cp .env.example .env
npm run example:express
curl -X POST "http://localhost:8000/orders?product=Kitob&amount=5000"
```

---

## To'lov qanday o'tadi

```
  Foydalanuvchi          Sizning serveringiz              Click serveri
       │                         │                              │
       │  "sotib olaman"         │                              │
       ├────────────────────────>│                              │
       │                         │  paymentUrl(...)             │
       │      payUrl             │  (bazada: pending)           │
       │<────────────────────────┤                              │
       │                                                        │
       │  Click sahifasida kartasini tasdiqlaydi                │
       ├───────────────────────────────────────────────────────>│
       │                         │                              │
       │                         │   POST /api/click/prepare    │
       │                         │<─────────────────────────────┤
       │                         │  imzo + summa tekshiriladi   │
       │                         │  findOrder()                 │
       │                         │  error: 0, prepare_id: 42    │
       │                         ├─────────────────────────────>│
       │                         │                              │
       │                         │           💰 pul yechiladi    │
       │                         │                              │
       │                         │   POST /api/click/complete   │
       │                         │<─────────────────────────────┤
       │                         │  markPaid()  -> true         │
       │                         │  onPaid()    -> mahsulot!    │
       │                         │  error: 0                    │
       │                         ├─────────────────────────────>│
       │  return_url ga qaytadi  │                              │
       │<───────────────────────────────────────────────────────┤
```

**prepare** — "bu to'lovni qabul qila olasanmi?" Pul hali yechilmagan.
**complete** — "pul yechildi, mahsulotni ber." `onPaid()` shu yerda ishlaydi.

---

## Imzo (sign_string)

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
> holida kirishi kerak. Click `"5000.00"` yuborsa, `Number()` ga o'girib
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

1. **`return_url` ga tushish "to'landi" degani EMAS.** To'lovni faqat Click
   serveridan kelgan `complete` so'rovi tasdiqlaydi. Natija sahifasida holatni
   **bazangizdan** o'qing.

2. **`markPaid()` atomar bo'lsin.** "Node bir oqimli-ku" deb o'ylamang:
   Vercel/PM2/k8s da bir nechta instansiya parallel ishlaydi va `await`
   orasida boshqa so'rov kirib keladi. Prisma'da `update` emas, `updateMany`
   ishlating:

   ```ts
   const { count } = await prisma.order.updateMany({
     where: { id: order.id, status: "PENDING" },   // <- shart SQL ichida
     data: { status: "PAID", clickTransId },
   });
   return count > 0;
   ```

3. **`action` so'rovdan olinmaydi** — endpoint qaysi bo'lsa, o'shanikini
   ishlatamiz. Aks holda prepare imzosini complete'ga qo'yib yuborish mumkin
   bo'lardi.

4. **Summa har doim bazadan tekshiriladi.**

5. **`onPaid()` ichida uzoq ish qilmang** — Click javobni kutib turadi.

6. **Endpoint'larni middleware bilan yopmang** — yuqoriga qarang.

---

## Fayllar

```
click-payment/              ← loyihangizga shu papkani ko'chiring
├── click-orders.ts         ← FAQAT SHUNI TAHRIRLAYSIZ (bazangizga ulanish)
├── click-prepare.ts        prepare so'rovi
├── click-complete.ts       complete so'rovi
├── click-signature.ts      imzo qurish/tekshirish
├── click-config.ts         .env + to'lov havolasi
├── click-errors.ts         Click xato kodlari
├── click-utils.ts          so'rovni o'qish, yordamchilar
└── index.ts

examples/
├── nextjs-route-handlers.ts
└── express-app.ts

tests/
├── click.test.ts
└── e2e.test.ts
.env.example                ← sozlamalar
AI_PROMPT.md                ← AI'ga beriladigan ko'rsatma
```

Boshqa tillar: [`../python`](../python) · [`../php`](../php)

## Litsenziya

MIT
