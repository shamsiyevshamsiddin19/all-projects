/**
 * Kichik yordamchilar. Bu faylga tegishingiz shart emas.
 */

/** Summalarni solishtirishda ruxsat etilgan farq (tiyin yaxlitlashlari uchun). */
export const AMOUNT_TOLERANCE = 0.01;

export type ClickRequestData = Record<string, unknown>;

/** So'rovda yetishmayotgan majburiy maydonlar ro'yxati. */
export function missingFields(
  data: ClickRequestData,
  required: readonly string[],
): string[] {
  return required.filter((field) => {
    const value = data[field];
    return value === undefined || value === null || value === "";
  });
}

/** Xavfsiz int'ga o'girish — bo'lmasa 0. */
export function asInt(value: unknown): number {
  const n = Number(String(value ?? "").trim());
  return Number.isFinite(n) ? Math.trunc(n) : 0;
}

/**
 * Click yuborgan summa bazadagiga mos keladimi?
 *
 * Click "5000", "5000.00" yoki "5000.0" yuborishi mumkin — hammasi bir xil
 * summa. Shuning uchun kichik farq bilan solishtiramiz.
 */
export function amountsMatch(received: unknown, expected: number): boolean {
  const raw = String(received ?? "").trim();
  if (raw === "") return false;

  const got = Number(raw);
  if (!Number.isFinite(got)) return false;

  return Math.abs(got - expected) < AMOUNT_TOLERANCE;
}

/**
 * Click so'rovidan maydonlarni oladi (Web standartidagi Request uchun).
 *
 * Click odatda `application/x-www-form-urlencoded` POST yuboradi, lekin
 * sozlamaga qarab JSON ham kelishi mumkin. Ikkalasini ham qo'llab-quvvatlaymiz,
 * oxirida query parametrlariga tushamiz.
 *
 * Next.js App Router, Hono, Bun, Deno — hammasi shu Request'ni ishlatadi.
 * Express uchun `examples/express-app.ts` ga qarang.
 */
export async function readRequestData(req: Request): Promise<ClickRequestData> {
  const contentType = req.headers.get("content-type") ?? "";

  try {
    if (contentType.includes("application/x-www-form-urlencoded")) {
      const text = await req.text();
      if (text) {
        return Object.fromEntries(new URLSearchParams(text));
      }
    } else if (contentType.includes("application/json")) {
      const body = (await req.json()) as unknown;
      if (body && typeof body === "object") {
        return body as ClickRequestData;
      }
    } else if (contentType.includes("multipart/form-data")) {
      const form = await req.formData();
      const out: ClickRequestData = {};
      for (const [key, value] of form.entries()) {
        out[key] = typeof value === "string" ? value : String(value);
      }
      return out;
    }
  } catch {
    // Body o'qib bo'lmadi — quyida query parametrlariga tushamiz.
  }

  return Object.fromEntries(new URL(req.url).searchParams);
}

/**
 * Click hodisalarini loglaydi.
 *
 * Odatiy holda `console` ga yozadi. Loyihangizda o'z loggeringiz bo'lsa
 * (pino, winston), shu funksiyani o'zgartiring.
 */
export function clickLog(
  level: "info" | "warn" | "error",
  message: string,
  context: Record<string, unknown> = {},
): void {
  const line = `[click] ${message}`;

  if (level === "error") console.error(line, context);
  else if (level === "warn") console.warn(line, context);
  else console.log(line, context);
}
