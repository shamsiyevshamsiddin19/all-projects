// Click to'lov integratsiyasi — merchant_trans_id yasash va Click pay URL qurish.
//
// Haqiqiy Click imzosi (sign_string, secret_key) myxvest'dagi PHP ko'prikda (wstore_bridge.php)
// tekshiriladi — bu server (wstore.uz) hech qachon asl Click secret_key'ni bilmaydi, faqat
// ko'prik bilan ulashilgan CLICK_BRIDGE_SECRET orqali ishonch bildiriladi (baza_bridge.php
// naqshi bilan bir xil — subtitr_bridge.php'dagi "xom uzatish" emas).

export const CLICK_SERVICE_ID = process.env.CLICK_SERVICE_ID || "99657";
export const CLICK_MERCHANT_ID = process.env.CLICK_MERCHANT_ID || "59136";
export const CLICK_MERCHANT_USER_ID = process.env.CLICK_MERCHANT_USER_ID || "81435";
export const CLICK_BASE_URL = "https://my.click.uz/services/pay";

// PHP ko'prikda (wstore_bridge.php) shu prefikslar bilan tekshiriladi.
export const CLICK_PREFIX_PURCHASE = "WSTP";
export const CLICK_PREFIX_LISTING = "WSTL";

// Sotuvchi loyihasini e'lon qilish uchun bir martalik to'lov (so'mda).
export const LISTING_FEE_SOM = 5000;

// Platforma komissiyasi (foizda) — xarid to'langanda sotuvchi balansiga
// shuncha foiz ayirilib qo'shiladi. Hozircha 0% — butun summa sotuvchiga
// tushadi. O'zgartirmoqchi bo'lsangiz shu qiymatni yangilang.
export const PLATFORM_COMMISSION_PERCENT = 0;

export function amountAfterCommission(amountSom: number): number {
  return Math.round(amountSom * (1 - PLATFORM_COMMISSION_PERCENT / 100));
}

// Bitta yechib olish so'rovi uchun minimal summa (so'mda).
export const MIN_WITHDRAWAL_SOM = 50_000;

// Taklif qilingan do'st birinchi xaridini qilganda, taklif qilganga
// bir martalik bonus (so'mda).
export const REFERRAL_BONUS_SOM = 10_000;

// Mahsulot narxi (DB'da USD) -> Click to'lovi uchun so'm. To'lov yaratilganda
// QOTIRILADI (Order.amount'ga yoziladi) — keyinroq kurs o'zgarsa ham eski
// to'lovlar buzilmaydi. Providers.tsx dagi ko'rsatish kursi (RATES.UZS) bilan
// ATAYLAB alohida — u faqat vitrina uchun, bu esa to'lov haqiqati uchun.
export const PRODUCT_UZS_RATE = 12600;

export function usdToSom(usd: number): number {
  return Math.round(usd * PRODUCT_UZS_RATE);
}

// myxvest bridge -> wstore.uz so'rovlarini tasdiqlash uchun ichki sir.
export function clickBridgeSecret(): string {
  const s = process.env.CLICK_BRIDGE_SECRET;
  if (!s) throw new Error("CLICK_BRIDGE_SECRET .env da o'rnatilmagan");
  return s;
}

// merchant_trans_id ("WSTP42" / "WSTL7") ichidan ClickTransaction.id ni ajratib oladi.
export function parseClickTransactionId(merchantTransId: string): number {
  const m = String(merchantTransId || "").match(/^(WSTP|WSTL)(\d+)$/);
  if (!m) return 0;
  return parseInt(m[2], 10);
}

export function buildClickPaymentUrl(
  merchantTransId: string,
  amountSom: number,
  returnUrl: string,
): string {
  const q = new URLSearchParams({
    service_id: CLICK_SERVICE_ID,
    merchant_id: CLICK_MERCHANT_ID,
    amount: String(Math.round(amountSom)),
    transaction_param: merchantTransId,
    merchant_user_id: CLICK_MERCHANT_USER_ID,
    return_url: returnUrl,
  });
  return `${CLICK_BASE_URL}?${q.toString()}`;
}
