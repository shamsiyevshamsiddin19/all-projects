# Click to'lovini loyihaga ulash — AI uchun ko'rsatma (TypeScript)

> **Foydalanuvchi uchun:** bu faylni o'zingiz o'qishingiz shart emas.
> AI'ga (Claude Code, Cursor, Copilot, ChatGPT...) shunday deng:
>
> ```
> click/typescript papkasidagi AI_PROMPT.md ni o'qi va Click to'lovini
> loyihamga to'liq ulab ber.
> ```
>
> AI qolganini o'zi qiladi va oxirida sizdan nima talab qilinishini aytadi.

---

## Topshiriq

Sen shu loyihaga Click (my.click.uz) to'lov tizimini **to'liq ishlaydigan**
holatda ulaysan. `click-payment/` paketi tayyor — sen uni loyihaning bazasi va
framework'iga bog'laysan.

Ishni **taxmin qilib emas, loyihani o'qib** boshla.

---

## 0-qadam: loyihani o'rgan

Quyidagilarni aniqla va o'zingga yozib ol:

1. **Framework** — Next.js (App Router yoki Pages Router?), Express, Hono,
   NestJS, Remix? (`package.json`, `next.config.*`, papka tuzilishi)
2. **ORM / baza** — Prisma, Drizzle, TypeORM, xom SQL (`pg`, `mysql2`)?
   (`prisma/schema.prisma`, `drizzle.config.ts` ga qara)
3. **Buyurtma modeli** — to'lov qaysi modelga bog'lanadi? (`Order`, `Payment`,
   `Purchase`...) Narx qaysi maydonda va qaysi turda (`Int`, `Decimal`,
   `Float`)? Holat (`status`) qanday qiymatlarni oladi (`NEW`,
   `PENDING`, `PAID`...)?
4. **"Mahsulot berish" nima degani** — to'lov o'tgach nima bo'lishi kerak?
   Loyihada shunga o'xshash **mavjud funksiya** bormi — yangisini yozma, o'shani
   chaqir.
5. **Middleware / auth** — `middleware.ts` bormi? Global auth bormi? (Bu muhim
   — 5-qadamga qara.)
6. **Path alias** — `tsconfig.json` da `@/*` bormi? Import'larni shunga qarab yoz.

Agar 3 yoki 4-band kodni o'qib aniqlanmasa — **foydalanuvchidan so'ra**, taxmin
qilma. Qolganini o'zing hal qil.

---

## 1-qadam: paketni joylashtir

`click-payment/` papkasini loyihaga ko'chir (`src/click-payment/` yoki
`lib/click-payment/`). Import qilinishini tekshir.

Paket faqat `node:crypto` ga tayanadi — `npm install` kerak emas.

---

## 2-qadam: `.env`

`.env.example` dagi o'zgaruvchilarni loyihaning `.env` ga qo'sh:

```
CLICK_SERVICE_ID=
CLICK_MERCHANT_ID=
CLICK_SECRET_KEY=
CLICK_MERCHANT_USER_ID=
CLICK_RETURN_URL=
```

- Qiymatlarni **sen to'ldirmaysan** — foydalanuvchi kabinetdan oladi. Bo'sh
  qoldir va oxirida unga ayt.
- ⚠️ **`NEXT_PUBLIC_` prefiksini HECH QACHON qo'shma** — secret_key brauzerga
  chiqib ketadi.
- Loyihada sozlama tipli obyektda saqlansa (`env.ts`, `t3-env`, zod), `.env`
  o'rniga `setConfig()` ni ishlat va uni endpoint'lardan oldin chaqir:
  ```ts
  setConfig({
    serviceId: env.CLICK_SERVICE_ID,
    merchantId: env.CLICK_MERCHANT_ID,
    secretKey: env.CLICK_SECRET_KEY,
    merchantUserId: env.CLICK_MERCHANT_USER_ID,
  });
  ```
- `.env` `.gitignore` da borligini tekshir.

---

## 3-qadam: modelga ikkita maydon qo'sh

Prisma:

```prisma
model Order {
  // ...
  merchantTransId String?   @unique   // <- @unique SHART
  clickTransId    String?
  paidAt          DateTime?
}
```

- Migratsiya yarat (`prisma migrate dev --name click_payment`), qo'lda SQL yozma.
- Drizzle bo'lsa — schema fayliga qo'shib, `drizzle-kit generate` qil.
- Mos maydonlar allaqachon bo'lsa — yangisini qo'shma, borini ishlat.

---

## 4-qadam: `click-orders.ts` ni loyiha bazasiga bog'la

