<?php
/**
 * Click xato kodlari.
 *
 * Bu kodlarni Click belgilagan — o'zgartirmang. Click javobdagi `error`
 * maydoniga qarab to'lovni davom ettiradi yoki to'xtatadi.
 *
 * Bu faylga tegishingiz shart emas.
 */

// Muvaffaqiyat
define('CLICK_SUCCESS', 0);

// Imzo (sign_string) yoki service_id mos kelmadi
define('CLICK_SIGN_CHECK_FAILED', -1);

// So'rovdagi summa bazadagidan farq qiladi
define('CLICK_INCORRECT_AMOUNT', -2);

define('CLICK_ACTION_NOT_FOUND', -3);

// To'lov allaqachon to'langan
define('CLICK_ALREADY_PAID', -4);

// merchant_trans_id bo'yicha buyurtma topilmadi
define('CLICK_USER_NOT_FOUND', -5);

// merchant_prepare_id mos kelmadi
define('CLICK_TRANSACTION_NOT_FOUND', -6);

define('CLICK_FAILED_TO_UPDATE_USER', -7);

// So'rovda majburiy maydon yetishmayapti
define('CLICK_BAD_REQUEST', -8);

// To'lov bekor qilingan
define('CLICK_TRANSACTION_CANCELLED', -9);

if (!function_exists('clickErrorNote')) {
    /**
     * Xato kodiga mos izoh (Click javobidagi `error_note`).
     */
    function clickErrorNote($code)
    {
        $notes = array(
            CLICK_SUCCESS                => 'Success',
            CLICK_SIGN_CHECK_FAILED      => 'SIGN CHECK FAILED!',
            CLICK_INCORRECT_AMOUNT       => 'Incorrect parameter amount',
            CLICK_ACTION_NOT_FOUND       => 'Action not found',
            CLICK_ALREADY_PAID           => 'Already paid',
            CLICK_USER_NOT_FOUND         => 'User does not exist',
            CLICK_TRANSACTION_NOT_FOUND  => 'Transaction does not exist',
            CLICK_FAILED_TO_UPDATE_USER  => 'Failed to update user',
            CLICK_BAD_REQUEST            => 'Error in request from click',
            CLICK_TRANSACTION_CANCELLED  => 'Transaction cancelled',
        );

        $code = (int)$code;

        return isset($notes[$code]) ? $notes[$code] : 'Unknown error';
    }
}
