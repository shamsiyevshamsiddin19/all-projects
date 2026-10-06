<?php
/**
 * Uzum Bank Merchant API'ning 5 webhook'i.
 *
 * Bu modul HAR BIR funksiya `array($httpStatus, $body)` juftini qaytaradi.
 * FastAPI/Flask'dagidek — HTTP qatlamiga bog'liq emas.
 *
 * Click/Payme'dan FARQI: Uzum Bank BESHTA ALOHIDA manzilga so'rov yuboradi
 * (bitta JSON-RPC endpoint emas) va xato holatida HTTP 400 kutadi (200 emas):
 *
 *     POST /check    — "bu to'lovni qabul qila olasanmi?" (pul yo'q hali)
 *     POST /create   — Uzum Bank tranzaksiya ochadi
 *     POST /confirm  — PUL ALLAQACHON YECHILGAN, mahsulotni ber
 *     POST /reverse  — to'lovni yoki tasdiqlangan to'lovni bekor qil
 *     POST /status   — tranzaksiya holatini so'raydi
 *
 * Bu faylga tegishingiz shart emas — bazangizga ulanish uzum_orders.php da.
 */

require_once __DIR__ . '/uzum_errors.php';
require_once __DIR__ . '/uzum_config.php';
require_once __DIR__ . '/uzum_auth.php';
require_once __DIR__ . '/uzum_orders.php';

if (!function_exists('uzumRequireField')) {
    function uzumRequireField(array $data, $key)
    {
        if (!isset($data[$key]) || $data[$key] === '' || $data[$key] === null) {
            throw uzumRequiredFieldMissing();
        }
        return $data[$key];
    }
}

if (!function_exists('uzumRequireServiceId')) {
    function uzumRequireServiceId(array $data)
    {
        $raw = uzumRequireField($data, 'serviceId');
        if (!is_numeric($raw) || (int)$raw !== (int)uzumConfig('service_id')) {
            throw uzumInvalidServiceId();
        }
    }
}

if (!function_exists('uzumIsExpired')) {
    function uzumIsExpired($createTime)
    {
        return (uzumNowMs() - (int)$createTime) > UZUM_TRANSACTION_TIMEOUT_MS;
    }
}

// =============================================================================
//  1. /check — "bu to'lovni qabul qila olasanmi?"
// =============================================================================

if (!function_exists('uzumHandleCheck')) {
    function uzumHandleCheck(array $data, $authorizationHeader)
    {
        return uzumWrap(function () use ($data, $authorizationHeader) {
            if (!uzumCheckAuth($authorizationHeader)) {
                throw uzumAccessDenied();
            }

            uzumRequireServiceId($data);
            uzumRequireField($data, 'timestamp');
            $params = uzumRequireField($data, 'params');
            if (!is_array($params)) {
                throw uzumRequiredFieldMissing();
            }

            $account = uzumFindAccount($params);
            if ($account === null) {
                throw uzumAccountNotFound();
            }
            if (!$account->payable) {
                throw uzumAlreadyPaid();
            }

            return array(
                'serviceId' => (int)uzumConfig('service_id'),
                'timestamp' => uzumNowMs(),
                'status'    => 'OK',
            );
        });
    }
}

// =============================================================================
//  2. /create — Uzum Bank tranzaksiya ochadi
// =============================================================================

