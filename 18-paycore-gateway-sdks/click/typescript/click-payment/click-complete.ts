/**
 * Click COMPLETE so'rovi.
 *
 * Click bu so'rovni "pul yechildi, endi mahsulotni ber" deb yuboradi
 * (yoki "foydalanuvchi bekor qildi" deb — `error` maydoniga qarab).
 *
 * Biz tekshiramiz:
 *     - so'rov to'liqmi                       -> yo'q bo'lsa -8
 *     - imzo haqiqiymi                        -> yo'q bo'lsa -1
 *     - bunday buyurtma bormi                 -> yo'q bo'lsa -5
 *     - merchant_prepare_id prepare'dagi id'ga mos keladimi -> yo'q bo'lsa -6
 *     - summa bazadagiga mos keladimi         -> yo'q bo'lsa -2
 *
 * Hammasi joyida bo'lsa buyurtmani "to'landi" deb belgilaymiz va
 * onPaid() ni chaqiramiz — mahsulot o'sha yerda beriladi.
 *
 * Bu faylga tegishingiz shart emas — bazangizga ulanish click-orders.ts da.
 */

import { getConfig } from "./click-config.js";
import { ClickError, errorNote } from "./click-errors.js";
import {
  orders as defaultOrders,
  type ClickOrder,
  type ClickOrdersAdapter,
} from "./click-orders.js";
import { ACTION_COMPLETE, checkSign } from "./click-signature.js";
import {
  amountsMatch,
  asInt,
  clickLog,
  missingFields,
  type ClickRequestData,
} from "./click-utils.js";

/** Complete'da prepare'dagilarga qo'shimcha merchant_prepare_id ham keladi. */
export const COMPLETE_REQUIRED_FIELDS = [
  "click_trans_id",
  "service_id",
  "merchant_trans_id",
  "merchant_prepare_id",
  "amount",
  "sign_time",
  "sign_string",
] as const;

export interface ClickCompleteResponse {
  click_trans_id: number;
  merchant_trans_id: string;
  merchant_confirm_id: number;
  error: number;
  error_note: string;
}

/**
 * Click complete so'rovini qayta ishlaydi va javob obyektini qaytaradi.
 *
 * @param data   So'rovdagi maydonlar (form yoki JSON — farqi yo'q)
 * @param orders Bazangizga ulanish (odatda berilmaydi).
 */
export async function handleComplete(
  data: ClickRequestData,
  orders: ClickOrdersAdapter = defaultOrders,
): Promise<ClickCompleteResponse> {
  const missing = missingFields(data, COMPLETE_REQUIRED_FIELDS);
  if (missing.length > 0) {
    clickLog("warn", "complete: maydon yetishmayapti", { missing });
    return response(data, 0, ClickError.BAD_REQUEST);
  }

  if (!checkSign(data, ACTION_COMPLETE, getConfig())) {
    clickLog("warn", "complete: imzo xato", {
      merchant_trans_id: data.merchant_trans_id,
    });
    return response(data, 0, ClickError.SIGN_CHECK_FAILED);
  }

  const merchantTransId = String(data.merchant_trans_id);
  const clickTransId = String(data.click_trans_id);
  const order = await orders.findOrder(merchantTransId);

  if (order === null) {
    clickLog("warn", "complete: buyurtma topilmadi", { merchantTransId });
    return response(data, 0, ClickError.USER_NOT_FOUND);
  }

  // prepare'da qaytargan id bilan bir xil bo'lishi shart.
  if (asInt(data.merchant_prepare_id) !== order.id) {
    clickLog("warn", "complete: merchant_prepare_id mos emas", {
      kutilgan: order.id,
      kelgan: data.merchant_prepare_id,
    });
    return response(data, order.id, ClickError.TRANSACTION_NOT_FOUND);
  }

  if (!amountsMatch(data.amount, order.amount)) {
    clickLog("warn", "complete: summa mos emas", {
      bazada: order.amount,
      sorovda: data.amount,
    });
    return response(data, order.id, ClickError.INCORRECT_AMOUNT);
  }

  // Takroriy callback: Click javobni ololmay qayta urgan. Pul allaqachon
  // hisobga olingan — muvaffaqiyat deb javob beramiz, onPaid QAYTA
  // chaqirilmaydi.
  if (order.status === "paid") {
    clickLog("info", "complete: takroriy callback", { merchantTransId });
    return response(data, order.id, ClickError.SUCCESS);
  }

  if (order.status === "cancelled") {
    return response(data, order.id, ClickError.TRANSACTION_CANCELLED);
  }

  // Click o'zi bekor qilish/xato haqida xabar bergan.
  const clickError = asInt(data.error ?? 0);
  if (clickError !== 0) {
    await orders.markCancelled(order, clickTransId);
    order.status = "cancelled";

    clickLog("info", "complete: to'lov bekor qilindi", {
      merchantTransId,
      clickError,
    });

    await safeCall(() => orders.onCancelled(order), "onCancelled", order);

    return response(data, order.id, ClickError.TRANSACTION_CANCELLED);
  }

  // Asosiy holat: to'lov muvaffaqiyatli.
  //
  // markPaid() faqat HAQIQATAN pending -> paid o'tkazgan bo'lsa true
  // qaytaradi. Parallel kelgan ikkinchi callback false oladi va mahsulot
  // ikki marta berilmaydi.
  const won = await orders.markPaid(order, clickTransId);
  if (!won) {
    clickLog("info", "complete: boshqa callback ulgurdi — onPaid o'tkazib yuborildi", {
      merchantTransId,
    });
    return response(data, order.id, ClickError.SUCCESS);
  }

  order.status = "paid";

  clickLog("info", "complete OK", {
    merchantTransId,
    orderId: order.id,
    amount: order.amount,
  });

  await safeCall(() => orders.onPaid(order), "onPaid", order);

  return response(data, order.id, ClickError.SUCCESS);
}

/**
 * Hodisa funksiyasini chaqiradi; xato bo'lsa loglaydi, javobni buzmaydi.
 *
 * Nega xatoni yutamiz? Bu nuqtaga yetganda pul yechilgan va buyurtma
 * "paid" deb belgilangan. Click'ga xato qaytarsak u qayta uradi — lekin
 * yuqorida "allaqachon to'langan" bo'lib SUCCESS oladi, ya'ni onPaid
 * baribir qayta ishlamaydi. Shuning uchun to'g'ri yo'l: xatoni loglab,
 * keyin qo'lda hal qilish.
 */
async function safeCall(
  fn: () => Promise<void>,
  name: string,
  order: ClickOrder,
): Promise<void> {
  try {
    await fn();
  } catch (e) {
    clickLog(
      "error",
      `${name}() xatosi — to'lov "paid" holicha qoldi, qo'lda tekshiring`,
      {
        merchantTransId: order.merchantTransId,
        xato: e instanceof Error ? e.message : String(e),
      },
    );
  }
}

/**
 * Click kutadigan javob shakli.
 *
 * Diqqat: prepare'da `merchant_prepare_id`, complete'da esa
 * `merchant_confirm_id` deb nomlanadi.
 */
function response(
  data: ClickRequestData,
  merchantConfirmId: number,
  error: number,
): ClickCompleteResponse {
  return {
    click_trans_id: asInt(data.click_trans_id),
    merchant_trans_id: String(data.merchant_trans_id ?? ""),
    merchant_confirm_id: merchantConfirmId,
    error,
    error_note: errorNote(error),
  };
}
