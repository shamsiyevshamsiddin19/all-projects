/**
 * handleRequest (Payme 6 metodi) testlari.
 *
 * Ishga tushirish (loyiha ildizidan):
 *
 *     npm install
 *     npm test
 */

import assert from "node:assert/strict";
import { beforeEach, describe, it } from "node:test";

import {
  PaymeReason,
  PaymeState,
  checkoutUrl,
  demoCreateOrder,
  demoReset,
  handleRequest,
  orders,
  setConfig,
  somToTiyin,
  type PaymeOrdersAdapter,
  type PaymeTransaction,
} from "../payme-payment/index.js";

const MERCHANT_ID = "5cd108976ce4a8423da6d5c9";
const SECRET_KEY = "test_secret_key";
const LOGIN = "Paycom";

function authHeader(login = LOGIN, key = SECRET_KEY): string {
  return "Basic " + Buffer.from(`${login}:${key}`, "utf8").toString("base64");
}

beforeEach(() => {
  setConfig(null);
  setConfig({ merchantId: MERCHANT_ID, secretKey: SECRET_KEY, merchantLogin: LOGIN });
  demoReset();
});

/** onPaid/onCancelled chaqiruvlarini yozib boradigan adapter. */
function tracking() {
  const paid: string[] = [];
  const cancelled: string[] = [];
  const adapter: PaymeOrdersAdapter = {
    ...orders,
    async onPaid(tx: PaymeTransaction) {
      paid.push(tx.paymeId);
    },
    async onCancelled(tx: PaymeTransaction) {
      cancelled.push(tx.paymeId);
    },
  };
  return { adapter, paid, cancelled };
}

function rpc(
  method: string,
  params: Record<string, unknown>,
  reqId = 1,
  auth: string | null | undefined = authHeader(),
  ordersAdapter?: PaymeOrdersAdapter,
) {
  return handleRequest(
    { method, params, id: reqId },
    auth,
    undefined,
    ordersAdapter,
  );
}

// =============================================================================

describe("auth", () => {
  it("sarlavha yo'q -> -32504", async () => {
    const res = await rpc("CheckTransaction", { id: "x" }, 1, null);
    assert.equal((res.error as { code: number }).code, -32504);
  });

  it("noto'g'ri parol -> -32504", async () => {
    const res = await rpc("CheckTransaction", { id: "x" }, 1, authHeader(LOGIN, "wrong"));
    assert.equal((res.error as { code: number }).code, -32504);
  });

  it("noto'g'ri login -> -32504", async () => {
    const res = await rpc("CheckTransaction", { id: "x" }, 1, authHeader("Hacker"));
    assert.equal((res.error as { code: number }).code, -32504);
  });

  it("noma'lum metod -> -32601", async () => {
    const res = await rpc("SomeMethod", {});
    assert.equal((res.error as { code: number }).code, -32601);
  });
});

// =============================================================================

describe("CheckPerformTransaction", () => {
  it("muvaffaqiyatli", async () => {
    demoCreateOrder("ORD1", 500000);
    const res = await rpc("CheckPerformTransaction", {
      amount: 500000,
      account: { order_id: "ORD1" },
    });
    assert.deepEqual(res.result, { allow: true });
  });

  it("order topilmadi -> -31050", async () => {
    const res = await rpc("CheckPerformTransaction", {
      amount: 500000,
      account: { order_id: "YOQ" },
    });
    assert.equal((res.error as { code: number }).code, -31050);
  });

  it("noto'g'ri summa -> -31001", async () => {
    demoCreateOrder("ORD1", 500000);
    const res = await rpc("CheckPerformTransaction", {
      amount: 1,
      account: { order_id: "ORD1" },
    });
    assert.equal((res.error as { code: number }).code, -31001);
  });

  it("tranzaksiya allaqachon bor -> -31099", async () => {
    demoCreateOrder("ORD1", 500000);
    await rpc("CreateTransaction", {
      id: "tx1",
      time: Date.now(),
      amount: 500000,
      account: { order_id: "ORD1" },
    });
    const res = await rpc("CheckPerformTransaction", {
      amount: 500000,
      account: { order_id: "ORD1" },
    });
    assert.equal((res.error as { code: number }).code, -31099);
  });
});