if (!function_exists('uzumHandleCreate')) {
    function uzumHandleCreate(array $data, $authorizationHeader)
    {
        return uzumWrap(function () use ($data, $authorizationHeader) {
            if (!uzumCheckAuth($authorizationHeader)) {
                throw uzumAccessDenied();
            }

            uzumRequireServiceId($data);
            uzumRequireField($data, 'timestamp');
            $transId = (string)uzumRequireField($data, 'transId');
            $params = uzumRequireField($data, 'params');
            $amount = uzumRequireField($data, 'amount');
            if (!is_array($params)) {
                throw uzumRequiredFieldMissing();
            }

            // DIQQAT: takroriy /create — Uzum Bank hujjati bo'yicha bu
            // XATO, Payme'dagidek "idempotent" emas.
            $existing = uzumGetTransaction($transId);
            if ($existing !== null) {
                throw uzumTransactionAlreadyCreated();
            }

            $account = uzumFindAccount($params);
            if ($account === null) {
                throw uzumAccountNotFound();
            }
            if (!$account->payable) {
                throw uzumAlreadyPaid();
            }

            $amount = (int)$amount;
            if ($amount !== $account->amount) {
                throw uzumInvalidAmount();
            }

            // Mudofaa uchun qo'shilgan (hujjatda so'zma-so'z yozilmagan):
            // bitta buyurtmaga ikkita PARALLEL faol tranzaksiya ochilmasin.
            $active = uzumGetActiveTransactionForAccount($params);
            if ($active !== null) {
                throw uzumAlreadyPaid();
            }

            $created = uzumCreateTransaction($transId, $amount, $params);

            return array(
                'serviceId' => (int)uzumConfig('service_id'),
                'transId'   => $created->transId,
                'status'    => UZUM_STATE_CREATED,
                'transTime' => $created->createTime,
            );
        }, array('transTime' => true));
    }
}

// =============================================================================
//  3. /confirm — PUL ALLAQACHON YECHILGAN, mahsulotni ber
// =============================================================================

if (!function_exists('uzumHandleConfirm')) {
    function uzumHandleConfirm(array $data, $authorizationHeader)
    {
        return uzumWrap(function () use ($data, $authorizationHeader) {
            if (!uzumCheckAuth($authorizationHeader)) {
                throw uzumAccessDenied();
            }

            uzumRequireServiceId($data);
            uzumRequireField($data, 'timestamp');
            $transId = (string)uzumRequireField($data, 'transId');
            uzumRequireField($data, 'paymentSource');
            uzumRequireField($data, 'phone');

            $tx = uzumGetTransaction($transId);
            if ($tx === null) {
                throw uzumTransactionNotFound();
            }

            if ($tx->state === UZUM_STATE_REVERSED) {
                throw uzumTransactionCancelled();
            }

            if ($tx->state === UZUM_STATE_CONFIRMED) {
                // Uzum Bank hujjati bo'yicha takroriy /confirm — XATO.
                throw uzumTransactionAlreadyConfirmed();
            }

            if (uzumIsExpired($tx->createTime)) {
                uzumMarkReversed($transId);
                throw uzumTransactionCancelled();
            }

            $updated = uzumMarkConfirmed($transId);
            if ($updated === null) {
                $again = uzumGetTransaction($transId);
                if ($again !== null && $again->state === UZUM_STATE_CONFIRMED) {
                    throw uzumTransactionAlreadyConfirmed();
                }
                throw uzumInternalError();
            }

            $account = uzumFindAccount($updated->params);
            $updated->accountExtra = $account ? $account->extra : array();
            uzumSafeCall('uzumOnConfirmed', $updated, 'uzumOnConfirmed');

            return array(
                'serviceId'   => (int)uzumConfig('service_id'),
                'transId'     => $updated->transId,
                'status'      => UZUM_STATE_CONFIRMED,
                'confirmTime' => $updated->confirmTime,
            );
        }, array('confirmTime' => true));
    }
}

// =============================================================================
//  4. /reverse — to'lovni (yoki tasdiqlangan to'lovni) bekor qiladi
// =============================================================================

if (!function_exists('uzumHandleReverse')) {
    function uzumHandleReverse(array $data, $authorizationHeader)
    {
        return uzumWrap(function () use ($data, $authorizationHeader) {
            if (!uzumCheckAuth($authorizationHeader)) {
                throw uzumAccessDenied();
            }

            uzumRequireServiceId($data);
            uzumRequireField($data, 'timestamp');
            $transId = (string)uzumRequireField($data, 'transId');

            $tx = uzumGetTransaction($transId);
            if ($tx === null) {
                throw uzumTransactionNotFound();
            }

            if ($tx->state === UZUM_STATE_REVERSED) {
                // Uzum Bank hujjati bo'yicha takroriy /reverse — XATO.
                throw uzumTransactionAlreadyCancelled();
            }

            if ($tx->state === UZUM_STATE_CONFIRMED) {
                $account = uzumFindAccount($tx->params);
                $tx->accountExtra = $account ? $account->extra : array();
                if (!uzumSafeCallBool('uzumCanReverse', $tx, true)) {
                    throw uzumUnableToCancel();
                }
            }

            $updated = uzumMarkReversed($transId);
            if ($updated === null) {
                throw uzumTransactionAlreadyCancelled();
            }

            $account = uzumFindAccount($updated->params);
            $updated->accountExtra = $account ? $account->extra : array();
            uzumSafeCall('uzumOnReversed', $updated, 'uzumOnReversed');

            return array(
                'serviceId'   => (int)uzumConfig('service_id'),
                'transId'     => $updated->transId,
                'status'      => UZUM_STATE_REVERSED,
                'reverseTime' => $updated->reverseTime,
            );
        }, array('reverseTime' => true));
    }
}

