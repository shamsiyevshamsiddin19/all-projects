<?php
/**
 * Click imzosi (sign_string) — qurish va tekshirish.
 *
 * Click har bir so'rovni md5 imzo bilan yuboradi. Formula prepare va
 * complete'da ozgina farq qiladi:
 *
 *     prepare  (action=0):
 *         md5(click_trans_id + service_id + secret_key + merchant_trans_id
 *             + amount + action + sign_time)
 *
 *     complete (action=1):
 *         md5(click_trans_id + service_id + secret_key + merchant_trans_id
 *             + merchant_prepare_id + amount + action + sign_time)
 *
 * Yagona farq — complete'da merchant_trans_id bilan amount orasiga
 * merchant_prepare_id qo'shiladi.
 *
 * Bu faylga tegishingiz shart emas.
 */

require_once __DIR__ . '/click_config.php';

define('CLICK_ACTION_PREPARE', '0');
define('CLICK_ACTION_COMPLETE', '1');

if (!function_exists('clickBuildSignString')) {
    /**
     * Imzolanadigan xom satrni yig'adi (hali md5 qilinmagan).
     *
     * @param array $p click_trans_id, service_id, secret_key, merchant_trans_id,
     *                 amount, action, sign_time, merchant_prepare_id
     */
    function clickBuildSignString(array $p)
    {
        $signString = (string)$p['click_trans_id']
            . (string)$p['service_id']
            . (string)$p['secret_key']
            . (string)$p['merchant_trans_id'];

        if ((string)$p['action'] === CLICK_ACTION_COMPLETE) {
            $signString .= (string)(isset($p['merchant_prepare_id']) ? $p['merchant_prepare_id'] : '');
        }

        return $signString
            . (string)$p['amount']
            . (string)$p['action']
            . (string)$p['sign_time'];
    }
}

if (!function_exists('clickMakeSign')) {
    /**
     * sign_string ni hisoblaydi (md5, kichik harfli hex).
     */
    function clickMakeSign(array $p)
    {
        return md5(clickBuildSignString($p));
    }
}

if (!function_exists('clickSignsEqual')) {
    /**
     * Ikki imzoni vaqt bo'yicha barqaror (timing-safe) solishtiradi.
     *
     * Oddiy `==` imzoni belgima-belgi topib olish hujumiga yo'l ochadi,
     * shuning uchun hash_equals ishlatiladi.
     */
    function clickSignsEqual($received, $expected)
    {
        $received = strtolower(trim((string)$received));
        $expected = strtolower(trim((string)$expected));

        if ($received === '' || $expected === '') {
            return false;
        }

        return hash_equals($expected, $received);
    }
}

if (!function_exists('clickCheckSign')) {
    /**
     * Click so'rovining imzosini tekshiradi.
     *
     * `$action` SO'ROVDAN OLINMAYDI — qaysi endpoint chaqirilgan bo'lsa,
     * o'shanikini ('0' yoki '1') beramiz. Aks holda hujumchi prepare uchun
     * olingan imzoni complete so'roviga qo'yib yuborishi mumkin bo'lardi.
     *
     * MUHIM: `amount` imzoga Click YUBORGAN XOM SATR holida kiradi. Click
     * "5000.00" yuborsa, uni float'ga o'girib qaytadan satrga aylantirsangiz
     * "5000" bo'lib qoladi va imzo mos kelmaydi. Shuning uchun bu yerda
     * qiymatlar o'zgartirilmasdan uzatiladi.
     *
     * @param array  $data   Click so'rovidagi maydonlar
     * @param string $action CLICK_ACTION_PREPARE yoki CLICK_ACTION_COMPLETE
     */
    function clickCheckSign(array $data, $action)
    {
        $serviceId = isset($data['service_id']) ? (string)$data['service_id'] : '';

        if ($serviceId === '' || !clickSignsEqual($serviceId, clickConfig('service_id'))) {
            return false;
        }

        $expected = clickMakeSign(array(
            'click_trans_id'      => isset($data['click_trans_id']) ? $data['click_trans_id'] : '',
            'service_id'          => $serviceId,
            'secret_key'          => clickConfig('secret_key'),
            'merchant_trans_id'   => isset($data['merchant_trans_id']) ? $data['merchant_trans_id'] : '',
            'amount'              => isset($data['amount']) ? $data['amount'] : '',
            'action'              => $action,
            'sign_time'           => isset($data['sign_time']) ? $data['sign_time'] : '',
            'merchant_prepare_id' => isset($data['merchant_prepare_id']) ? $data['merchant_prepare_id'] : '',
        ));

        $received = isset($data['sign_string']) ? $data['sign_string'] : '';

        return clickSignsEqual($received, $expected);
    }
}
