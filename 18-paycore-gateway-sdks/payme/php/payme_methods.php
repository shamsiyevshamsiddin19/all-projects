<?php
/**
 * Payme Merchant API'ning 6 metodi va JSON-RPC dispatcher.
 *
 * Bu fayl HECH QANDAY web-framework'ga bog'liq emas: kiruvchi so'rov
 * ma'lumotini oddiy massiv sifatida oladi, javobni ham massiv qilib
 * qaytaradi.
 *
 * Oqim (Click'dagi prepare/complete'dan farqli, Payme'da OLTITA metod bor):
 *
 *     CheckPerformTransaction — "bu to'lovni qabul qila olasanmi?"
 *     CreateTransaction       — Payme tranzaksiya ochadi (bizning "prepare"imiz)
 *     PerformTransaction      — pul yechildi, tasdiqla (bizning "complete"imiz)
 *     CancelTransaction       — to'lovni yoki tasdiqlangan to'lovni bekor qil
 *     CheckTransaction        — tranzaksiya holatini so'raydi
 *     GetStatement            — vaqt oralig'idagi tranzaksiyalar ro'yxati
 *
 * Bu faylga tegishingiz shart emas — bazangizga ulanish payme_orders.php da.
 */

require_once __DIR__ . '/payme_errors.php';
require_once __DIR__ . '/payme_config.php';
require_once __DIR__ . '/payme_auth.php';
require_once __DIR__ . '/payme_orders.php';

// =============================================================================
//  1. CheckPerformTransaction — "bu to'lovni qabul qila olasanmi?"
// =============================================================================

if (!function_exists('paymeCheckPerformTransaction')) {
    function paymeCheckPerformTransaction(array $params)
    {
        $account = paymeRequireArray($params, 'account');
        $amount = paymeRequireInt($params, 'amount');

        $acc = paymeFindAccount($account);
        if ($acc === null) {
            throw paymeOrderNotFound();
        }

        if (!$acc->payable) {
            throw paymeOrderNotPayable();
        }

        if ($amount !== $acc->amount) {
            throw paymeInvalidAmount();
        }

        $existing = paymeGetActiveTransactionForAccount($account);
        if ($existing !== null) {
            throw paymeTransactionAlreadyExists();
        }

        return array('allow' => true);
    }
}

// =============================================================================
//  2. CreateTransaction — Payme tranzaksiya ochadi ("prepare")
// =============================================================================

if (!function_exists('paymeCreateTransactionMethod')) {
    function paymeCreateTransactionMethod(array $params)
    {
        $paymeId = paymeRequireString($params, 'id');
        $paymeTime = paymeRequireInt($params, 'time');
        $amount = paymeRequireInt($params, 'amount');
        $account = paymeRequireArray($params, 'account');

        $existing = paymeGetTransaction($paymeId);

        if ($existing !== null) {
            if ($existing->state !== PAYME_STATE_PENDING) {
                throw paymeUnableToPerform();
            }

            if (paymeIsExpired($existing->paymeTime)) {
                paymeMarkCancelled($paymeId, PAYME_REASON_TIMEOUT);
                throw paymeUnableToPerform();
            }

            return paymeCreateResult($existing);
        }

        // Yangi tranzaksiya — avval CheckPerformTransaction bilan bir xil
        // tekshiruvlarni bajaramiz.
        paymeCheckPerformTransaction(array('account' => $account, 'amount' => $amount));

        $created = paymeCreateTransaction($paymeId, $paymeTime, $amount, $account);
        return paymeCreateResult($created);
    }
}

if (!function_exists('paymeCreateResult')) {
    function paymeCreateResult(PaymeTransaction $tx)
    {
        return array(
            'create_time' => $tx->createTime,
            'transaction' => $tx->ourId,
            'state' => $tx->state,
        );
    }
}

// =============================================================================
//  3. PerformTransaction — pul yechildi, tasdiqla ("complete")
// =============================================================================

