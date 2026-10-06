# Uzum Bank to'lov integratsiyasi — TypeScript

[Uzum Bank](https://uzumbank.uz) Merchant API integratsiyasi — 5 webhook
(`check`, `create`, `confirm`, `reverse`, `status`). Faqat `node:crypto`ga
tayanadi — boshqa hech qanday bog'liqlik yo'q.

> ⚠️ **Uzum Bank Click/Payme'dan tubdan farq qiladi**: bu yerda "to'lov
> havolasi" (checkout URL) YO'Q. Foydalanuvchi Uzum Bank ilovasida
> xizmatingizni `serviceId` orqali qidirib topadi va to'lovni O'SHA YERDA
> boshlaydi. Sizning serveringiz faqat 5 ta webhook so'roviga javob beradi.

- ✅ 5 webhook to'liq — imzo o'rniga HTTP Basic Auth
- ✅ Uzum Bank'ning **idempotent-emas** protokoliga mos: takroriy
  `/create`/`/confirm` aniq xato qaytaradi (Click/Payme'dan farqli!)
- ✅ 30 daqiqalik avtomatik muddat tekshiruvi
- ✅ To'langandan keyin bekor qilish (refund) qo'llab-quvvatlanadi
- ✅ Next.js (App Router), Express
- ✅ 25 test

> **Node 18+**. Next.js Edge runtime'da ishlamaydi — `node:crypto` kerak.

---

## ⚠️ Next.js uchun eng muhim qator

```ts
export const runtime = "nodejs";   // Edge'da timingSafeEqual YO'Q
```

---

## 1. Papkani ko'chiring

`uzum-payment/` papkasini loyihangizga ko'chiring.

## 2. `.env` ni to'ldiring

| O'zgaruvchi | Nima bu |
|---|---|
| `UZUM_SERVICE_ID` | Xizmat ID — foydalanuvchi sizni shu orqali topadi |
| `UZUM_WEBHOOK_LOGIN` | Webhook auth login (kabinetda o'zingiz belgilaysiz) |
| `UZUM_WEBHOOK_SECRET` | Webhook auth parol (⚠️ `NEXT_PUBLIC_` PREFIKSSIZ) |

## 3. Kabinetga callback manzilini yozing

```
https://sizning-domen.uz/api/uzum
```

## 4. `uzum-orders.ts` ni bazangizga bog'lang

**Faqat shu faylni tahrirlaysiz.** `UzumOrdersAdapter` interfeysi — TypeScript
xatoni o'zi tutadi. Xotiradagi namuna tayyor (klon qilib sinaysiz), Prisma
namunasi fayl oxirida.

---

## Endpoint'larni ulash

<details open>
<summary><b>Next.js (App Router)</b></summary>

```ts
// src/app/api/uzum/check/route.ts
import { NextResponse } from "next/server";
import { handleCheck } from "@/uzum-payment";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const body = await req.json();
  const [status, result] = await handleCheck(body, req.headers.get("authorization"));
  return NextResponse.json(result, { status });
}
```

Xuddi shu shaklda `create`, `confirm`, `reverse`, `status` uchun ham
(`handleCreate`, `handleConfirm`, `handleReverse`, `handleStatus`).

To'liq namuna: [`examples/nextjs-route-handlers.ts`](examples/nextjs-route-handlers.ts)
</details>

<details>
<summary><b>Express</b></summary>

```ts
import { handleCheck } from "./uzum-payment/index.js";

app.post("/uzum/check", async (req, res) => {
  const [status, body] = await handleCheck(req.body, req.headers.authorization);
  res.status(status).json(body);
});
```

To'liq namuna: [`examples/express-app.ts`](examples/express-app.ts)
</details>

> ⚠️ Endpoint'lar auth middleware'dan istisno qilinishi kerak — so'rovlar
> Uzum Bank serveridan keladi, cookie/CSRF yo'q.

---

## Xato kodlari

| Kod | Ma'nosi | Qaysi metodda |
|---:|---|---|
| `10001` | Ruxsat yo'q (auth xato) | hammasi |
| `10005` | Majburiy maydon yo'q | hammasi |
| `10006` | Noto'g'ri `serviceId` | check, create |
| `10007` | Hisob topilmadi | check, create |
| `10008` | Allaqachon to'langan | check, create |
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
`/create` → `10010`, takroriy `/confirm` → `10016`. Testlarga qarang:
`takroriy create -> 10010 (idempotent EMAS)`.

## 30 daqiqalik muddat

`/create` dan keyin 30 daqiqa ichida `/confirm` kelmasa — SIZ o'zingiz
tranzaksiyani bekor deb belgilaysiz. Kod buni `handleConfirm`/`handleStatus`
ichida avtomatik bajaradi.

---

## Sinab ko'rish

```bash
npm install
npm test           # 25 test
npm run typecheck  # tsc --noEmit
```

Express namunasini haydash:

```bash
cp .env.example .env
npm run example:express
```

---

## Fayllar

```
uzum-payment/
├── uzum-orders.ts     ← FAQAT SHUNI TAHRIRLAYSIZ
├── uzum-methods.ts     5 webhook handleri
├── uzum-auth.ts         Basic Auth tekshiruvi
├── uzum-config.ts       .env
├── uzum-errors.ts       xato kodlari
└── index.ts

examples/
├── nextjs-route-handlers.ts
└── express-app.ts

tests/uzum.test.ts
.env.example
AI_PROMPT.md
```

Boshqa tillar: [`../python`](../python) · [`../php`](../php)
Boshqa to'lov tizimlari: [`../../click`](../../click) · [`../../payme`](../../payme)

## Litsenziya

MIT