// =============================================================================
//  5. /status — tranzaksiya holatini so'raydi
// =============================================================================

if (!function_exists('uzumHandleStatus')) {
    function uzumHandleStatus(array $data, $authorizationHeader)
    {
        return uzumWrap(function () use ($data, $authorizationHeader) {
            if (!uzumCheckAuth($authorizationHeader)) {
                throw uzumAccessDenied();
            }

            uzumRequireServiceId($data);
            uzumRequireField($data, 'timestamp');
            $transId = (string)uzumRequireField($data, 'transId');

            $tx = uzumGetTransaction($transId);
            if ($tx === null) {
                throw uzumTransactionNotFound();
            }

            if ($tx->state === UZUM_STATE_CREATED && uzumIsExpired($tx->createTime)) {
                $expired = uzumMarkReversed($transId);
                if ($expired !== null) {
                    $tx = $expired;
                }
            }

            $result = array(
                'serviceId' => (int)uzumConfig('service_id'),
                'transId'   => $tx->transId,
                'status'    => $tx->state,
                'transTime' => $tx->createTime,
            );
            if ($tx->confirmTime) {
                $result['confirmTime'] = $tx->confirmTime;
            }
            if ($tx->reverseTime) {
                $result['reverseTime'] = $tx->reverseTime;
            }

            return $result;
        });
    }
}

// =============================================================================
//  Ichki yordamchilar
// =============================================================================

if (!function_exists('uzumWrap')) {
    /**
     * Handler'ni chaqiradi va array($httpStatus, $body) juftini qaytaradi.
     *
     * $extraTimeFields — xato javobida qaysi vaqt maydonlarini qo'shish
     * kerakligini bildiradi (Uzum Bank ba'zi xato javoblarida ham
     * transTime/confirmTime/reverseTime kutadi).
     */
    function uzumWrap($fn, array $extraTimeFields = array())
    {
        try {
            return array(200, $fn());
        } catch (UzumError $e) {
            $body = $e->toArray();
            $now = uzumNowMs();
            if (!empty($extraTimeFields['transTime'])) {
                $body['transTime'] = $now;
            }
            if (!empty($extraTimeFields['confirmTime'])) {
                $body['confirmTime'] = $now;
            }
            if (!empty($extraTimeFields['reverseTime'])) {
                $body['reverseTime'] = $now;
            }
            return array(400, $body);
        } catch (Throwable $e) {
            uzumLog('error', 'Kutilmagan xato', array('message' => $e->getMessage()));
            return array(400, uzumInternalError()->toArray());
        }
    }
}

if (!function_exists('uzumSafeCall')) {
    /**
     * Hodisa funksiyasini chaqiradi; xato bo'lsa loglaydi, javobni buzmaydi.
     */
    function uzumSafeCall($function, UzumTransaction $transaction, $name)
    {
        try {
            call_user_func($function, $transaction);
        } catch (Throwable $e) {
            uzumLog('error', $name . '() xatosi — holat bazada o\'zgargan, qo\'lda tekshiring', array(
                'trans_id' => $transaction->transId,
                'xato'     => $e->getMessage(),
            ));
        }
    }
}

if (!function_exists('uzumSafeCallBool')) {
    function uzumSafeCallBool($function, UzumTransaction $transaction, $default)
    {
        try {
            return (bool)call_user_func($function, $transaction);
        } catch (Throwable $e) {
            uzumLog('error', 'uzumCanReverse() xatosi — standart qiymat ishlatiladi');
            return $default;
        }
    }
}
