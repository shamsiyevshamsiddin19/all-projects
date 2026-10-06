/**
 * handlePrepare va handleComplete testlari.
 *
 * Ishga tushirish (loyiha ildizidan):
 *
 *     npm install
 *     npm test
 */

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { beforeEach, describe, it } from "node:test";

import {
  ClickError,
  demoCreateOrder,
  demoReset,
  handleComplete,
  handlePrepare,
  orders,
  paymentUrl,
  setConfig,
  type ClickOrdersAdapter,
  type ClickRequestData,
} from "../click-payment/index.js";

const SERVICE_ID = "12345";
const SECRET_KEY = "test_secret_key";
const SIGN_TIME = "2026-07-17 12:00:00";
const CLICK_TRANS_ID = "987654321";

/** Imzoni "qo'lda" hisoblaymiz — kutubxona kodidan mustaqil tekshirish uchun. */
function sign(...parts: string[]): string {
  return createHash("md5").update(parts.join(""), "utf8").digest("hex");
}

function prepareReq(
  merchantTransId: string,
  amount: string,
  over: ClickRequestData = {},
): ClickRequestData {
  return {
    click_trans_id: CLICK_TRANS_ID,
    service_id: SERVICE_ID,
    merchant_trans_id: merchantTransId,
    amount,
    action: "0",
    sign_time: SIGN_TIME,
    sign_string: sign(
      CLICK_TRANS_ID,
      SERVICE_ID,
      SECRET_KEY,
      merchantTransId,
      amount,
      "0",
      SIGN_TIME,
    ),
    ...over,
  };
}

function completeReq(
  merchantTransId: string,
  amount: string,
  prepareId: number,
  over: ClickRequestData = {},
): ClickRequestData {
  return {
    click_trans_id: CLICK_TRANS_ID,
    service_id: SERVICE_ID,
    merchant_trans_id: merchantTransId,
    merchant_prepare_id: String(prepareId),
    amount,
    action: "1",
    error: "0",
    sign_time: SIGN_TIME,
    sign_string: sign(
      CLICK_TRANS_ID,
      SERVICE_ID,
      SECRET_KEY,
      merchantTransId,
      String(prepareId),
      amount,
      "1",
      SIGN_TIME,
    ),
    ...over,
  };
}

/** onPaid/onCancelled chaqiruvlarini yozib boradigan adapter. */
function tracking() {
  const paid: string[] = [];
  const cancelled: string[] = [];

  const adapter: ClickOrdersAdapter = {
    ...orders,
    async onPaid(order) {
      paid.push(order.merchantTransId);
    },
    async onCancelled(order) {
      cancelled.push(order.merchantTransId);
    },
  };

  return { adapter, paid, cancelled };
}

beforeEach(() => {
  demoReset();
  setConfig(null);
  setConfig({
    serviceId: SERVICE_ID,
    merchantId: "54321",
    secretKey: SECRET_KEY,
    merchantUserId: "67890",
  });
});

// =============================================================================

