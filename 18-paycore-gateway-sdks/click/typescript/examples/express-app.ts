/**
 * Express loyihangizga ulash — to'liq ishlaydigan namuna.
 *
 * Ishga tushirish:
 *     npm install express
 *     npx tsx examples/express-app.ts
 */

import express from "express";

import {
  demoCreateOrder,
  handleComplete,
  handlePrepare,
  orders,
  paymentUrl,
} from "../click-payment/index.js";

const app = express();

// ⚠️ ENG KO'P UNUTILADIGAN QATOR
//
// Click `application/x-www-form-urlencoded` POST yuboradi. Agar faqat
// `express.json()` qo'ysangiz, `req.body` BO'SH bo'ladi va hamma so'rov
// "-8 Error in request from click" oladi.
app.use(express.urlencoded({ extended: false }));
app.use(express.json());

// =============================================================================
//  CLICK ENDPOINT'LARI — loyihangizga aynan shu ikkitasini qo'shasiz
// =============================================================================
//
// DIQQAT: bu ikkala manzil auth middleware'dan OLDIN turishi yoki undan
// istisno qilinishi kerak. So'rov Click serveridan keladi — u login qila
// olmaydi. Xavfsizlik imzo (sign_string) orqali ta'minlanadi.

app.post("/click/prepare", async (req, res) => {
  res.json(await handlePrepare(req.body));
});

app.post("/click/complete", async (req, res) => {
  res.json(await handleComplete(req.body));
});

// =============================================================================
//  SIZNING ILOVANGIZ
// =============================================================================

let nextOrderId = 1;

app.post("/orders", async (req, res) => {
  const amount = Number(req.query.amount ?? 5000);
  const product = String(req.query.product ?? "Mahsulot");

  // O'z tizimingizda buyurtma allaqachon bazangizda bo'ladi — siz faqat
  // unga unikal merchantTransId berasiz.
  const order = await demoCreateOrder(`ORD${nextOrderId++}`, amount, {
    userId: 1,
    product,
  });

  res.json({
    merchantTransId: order.merchantTransId,
    amount: order.amount,
    payUrl: paymentUrl(order.merchantTransId, order.amount),
  });
});

app.get("/orders/:merchantTransId", async (req, res) => {
  const order = await orders.findOrder(req.params.merchantTransId);

  if (!order) {
    res.status(404).json({ error: "topilmadi" });
    return;
  }

  // To'lov holatini BAZADAN o'qiymiz — return_url ga ishonmaymiz.
  res.json({
    merchantTransId: order.merchantTransId,
    status: order.status,
    amount: order.amount,
  });
});

const port = Number(process.env.PORT ?? 8000);
app.listen(port, () => {
  console.log(`http://localhost:${port}`);
});
