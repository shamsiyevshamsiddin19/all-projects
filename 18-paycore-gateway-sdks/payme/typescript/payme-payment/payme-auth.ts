/**
 * Payme'ning Basic Auth so'rovini tekshirish.
 *
 * Click'dan farqli o'laroq, Payme har bir so'rovni imzo (sign_string) bilan
 * emas, oddiy HTTP Basic Authentication bilan tasdiqlaydi:
 *
 *     Authorization: Basic base64("Paycom:MAXFIY_KALIT")
 *
 * Login har doim "Paycom" (yoki kabinetda o'zgartirilgan bo'lsa, shu qiymat).
 * Parol — kabinetdagi kassa uchun berilgan maxfiy kalit.
 *
 * ⚠️ Bu modul `node:crypto` ga tayanadi — Next.js Edge runtime'da
 * ishlamaydi (`export const runtime = "nodejs"` yozing).
 *
 * Bu faylga tegishingiz shart emas.
 */

import { timingSafeEqual } from "node:crypto";

import type { PaymeConfig } from "./payme-config.js";

function safeEqual(a: string, b: string): boolean {
  const bufA = Buffer.from(a, "utf8");
  const bufB = Buffer.from(b, "utf8");
  if (bufA.length !== bufB.length) return false;
  return timingSafeEqual(bufA, bufB);
}

/**
 * `Authorization` sarlavhasini tekshiradi.
 *
 * Login va parol vaqt bo'yicha barqaror (timing-safe) solishtiriladi.
 */
export function checkAuth(
  authorizationHeader: string | null | undefined,
  config: PaymeConfig,
): boolean {
  if (!authorizationHeader || !authorizationHeader.startsWith("Basic ")) {
    return false;
  }

  const token = authorizationHeader.slice("Basic ".length).trim();

  let decoded: string;
  try {
    decoded = Buffer.from(token, "base64").toString("utf8");
  } catch {
    return false;
  }

  const sepIndex = decoded.indexOf(":");
  if (sepIndex === -1) return false;

  const login = decoded.slice(0, sepIndex);
  const password = decoded.slice(sepIndex + 1);
  if (!password) return false;

  return safeEqual(login, config.merchantLogin) && safeEqual(password, config.secretKey);
}