describe("prepare", () => {
  it("muvaffaqiyatli", async () => {
    const order = await demoCreateOrder("ORD1", 5000);

    const res = await handlePrepare(prepareReq("ORD1", "5000"));

    assert.equal(res.error, ClickError.SUCCESS);
    assert.equal(res.merchant_prepare_id, order.id);
    assert.equal(res.merchant_trans_id, "ORD1");
  });

  it('"5000.00" kasrli summani qabul qiladi', async () => {
    await demoCreateOrder("ORD1", 5000);

    const res = await handlePrepare(prepareReq("ORD1", "5000.00"));

    assert.equal(res.error, ClickError.SUCCESS);
  });

  it("soxta imzoni rad etadi", async () => {
    await demoCreateOrder("ORD1", 5000);

    const res = await handlePrepare(
      prepareReq("ORD1", "5000", { sign_string: "a".repeat(32) }),
    );

    assert.equal(res.error, ClickError.SIGN_CHECK_FAILED);
  });

  it("boshqa service_id ni rad etadi", async () => {
    await demoCreateOrder("ORD1", 5000);

    const res = await handlePrepare(
      prepareReq("ORD1", "5000", { service_id: "99999" }),
    );

    assert.equal(res.error, ClickError.SIGN_CHECK_FAILED);
  });

  it("to'liqmas so'rovni rad etadi", async () => {
    await demoCreateOrder("ORD1", 5000);
    const req = prepareReq("ORD1", "5000");
    delete req.sign_time;

    const res = await handlePrepare(req);

    assert.equal(res.error, ClickError.BAD_REQUEST);
  });

  it("noto'g'ri summani rad etadi", async () => {
    await demoCreateOrder("ORD1", 5000);

    const res = await handlePrepare(prepareReq("ORD1", "100"));

    assert.equal(res.error, ClickError.INCORRECT_AMOUNT);
  });

  it("topilmagan buyurtmaga -5 qaytaradi", async () => {
    const res = await handlePrepare(prepareReq("YOQ404", "5000"));

    assert.equal(res.error, ClickError.USER_NOT_FOUND);
  });

  it("to'langan buyurtmaga -4 qaytaradi", async () => {
    const order = await demoCreateOrder("ORD1", 5000);
    await orders.markPaid(order, CLICK_TRANS_ID);

    const res = await handlePrepare(prepareReq("ORD1", "5000"));

    assert.equal(res.error, ClickError.ALREADY_PAID);
  });

  it("bekor qilingan buyurtmaga -9 qaytaradi", async () => {
    const order = await demoCreateOrder("ORD1", 5000);
    await orders.markCancelled(order, CLICK_TRANS_ID);

    const res = await handlePrepare(prepareReq("ORD1", "5000"));

    assert.equal(res.error, ClickError.TRANSACTION_CANCELLED);
  });
});

// =============================================================================

describe("complete", () => {
  it("muvaffaqiyatli va onPaid ni chaqiradi", async () => {
    const { adapter, paid } = tracking();
    const order = await demoCreateOrder("ORD1", 5000, { userId: 7 });
    await handlePrepare(prepareReq("ORD1", "5000"), adapter);

    const res = await handleComplete(completeReq("ORD1", "5000", order.id), adapter);

    assert.equal(res.error, ClickError.SUCCESS);
    assert.equal(res.merchant_confirm_id, order.id);
    assert.equal((await orders.findOrder("ORD1"))?.status, "paid");
    assert.deepEqual(paid, ["ORD1"]);
  });

  it("takroriy callback: OK, lekin onPaid FAQAT BIR MARTA", async () => {
    const { adapter, paid } = tracking();
    const order = await demoCreateOrder("ORD1", 5000);
    await handlePrepare(prepareReq("ORD1", "5000"), adapter);

    const first = await handleComplete(completeReq("ORD1", "5000", order.id), adapter);
    const second = await handleComplete(completeReq("ORD1", "5000", order.id), adapter);

    assert.equal(first.error, ClickError.SUCCESS);
    assert.equal(second.error, ClickError.SUCCESS);
    assert.deepEqual(paid, ["ORD1"]);
  });

  it("soxta imzoni rad etadi va bazani o'zgartirmaydi", async () => {
    const { adapter, paid } = tracking();
    const order = await demoCreateOrder("ORD1", 5000);
    await handlePrepare(prepareReq("ORD1", "5000"), adapter);

    const res = await handleComplete(
      completeReq("ORD1", "5000", order.id, { sign_string: "b".repeat(32) }),
      adapter,
    );

    assert.equal(res.error, ClickError.SIGN_CHECK_FAILED);
    assert.equal((await orders.findOrder("ORD1"))?.status, "pending");
    assert.deepEqual(paid, []);
  });

  it("prepare imzosi complete'da ishlamaydi", async () => {
    const order = await demoCreateOrder("ORD1", 5000);
    const p = prepareReq("ORD1", "5000");

    const res = await handleComplete(
      completeReq("ORD1", "5000", order.id, { sign_string: p.sign_string }),
    );

    assert.equal(res.error, ClickError.SIGN_CHECK_FAILED);
  });

  it("noto'g'ri merchant_prepare_id ni rad etadi", async () => {
    const order = await demoCreateOrder("ORD1", 5000);
    await handlePrepare(prepareReq("ORD1", "5000"));

    const res = await handleComplete(completeReq("ORD1", "5000", order.id + 777));

    assert.equal(res.error, ClickError.TRANSACTION_NOT_FOUND);
  });

  it("noto'g'ri summani rad etadi", async () => {
    const order = await demoCreateOrder("ORD1", 5000);
    await handlePrepare(prepareReq("ORD1", "5000"));

    const res = await handleComplete(completeReq("ORD1", "1", order.id));

    assert.equal(res.error, ClickError.INCORRECT_AMOUNT);
    assert.equal((await orders.findOrder("ORD1"))?.status, "pending");
  });

  it("Click xatosida to'lovni bekor qiladi", async () => {
    const { adapter, paid, cancelled } = tracking();
    const order = await demoCreateOrder("ORD1", 5000);
    await handlePrepare(prepareReq("ORD1", "5000"), adapter);

    const res = await handleComplete(
      completeReq("ORD1", "5000", order.id, { error: "-5017" }),
      adapter,
    );

    assert.equal(res.error, ClickError.TRANSACTION_CANCELLED);
    assert.equal((await orders.findOrder("ORD1"))?.status, "cancelled");
    assert.deepEqual(paid, []);
    assert.deepEqual(cancelled, ["ORD1"]);
  });

  it("topilmagan buyurtmaga -5 qaytaradi", async () => {
    const res = await handleComplete(completeReq("YOQ404", "5000", 1));

    assert.equal(res.error, ClickError.USER_NOT_FOUND);
  });

  it("onPaid xatosi javobni buzmaydi, to'lov 'paid' qoladi", async () => {
    const broken: ClickOrdersAdapter = {
      ...orders,
      async onPaid() {
        throw new Error("baza yiqildi");
      },
    };

    const order = await demoCreateOrder("ORD1", 5000);
    await handlePrepare(prepareReq("ORD1", "5000"), broken);

    const res = await handleComplete(completeReq("ORD1", "5000", order.id), broken);

    assert.equal(res.error, ClickError.SUCCESS);
    assert.equal((await orders.findOrder("ORD1"))?.status, "paid");
  });
});

