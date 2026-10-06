/**
 * Payme to'lov havolasini (checkout link) qurish.
 *
 * Click'dan farqli — Payme havolasi query-string emas, parametrlarni
 * `key=value;key=value` shaklida yig'ib, BUTUN satrni base64 qiladi:
 *
 *     https://checkout.paycom.uz/<base64("m=MERCHANT_ID;ac.order_id=42;a=500000")>
 *
 * Bu faylga tegishingiz shart emas.
 */

import { getConfig, type PaymeConfig } from "./payme-config.js";

/** So'mni tiyinga o'giradi (1 so'm = 100 tiyin). Payme SUMMA TIYINDA kutadi. */
export function somToTiyin(som: number | string): number {
  return Math.round(Number(som) * 100);
}

export interface CheckoutOptions {
  returnUrl?: string;
  lang?: string;
  config?: PaymeConfig;
}

/**
 * Foydalanuvchi yuboriladigan Payme to'lov havolasini quradi.
 *
 * `account` — Payme'ga yuboriladigan hisob maydonlari (masalan
 * `{ order_id: "42" }`). Shu maydonlar `payme-orders.ts` dagi
 * `findAccount()` ga qaytib keladi.
 *
 * `amountTiyin` — summa TIYINDA (so'm emas!). `somToTiyin()` bilan o'giring.
 *
 * @example
 * const url = checkoutUrl({ order_id: 42 }, somToTiyin(5000));
 */
export function checkoutUrl(
  account: Record<string, string | number>,
  amountTiyin: number,
  options: CheckoutOptions = {},
): string {
  const config = options.config ?? getConfig();

  const parts = [`m=${config.merchantId}`];
  for (const [key, value] of Object.entries(account)) {
    parts.push(`ac.${key}=${value}`);
  }
  parts.push(`a=${Math.trunc(amountTiyin)}`);

  if (options.returnUrl) parts.push(`c=${options.returnUrl}`);
  if (options.lang) parts.push(`l=${options.lang}`);

  const raw = parts.join(";");
  const encoded = Buffer.from(raw, "utf8").toString("base64");

  return `${config.checkoutBaseUrl.replace(/\/$/, "")}/${encoded}`;
}