// =============================================================================

describe("CreateTransaction", () => {
  it("muvaffaqiyatli", async () => {
    demoCreateOrder("ORD1", 500000);
    const res = await rpc("CreateTransaction", {
      id: "tx1",
      time: Date.now(),
      amount: 500000,
      account: { order_id: "ORD1" },
    });
    const result = res.result as { state: number; transaction: string };
    assert.equal(result.state, PaymeState.PENDING);
    assert.equal(result.transaction, "tx1");
  });

  it("idempotent takroriy so'rov", async () => {
    demoCreateOrder("ORD1", 500000);
    const params = { id: "tx1", time: Date.now(), amount: 500000, account: { order_id: "ORD1" } };
    const first = await rpc("CreateTransaction", params);
    const second = await rpc("CreateTransaction", params);
    assert.equal(
      (first.result as { create_time: number }).create_time,
      (second.result as { create_time: number }).create_time,
    );
  });

  it("order topilmadi -> -31050", async () => {
    const res = await rpc("CreateTransaction", {
      id: "tx1",
      time: Date.now(),
      amount: 500000,
      account: { order_id: "YOQ" },
    });
    assert.equal((res.error as { code: number }).code, -31050);
  });

  it("muddati o'tgan -> -31008 va avtomatik bekor qilinadi", async () => {
    demoCreateOrder("ORD1", 500000);
    const oldTime = Date.now() - 43_200_000 - 1000;
    const params = { id: "tx1", time: oldTime, amount: 500000, account: { order_id: "ORD1" } };
    await rpc("CreateTransaction", params);

    const res = await rpc("CreateTransaction", params);
    assert.equal((res.error as { code: number }).code, -31008);

    const tx = await orders.getTransaction("tx1");
    assert.equal(tx?.state, PaymeState.CANCELLED);
    assert.equal(tx?.reason, PaymeReason.TIMEOUT);
  });

  it("bitta orderga ikkinchi tranzaksiya -> -31099", async () => {
    demoCreateOrder("ORD1", 500000);
    await rpc("CreateTransaction", {
      id: "tx1",
      time: Date.now(),
      amount: 500000,
      account: { order_id: "ORD1" },
    });
    const res = await rpc("CreateTransaction", {
      id: "tx2",
      time: Date.now(),
      amount: 500000,
      account: { order_id: "ORD1" },
    });
    assert.equal((res.error as { code: number }).code, -31099);
  });
});

// =============================================================================