// =============================================================================

describe("poyga himoyasi", () => {
  it("markPaid ikkinchi marta false qaytaradi", async () => {
    const order = await demoCreateOrder("ORD1", 5000);

    assert.equal(await orders.markPaid(order, "111"), true);
    assert.equal(await orders.markPaid(order, "111"), false);
  });

  it("parallel complete'da onPaid faqat bir marta chaqiriladi", async () => {
    const { adapter, paid } = tracking();
    const order = await demoCreateOrder("ORD1", 5000);
    await handlePrepare(prepareReq("ORD1", "5000"), adapter);

    // Ikkala callback'ni bir vaqtda yuboramiz.
    const [a, b] = await Promise.all([
      handleComplete(completeReq("ORD1", "5000", order.id), adapter),
      handleComplete(completeReq("ORD1", "5000", order.id), adapter),
    ]);

    assert.equal(a.error, ClickError.SUCCESS);
    assert.equal(b.error, ClickError.SUCCESS);
    assert.deepEqual(paid, ["ORD1"]);
  });
});

// =============================================================================

describe("to'lov havolasi", () => {
  it("to'g'ri quriladi", () => {
    const url = paymentUrl("ORD1", 5000, "https://a.uz/ok");

    assert.ok(url.startsWith("https://my.click.uz/services/pay?"));
    assert.ok(url.includes("service_id=12345"));
    assert.ok(url.includes("merchant_id=54321"));
    assert.ok(url.includes("amount=5000"));
    assert.ok(url.includes("transaction_param=ORD1"));
    assert.ok(url.includes("merchant_user_id=67890"));
    assert.ok(url.includes("return_url=https%3A%2F%2Fa.uz%2Fok"));
  });

  it("secret_key ni havolaga qo'shmaydi", () => {
    const url = paymentUrl("ORD1", 5000);

    assert.ok(!url.includes(SECRET_KEY));
  });
});
