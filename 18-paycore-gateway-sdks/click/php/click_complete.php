<?php
/**
 * Click COMPLETE so'rovi.
 *
 * Click bu so'rovni "pul yechildi, endi mahsulotni ber" deb yuboradi
 * (yoki "foydalanuvchi bekor qildi" deb — `error` maydoniga qarab).
 *
 * Biz tekshiramiz:
 *     - so'rov to'liqmi                       -> yo'q bo'lsa -8
 *     - imzo haqiqiymi                        -> yo'q bo'lsa -1
 *     - bunday buyurtma bormi                 -> yo'q bo'lsa -5
 *     - merchant_prepare_id prepare'dagi id'ga mos keladimi -> yo'q bo'lsa -6
 *     - summa bazadagiga mos keladimi         -> yo'q bo'lsa -2
 *
 * Hammasi joyida bo'lsa buyurtmani "to'landi" deb belgilaymiz va
 * clickOnPaid() ni chaqiramiz — mahsulot o'sha yerda beriladi.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * IKKI XIL ISHLATILADI:
 *
 *   1. Oddiy hosting — Click to'g'ridan-to'g'ri shu faylga uradi:
 *          https://domen.uz/click_complete.php
 *
 *   2. Framework:
 *          require_once __DIR__ . '/click/php/click_complete.php';
 *          $javob = clickHandleComplete($sorovMaydonlari);
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Bu faylga tegishingiz shart emas — bazangizga ulanish click_orders.php da.
 */

require_once __DIR__ . '/click_errors.php';
require_once __DIR__ . '/click_utils.php';
require_once __DIR__ . '/click_config.php';
require_once __DIR__ . '/click_signature.php';
require_once __DIR__ . '/click_orders.php';

// Complete'da prepare'dagilarga qo'shimcha merchant_prepare_id ham keladi.
if (!defined('CLICK_COMPLETE_REQUIRED_FIELDS')) {
    define('CLICK_COMPLETE_REQUIRED_FIELDS', array(
        'click_trans_id',
        'service_id',
        'merchant_trans_id',
        'merchant_prepare_id',
        'amount',
        'sign_time',
        'sign_string',
    ));
}

if (!function_exists('clickHandleComplete')) {
    /**
     * Click complete so'rovini qayta ishlaydi va javob massivini qaytaradi.
     *
     * @param array $data So'rovdagi maydonlar (POST form yoki JSON — farqi yo'q)
     * @return array Click'ga JSON qilib qaytariladigan javob
     */
    function clickHandleComplete(array $data)
    {
        $missing = clickMissingFields($data, CLICK_COMPLETE_REQUIRED_FIELDS);
        if (!empty($missing)) {
            clickLog('warning', 'complete: maydon yetishmayapti', array('missing' => $missing));
            return clickCompleteResponse($data, 0, CLICK_BAD_REQUEST);
        }

        if (!clickCheckSign($data, CLICK_ACTION_COMPLETE)) {
            clickLog('warning', 'complete: imzo xato', array(
                'merchant_trans_id' => $data['merchant_trans_id'],
            ));
            return clickCompleteResponse($data, 0, CLICK_SIGN_CHECK_FAILED);
        }

        $merchantTransId = (string)$data['merchant_trans_id'];
        $clickTransId = (string)$data['click_trans_id'];
        $order = clickFindOrder($merchantTransId);

        if ($order === null) {
            clickLog('warning', 'complete: buyurtma topilmadi', array(
                'merchant_trans_id' => $merchantTransId,
            ));
            return clickCompleteResponse($data, 0, CLICK_USER_NOT_FOUND);
        }

        // prepare'da qaytargan id bilan bir xil bo'lishi shart.
        if (clickAsInt($data['merchant_prepare_id']) !== $order->id) {
            clickLog('warning', 'complete: merchant_prepare_id mos emas', array(
                'kutilgan' => $order->id,
                'kelgan'   => $data['merchant_prepare_id'],
            ));
            return clickCompleteResponse($data, $order->id, CLICK_TRANSACTION_NOT_FOUND);
        }

        if (!clickAmountsMatch($data['amount'], $order->amount)) {
            clickLog('warning', 'complete: summa mos emas', array(
                'bazada'  => $order->amount,
                'sorovda' => $data['amount'],
            ));
            return clickCompleteResponse($data, $order->id, CLICK_INCORRECT_AMOUNT);
        }

        // Takroriy callback: Click javobni ololmay qayta urgan. Pul allaqachon
        // hisobga olingan — muvaffaqiyat deb javob beramiz, clickOnPaid()
        // QAYTA chaqirilmaydi.
        if ($order->status === CLICK_STATUS_PAID) {
            clickLog('info', 'complete: takroriy callback', array(
                'merchant_trans_id' => $merchantTransId,
            ));
            return clickCompleteResponse($data, $order->id, CLICK_SUCCESS);
        }

        if ($order->status === CLICK_STATUS_CANCELLED) {
            return clickCompleteResponse($data, $order->id, CLICK_TRANSACTION_CANCELLED);
        }

        // Click o'zi bekor qilish/xato haqida xabar bergan.
        $clickError = clickAsInt(isset($data['error']) ? $data['error'] : 0);
        if ($clickError !== 0) {
            clickMarkCancelled($order, $clickTransId);
            $order->status = CLICK_STATUS_CANCELLED;

            clickLog('info', 'complete: to\'lov bekor qilindi', array(
                'merchant_trans_id' => $merchantTransId,
                'click_error'       => $clickError,
            ));

            clickSafeCall('clickOnCancelled', $order);

            return clickCompleteResponse($data, $order->id, CLICK_TRANSACTION_CANCELLED);
        }

        // Asosiy holat: to'lov muvaffaqiyatli.
        //
        // clickMarkPaid() faqat HAQIQATAN pending -> paid o'tkazgan bo'lsa true
        // qaytaradi. Parallel kelgan ikkinchi callback false oladi va mahsulot
        // ikki marta berilmaydi.
        if (!clickMarkPaid($order, $clickTransId)) {
            clickLog('info', 'complete: boshqa callback ulgurdi — clickOnPaid o\'tkazib yuborildi', array(
                'merchant_trans_id' => $merchantTransId,
            ));
            return clickCompleteResponse($data, $order->id, CLICK_SUCCESS);
        }

        $order->status = CLICK_STATUS_PAID;

        clickLog('info', 'complete OK', array(
            'merchant_trans_id' => $merchantTransId,
            'order_id'          => $order->id,
            'amount'            => $order->amount,
        ));

        clickSafeCall('clickOnPaid', $order);

        return clickCompleteResponse($data, $order->id, CLICK_SUCCESS);
    }
}

