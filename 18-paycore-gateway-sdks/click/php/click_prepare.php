<?php
/**
 * Click PREPARE so'rovi.
 *
 * Click bu so'rovni "shu to'lovni qabul qila olasanmi?" deb yuboradi.
 * Bu bosqichda pul HALI YECHILMAGAN.
 *
 * Biz tekshiramiz:
 *     - so'rov to'liqmi                    -> yo'q bo'lsa -8
 *     - imzo haqiqiymi                     -> yo'q bo'lsa -1
 *     - bunday buyurtma bormi              -> yo'q bo'lsa -5
 *     - summa bazadagiga mos keladimi      -> yo'q bo'lsa -2
 *     - allaqachon to'lanmaganmi           -> to'langan bo'lsa -4
 *     - bekor qilinmaganmi                 -> bekor bo'lsa -9
 *
 * Hammasi joyida bo'lsa `error: 0` va `merchant_prepare_id` (buyurtma id'si)
 * qaytaramiz. Click keyin pulni yechib, click_complete.php ga murojaat qiladi.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * IKKI XIL ISHLATILADI:
 *
 *   1. Oddiy hosting — Click to'g'ridan-to'g'ri shu faylga uradi:
 *          https://domen.uz/click_prepare.php
 *      Boshqa hech narsa qilish shart emas, fayl o'zi javob beradi.
 *
 *   2. Framework (Laravel, Slim, Symfony, CodeIgniter...):
 *          require_once __DIR__ . '/click/php/click_prepare.php';
 *          $javob = clickHandlePrepare($sorovMaydonlari);
 *      Bunda fayl o'zi hech narsa chiqarmaydi.
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Bu faylga tegishingiz shart emas — bazangizga ulanish click_orders.php da.
 */

require_once __DIR__ . '/click_errors.php';
require_once __DIR__ . '/click_utils.php';
require_once __DIR__ . '/click_config.php';
require_once __DIR__ . '/click_signature.php';
require_once __DIR__ . '/click_orders.php';

// Click prepare so'rovida yuboradigan majburiy maydonlar.
if (!defined('CLICK_PREPARE_REQUIRED_FIELDS')) {
    define('CLICK_PREPARE_REQUIRED_FIELDS', array(
        'click_trans_id',
        'service_id',
        'merchant_trans_id',
        'amount',
        'sign_time',
        'sign_string',
    ));
}

if (!function_exists('clickHandlePrepare')) {
    /**
     * Click prepare so'rovini qayta ishlaydi va javob massivini qaytaradi.
     *
     * @param array $data So'rovdagi maydonlar (POST form yoki JSON — farqi yo'q)
     * @return array Click'ga JSON qilib qaytariladigan javob
     */
    function clickHandlePrepare(array $data)
    {
        $missing = clickMissingFields($data, CLICK_PREPARE_REQUIRED_FIELDS);
        if (!empty($missing)) {
            clickLog('warning', 'prepare: maydon yetishmayapti', array('missing' => $missing));
            return clickPrepareResponse($data, 0, CLICK_BAD_REQUEST);
        }

        if (!clickCheckSign($data, CLICK_ACTION_PREPARE)) {
            clickLog('warning', 'prepare: imzo xato', array(
                'merchant_trans_id' => $data['merchant_trans_id'],
            ));
            return clickPrepareResponse($data, 0, CLICK_SIGN_CHECK_FAILED);
        }

        $merchantTransId = (string)$data['merchant_trans_id'];
        $order = clickFindOrder($merchantTransId);

        if ($order === null) {
            clickLog('warning', 'prepare: buyurtma topilmadi', array(
                'merchant_trans_id' => $merchantTransId,
            ));
            return clickPrepareResponse($data, 0, CLICK_USER_NOT_FOUND);
        }

        // Summani HAR DOIM bazadan tekshiramiz — so'rovdagi qiymatga ishonmaymiz.
        if (!clickAmountsMatch($data['amount'], $order->amount)) {
            clickLog('warning', 'prepare: summa mos emas', array(
                'bazada'  => $order->amount,
                'sorovda' => $data['amount'],
            ));
            return clickPrepareResponse($data, $order->id, CLICK_INCORRECT_AMOUNT);
        }

        if ($order->status === CLICK_STATUS_PAID) {
            return clickPrepareResponse($data, $order->id, CLICK_ALREADY_PAID);
        }

        if ($order->status === CLICK_STATUS_CANCELLED) {
            return clickPrepareResponse($data, $order->id, CLICK_TRANSACTION_CANCELLED);
        }

        clickLog('info', 'prepare OK', array(
            'merchant_trans_id' => $merchantTransId,
            'order_id'          => $order->id,
            'click_trans_id'    => $data['click_trans_id'],
        ));

        return clickPrepareResponse($data, $order->id, CLICK_SUCCESS);
    }
}

if (!function_exists('clickPrepareResponse')) {
    /**
     * Click kutadigan javob shakli.
     */
    function clickPrepareResponse(array $data, $merchantPrepareId, $error)
    {
        return array(
            'click_trans_id'      => clickAsInt(isset($data['click_trans_id']) ? $data['click_trans_id'] : 0),
            'merchant_trans_id'   => (string)(isset($data['merchant_trans_id']) ? $data['merchant_trans_id'] : ''),
            'merchant_prepare_id' => (int)$merchantPrepareId,
            'error'               => (int)$error,
            'error_note'          => clickErrorNote($error),
        );
    }
}

// --- Endpoint ---------------------------------------------------------------
// Fayl web-server orqali to'g'ridan-to'g'ri chaqirilgan bo'lsa — javob beramiz.
// require qilingan bo'lsa (framework) — hech narsa qilmaymiz.

if (clickIsDirectRequest(__FILE__)) {
    clickSendJson(clickHandlePrepare(clickRequestData()));
}
