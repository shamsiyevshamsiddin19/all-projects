# Payme to'lovini loyihaga ulash — AI uchun ko'rsatma (TypeScript)

> **Foydalanuvchi uchun:** bu faylni o'zingiz o'qishingiz shart emas.
> AI'ga shunday deng:
>
> ```
> payme/typescript papkasidagi AI_PROMPT.md ni o'qi va Payme to'lovini
> loyihamga to'liq ulab ber.
> ```

---

## Topshiriq

Sen shu loyihaga Payme (checkout.paycom.uz) to'lov tizimini **to'liq
ishlaydigan** holatda ulaysan. `payme-payment/` paketi tayyor — sen uni
loyihaning bazasi va framework'iga bog'laysan.

Ishni **taxmin qilib emas, loyihani o'qib** boshla. Agar loyihada
[Click integratsiyasi](../../click/typescript) allaqachon ulangan bo'lsa,
o'sha `click-orders.ts` ni ham o'qi — bir xil buyurtma modeliga ulanasan.

---

## 0-qadam: loyihani o'rgan

1. Framework — Next.js (App Router?), Express, Hono, NestJS?
2. ORM — Prisma, Drizzle, TypeORM, xom SQL?
3. Buyurtma modeli — narx qaysi maydonda, qaysi birlikda? **Payme summani
   TIYINDA kutadi** (1 so'm = 100 tiyin) — bazada so'mda saqlangan bo'lsa
   `findAccount()` ichida `* 100` qil.
4. "Mahsulot berish" — mavjud funksiyani ishlat.
5. `middleware.ts` da global auth bormi?
6. `tsconfig.json` da `@/*` alias bormi?

Aniqlanmasa — foydalanuvchidan so'ra.

---

## 1-qadam: paketni joylashtir

`payme-payment/` papkasini ko'chir. Faqat `node:crypto` ga tayanadi —
`npm install` kerak emas.

---

## 2-qadam: `.env`

```
PAYME_MERCHANT_ID=
PAYME_SECRET_KEY=
```

Qiymatlarni **sen to'ldirmaysan**. ⚠️ `NEXT_PUBLIC_` prefiksini hech qachon
qo'shma. Sozlamani loyiha config'idan bermoqchi bo'lsang:

```ts
setConfig({
  merchantId: env.PAYME_MERCHANT_ID,
  secretKey: env.PAYME_SECRET_KEY,
});
```

---

## 3-qadam: modelga tranzaksiya kundaligi qo'sh

Payme protokoli o'z bookkeeping'ini talab qiladi. Prisma:

```prisma
model PaymeTransaction {
  paymeId     String   @id
  ourId       String
  accountJson String
  amount      Int      // TIYINDA
  state       Int
  paymeTime   BigInt
  createTime  BigInt
  performTime BigInt   @default(0)
  cancelTime  BigInt   @default(0)
  reason      Int?

  @@index([createTime])
}
```

Migratsiya yarat (`prisma migrate dev`), qo'lda SQL yozma.

---

## 4-qadam: `payme-orders.ts` ni loyiha bazasiga bog'la

Xotiradagi namunani (`demoOrders`, `demoTransactions`, `demoCreateOrder`,
`demoReset` va `orders` obyektining ichi) o'chirib, `PaymeOrdersAdapter` ni
loyihaning ORM'i bilan yoz. Fayl oxirida Prisma namunasi bor.

TypeScript interfeysni o'zi tekshiradi — `npx tsc --noEmit` bilan tasdiqla.

### Biznes qismi

`findAccount(account)` — `account.order_id` orqali buyurtmani top,
`{ id, amount (TIYINDA!), payable, extra }` qaytar. Allaqachon
to'langan/bekor bo'lgan buyurtma uchun `payable: false`.

`onPaid(tx)` — mahsulotni ber. Uzoq ish qilma.

`onCancelled(tx)` — `tx.state === PaymeState.CANCELLED_AFTER_PAID` bo'lsa bu
QAYTARISH — ruxsatni bekor qil.

`canRefund(tx)` — to'langanni bekor qilish mumkinmi? Standart `true`.

### Tranzaksiya kundaligi — atomarlikni saqla

```ts
// TO'G'RI — atomar
async markPerformed(paymeId) {
  const { count } = await prisma.paymeTransaction.updateMany({
    where: { paymeId, state: 1 },
    data: { state: 2, performTime: Date.now() },
  });
  if (count === 0) return null;   // <- allaqachon to'langan, onPaid QAYTA chaqirilmaydi
  return this.getTransaction(paymeId);
}
```

"Node bir oqimli-ku" deb o'ylama — Vercel/PM2/k8s da bir nechta instansiya
parallel ishlaydi. `update` emas, `updateMany` + `where.state` ishlat.

---

## 5-qadam: bitta endpoint qo'sh

Click'dagidek IKKITA emas, **BITTA**:

```ts
// src/app/api/payme/route.ts
import { NextResponse } from "next/server";
import { handleRequest } from "@/payme-payment";

export const runtime = "nodejs";       // MAJBURIY — Edge'da timingSafeEqual yo'q
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  const body = await req.json();
  return NextResponse.json(await handleRequest(body, req.headers.get("authorization")));
}
```

Express:
```ts
app.use(express.json());
app.post("/payme", async (req, res) => {
  res.json(await handleRequest(req.body, req.headers.authorization ?? null));
});
```

**Auth**: HTTP Basic Auth (`handleRequest` ichida avtomatik tekshiriladi).
`middleware.ts` da global auth bo'lsa `/api/payme` ni istisno qil:

```ts
export const config = {
  matcher: ["/((?!api/payme|_next/static|_next/image).*)"],
};
```

---

## 6-qadam: to'lov havolasi

```ts
import { checkoutUrl, somToTiyin } from "@/payme-payment";

const url = checkoutUrl({ order_id: order.id }, somToTiyin(order.priceSom));
```

---

## 7-qadam: tekshir

1. `npx tsc --noEmit` — tip xatosi bo'lmasin.
2. `tests/payme.test.ts` xotiradagi namunaga tayangan — loyihaning test
   bazasiga moslab yoz, keyin `npm test`.
3. `markPerformed` ikki marta `null` bo'lmagan natija qaytarmasligini tekshir.
4. Serverni ko'tarib, oltita metodni Basic Auth bilan qo'lda sina.
5. Middleware `/api/payme` ni bloklamayotganini tekshir.

---

## Qat'iy qoidalar

1. Faqat `payme-orders.ts` ni tahrirla.
2. `runtime = "nodejs"` ni olib tashlama (Next.js).
3. Summa har doim TIYINDA.
4. `PAYME_SECRET_KEY` ni `NEXT_PUBLIC_` qilma.
5. `createTime` — server vaqti, Payme yuborgan `time` emas.
6. Takroriy `CancelTransaction` — sababni yangilama.

---

## Yakunda foydalanuvchiga ayt

1. `.env` ga `PAYME_MERCHANT_ID` va `PAYME_SECRET_KEY`.
2. Kabinetga yoziladigan yagona manzil: `https://<domen>/api/payme`.
3. Migratsiya ishga tushirilishi kerakligi.
4. `onPaid()`/`onCancelled()` ichiga nima yozganing.
5. Sandbox bilan sinov o'tkazilmagani.