if (!function_exists('clickSafeCall')) {
    /**
     * Hodisa funksiyasini chaqiradi; xato bo'lsa loglaydi, javobni buzmaydi.
     *
     * Nega xatoni yutamiz? Bu nuqtaga yetganda pul yechilgan va buyurtma
     * "paid" deb belgilangan. Click'ga xato qaytarsak u qayta uradi — lekin
     * yuqorida "allaqachon to'langan" bo'lib SUCCESS oladi, ya'ni clickOnPaid
     * baribir qayta ishlamaydi. Shuning uchun to'g'ri yo'l: xatoni loglab,
     * keyin qo'lda hal qilish.
     */
    function clickSafeCall($function, ClickOrder $order)
    {
        try {
            call_user_func($function, $order);
        } catch (Throwable $e) {
            // PHP 7+ — Error va Exception ikkalasini ham tutadi.
            clickLog('error', $function . '() xatosi — to\'lov "paid" holicha qoldi, qo\'lda tekshiring', array(
                'merchant_trans_id' => $order->merchantTransId,
                'xato'              => $e->getMessage(),
            ));
        }
    }
}

if (!function_exists('clickCompleteResponse')) {
    /**
     * Click kutadigan javob shakli.
     *
     * Diqqat: prepare'da `merchant_prepare_id`, complete'da esa
     * `merchant_confirm_id` deb nomlanadi.
     */
    function clickCompleteResponse(array $data, $merchantConfirmId, $error)
    {
        return array(
            'click_trans_id'      => clickAsInt(isset($data['click_trans_id']) ? $data['click_trans_id'] : 0),
            'merchant_trans_id'   => (string)(isset($data['merchant_trans_id']) ? $data['merchant_trans_id'] : ''),
            'merchant_confirm_id' => (int)$merchantConfirmId,
            'error'               => (int)$error,
            'error_note'          => clickErrorNote($error),
        );
    }
}

// --- Endpoint ---------------------------------------------------------------
// Fayl web-server orqali to'g'ridan-to'g'ri chaqirilgan bo'lsa — javob beramiz.
// require qilingan bo'lsa (framework) — hech narsa qilmaymiz.

if (clickIsDirectRequest(__FILE__)) {
    clickSendJson(clickHandleComplete(clickRequestData()));
}