if (!function_exists('paymePerformTransactionMethod')) {
    function paymePerformTransactionMethod(array $params)
    {
        $paymeId = paymeRequireString($params, 'id');

        $tx = paymeGetTransaction($paymeId);
        if ($tx === null) {
            throw paymeTransactionNotFound();
        }

        if ($tx->state === PAYME_STATE_PAID) {
            // Takroriy callback — mahsulot allaqachon berilgan.
            return paymePerformResult($tx);
        }

        if ($tx->state !== PAYME_STATE_PENDING) {
            throw paymeUnableToPerform();
        }

        if (paymeIsExpired($tx->paymeTime)) {
            paymeMarkCancelled($paymeId, PAYME_REASON_TIMEOUT);
            throw paymeUnableToPerform();
        }

        $updated = paymeMarkPerformed($paymeId);
        if ($updated === null) {
            // Parallel so'rov bizdan oldin ulgurdi.
            $again = paymeGetTransaction($paymeId);
            return paymePerformResult($again !== null ? $again : $tx);
        }

        $account = paymeFindAccount($updated->account);
        $updated->accountExtra = $account !== null ? $account->extra : array();
        paymeSafeCall('paymeOnPaid', $updated, 'paymeOnPaid');

        return paymePerformResult($updated);
    }
}

if (!function_exists('paymePerformResult')) {
    function paymePerformResult(PaymeTransaction $tx)
    {
        return array(
            'transaction' => $tx->ourId,
            'perform_time' => $tx->performTime,
            'state' => $tx->state,
        );
    }
}

// =============================================================================
//  4. CancelTransaction — to'lovni (yoki tasdiqlangan to'lovni) bekor qiladi
// =============================================================================

if (!function_exists('paymeCancelTransactionMethod')) {
    function paymeCancelTransactionMethod(array $params)
    {
        $paymeId = paymeRequireString($params, 'id');
        $reason = paymeRequireInt($params, 'reason');

        $tx = paymeGetTransaction($paymeId);
        if ($tx === null) {
            throw paymeTransactionNotFound();
        }

        if (in_array($tx->state, array(PAYME_STATE_CANCELLED, PAYME_STATE_CANCELLED_AFTER_PAID), true)) {
            // Idempotent — mavjud natijani qaytaramiz, sababni yangilamaymiz.
            return paymeCancelResult($tx);
        }

        if ($tx->state === PAYME_STATE_PAID) {
            $account = paymeFindAccount($tx->account);
            $tx->accountExtra = $account !== null ? $account->extra : array();
            if (!paymeSafeCallBool('paymeCanRefund', $tx, true)) {
                throw paymeUnableToCancel();
            }
        }

        $updated = paymeMarkCancelled($paymeId, $reason);
        if ($updated === null) {
            $again = paymeGetTransaction($paymeId);
            return paymeCancelResult($again !== null ? $again : $tx);
        }

        $account = paymeFindAccount($updated->account);
        $updated->accountExtra = $account !== null ? $account->extra : array();
        paymeSafeCall('paymeOnCancelled', $updated, 'paymeOnCancelled');

        return paymeCancelResult($updated);
    }
}

if (!function_exists('paymeCancelResult')) {
    function paymeCancelResult(PaymeTransaction $tx)
    {
        return array(
            'transaction' => $tx->ourId,
            'cancel_time' => $tx->cancelTime,
            'state' => $tx->state,
        );
    }
}

// =============================================================================
//  5. CheckTransaction — tranzaksiya holatini so'raydi
// =============================================================================

if (!function_exists('paymeCheckTransactionMethod')) {
    function paymeCheckTransactionMethod(array $params)
    {
        $paymeId = paymeRequireString($params, 'id');

        $tx = paymeGetTransaction($paymeId);
        if ($tx === null) {
            throw paymeTransactionNotFound();
        }

        return array(
            'create_time' => $tx->createTime,
            'perform_time' => $tx->performTime,
            'cancel_time' => $tx->cancelTime,
            'transaction' => $tx->ourId,
            'state' => $tx->state,
            'reason' => $tx->reason,
        );
    }
}

// =============================================================================
//  6. GetStatement — vaqt oralig'idagi tranzaksiyalar ro'yxati
// =============================================================================

if (!function_exists('paymeGetStatementMethod')) {
    function paymeGetStatementMethod(array $params)
    {
        $fromMs = paymeRequireInt($params, 'from');
        $toMs = paymeRequireInt($params, 'to');

        $txs = paymeListTransactions($fromMs, $toMs);

        $result = array();
        foreach ($txs as $tx) {
            $result[] = array(
                'id' => $tx->paymeId,
                'time' => $tx->paymeTime,
                'amount' => $tx->amount,
                'account' => $tx->account,
                'create_time' => $tx->createTime,
                'perform_time' => $tx->performTime,
                'cancel_time' => $tx->cancelTime,
                'transaction' => $tx->ourId,
                'state' => $tx->state,
                'reason' => $tx->reason,
            );
        }

        return array('transactions' => $result);
    }
}

