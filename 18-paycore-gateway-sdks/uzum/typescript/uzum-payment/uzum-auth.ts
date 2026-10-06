/**
 * Uzum Bank'ning Basic Auth so'rovini tekshirish.
 *
 * Payme'ga o'xshab, Uzum Bank ham har bir webhook so'rovini oddiy HTTP Basic
 * Authentication bilan tasdiqlaydi:
 *
 *     Authorization: Basic base64("login:parol")
 *
 * Farqi: Payme'da login doim "Paycom", Uzum'da esa LOGIN HAM, PAROL HAM siz
 * kabinetda o'zingiz belgilaysiz.
 *
 * ⚠️ Bu modul `node:crypto` ga tayanadi — Next.js Edge runtime'da
 * ishlamaydi (`export const runtime = "nodejs"` yozing).
 *
 * Bu faylga tegishingiz shart emas.
 */

import { timingSafeEqual } from "node:crypto";

import type { UzumConfig } from "./uzum-config.js";

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
  config: UzumConfig,
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

  return safeEqual(login, config.webhookLogin) && safeEqual(password, config.webhookSecret);
}
