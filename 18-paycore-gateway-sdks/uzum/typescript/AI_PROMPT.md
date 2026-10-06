# Uzum Bank to'lovini loyihaga ulash — AI uchun ko'rsatma (TypeScript)

> **Foydalanuvchi uchun:** bu faylni o'zingiz o'qishingiz shart emas.
> AI'ga shunday deng:
>
> ```
> uzum/typescript papkasidagi AI_PROMPT.md ni o'qi va Uzum Bank to'lovini
> loyihamga to'liq ulab ber.
> ```

---

## Topshiriq

Sen shu loyihaga Uzum Bank Merchant API'ni **to'liq ishlaydigan** holatda
ulaysan. `uzum-payment/` paketi tayyor.

**Uzum Bank Click/Payme'dan tubdan farq qiladi — bu farqni tushunmasdan
boshlama:**

1. **To'lov havolasi YO'Q.** Foydalanuvchi Uzum Bank ilovasida
   xizmatingizni `serviceId` orqali topadi va to'lovni O'SHA YERDA
   boshlaydi. `checkoutUrl()` kabi funksiya YOZMA — bunday narsa
   Uzum Bank protokolida umuman mavjud emas.
2. **Beshta ALOHIDA endpoint kerak** (`/check`, `/create`, `/confirm`,
   `/reverse`, `/status`).
3. **Xato holatida HTTP 400 qaytariladi** (Click/Payme'da har doim 200).
4. **Takroriy so'rov = XATO, muvaffaqiyat emas.** Bir xil `transId` bilan
   ikkinchi `/create` yoki `/confirm` — to'g'ri javob mos xato kodi
   (`10010` / `10016`), oldingi muvaffaqiyatni QAYTA qaytarish EMAS. Kodda
   bu allaqachon to'g'ri qilingan — "tuzatib qo'ymang".

Ishni **taxmin qilib emas, loyihani o'qib** boshla.

---

## 0-qadam: loyihani o'rgan

1. **Framework** — Next.js (App Router), Express, Hono?
2. **ORM** — Prisma, Drizzle, xom SQL?
3. **Buyurtma modeli** — narx qaysi maydonda?
4. **"Mahsulot berish" nima degani** — `onConfirmed()` ichida nima
   qilinishi kerak?
5. **Middleware** — global auth bormi?
6. **Path alias** — `@/*` bormi?

Aniqlanmasa — foydalanuvchidan so'ra.

---

## 1-qadam: paketni joylashtir

`uzum-payment/` ni loyihaga ko'chir. `npm install` kerak emas (faqat
`node:crypto`).

---

## 2-qadam: `.env`

```
UZUM_SERVICE_ID=
UZUM_WEBHOOK_LOGIN=
UZUM_WEBHOOK_SECRET=
```

⚠️ `NEXT_PUBLIC_` prefiksini HECH QACHON qo'shma.

---

## 3-qadam: modelga maydon qo'sh

```prisma
model UzumTransaction {
  transId     String   @id
  params      Json
  amount      Int
  state       String   // "CREATED" | "CONFIRMED" | "REVERSED"
  createTime  BigInt
  confirmTime BigInt   @default(0)
  reverseTime BigInt   @default(0)
}
```

---

## 4-qadam: `uzum-orders.ts` ni loyiha bazasiga bog'la

**Faqat shu faylni tahrirlaysan.** Xotiradagi namunani o'chirib,
`UzumOrdersAdapter` ni loyihaning ORM'i bilan yoz. `npx tsc --noEmit` bilan
tasdiqla — interfeysni noto'g'ri bajarsang shu yerda chiqadi.

### `findAccount(params)`

`params.account` — foydalanuvchi Uzum Bank ilovasida kiritgan qiymat.
`amount` TIYINDA.

### `markConfirmed(transId)`

**Atomar bo'lishi SHART:**
```ts
async markConfirmed(transId) {
  const { count } = await prisma.uzumTransaction.updateMany({
    where: { transId, state: "CREATED" },
    data: { state: "CONFIRMED", confirmTime: Date.now() },
  });
  if (count === 0) return null;      // <- boshqa so'rov ulgurgan
  return this.getTransaction(transId);
}
```

### `onConfirmed(transaction)`

Mahsulotni ber. Pul ALLAQACHON yechilgan — xato bersa ham qaytarilmaydi.

### `onReversed`, `canReverse`

Ixtiyoriy / standart `true`.

---

## 5-qadam: BESHTA endpoint qo'sh

```ts
// src/app/api/uzum/check/route.ts
import { NextResponse } from "next/server";
import { handleCheck } from "@/uzum-payment";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const [status, result] = await handleCheck(await req.json(), req.headers.get("authorization"));
  return NextResponse.json(result, { status });
}
```

Xuddi shunday `create/confirm/reverse/status` uchun ham. Namunalar:
`examples/nextjs-route-handlers.ts`, `examples/express-app.ts`.

**Endpoint'lar ochiq bo'lishi kerak** — `middleware.ts` da auth bo'lsa
`/api/uzum/*` ni istisno qil.

---

## 6-qadam: tekshir

1. **`npx tsc --noEmit`**
2. **Testlarni moslab ishlatib ko'r** (`tests/uzum.test.ts` xotiradagi
   namunaga tayangan), keyin `npm test`.
3. **Takroriy so'rov haqiqatan xato qaytarishini tekshir:**
   ```ts
   const [s1] = await handleCreate(data, auth);   // 200
   const [s2, b2] = await handleCreate(data, auth); // 400, errorCode="10010" <- SHART
   ```
4. **Auth'ni tekshir.**

---

## Qat'iy qoidalar

1. **Faqat `uzum-orders.ts` ni tahrirla.**
2. **`runtime = "nodejs"` ni olib tashlama** (Next.js).
3. **Checkout havolasi funksiyasini o'ylab topma.** Uzum Bank'da yo'q.
4. **Takroriy so'rovni idempotent qilib "tuzatma"** — ataylab xato qaytaradi.
5. **Summa TIYINDA.**
6. **Parolni `NEXT_PUBLIC_` qilma, kodga yozma.**

---

## Yakunda foydalanuvchiga ayt

1. `.env` ga qaysi 3 ta qiymatni kabinetdan olib qo'yish kerakligi.
2. Kabinetga yoziladigan callback manzil.
3. Migratsiya ishga tushirilishi kerakligi.
4. `onConfirmed()` ichiga aniq nima yozganing.
5. Uzum Bank'da to'lov havolasi yo'qligini tushuntirganingni.
6. Nimani tekshira olmaganing (haqiqiy Uzum Bank kabineti bilan sinov
   o'tkazilmagan).