**Faqat shu faylni tahrirlaysan.** Xotiradagi namunani (`demoRows`,
`demoCreateOrder`, `demoReset` va `orders` obyektining ichi) o'chirib,
`ClickOrdersAdapter` ni loyihaning ORM'i bilan yoz. Fayl oxirida Prisma,
Drizzle va xom SQL uchun namunalar bor.

TypeScript interfeysni o'zi tekshiradi — `npx tsc --noEmit` bilan tasdiqla.

### `findOrder(merchantTransId): Promise<ClickOrder | null>`

- `id` — raqamli id (Click'ga `merchant_prepare_id` bo'lib ketadi). Model
  `id` i `string`/`cuid` bo'lsa, `merchantTransId` dan raqam ajratib olishga
  urinma — modelga alohida `Int @default(autoincrement())` maydon qo'sh yoki
  foydalanuvchidan so'ra.
- `amount` — `number`. Prisma `Decimal` qaytarsa `Number(o.amount)` qil.
- `status` — loyihaning holatini `"pending"` / `"paid"` / `"cancelled"` ga
  **o'girib** ber:
  ```ts
  const statusMap: Record<string, ClickOrderStatus> = {
    NEW: "pending",
    PENDING: "pending",
    PAID: "paid",
    DELIVERED: "paid",     // allaqachon bajarilgan
  };
  status: statusMap[o.status] ?? "cancelled",
  ```
  Diqqat: allaqachon bajarilgan buyurtma `"paid"` bo'lishi kerak, aks holda
  ikkinchi marta to'lanib ketadi.
- `extra` — `onPaid()` da kerak bo'ladigan hamma narsa.

### `markPaid(order, clickTransId): Promise<boolean>`

**Bu yerda xato qilish — eng qimmat xato.**

Shartni **bazaning o'ziga** qo'y va o'zgargan qatorlar sonini qaytar:

```ts
// TO'G'RI — atomar
const { count } = await prisma.order.updateMany({
  where: { id: order.id, status: "PENDING" },
  data: { status: "PAID", clickTransId, paidAt: new Date() },
});
return count > 0;
```

```ts
// NOTO'G'RI — poyga bor, mahsulot IKKI MARTA beriladi
if (order.status === "pending") {              // avval o'qish
  await prisma.order.update({ where: { id: order.id }, data: { status: "PAID" } });
  return true;                                 // keyin yozish
}
```

"Node bir oqimli-ku, poyga bo'lmaydi" deb o'ylama: Vercel/PM2/k8s da bir
nechta instansiya parallel ishlaydi va `await` orasida boshqa so'rov kirib
keladi. `update` emas, **`updateMany` + `where.status`** ishlat.

Drizzle: `result.rowCount > 0` (pg) / `result.rowsAffected > 0` (mysql).

### `markCancelled(order, clickTransId): Promise<void>`

Buyurtmani bekor qilingan holatga o'tkaz (faqat u hali pending bo'lsa).

### `onPaid(order): Promise<void>`

Mahsulotni shu yerda ber — 0-qadamning 4-bandida aniqlagan ishni qil. Bir
nechta yozuvni o'zgartirsang `prisma.$transaction` ga o'ra.

- Uzoq ish qilma — Click javobni kutib turadi. Og'ir ishni navbatga qo'y.
- Bu funksiya xato bersa, to'lov baribir `paid` bo'lib qoladi va xato logga
  yoziladi — bu ataylab shunday.

### `onCancelled(order): Promise<void>`

Ixtiyoriy.

---

## 5-qadam: endpoint'larni ula

### Next.js (App Router)

```ts
// src/app/api/click/prepare/route.ts
import { NextResponse } from "next/server";
import { handlePrepare, readRequestData } from "@/click-payment";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  return NextResponse.json(await handlePrepare(await readRequestData(req)));
}
```

`complete` uchun ham xuddi shunday (`handleComplete`).

**`export const runtime = "nodejs"` — MAJBURIY.** Click imzosi md5 bilan
hisoblanadi, Web Crypto API esa md5 ni umuman qo'llab-quvvatlamaydi. Edge
runtime'da butun integratsiya ishlamaydi. `dynamic = "force-dynamic"` ham
qo'y — callback keshlanmasin.

### Express

```ts
app.use(express.urlencoded({ extended: false }));   // ⚠️ SHUSIZ hamma so'rov -8 oladi

app.post("/click/prepare", async (req, res) => {
  res.json(await handlePrepare(req.body));
});
```

Click `application/x-www-form-urlencoded` yuboradi. Faqat `express.json()`
bo'lsa `req.body` bo'sh keladi.

### Hono / Bun / Deno

```ts
app.post("/click/prepare", async (c) =>
  c.json(await handlePrepare(await readRequestData(c.req.raw))),
);
```