describe("PerformTransaction", () => {
  it("muvaffaqiyatli va onPaid ni chaqiradi", async () => {
    const { adapter, paid } = tracking();
    demoCreateOrder("ORD1", 500000, "Kitob");
    await rpc(
      "CreateTransaction",
      { id: "tx1", time: Date.now(), amount: 500000, account: { order_id: "ORD1" } },
      1,
      undefined,
      adapter,
    );

    const res = await rpc("PerformTransaction", { id: "tx1" }, 1, undefined, adapter);
    assert.equal((res.result as { state: number }).state, PaymeState.PAID);
    assert.deepEqual(paid, ["tx1"]);
  });

  it("idempotent — onPaid FAQAT bir marta", async () => {
    const { adapter, paid } = tracking();
    demoCreateOrder("ORD1", 500000);
    await rpc(
      "CreateTransaction",
      { id: "tx1", time: Date.now(), amount: 500000, account: { order_id: "ORD1" } },
      1,
      undefined,
      adapter,
    );

    const first = await rpc("PerformTransaction", { id: "tx1" }, 1, undefined, adapter);
    const second = await rpc("PerformTransaction", { id: "tx1" }, 1, undefined, adapter);

    assert.equal(
      (first.result as { perform_time: number }).perform_time,
      (second.result as { perform_time: number }).perform_time,
    );
    assert.deepEqual(paid, ["tx1"]);
  });

  it("topilmagan -> -31003", async () => {
    const res = await rpc("PerformTransaction", { id: "yoq" });
    assert.equal((res.error as { code: number }).code, -31003);
  });

  it("bekor qilingandan keyin -> -31008", async () => {
    demoCreateOrder("ORD1", 500000);
    await rpc("CreateTransaction", {
      id: "tx1",
      time: Date.now(),
      amount: 500000,
      account: { order_id: "ORD1" },
    });
    await rpc("CancelTransaction", { id: "tx1", reason: 3 });

    const res = await rpc("PerformTransaction", { id: "tx1" });
    assert.equal((res.error as { code: number }).code, -31008);
  });

  it("muddati o'tgan -> -31008", async () => {
    demoCreateOrder("ORD1", 500000);
    const oldTime = Date.now() - 43_200_000 - 1000;
    await rpc("CreateTransaction", {
      id: "tx1",
      time: oldTime,
      amount: 500000,
      account: { order_id: "ORD1" },
    });

    const res = await rpc("PerformTransaction", { id: "tx1" });
    assert.equal((res.error as { code: number }).code, -31008);
    const tx = await orders.getTransaction("tx1");
    assert.equal(tx?.state, PaymeState.CANCELLED);
  });
});

// =============================================================================

describe("CancelTransaction", () => {
  it("pending -> CANCELLED", async () => {
    const { adapter, cancelled } = tracking();
    demoCreateOrder("ORD1", 500000);
    await rpc(
      "CreateTransaction",
      { id: "tx1", time: Date.now(), amount: 500000, account: { order_id: "ORD1" } },
      1,
      undefined,
      adapter,
    );

    const res = await rpc("CancelTransaction", { id: "tx1", reason: 3 }, 1, undefined, adapter);
    assert.equal((res.result as { state: number }).state, PaymeState.CANCELLED);
    assert.deepEqual(cancelled, ["tx1"]);
  });

  it("paid -> CANCELLED_AFTER_PAID (refund)", async () => {
    const { adapter, paid, cancelled } = tracking();
    demoCreateOrder("ORD1", 500000);
    await rpc(
      "CreateTransaction",
      { id: "tx1", time: Date.now(), amount: 500000, account: { order_id: "ORD1" } },
      1,
      undefined,
      adapter,
    );
    await rpc("PerformTransaction", { id: "tx1" }, 1, undefined, adapter);

    const res = await rpc("CancelTransaction", { id: "tx1", reason: 5 }, 1, undefined, adapter);
    assert.equal((res.result as { state: number }).state, PaymeState.CANCELLED_AFTER_PAID);
    assert.deepEqual(paid, ["tx1"]);
    assert.deepEqual(cancelled, ["tx1"]);
  });

  it("idempotent — onCancelled FAQAT bir marta", async () => {
    const { adapter, cancelled } = tracking();
    demoCreateOrder("ORD1", 500000);
    await rpc(
      "CreateTransaction",
      { id: "tx1", time: Date.now(), amount: 500000, account: { order_id: "ORD1" } },
      1,
      undefined,
      adapter,
    );

    const first = await rpc("CancelTransaction", { id: "tx1", reason: 3 }, 1, undefined, adapter);
    const second = await rpc("CancelTransaction", { id: "tx1", reason: 1 }, 1, undefined, adapter);

    assert.equal(
      (first.result as { cancel_time: number }).cancel_time,
      (second.result as { cancel_time: number }).cancel_time,
    );
    assert.deepEqual(cancelled, ["tx1"]);
  });

  it("topilmagan -> -31003", async () => {
    const res = await rpc("CancelTransaction", { id: "yoq", reason: 1 });
    assert.equal((res.error as { code: number }).code, -31003);
  });

  it("canRefund false -> -31007", async () => {
    demoCreateOrder("ORD1", 500000);
    const adapter: PaymeOrdersAdapter = { ...orders, async canRefund() { return false; } };
    await rpc(
      "CreateTransaction",
      { id: "tx1", time: Date.now(), amount: 500000, account: { order_id: "ORD1" } },
      1,
      undefined,
      adapter,
    );
    await rpc("PerformTransaction", { id: "tx1" }, 1, undefined, adapter);

    const res = await rpc("CancelTransaction", { id: "tx1", reason: 5 }, 1, undefined, adapter);
    assert.equal((res.error as { code: number }).code, -31007);

    const tx = await orders.getTransaction("tx1");
    assert.equal(tx?.state, PaymeState.PAID);
  });
});

