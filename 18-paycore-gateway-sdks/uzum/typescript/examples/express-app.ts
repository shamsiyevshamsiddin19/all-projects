/**
 * Express loyihangizga ulash — to'liq ishlaydigan namuna.
 *
 * Click/Payme'dan farqli — Uzum Bank'da to'lov havolasi YO'Q va BESHTA
 * alohida webhook manzili kerak.
 *
 * Ishga tushirish:
 *     npm install express
 *     npx tsx examples/express-app.ts
 */

import express from "express";

import {
  demoCreateOrder,
  handleCheck,
  handleConfirm,
  handleCreate,
  handleReverse,
  handleStatus,
  getConfig,
} from "../uzum-payment/index.js";

const app = express();

app.use(express.json());

// =============================================================================
//  UZUM BANK WEBHOOK'LARI — loyihangizga aynan shu beshtasini qo'shasiz
// =============================================================================
//
// DIQQAT: bu manzillar auth middleware'dan OLDIN turishi yoki undan istisno
// qilinishi kerak. So'rovlar Uzum Bank serveridan keladi. Xavfsizlik HTTP
// Basic Auth orqali ta'minlanadi (handle*() funksiyalari ichida tekshiriladi).

app.post("/uzum/check", async (req, res) => {
  const [status, body] = await handleCheck(req.body, req.headers.authorization);
  res.status(status).json(body);
});

app.post("/uzum/create", async (req, res) => {
  const [status, body] = await handleCreate(req.body, req.headers.authorization);
  res.status(status).json(body);
});

app.post("/uzum/confirm", async (req, res) => {
  const [status, body] = await handleConfirm(req.body, req.headers.authorization);
  res.status(status).json(body);
});

app.post("/uzum/reverse", async (req, res) => {
  const [status, body] = await handleReverse(req.body, req.headers.authorization);
  res.status(status).json(body);
});

app.post("/uzum/status", async (req, res) => {
  const [status, body] = await handleStatus(req.body, req.headers.authorization);
  res.status(status).json(body);
});

// =============================================================================
//  SIZNING ILOVANGIZ
// =============================================================================

let nextOrderId = 1;

app.post("/orders", (req, res) => {
  const amountSom = Number(req.query.amount ?? 25000);
  const product = String(req.query.product ?? "Mahsulot");
  const orderId = String(nextOrderId++);

  demoCreateOrder(orderId, amountSom * 100, product);

  res.json({
    orderId,
    amountTiyin: amountSom * 100,
    serviceId: getConfig().serviceId,
    eslatma:
      "Foydalanuvchi Uzum Bank ilovasida xizmatingizni service_id orqali " +
      `topadi va 'account' maydoniga ${orderId} kiritadi.`,
  });
});

const port = Number(process.env.PORT ?? 8000);
app.listen(port, () => {
  console.log(`http://localhost:${port}`);
});