### Eng ko'p unutiladigan narsa — endpoint'lar ochiq bo'lishi kerak

- So'rovlar **Click serveridan** keladi. Click login qila olmaydi, cookie va
  CSRF token yubormaydi.
- `middleware.ts` da auth bo'lsa `/api/click/*` ni **istisno** qil:
  ```ts
  export const config = {
    matcher: ["/((?!api/click|_next/static|_next/image).*)"],
  };
  ```
- Express/NestJS'da auth guard'dan chiqar. Rate-limit bo'lsa ham chiqar.

Xavfsizlik imzo (`sign_string`) orqali ta'minlanadi — `handlePrepare()` va
`handleComplete()` ichida tekshiriladi. Qo'shimcha auth kerak emas.

---

## 6-qadam: to'lov havolasi

```ts
import { paymentUrl } from "@/click-payment";

// buyurtmaga unikal merchantTransId ber (bir marta)
if (!order.merchantTransId) {
  await prisma.order.update({
    where: { id: order.id },
    data: { merchantTransId: `ORD${order.id}` },
  });
}

const url = paymentUrl(`ORD${order.id}`, Number(order.price));
redirect(url);
```

Bir nechta to'lov turi bo'lsa prefiks bilan ajrat: `ORD42` (xarid), `SUB7`
(obuna) — `findOrder()` ichida prefiksga qarab kerakli modelni topasan.

---

## 7-qadam: tekshir — bu qadamni o'tkazib yuborma

1. **`npx tsc --noEmit`** — tip xatosi bo'lmasin. `ClickOrdersAdapter` ni
   noto'g'ri bajargan bo'lsang, shu yerda chiqadi.

2. **Testlarni moslab ishlatib ko'r.**

   `tests/click.test.ts` xotiradagi namunaga tayangan (`demoCreateOrder`,
   `demoReset`). Sen `click-orders.ts` ni o'zgartirganingdan keyin ular
   ishlamaydi — testlarni loyihaning test bazasiga moslab yoz, keyin:

   ```
   npm test
   ```

   Bu testlar imzo, summa, takroriy callback va bekor qilishni tekshiradi —
   o'chirib tashlama, moslab qo'y.

3. **`markPaid` ikki marta `true` qaytarmasligini alohida tekshir:**

   ```ts
   assert.equal(await orders.markPaid(order, "123"), true);
   assert.equal(await orders.markPaid(order, "123"), false);   // <- shu SHART
   ```

4. **Serverni ko'tarib, prepare/complete ni imitatsiya qil** — imzoni qo'lda
   hisoblab, form-encoded POST yubor:

   ```bash
   curl -X POST http://localhost:3000/api/click/prepare \
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

5. **Middleware bu endpoint'larni bloklamayotganini tekshir** — login qilmasdan
   POST yuborib ko'r, 307/401 kelmasligi kerak.

---

## Qat'iy qoidalar

1. **Faqat `click-orders.ts` ni tahrirla.** `click-prepare.ts`,
   `click-complete.ts`, `click-signature.ts`, `click-config.ts`,
   `click-errors.ts`, `click-utils.ts` — tegma.

2. **`runtime = "nodejs"` ni olib tashlama** (Next.js). Edge'da md5 yo'q.

3. **`amount` ni imzo uchun qayta formatlama.** `Number("5000.00")` → `"5000"`
   bo'lib imzo buziladi. Kod buni to'g'ri qiladi — aralashma.

4. **`secret_key` ni kodga yozma, `NEXT_PUBLIC_` qilma, loglarga chiqarma.**

5. **`return_url` ga tushishni "to'landi" deb hisoblama.** Holatni bazadan o'qi.

6. **Click'ning `error` maydonini `sign_string` bilan aralashtirma.** U
   complete'da "foydalanuvchi bekor qildi" degani va imzoga kirmaydi.

7. **To'lov holatini faqat `complete` tasdiqlaydi**, `prepare` emas.

---

## Yakunda foydalanuvchiga ayt

1. `.env` ga qaysi 4 ta qiymatni kabinetdan olib qo'yish kerakligi.
2. Click kabinetiga yozilishi kerak bo'lgan **aniq** manzillar:
   ```
   Prepare URL:   https://<domen>/api/click/prepare
   Complete URL:  https://<domen>/api/click/complete
   ```
   Domen HTTPS va tashqaridan ochiq bo'lishi shart (lokal sinash uchun ngrok).
3. Migratsiya ishga tushirilishi kerakligi (`prisma migrate deploy`).
4. `onPaid()` ichiga aniq nima yozganing.
5. Nimani tekshirganing va nimani tekshira olmaganing (masalan: haqiqiy Click
   kabineti bilan sinov o'tkazilmagan).
