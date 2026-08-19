// Oddiy xotiradagi (in-memory) rate-limit — bitta Node jarayoni uchun yetarli
// (server gorizontal ko'paytirilmagan). Redis shart emas.

const buckets = new Map<string, { count: number; resetAt: number }>();

// Eski bucket'larni vaqti-vaqti bilan tozalab turamiz (xotira sizib ketmasin).
setInterval(
  () => {
    const now = Date.now();
    for (const [key, b] of buckets) {
      if (b.resetAt < now) buckets.delete(key);
    }
  },
  5 * 60 * 1000,
).unref?.();

/**
 * `key` (masalan IP+route) bo'yicha `limit` marta `windowMs` ichida ruxsat beradi.
 * Chegaradan oshsa `false` qaytaradi.
 */
export function rateLimit(key: string, limit: number, windowMs: number): boolean {
  const now = Date.now();
  const b = buckets.get(key);
  if (!b || b.resetAt < now) {
    buckets.set(key, { count: 1, resetAt: now + windowMs });
    return true;
  }
  if (b.count >= limit) return false;
  b.count++;
  return true;
}

export function clientIp(req: Request): string {
  const fwd = req.headers.get("x-real-ip") || req.headers.get("x-forwarded-for");
  return fwd?.split(",")[0]?.trim() || "unknown";
}
