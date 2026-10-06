/**
 * Express loyihangizga ulash — to'liq ishlaydigan namuna.
 *
 * Click'dan farqli — Payme'da bitta endpoint bor: `/payme`. Payme "method"
 * maydoniga qarab qaysi amalni bajarishni o'zi aytadi.
 *
 * Ishga tushirish:
 *     npm install express
 *     npx tsx examples/express-app.ts
 */

import express from "express";

import {
  checkoutUrl,
  demoCreateOrder,
  handleRequest,
  orders,
  somToTiyin,
} from "../payme-payment/index.js";

const app = express();

app.use(express.json());

// =============================================================================
//  CLICK'DAN FARQLI — YAGONA ENDPOINT
// =============================================================================
//
// DIQQAT: bu manzil auth middleware'dan OLDIN turishi yoki undan istisno
// qilinishi kerak. So'rov Payme serveridan keladi. Xavfsizlik HTTP Basic
// Auth orqali ta'minlanadi (handleRequest ichida tekshiriladi).

app.post("/payme", async (req, res) => {
  const authorization = req.headers.authorization ?? null;
  res.json(await handleRequest(req.body, authorization));
});

// =============================================================================
//  SIZNING ILOVANGIZ
// =============================================================================

let nextOrderId = 1;

app.post("/orders", (req, res) => {
  const amount = Number(req.query.amount ?? 5000);
  const product = String(req.query.product ?? "Mahsulot");
  const orderId = `ORD${nextOrderId++}`;

  demoCreateOrder(orderId, somToTiyin(amount), product);

  res.json({
    orderId,
    amount,
    payUrl: checkoutUrl({ order_id: orderId }, somToTiyin(amount)),
  });
});

app.get("/orders/:orderId", async (req, res) => {
  const account = await orders.findAccount({ order_id: req.params.orderId });
  if (!account) {
    res.status(404).json({ error: "topilmadi" });
    return;
  }
  res.json({ orderId: req.params.orderId, payable: account.payable, amountTiyin: account.amount });
});

const port = Number(process.env.PORT ?? 8000);
app.listen(port, () => {
  console.log(`http://localhost:${port}`);
});