// =============================================================================

describe("CheckTransaction", () => {
  it("holatni to'liq qaytaradi", async () => {
    demoCreateOrder("ORD1", 500000);
    await rpc("CreateTransaction", {
      id: "tx1",
      time: Date.now(),
      amount: 500000,
      account: { order_id: "ORD1" },
    });

    const res = await rpc("CheckTransaction", { id: "tx1" });
    const result = res.result as {
      state: number;
      perform_time: number;
      cancel_time: number;
      reason: number | null;
    };
    assert.equal(result.state, PaymeState.PENDING);
    assert.equal(result.perform_time, 0);
    assert.equal(result.cancel_time, 0);
    assert.equal(result.reason, null);
  });

  it("topilmagan -> -31003", async () => {
    const res = await rpc("CheckTransaction", { id: "yoq" });
    assert.equal((res.error as { code: number }).code, -31003);
  });
});

// =============================================================================

describe("GetStatement", () => {
  it("vaqt oralig'idagi tranzaksiyalarni qaytaradi", async () => {
    demoCreateOrder("ORD1", 500000);
    demoCreateOrder("ORD2", 100000);
    const t0 = Date.now();
    await rpc("CreateTransaction", {
      id: "tx1",
      time: Date.now(),
      amount: 500000,
      account: { order_id: "ORD1" },
    });
    await rpc("CreateTransaction", {
      id: "tx2",
      time: Date.now(),
      amount: 100000,
      account: { order_id: "ORD2" },
    });
    const t1 = Date.now() + 1000;

    const res = await rpc("GetStatement", { from: t0 - 1000, to: t1 });
    const ids = (res.result as { transactions: { id: string }[] }).transactions.map((t) => t.id);
    assert.deepEqual(new Set(ids), new Set(["tx1", "tx2"]));
  });

  it("bo'sh oraliq", async () => {
    const res = await rpc("GetStatement", { from: 0, to: 1 });
    assert.deepEqual((res.result as { transactions: unknown[] }).transactions, []);
  });
});

// =============================================================================

describe("to'lov havolasi", () => {
  it("to'g'ri quriladi", () => {
    const url = checkoutUrl({ order_id: 42 }, somToTiyin(5000));
    assert.ok(url.startsWith("https://checkout.paycom.uz/"));

    const encoded = url.split("/").pop()!;
    const decoded = Buffer.from(encoded, "base64").toString("utf8");
    assert.equal(decoded, `m=${MERCHANT_ID};ac.order_id=42;a=500000`);
  });

  it("secret_key ni havolaga qo'shmaydi", () => {
    const url = checkoutUrl({ order_id: 42 }, somToTiyin(5000));
    assert.ok(!url.includes(SECRET_KEY));
  });

  it("somToTiyin to'g'ri hisoblaydi", () => {
    assert.equal(somToTiyin(5000), 500000);
    assert.equal(somToTiyin("123.45"), 12345);
  });
});
