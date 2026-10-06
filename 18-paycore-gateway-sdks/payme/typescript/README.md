# Payme to'lov integratsiyasi — TypeScript

[Payme](https://payme.uz) (checkout.paycom.uz / business.payme.uz) to'lov
tizimining **Merchant API** integratsiyasi. Nol tashqi bog'liqlik — faqat
`node:crypto`.

- ✅ Oltita metod to'liq: `CheckPerformTransaction`, `CreateTransaction`,
  `PerformTransaction`, `CancelTransaction`, `CheckTransaction`, `GetStatement`
- ✅ HTTP Basic Auth tekshiruvi — `timingSafeEqual` bilan
- ✅ 12 soatlik avtomatik timeout
- ✅ To'langandan keyingi bekor qilish (refund) qo'llab-quvvatlanadi
- ✅ Takroriy so'rovlarga chidamli (idempotent)
- ✅ Tipli shartnoma — `PaymeOrdersAdapter` interfeysi
- ✅ 30 ta test
- ✅ Next.js (App Router), Express

> **Node 18+**. Bu repo'da [Click](../../click/typescript) integratsiyasi
> ham bor — ikkalasi bir xil naqshda, lekin protokollari tubdan farq qiladi.

---

## ⚠️ Next.js uchun eng muhim ikkita qator

```ts
// app/api/payme/route.ts
export const runtime = "nodejs";        // Edge'da timingSafeEqual YO'Q
export const dynamic = "force-dynamic";
```

Basic Auth tekshiruvi `node:crypto` (`timingSafeEqual`) bilan ishlaydi —
Web Crypto API buni bermaydi, shuning uchun Edge runtime ishlamaydi.

---

## Payme Click'dan nimasi bilan farq qiladi

| | Click | Payme |
|---|---|---|
| Endpoint soni | 2 (`prepare`, `complete`) | **1** (hammasi `method` maydoniga qarab) |
| Autentifikatsiya | `sign_string` (md5 imzo) | **HTTP Basic Auth** |
| Summa birligi | so'm | **tiyin** (1 so'm = 100 tiyin) |
| Metodlar soni | 2 | **6** |
| Muddat | yo'q | **12 soat** |
| To'langandan keyin bekor qilish | yo'q | **bor** (refund) |
| To'lov havolasi | query-string | **base64** kodlangan `key=value;...` |

---

## 3 qadamda ulash

### 1-qadam: papkani ko'chiring

`payme-payment/` papkasini loyihangizga ko'chiring.

### 2-qadam: `.env` ni to'ldiring

| O'zgaruvchi | Majburiy | Nima bu |
|---|:---:|---|
| `PAYME_MERCHANT_ID` | ✅ | Kassa ID |
| `PAYME_SECRET_KEY` | ✅ | **Maxfiy kalit** |
| `PAYME_MERCHANT_LOGIN` | ➖ | Odatda `Paycom` |

### 3-qadam: `payme-orders.ts` ni o'z bazangizga moslang

**Faqat shu faylni tahrirlaysiz.** `PaymeOrdersAdapter` interfeysi ikki
guruh metoddan iborat:

```ts
export const orders: PaymeOrdersAdapter = {
  // BIZNES
  async findAccount(account) { /* buyurtmani toping */ },
  async onPaid(tx) { /* mahsulotni bering */ },
  async onCancelled(tx) { /* ixtiyoriy */ },
  async canRefund(tx) { return true; },

  // TRANZAKSIYA KUNDALIGI — Payme talab qiladi
  async getTransaction(paymeId) { /* ... */ },
  async getActiveTransactionForAccount(account) { /* ... */ },
  async createTransaction(paymeId, paymeTime, amount, account) { /* ... */ },
  async markPerformed(paymeId) { /* -> PaymeTransaction | null, atomar! */ },
  async markCancelled(paymeId, reason) { /* ... */ },
  async listTransactions(fromMs, toMs) { /* ... */ },
};
```

Hozir xotirada ishlaydigan namuna turibdi (klon qilib darrov sinaysiz, lekin
ishlab chiqarishga yaroqsiz). Fayl **oxirida** Prisma namunasi bor.

---

## Endpoint (bitta manzil)

<details open>
<summary><b>Next.js (App Router)</b></summary>

```ts
// src/app/api/payme/route.ts
import { NextResponse } from "next/server";
import { handleRequest } from "@/payme-payment";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const body = await req.json();
  return NextResponse.json(await handleRequest(body, req.headers.get("authorization")));
}
```

`middleware.ts` da auth bo'lsa `/api/payme` ni istisno qiling.

To'liq namuna: [`examples/nextjs-route-handler.ts`](examples/nextjs-route-handler.ts)
</details>

<details>
<summary><b>Express</b></summary>

```ts
import express from "express";
import { handleRequest } from "./payme-payment/index.js";

const app = express();
app.use(express.json());

app.post("/payme", async (req, res) => {
  res.json(await handleRequest(req.body, req.headers.authorization ?? null));
});
```

To'liq namuna: [`examples/express-app.ts`](examples/express-app.ts)
</details>

Kabinetga yoziladigan manzil: `https://sizning-domen.uz/api/payme`

## To'lov havolasi

```ts
import { checkoutUrl, somToTiyin } from "@/payme-payment";

const url = checkoutUrl({ order_id: order.id }, somToTiyin(order.priceSom));
```

`somToTiyin()` ni unutmang — Payme summani TIYINDA kutadi.

---

## Sinab ko'rish

```bash
npm install
npm test           # 30 ta test
npm run typecheck  # tsc --noEmit
npm run example:express
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

## Xavfsizlik

1. **`PAYME_SECRET_KEY` faqat `.env` da**, `NEXT_PUBLIC_` prefiksisiz.
2. **`markPerformed`/`markCancelled` atomar bo'lsin** — Prisma'da `update`
   emas, `updateMany` + `where.state` ishlating (Click'dagi `markPaid` bilan
   bir xil qoida).
3. **Summa har doim bazadan tekshiriladi.**
4. **`onPaid()` ichida uzoq ish qilmang.**

## Fayllar

```
payme-payment/
├── payme-orders.ts      ← FAQAT SHUNI TAHRIRLAYSIZ
├── payme-methods.ts     6 metod + JSON-RPC dispatcher
├── payme-auth.ts        Basic Auth
├── payme-checkout.ts    to'lov havolasi
├── payme-config.ts      .env
├── payme-errors.ts      xato kodlari
└── index.ts

examples/
├── nextjs-route-handler.ts
└── express-app.ts

tests/payme.test.ts
AI_PROMPT.md
```

Boshqa tillar: [`../python`](../python) · [`../php`](../php)

## Litsenziya

MIT
