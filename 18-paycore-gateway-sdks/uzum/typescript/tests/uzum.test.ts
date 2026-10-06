/**
 * handleCheck/handleCreate/handleConfirm/handleReverse/handleStatus testlari.
 *
 * Ishga tushirish (loyiha ildizidan):
 *
 *     npm install
 *     npm test
 */

import assert from "node:assert/strict";
import { beforeEach, describe, it } from "node:test";

import {
  demoCreateOrder,
  demoReset,
  handleCheck,
  handleConfirm,
  handleCreate,
  handleReverse,
  handleStatus,
  orders,
  setConfig,
  UzumState,
  type UzumOrdersAdapter,
} from "../uzum-payment/index.js";

const SERVICE_ID = 101202;
const LOGIN = "myLogin";
const SECRET = "myPassword";

const AUTH = "Basic " + Buffer.from(`${LOGIN}:${SECRET}`).toString("base64");
const BAD_AUTH = "Basic " + Buffer.from("wrong:wrong").toString("base64");

beforeEach(() => {
  demoReset();
  setConfig({ serviceId: SERVICE_ID, webhookLogin: LOGIN, webhookSecret: SECRET });
});

function checkReq(account = "42", over: Record<string, unknown> = {}) {
  return { serviceId: SERVICE_ID, timestamp: 1, params: { account }, ...over };
}

function createReq(
  transId: string,
  account = "42",
  amount = 2500000,
  over: Record<string, unknown> = {},
) {
  return { serviceId: SERVICE_ID, timestamp: 1, transId, params: { account }, amount, ...over };
}

function confirmReq(transId: string, over: Record<string, unknown> = {}) {
  return {
    serviceId: SERVICE_ID,
    timestamp: 1,
    transId,
    paymentSource: "UZCARD",
    phone: "998901234567",
    ...over,
  };
}

function reverseReq(transId: string, over: Record<string, unknown> = {}) {
  return { serviceId: SERVICE_ID, timestamp: 1, transId, ...over };
}

function tracking() {
  const confirmed: string[] = [];
  const reversed: string[] = [];
  const adapter: UzumOrdersAdapter = {
    ...orders,
    async onConfirmed(tx) {
      confirmed.push(tx.transId);
    },
    async onReversed(tx) {
      reversed.push(tx.transId);
    },
  };
  return { adapter, confirmed, reversed };
}

// =============================================================================

describe("auth", () => {
  it("soxta auth -> 400/10001", async () => {
    demoCreateOrder("42", 2500000);
    const [status, body] = await handleCheck(checkReq(), BAD_AUTH);
    assert.equal(status, 400);
    assert.equal(body.errorCode, "10001");
  });

  it("auth yo'q -> 400/10001", async () => {
    demoCreateOrder("42", 2500000);
    const [status, body] = await handleCheck(checkReq(), null);
    assert.equal(status, 400);
    assert.equal(body.errorCode, "10001");
  });
});

describe("check", () => {
  it("muvaffaqiyatli", async () => {
    demoCreateOrder("42", 2500000);
    const [status, body] = await handleCheck(checkReq(), AUTH);
    assert.equal(status, 200);
    assert.equal(body.status, "OK");
  });

  it("topilmagan hisob -> 10007", async () => {
    const [status, body] = await handleCheck(checkReq("999"), AUTH);
    assert.equal(status, 400);
    assert.equal(body.errorCode, "10007");
  });

  it("noto'g'ri serviceId -> 10006", async () => {
    demoCreateOrder("42", 2500000);
    const [, body] = await handleCheck(checkReq("42", { serviceId: 555 }), AUTH);
    assert.equal(body.errorCode, "10006");
  });

  it("timestamp yo'q -> 10005", async () => {
    demoCreateOrder("42", 2500000);
    const req: Record<string, unknown> = checkReq();
    delete req.timestamp;
    const [, body] = await handleCheck(req, AUTH);
    assert.equal(body.errorCode, "10005");
  });
});

describe("create", () => {
  it("muvaffaqiyatli", async () => {
    demoCreateOrder("42", 2500000);
    const [status, body] = await handleCreate(createReq("t1"), AUTH);
    assert.equal(status, 200);
    assert.equal(body.status, UzumState.CREATED);
    assert.equal(body.transId, "t1");
  });

  it("takroriy create -> 10010 (idempotent EMAS)", async () => {
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH);

    const [status, body] = await handleCreate(createReq("t1"), AUTH);
    assert.equal(status, 400);
    assert.equal(body.errorCode, "10010");
  });

  it("noto'g'ri summa -> 10011", async () => {
    demoCreateOrder("42", 2500000);
    const [, body] = await handleCreate(createReq("t1", "42", 100), AUTH);
    assert.equal(body.errorCode, "10011");
  });

  it("topilmagan hisob -> 10007", async () => {
    const [, body] = await handleCreate(createReq("t1", "999"), AUTH);
    assert.equal(body.errorCode, "10007");
  });
});

