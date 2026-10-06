/**
 * Uzum Bank sozlamalari — hammasi muhit o'zgaruvchilaridan (.env) o'qiladi.
 *
 * Qaysi qiymat kerakligi `.env.example` da yozilgan.
 * Bu faylga tegishingiz shart emas.
 */

export interface UzumConfig {
  /**
   * Kabinetda xizmatingizga berilgan raqam. Uzum Bank ilovasida
   * foydalanuvchilar aynan shu ID orqali xizmatingizni topadi (Click/Payme'
   * dagidek to'lov havolasi YO'Q).
   */
  serviceId: number;

  /**
   * Webhook so'rovlarini tasdiqlash uchun LOGIN (Payme'dagi doim "Paycom"
   * bo'ladigan login'dan farqli, bu yerda o'zingiz kabinetda belgilaysiz).
   */
  webhookLogin: string;

  /** Webhook so'rovlarini tasdiqlash uchun PAROL. */
  webhookSecret: string;
}

export class UzumConfigError extends Error {}

function require_(name: string): string {
  const value = (process.env[name] ?? "").trim();
  if (!value) {
    throw new UzumConfigError(
      `${name} .env da yo'q. \`.env.example\` dan \`.env\` yasang va ` +
        `qiymatlarni Uzum Bank kabinetidan (merchants.uzumbank.uz) to'ldiring.`,
    );
  }
  return value;
}

let cached: UzumConfig | null = null;

/** Sozlamani o'qiydi (bir marta) va keshdan beradi. */
export function getConfig(): UzumConfig {
  if (cached === null) {
    cached = {
      serviceId: Number(require_("UZUM_SERVICE_ID")),
      webhookLogin: require_("UZUM_WEBHOOK_LOGIN"),
      webhookSecret: require_("UZUM_WEBHOOK_SECRET"),
    };
  }
  return cached;
}

/**
 * Sozlamani qo'lda o'rnatish — .env ishlatmasangiz yoki testlarda.
 * `null` bersangiz kesh tozalanadi.
 */
export function setConfig(config: UzumConfig | null): void {
  cached = config;
}
