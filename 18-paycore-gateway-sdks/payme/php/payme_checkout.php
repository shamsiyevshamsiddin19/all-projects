<?php
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

require_once __DIR__ . '/payme_config.php';

if (!function_exists('paymeSomToTiyin')) {
    /** So'mni tiyinga o'giradi (1 so'm = 100 tiyin). Payme SUMMA TIYINDA kutadi. */
    function paymeSomToTiyin($som)
    {
        return (int)round(((float)$som) * 100);
    }
}

if (!function_exists('paymeCheckoutUrl')) {
    /**
     * Foydalanuvchi yuboriladigan Payme to'lov havolasini quradi.
     *
     * `$account` — Payme'ga yuboriladigan hisob maydonlari (masalan
     * `['order_id' => 42]`). Shu maydonlar `payme_orders.php`dagi
     * `paymeFindAccount()` ga qaytib keladi.
     *
     * `$amountTiyin` — summa TIYINDA (so'm emas!). `paymeSomToTiyin()`
     * bilan o'giring.
     *
     * Namuna:
     *     $url = paymeCheckoutUrl(['order_id' => 42], paymeSomToTiyin(5000));
     */
    function paymeCheckoutUrl(array $account, $amountTiyin, $returnUrl = null, $lang = null)
    {
        $parts = array('m=' . paymeConfig('merchant_id'));

        foreach ($account as $key => $value) {
            $parts[] = 'ac.' . $key . '=' . $value;
        }

        $parts[] = 'a=' . (int)$amountTiyin;

        if ($returnUrl !== null) {
            $parts[] = 'c=' . $returnUrl;
        }
        if ($lang !== null) {
            $parts[] = 'l=' . $lang;
        }

        $raw = implode(';', $parts);
        $encoded = base64_encode($raw);

        return rtrim(paymeConfig('checkout_base_url'), '/') . '/' . $encoded;
    }
}
