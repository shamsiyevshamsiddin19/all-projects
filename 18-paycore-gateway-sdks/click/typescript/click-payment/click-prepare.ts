/**
 * Click PREPARE so'rovi.
 *
 * Click bu so'rovni "shu to'lovni qabul qila olasanmi?" deb yuboradi.
 * Bu bosqichda pul HALI YECHILMAGAN.
 *
 * Biz tekshiramiz:
 *     - so'rov to'liqmi                    -> yo'q bo'lsa -8
 *     - imzo haqiqiymi                     -> yo'q bo'lsa -1
 *     - bunday buyurtma bormi              -> yo'q bo'lsa -5
 *     - summa bazadagiga mos keladimi      -> yo'q bo'lsa -2
 *     - allaqachon to'lanmaganmi           -> to'langan bo'lsa -4
 *     - bekor qilinmaganmi                 -> bekor bo'lsa -9
 *
 * Hammasi joyida bo'lsa `error: 0` va `merchant_prepare_id` (buyurtma id'si)
 * qaytaramiz. Click keyin pulni yechib, click-complete.ts ga murojaat qiladi.
 *
 * Bu faylga tegishingiz shart emas — bazangizga ulanish click-orders.ts da.
 */

import { getConfig } from "./click-config.js";
import { ClickError, errorNote } from "./click-errors.js";
import { orders as defaultOrders, type ClickOrdersAdapter } from "./click-orders.js";
import { ACTION_PREPARE, checkSign } from "./click-signature.js";
import {
  amountsMatch,
  asInt,
  clickLog,
  missingFields,
  type ClickRequestData,
} from "./click-utils.js";

/** Click prepare so'rovida yuboradigan majburiy maydonlar. */
export const PREPARE_REQUIRED_FIELDS = [
  "click_trans_id",
  "service_id",
  "merchant_trans_id",
  "amount",
  "sign_time",
  "sign_string",
] as const;

export interface ClickPrepareResponse {
  click_trans_id: number;
  merchant_trans_id: string;
  merchant_prepare_id: number;
  error: number;
  error_note: string;
}

/**
 * Click prepare so'rovini qayta ishlaydi va javob obyektini qaytaradi.
 *
 * @param data   So'rovdagi maydonlar (form yoki JSON — farqi yo'q)
 * @param orders Bazangizga ulanish. Odatda berilmaydi — click-orders.ts
 *               dagi `orders` ishlatiladi. Testlarda yoki bir nechta baza
 *               bilan ishlaganda o'zingiznikini bering.
 */
export async function handlePrepare(
  data: ClickRequestData,
  orders: ClickOrdersAdapter = defaultOrders,
): Promise<ClickPrepareResponse> {
  const missing = missingFields(data, PREPARE_REQUIRED_FIELDS);
  if (missing.length > 0) {
    clickLog("warn", "prepare: maydon yetishmayapti", { missing });
    return response(data, 0, ClickError.BAD_REQUEST);
  }

  if (!checkSign(data, ACTION_PREPARE, getConfig())) {
    clickLog("warn", "prepare: imzo xato", {
      merchant_trans_id: data.merchant_trans_id,
    });
    return response(data, 0, ClickError.SIGN_CHECK_FAILED);
  }

  const merchantTransId = String(data.merchant_trans_id);
  const order = await orders.findOrder(merchantTransId);

  if (order === null) {
    clickLog("warn", "prepare: buyurtma topilmadi", { merchantTransId });
    return response(data, 0, ClickError.USER_NOT_FOUND);
  }

  // Summani HAR DOIM bazadan tekshiramiz — so'rovdagi qiymatga ishonmaymiz.
  if (!amountsMatch(data.amount, order.amount)) {
    clickLog("warn", "prepare: summa mos emas", {
      bazada: order.amount,
      sorovda: data.amount,
    });
    return response(data, order.id, ClickError.INCORRECT_AMOUNT);
  }

  if (order.status === "paid") {
    return response(data, order.id, ClickError.ALREADY_PAID);
  }

  if (order.status === "cancelled") {
    return response(data, order.id, ClickError.TRANSACTION_CANCELLED);
  }

  clickLog("info", "prepare OK", {
    merchantTransId,
    orderId: order.id,
    click_trans_id: data.click_trans_id,
  });

  return response(data, order.id, ClickError.SUCCESS);
}

/** Click kutadigan javob shakli. */
function response(
  data: ClickRequestData,
  merchantPrepareId: number,
  error: number,
): ClickPrepareResponse {
  return {
    click_trans_id: asInt(data.click_trans_id),
    merchant_trans_id: String(data.merchant_trans_id ?? ""),
    merchant_prepare_id: merchantPrepareId,
    error,
    error_note: errorNote(error),
  };
}