describe("confirm", () => {
  it("muvaffaqiyatli va onConfirmed ni chaqiradi", async () => {
    const { adapter, confirmed } = tracking();
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH, undefined, adapter);

    const [status, body] = await handleConfirm(confirmReq("t1"), AUTH, undefined, adapter);
    assert.equal(status, 200);
    assert.equal(body.status, UzumState.CONFIRMED);
    assert.deepEqual(confirmed, ["t1"]);
  });

  it("takroriy confirm -> 10016 (idempotent EMAS)", async () => {
    const { adapter, confirmed } = tracking();
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH, undefined, adapter);
    await handleConfirm(confirmReq("t1"), AUTH, undefined, adapter);

    const [status, body] = await handleConfirm(confirmReq("t1"), AUTH, undefined, adapter);
    assert.equal(status, 400);
    assert.equal(body.errorCode, "10016");
    assert.deepEqual(confirmed, ["t1"]); // onConfirmed FAQAT bir marta
  });

  it("topilmagan tranzaksiya -> 10014", async () => {
    const [, body] = await handleConfirm(confirmReq("yoq"), AUTH);
    assert.equal(body.errorCode, "10014");
  });

  it("paymentSource yo'q -> 10005", async () => {
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH);
    const req: Record<string, unknown> = confirmReq("t1");
    delete req.paymentSource;
    const [, body] = await handleConfirm(req, AUTH);
    assert.equal(body.errorCode, "10005");
  });

  it("bekor qilingandan keyin confirm -> 10015", async () => {
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH);
    await handleReverse(reverseReq("t1"), AUTH);

    const [, body] = await handleConfirm(confirmReq("t1"), AUTH);
    assert.equal(body.errorCode, "10015");
  });
});

describe("reverse", () => {
  it("CREATED holatidan", async () => {
    const { adapter, reversed } = tracking();
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH, undefined, adapter);

    const [status, body] = await handleReverse(reverseReq("t1"), AUTH, undefined, adapter);
    assert.equal(status, 200);
    assert.equal(body.status, UzumState.REVERSED);
    assert.deepEqual(reversed, ["t1"]);
  });

  it("CONFIRMED holatidan (refund)", async () => {
    const { adapter, reversed } = tracking();
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH, undefined, adapter);
    await handleConfirm(confirmReq("t1"), AUTH, undefined, adapter);

    const [status, body] = await handleReverse(reverseReq("t1"), AUTH, undefined, adapter);
    assert.equal(status, 200);
    assert.equal(body.status, UzumState.REVERSED);
    assert.deepEqual(reversed, ["t1"]);
  });

  it("takroriy reverse -> 10018", async () => {
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH);
    await handleReverse(reverseReq("t1"), AUTH);

    const [status, body] = await handleReverse(reverseReq("t1"), AUTH);
    assert.equal(status, 400);
    assert.equal(body.errorCode, "10018");
  });

  it("topilmagan tranzaksiya -> 10014", async () => {
    const [, body] = await handleReverse(reverseReq("yoq"), AUTH);
    assert.equal(body.errorCode, "10014");
  });

  it("canReverse false bo'lsa -> 10017", async () => {
    const adapter: UzumOrdersAdapter = { ...orders, async canReverse() { return false; } };
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH, undefined, adapter);
    await handleConfirm(confirmReq("t1"), AUTH, undefined, adapter);

    const [status, body] = await handleReverse(reverseReq("t1"), AUTH, undefined, adapter);
    assert.equal(status, 400);
    assert.equal(body.errorCode, "10017");
  });
});

describe("status", () => {
  it("CREATED holati", async () => {
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH);

    const [status, body] = await handleStatus(reverseReq("t1"), AUTH);
    assert.equal(status, 200);
    assert.equal(body.status, UzumState.CREATED);
    assert.equal("confirmTime" in body, false);
  });

  it("CONFIRMED holati", async () => {
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH);
    await handleConfirm(confirmReq("t1"), AUTH);

    const [, body] = await handleStatus(reverseReq("t1"), AUTH);
    assert.equal(body.status, UzumState.CONFIRMED);
    assert.equal("confirmTime" in body, true);
  });

  it("topilmagan -> 10014", async () => {
    const [, body] = await handleStatus(reverseReq("yoq"), AUTH);
    assert.equal(body.errorCode, "10014");
  });
});

describe("poyga himoyasi", () => {
  it("markConfirmed ikkinchi marta null qaytaradi", async () => {
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH);

    const first = await orders.markConfirmed("t1");
    const second = await orders.markConfirmed("t1");
    assert.notEqual(first, null);
    assert.equal(second, null);
  });

  it("onConfirmed xatosi javobni buzmaydi", async () => {
    const adapter: UzumOrdersAdapter = {
      ...orders,
      async onConfirmed() {
        throw new Error("baza yiqildi");
      },
    };
    demoCreateOrder("42", 2500000);
    await handleCreate(createReq("t1"), AUTH, undefined, adapter);

    const [status, body] = await handleConfirm(confirmReq("t1"), AUTH, undefined, adapter);
    assert.equal(status, 200);
    assert.equal(body.status, UzumState.CONFIRMED);
  });
});
