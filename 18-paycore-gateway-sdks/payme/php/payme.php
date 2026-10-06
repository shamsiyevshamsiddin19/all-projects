<?php
/**
 * Payme uchun YAGONA endpoint.
 *
 * Click'dan farqli — Payme'da ikkita fayl (prepare/complete) emas, BITTA
 * manzil bor. Payme "method" maydoniga qarab qaysi amalni bajarishni o'zi
 * aytadi (CheckPerformTransaction, CreateTransaction va h.k.).
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * IKKI XIL ISHLATILADI:
 *
 *   1. Oddiy hosting — Payme to'g'ridan-to'g'ri shu faylga uradi:
 *          https://domen.uz/payme.php
 *
 *   2. Framework (Laravel, Slim...):
 *          require_once __DIR__ . '/payme/php/payme_methods.php';
 *          require_once __DIR__ . '/payme/php/payme_utils.php';
 *          $javob = paymeHandleRequest(paymeRequestData(), paymeAuthorizationHeader());
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Payme kabinetiga yoziladigan manzil: https://sizning-domen.uz/payme.php
 */

require_once __DIR__ . '/payme_methods.php';
require_once __DIR__ . '/payme_utils.php';

if (paymeIsDirectRequest(__FILE__)) {
    $response = paymeHandleRequest(paymeRequestData(), paymeAuthorizationHeader());
    paymeSendJson($response);
}
