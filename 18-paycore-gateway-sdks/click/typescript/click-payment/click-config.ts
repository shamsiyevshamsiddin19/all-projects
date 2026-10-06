/**
 * Click sozlamalari — hammasi muhit o'zgaruvchilaridan (.env) o'qiladi.
 *
 * Qaysi qiymat kerakligi `.env.example` da yozilgan.
 * Bu faylga tegishingiz shart emas.
 *
 * Next.js `.env` ni o'zi o'qiydi. Oddiy Node loyihasida `dotenv` yoki
 * `node --env-file=.env` ishlating.
 */

export interface ClickConfig {
  serviceId: string;
  merchantId: string;
  secretKey: string;
  merchantUserId: string;
  payBaseUrl: string;
  returnUrl: string;
}

export class ClickConfigError extends Error {}

function require_(name: string): string {
  const value = (process.env[name] ?? "").trim();

  if (!value) {
    throw new ClickConfigError(
      `${name} .env da yo'q. \`.env.example\` dan \`.env\` yasang va ` +
        `qiymatlarni Click kabinetidan (merchant.click.uz) to'ldiring.`,
    );
  }

  return value;
}

let cached: ClickConfig | null = null;

/** Sozlamani o'qiydi (bir marta) va keshdan beradi. */
export function getConfig(): ClickConfig {
  if (cached === null) {
    cached = {
      serviceId: require_("CLICK_SERVICE_ID"),
      merchantId: require_("CLICK_MERCHANT_ID"),
      secretKey: require_("CLICK_SECRET_KEY"),
      merchantUserId: require_("CLICK_MERCHANT_USER_ID"),
      payBaseUrl: (
        process.env.CLICK_PAY_BASE_URL ?? "https://my.click.uz/services/pay"
      ).trim(),
      returnUrl: (process.env.CLICK_RETURN_URL ?? "").trim(),
    };
  }

  return cached;
}

/**
 * Sozlamani qo'lda o'rnatish — .env ishlatmasangiz yoki testlarda.
 *
 * `null` bersangiz kesh tozalanadi.
 */
export function setConfig(config: Partial<ClickConfig> | null): void {
  if (config === null) {
    cached = null;
    return;
  }

  cached = {
    payBaseUrl: "https://my.click.uz/services/pay",
    returnUrl: "",
    ...(cached ?? {}),
    ...config,
  } as ClickConfig;
}

/**
 * Summani to'lov havolasi uchun chiqaradi (5000.00 -> "5000").
 *
 * Bu faqat HAVOLA uchun — imzo hisoblashda Click yuborgan xom satr
 * ishlatiladi (click-signature.ts izohiga qarang).
 */
export function formatAmount(amount: number | string): string {
  const value = Number(amount);

  if (!Number.isFinite(value)) {
    throw new ClickConfigError(`Click: noto'g'ri summa: ${String(amount)}`);
  }

  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

/**
 * Foydalanuvchi yuboriladigan Click to'lov havolasini quradi.
 *
 * `merchantTransId` — sizning to'lov identifikatoringiz (masalan "ORD42").
 * Click uni prepare/complete so'rovlarida aynan shu holda qaytarib yuboradi.
 *
 * @example
 * const url = paymentUrl("ORD42", 5000);
 * // foydalanuvchini shu havolaga yuboring
 */
export function paymentUrl(
  merchantTransId: string,
  amount: number | string,
  returnUrl?: string,
): string {
  const config = getConfig();

  const params = new URLSearchParams({
    service_id: config.serviceId,
    merchant_id: config.merchantId,
    amount: formatAmount(amount),
    transaction_param: String(merchantTransId),
    merchant_user_id: config.merchantUserId,
  });

  const finalReturnUrl = returnUrl ?? config.returnUrl;
  if (finalReturnUrl) {
    params.set("return_url", finalReturnUrl);
  }

  return `${config.payBaseUrl}?${params.toString()}`;
}
