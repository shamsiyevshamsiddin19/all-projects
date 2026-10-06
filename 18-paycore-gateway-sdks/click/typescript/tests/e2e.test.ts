/**
 * Uchdan-uchgacha sinov — Click qanday ursa, xuddi shunday.
 *
 * Ikkita yo'l tekshiriladi:
 *   1. Web standartidagi `Request` (Next.js App Router, Hono, Bun, Deno)
 *   2. Express (form-encoded body)
 *
 *     npm test
 */

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { beforeEach, describe, it } from "node:test";

import {
  demoCreateOrder,
  demoReset,
  handleComplete,
  handlePrepare,
  orders,
  readRequestData,
  setConfig,
} from "../click-payment/index.js";

const SERVICE_ID = "12345";
const SECRET_KEY = "test_secret_key";
const SIGN_TIME = "2026-07-17 12:00:00";
const CTID = "987654321";

const sign = (...p: string[]) =>
  createHash("md5").update(p.join(""), "utf8").digest("hex");

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

describe("Web Request (Next.js yo'li)", () => {
  it("form-encoded POST — Click aynan shunday yuboradi", async () => {
    const order = await demoCreateOrder("ORD1", 5000);

    const body = new URLSearchParams({
      click_trans_id: CTID,
      service_id: SERVICE_ID,
      merchant_trans_id: "ORD1",
      amount: "5000.00",
      action: "0",
      sign_time: SIGN_TIME,
      sign_string: sign(CTID, SERVICE_ID, SECRET_KEY, "ORD1", "5000.00", "0", SIGN_TIME),
    });

    const req = new Request("https://domen.uz/api/click/prepare", {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });

    const data = await readRequestData(req);
    const res = await handlePrepare(data);

    assert.equal(res.error, 0);
    assert.equal(res.merchant_prepare_id, order.id);
  });

  it("JSON body ham qabul qilinadi", async () => {
    await demoCreateOrder("ORD2", 12000);

    const req = new Request("https://domen.uz/api/click/prepare", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        click_trans_id: CTID,
        service_id: SERVICE_ID,
        merchant_trans_id: "ORD2",
        amount: "12000",
        action: "0",
        sign_time: SIGN_TIME,
        sign_string: sign(CTID, SERVICE_ID, SECRET_KEY, "ORD2", "12000", "0", SIGN_TIME),
      }),
    });

    const res = await handlePrepare(await readRequestData(req));

    assert.equal(res.error, 0);
  });

  it("to'liq oqim: prepare -> complete -> paid", async () => {
    const order = await demoCreateOrder("ORD3", 5000, { userId: 1 });

    const prepareBody = new URLSearchParams({
      click_trans_id: CTID,
      service_id: SERVICE_ID,
      merchant_trans_id: "ORD3",
      amount: "5000",
      action: "0",
      sign_time: SIGN_TIME,
      sign_string: sign(CTID, SERVICE_ID, SECRET_KEY, "ORD3", "5000", "0", SIGN_TIME),
    });

    const prepareRes = await handlePrepare(
      await readRequestData(
        new Request("https://d.uz/api/click/prepare", {
          method: "POST",
          headers: { "content-type": "application/x-www-form-urlencoded" },
          body: prepareBody.toString(),
        }),
      ),
    );
    assert.equal(prepareRes.error, 0);

    const pid = String(prepareRes.merchant_prepare_id);
    const completeBody = new URLSearchParams({
      click_trans_id: CTID,
      service_id: SERVICE_ID,
      merchant_trans_id: "ORD3",
      merchant_prepare_id: pid,
      amount: "5000",
      action: "1",
      error: "0",
      sign_time: SIGN_TIME,
      sign_string: sign(CTID, SERVICE_ID, SECRET_KEY, "ORD3", pid, "5000", "1", SIGN_TIME),
    });

    const completeRes = await handleComplete(
      await readRequestData(
        new Request("https://d.uz/api/click/complete", {
          method: "POST",
          headers: { "content-type": "application/x-www-form-urlencoded" },
          body: completeBody.toString(),
        }),
      ),
    );

    assert.equal(completeRes.error, 0);
    assert.equal(completeRes.merchant_confirm_id, order.id);
    assert.equal((await orders.findOrder("ORD3"))?.status, "paid");
  });

  it("soxta imzo -1 oladi", async () => {
    await demoCreateOrder("ORD4", 5000);

    const body = new URLSearchParams({
      click_trans_id: CTID,
      service_id: SERVICE_ID,
      merchant_trans_id: "ORD4",
      amount: "5000",
      action: "0",
      sign_time: SIGN_TIME,
      sign_string: "0".repeat(32),
    });

    const res = await handlePrepare(
      await readRequestData(
        new Request("https://d.uz/api/click/prepare", {
          method: "POST",
          headers: { "content-type": "application/x-www-form-urlencoded" },
          body: body.toString(),
        }),
      ),
    );

    assert.equal(res.error, -1);
  });
});
