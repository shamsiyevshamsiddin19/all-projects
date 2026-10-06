/**
 * Click imzosi (sign_string) — qurish va tekshirish.
 *
 * Click har bir so'rovni md5 imzo bilan yuboradi. Formula prepare va
 * complete'da ozgina farq qiladi:
 *
 *     prepare  (action=0):
 *         md5(click_trans_id + service_id + secret_key + merchant_trans_id
 *             + amount + action + sign_time)
 *
 *     complete (action=1):
 *         md5(click_trans_id + service_id + secret_key + merchant_trans_id
 *             + merchant_prepare_id + amount + action + sign_time)
 *
 * Yagona farq — complete'da merchant_trans_id bilan amount orasiga
 * merchant_prepare_id qo'shiladi.
 *
 * ⚠️ MUHIM (Next.js / Vercel): bu modul `node:crypto` ga tayanadi, chunki
 * Web Crypto API md5 ni umuman qo'llab-quvvatlamaydi. Shuning uchun Click
 * endpoint'laringiz EDGE runtime'da ISHLAMAYDI — route faylida
 * `export const runtime = "nodejs"` yozing.
 *
 * Bu faylga tegishingiz shart emas.
 */

import { createHash, timingSafeEqual } from "node:crypto";

import type { ClickConfig } from "./click-config.js";

export const ACTION_PREPARE = "0";
export const ACTION_COMPLETE = "1";

export interface SignParts {
  clickTransId: string;
  serviceId: string;
  secretKey: string;
  merchantTransId: string;
  amount: string;
  action: string;
  signTime: string;
  merchantPrepareId?: string;
}

/** Imzolanadigan xom satrni yig'adi (hali md5 qilinmagan). */
export function buildSignString(p: SignParts): string {
  let signString =
    String(p.clickTransId) +
    String(p.serviceId) +
    String(p.secretKey) +
    String(p.merchantTransId);

  if (String(p.action) === ACTION_COMPLETE) {
    signString += String(p.merchantPrepareId ?? "");
  }

  return signString + String(p.amount) + String(p.action) + String(p.signTime);
}

/** sign_string ni hisoblaydi (md5, kichik harfli hex). */
export function makeSign(p: SignParts): string {
  return createHash("md5").update(buildSignString(p), "utf8").digest("hex");
}

/**
 * Ikki imzoni vaqt bo'yicha barqaror (timing-safe) solishtiradi.
 *
 * Oddiy `===` imzoni belgima-belgi topib olish hujumiga yo'l ochadi.
 */
export function signsEqual(received: string, expected: string): boolean {
  const a = String(received ?? "").trim().toLowerCase();
  const b = String(expected ?? "").trim().toLowerCase();

  if (a === "" || b === "") return false;

  const bufA = Buffer.from(a, "utf8");
  const bufB = Buffer.from(b, "utf8");

  // timingSafeEqual uzunliklar teng bo'lishini talab qiladi.
  if (bufA.length !== bufB.length) return false;

  return timingSafeEqual(bufA, bufB);
}

/**
 * Click so'rovining imzosini tekshiradi.
 *
 * `action` SO'ROVDAN OLINMAYDI — qaysi endpoint chaqirilgan bo'lsa,
 * o'shanikini ("0" yoki "1") beramiz. Aks holda hujumchi prepare uchun
 * olingan imzoni complete so'roviga qo'yib yuborishi mumkin bo'lardi.
 *
 * MUHIM: `amount` imzoga Click YUBORGAN XOM SATR holida kiradi. Click
 * "5000.00" yuborsa, uni Number() ga o'girib qaytarsangiz "5000" bo'lib
 * qoladi va imzo mos kelmaydi. Shuning uchun bu yerda qiymatlar
 * o'zgartirilmasdan uzatiladi.
 */
export function checkSign(
  data: Record<string, unknown>,
  action: string,
  config: ClickConfig,
): boolean {
  const serviceId = String(data.service_id ?? "");

  if (serviceId === "" || !signsEqual(serviceId, config.serviceId)) {
    return false;
  }

  const expected = makeSign({
    clickTransId: String(data.click_trans_id ?? ""),
    serviceId,
    secretKey: config.secretKey,
    merchantTransId: String(data.merchant_trans_id ?? ""),
    amount: String(data.amount ?? ""),
    action,
    signTime: String(data.sign_time ?? ""),
    merchantPrepareId: String(data.merchant_prepare_id ?? ""),
  });

  return signsEqual(String(data.sign_string ?? ""), expected);
}
