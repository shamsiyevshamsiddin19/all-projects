/**
 * Payme sozlamalari — hammasi muhit o'zgaruvchilaridan (.env) o'qiladi.
 *
 * Qaysi qiymat kerakligi `.env.example` da yozilgan.
 * Bu faylga tegishingiz shart emas.
 */

export interface PaymeConfig {
  merchantId: string;
  secretKey: string;
  merchantLogin: string;
  checkoutBaseUrl: string;
}

export class PaymeConfigError extends Error {}

function require_(name: string): string {
  const value = (process.env[name] ?? "").trim();
  if (!value) {
    throw new PaymeConfigError(
      `${name} .env da yo'q. \`.env.example\` dan \`.env\` yasang va ` +
        `qiymatlarni Payme kabinetidan (business.payme.uz) to'ldiring.`,
    );
  }
  return value;
}

let cached: PaymeConfig | null = null;

/** Sozlamani o'qiydi (bir marta) va keshdan beradi. */
export function getConfig(): PaymeConfig {
  if (cached === null) {
    cached = {
      merchantId: require_("PAYME_MERCHANT_ID"),
      secretKey: require_("PAYME_SECRET_KEY"),
      merchantLogin: (process.env.PAYME_MERCHANT_LOGIN ?? "Paycom").trim() || "Paycom",
      checkoutBaseUrl: (
        process.env.PAYME_CHECKOUT_BASE_URL ?? "https://checkout.paycom.uz"
      ).trim(),
    };
  }
  return cached;
}

/**
 * Sozlamani qo'lda o'rnatish — .env ishlatmasangiz yoki testlarda.
 *
 * `null` bersangiz kesh tozalanadi.
 */
export function setConfig(config: Partial<PaymeConfig> | null): void {
  if (config === null) {
    cached = null;
    return;
  }
  cached = {
    merchantLogin: "Paycom",
    checkoutBaseUrl: "https://checkout.paycom.uz",
    ...(cached ?? {}),
    ...config,
  } as PaymeConfig;
}