// =============================================================================
//  JSON-RPC dispatcher — HTTP qatlami shu bitta funksiyani chaqiradi
// =============================================================================

if (!function_exists('paymeHandleRequest')) {
    /**
     * Payme'dan kelgan JSON-RPC so'rovini to'liq qayta ishlaydi.
     *
     * `$body` — so'rov massivi (`['method', 'params', 'id']`).
     * `$authorizationHeader` — HTTP `Authorization` sarlavhasi (Basic ...).
     *
     * Har doim `['result' => ...]` yoki `['error' => [...]]` massiv
     * qaytaradi — bu javobni HTTP 200 bilan qaytaring.
     */
    function paymeHandleRequest($body, $authorizationHeader)
    {
        $requestId = is_array($body) && isset($body['id']) ? $body['id'] : null;

        try {
            if (!paymeCheckAuth($authorizationHeader)) {
                throw paymeUnauthorized();
            }

            if (!is_array($body)) {
                throw paymeJsonParseError();
            }

            $method = isset($body['method']) ? $body['method'] : null;
            if (empty($method) || !is_string($method)) {
                throw paymeRequiredFieldMissing('method');
            }

            $handlers = array(
                'CheckPerformTransaction' => 'paymeCheckPerformTransaction',
                'CreateTransaction' => 'paymeCreateTransactionMethod',
                'PerformTransaction' => 'paymePerformTransactionMethod',
                'CancelTransaction' => 'paymeCancelTransactionMethod',
                'CheckTransaction' => 'paymeCheckTransactionMethod',
                'GetStatement' => 'paymeGetStatementMethod',
            );

            if (!isset($handlers[$method])) {
                throw paymeMethodNotFound();
            }

            $params = isset($body['params']) && is_array($body['params']) ? $body['params'] : array();

            $result = call_user_func($handlers[$method], $params);

            return array('result' => $result, 'id' => $requestId);
        } catch (PaymeError $e) {
            return array('error' => $e->toArray(), 'id' => $requestId);
        }
    }
}

// --- Ichki yordamchilar -------------------------------------------------------

if (!function_exists('paymeIsExpired')) {
    function paymeIsExpired($paymeTime)
    {
        return (paymeNowMs() - (int)$paymeTime) > PAYME_TRANSACTION_TIMEOUT_MS;
    }
}

if (!function_exists('paymeRequireArray')) {
    function paymeRequireArray(array $params, $key)
    {
        if (!isset($params[$key]) || !is_array($params[$key])) {
            throw paymeRequiredFieldMissing($key);
        }
        return $params[$key];
    }
}

if (!function_exists('paymeRequireString')) {
    function paymeRequireString(array $params, $key)
    {
        if (empty($params[$key]) || !is_string($params[$key])) {
            throw paymeRequiredFieldMissing($key);
        }
        return $params[$key];
    }
}

if (!function_exists('paymeRequireInt')) {
    function paymeRequireInt(array $params, $key)
    {
        if (!isset($params[$key]) || !is_numeric($params[$key])) {
            throw paymeRequiredFieldMissing($key);
        }
        return (int)$params[$key];
    }
}

if (!function_exists('paymeSafeCall')) {
    /**
     * Hodisa funksiyasini chaqiradi; xato bo'lsa loglaydi, javobni buzmaydi.
     *
     * Bu nuqtaga yetganda pul allaqachon yechilgan/qaytarilgan. Xato bo'lsa
     * ham Payme'ga muvaffaqiyat javobi ketadi — holat bazada o'zgargan,
     * faqat callback ishlamay qolgan. Buni logdan kuzatib, qo'lda hal qilasiz.
     */
    function paymeSafeCall($function, PaymeTransaction $transaction, $name)
    {
        try {
            call_user_func($function, $transaction);
        } catch (Throwable $e) {
            paymeLog('error', $name . '() xatosi — holat bazada o\'zgargan, qo\'lda tekshiring', array(
                'payme_id' => $transaction->paymeId,
                'xato' => $e->getMessage(),
            ));
        }
    }
}

if (!function_exists('paymeSafeCallBool')) {
    function paymeSafeCallBool($function, PaymeTransaction $transaction, $default)
    {
        try {
            return (bool)call_user_func($function, $transaction);
        } catch (Throwable $e) {
            paymeLog('error', 'paymeCanRefund() xatosi — standart qiymat ishlatiladi', array(
                'xato' => $e->getMessage(),
            ));
            return $default;
        }
    }
}
