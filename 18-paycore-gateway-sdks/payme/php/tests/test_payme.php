<?php
/**
 * Payme metodlarining testlari.
 *
 * Ishga tushirish (loyiha ildizidan):
 *
 *     php tests/test_payme.php
 *
 * PHPUnit kerak emas — oddiy skript.
 */

// --- Hodisalarni kuzatish ----------------------------------------------------
// MUHIM: bularni payme_orders.php dan OLDIN e'lon qilamiz — u
// `if (!function_exists(...))` bilan o'ralgan, shuning uchun bizniki kuchda
// qoladi.

$GLOBALS['paid_calls'] = array();
$GLOBALS['cancelled_calls'] = array();
$GLOBALS['can_refund_result'] = true;

function paymeOnPaid(PaymeTransaction $tx)
{
    $GLOBALS['paid_calls'][] = $tx->paymeId;
}

function paymeOnCancelled(PaymeTransaction $tx)
{
    $GLOBALS['cancelled_calls'][] = $tx->paymeId;
}

function paymeCanRefund(PaymeTransaction $tx)
{
    return $GLOBALS['can_refund_result'];
}

putenv('PAYME_DB_PATH=:memory:');

require_once __DIR__ . '/../payme_methods.php';
require_once __DIR__ . '/../payme_checkout.php';

define('T_MERCHANT_ID', '5cd108976ce4a8423da6d5c9');
define('T_SECRET_KEY', 'test_secret_key');
define('T_LOGIN', 'Paycom');

paymeSetConfig(array(
    'merchant_id' => T_MERCHANT_ID,
    'secret_key' => T_SECRET_KEY,
    'merchant_login' => T_LOGIN,
));

function tAuthHeader($login = T_LOGIN, $key = T_SECRET_KEY)
{
    return 'Basic ' . base64_encode($login . ':' . $key);
}

function tRpc($method, array $params, $reqId = 1, $auth = 'USE_DEFAULT_AUTH')
{
    // Sentinel: chaqiruvchi $auth ni umuman bermasa, standart (to'g'ri) auth
    // ishlatiladi. Aynan `null` berilsa (sarlavha yo'q holatini sinash uchun)
    // shu holicha uzatiladi — Payme'dan auth sarlavhasisiz kelgan so'rovni
    // taqlid qiladi.
    if ($auth === 'USE_DEFAULT_AUTH') {
        $auth = tAuthHeader();
    }
    return paymeHandleRequest(array('method' => $method, 'params' => $params, 'id' => $reqId), $auth);
}

function tNowMs()
{
    return paymeNowMs();
}

// --- Kichik test runner ------------------------------------------------------

$GLOBALS['tests_run'] = 0;
$GLOBALS['tests_failed'] = 0;

function check($condition, $name, $info = '')
{
    $GLOBALS['tests_run']++;
    if ($condition) {
        echo "  OK   {$name}\n";
    } else {
        $GLOBALS['tests_failed']++;
        echo "  XATO {$name}" . ($info !== '' ? " -> {$info}" : '') . "\n";
    }
}

function checkEq($expected, $actual, $name)
{
    check(
        $expected === $actual,
        $name,
        'kutilgan: ' . var_export($expected, true) . ', kelgan: ' . var_export($actual, true)
    );
}

function resetState()
{
    $GLOBALS['paid_calls'] = array();
    $GLOBALS['cancelled_calls'] = array();
    $GLOBALS['can_refund_result'] = true;
}

// =============================================================================
//  AUTH
// =============================================================================

echo "\nAUTH\n";
resetState();

$res = tRpc('CheckTransaction', array('id' => 'x'), 1, null);
checkEq(-32504, $res['error']['code'], 'auth: sarlavha yo\'q -> -32504');

$res = tRpc('CheckTransaction', array('id' => 'x'), 1, tAuthHeader(T_LOGIN, 'noto\'g\'ri'));
checkEq(-32504, $res['error']['code'], 'auth: noto\'g\'ri parol -> -32504');

$res = tRpc('CheckTransaction', array('id' => 'x'), 1, tAuthHeader('Hacker', T_SECRET_KEY));
checkEq(-32504, $res['error']['code'], 'auth: noto\'g\'ri login -> -32504');

$res = tRpc('NomalumMetod', array());
checkEq(-32601, $res['error']['code'], 'noma\'lum metod -> -32601');

// =============================================================================
//  CheckPerformTransaction
// =============================================================================

echo "\nCheckPerformTransaction\n";
resetState();

paymeDemoCreateOrder('ORD1', 500000);
$res = tRpc('CheckPerformTransaction', array('amount' => 500000, 'account' => array('order_id' => 'ORD1')));
checkEq(true, $res['result']['allow'], 'check-perform: muvaffaqiyatli');

$res = tRpc('CheckPerformTransaction', array('amount' => 500000, 'account' => array('order_id' => 'YOQ')));
checkEq(-31050, $res['error']['code'], 'check-perform: order topilmadi -> -31050');

$res = tRpc('CheckPerformTransaction', array('amount' => 1, 'account' => array('order_id' => 'ORD1')));
checkEq(-31001, $res['error']['code'], 'check-perform: noto\'g\'ri summa -> -31001');

paymeDemoCreateOrder('ORD2', 500000);
tRpc('CreateTransaction', array('id' => 'tx-existing', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD2')));
$res = tRpc('CheckPerformTransaction', array('amount' => 500000, 'account' => array('order_id' => 'ORD2')));
checkEq(-31099, $res['error']['code'], 'check-perform: tranzaksiya allaqachon bor -> -31099');

// =============================================================================
//  CreateTransaction
// =============================================================================

echo "\nCreateTransaction\n";
resetState();

paymeDemoCreateOrder('ORD3', 500000);
$res = tRpc('CreateTransaction', array('id' => 'tx1', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD3')));
checkEq(PAYME_STATE_PENDING, $res['result']['state'], 'create: state=1 (pending)');
checkEq('tx1', $res['result']['transaction'], 'create: transaction id qaytadi');

$first = tRpc('CreateTransaction', array('id' => 'tx1', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD3')));
checkEq($res['result']['create_time'], $first['result']['create_time'], 'create: idempotent takroriy so\'rov');

$res = tRpc('CreateTransaction', array('id' => 'tx-yoq', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'YOQORDER')));
checkEq(-31050, $res['error']['code'], 'create: order topilmadi -> -31050');

paymeDemoCreateOrder('ORD4', 500000);
$oldTime = tNowMs() - PAYME_TRANSACTION_TIMEOUT_MS - 1000;
tRpc('CreateTransaction', array('id' => 'tx-timeout', 'time' => $oldTime, 'amount' => 500000, 'account' => array('order_id' => 'ORD4')));
$res = tRpc('CreateTransaction', array('id' => 'tx-timeout', 'time' => $oldTime, 'amount' => 500000, 'account' => array('order_id' => 'ORD4')));
checkEq(-31008, $res['error']['code'], 'create: muddati o\'tgan -> -31008');
$tx = paymeGetTransaction('tx-timeout');
checkEq(PAYME_STATE_CANCELLED, $tx->state, 'create: muddati o\'tganda avtomatik bekor qilinadi');
checkEq(PAYME_REASON_TIMEOUT, $tx->reason, 'create: sabab=TIMEOUT');

paymeDemoCreateOrder('ORD5', 500000);
tRpc('CreateTransaction', array('id' => 'tx-a', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD5')));
$res = tRpc('CreateTransaction', array('id' => 'tx-b', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD5')));
checkEq(-31099, $res['error']['code'], 'create: bitta orderga ikkinchi tranzaksiya -> -31099');

// =============================================================================
//  PerformTransaction
// =============================================================================

echo "\nPerformTransaction\n";
resetState();

paymeDemoCreateOrder('ORD6', 500000);
tRpc('CreateTransaction', array('id' => 'tx2', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD6')));
$res = tRpc('PerformTransaction', array('id' => 'tx2'));
checkEq(PAYME_STATE_PAID, $res['result']['state'], 'perform: state=2 (paid)');
checkEq(array('tx2'), $GLOBALS['paid_calls'], 'perform: paymeOnPaid chaqirildi');

$second = tRpc('PerformTransaction', array('id' => 'tx2'));
checkEq($res['result']['perform_time'], $second['result']['perform_time'], 'perform: idempotent takroriy so\'rov');
checkEq(array('tx2'), $GLOBALS['paid_calls'], 'perform: paymeOnPaid FAQAT bir marta');

$res = tRpc('PerformTransaction', array('id' => 'yoq'));
checkEq(-31003, $res['error']['code'], 'perform: topilmagan tranzaksiya -> -31003');

paymeDemoCreateOrder('ORD7', 500000);
tRpc('CreateTransaction', array('id' => 'tx-cancel', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD7')));
tRpc('CancelTransaction', array('id' => 'tx-cancel', 'reason' => 3));
$res = tRpc('PerformTransaction', array('id' => 'tx-cancel'));
checkEq(-31008, $res['error']['code'], 'perform: bekor qilingandan keyin -> -31008');

paymeDemoCreateOrder('ORD8', 500000);
$oldTime2 = tNowMs() - PAYME_TRANSACTION_TIMEOUT_MS - 1000;
tRpc('CreateTransaction', array('id' => 'tx-expired', 'time' => $oldTime2, 'amount' => 500000, 'account' => array('order_id' => 'ORD8')));
$res = tRpc('PerformTransaction', array('id' => 'tx-expired'));
checkEq(-31008, $res['error']['code'], 'perform: muddati o\'tgan -> -31008');
checkEq(PAYME_STATE_CANCELLED, paymeGetTransaction('tx-expired')->state, 'perform: muddati o\'tganda bekor qilinadi');

// =============================================================================
//  CancelTransaction
// =============================================================================

echo "\nCancelTransaction\n";
resetState();

paymeDemoCreateOrder('ORD9', 500000);
tRpc('CreateTransaction', array('id' => 'tx3', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD9')));
$res = tRpc('CancelTransaction', array('id' => 'tx3', 'reason' => 3));
checkEq(PAYME_STATE_CANCELLED, $res['result']['state'], 'cancel: pending -> CANCELLED');
checkEq(array('tx3'), $GLOBALS['cancelled_calls'], 'cancel: paymeOnCancelled chaqirildi');

resetState();
paymeDemoCreateOrder('ORD10', 500000);
tRpc('CreateTransaction', array('id' => 'tx4', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD10')));
tRpc('PerformTransaction', array('id' => 'tx4'));
$res = tRpc('CancelTransaction', array('id' => 'tx4', 'reason' => 5));
checkEq(PAYME_STATE_CANCELLED_AFTER_PAID, $res['result']['state'], 'cancel: paid -> CANCELLED_AFTER_PAID (refund)');
checkEq(array('tx4'), $GLOBALS['paid_calls'], 'cancel: paymeOnPaid oldin chaqirilgan edi');
checkEq(array('tx4'), $GLOBALS['cancelled_calls'], 'cancel: paymeOnCancelled ham chaqirildi');

resetState();
paymeDemoCreateOrder('ORD11', 500000);
tRpc('CreateTransaction', array('id' => 'tx5', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD11')));
$first = tRpc('CancelTransaction', array('id' => 'tx5', 'reason' => 3));
$second = tRpc('CancelTransaction', array('id' => 'tx5', 'reason' => 1));
checkEq($first['result']['cancel_time'], $second['result']['cancel_time'], 'cancel: idempotent (vaqt o\'zgarmaydi)');
checkEq(array('tx5'), $GLOBALS['cancelled_calls'], 'cancel: paymeOnCancelled FAQAT bir marta');

$res = tRpc('CancelTransaction', array('id' => 'yoq', 'reason' => 1));
checkEq(-31003, $res['error']['code'], 'cancel: topilmagan tranzaksiya -> -31003');

resetState();
$GLOBALS['can_refund_result'] = false;
paymeDemoCreateOrder('ORD12', 500000);
tRpc('CreateTransaction', array('id' => 'tx6', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD12')));
tRpc('PerformTransaction', array('id' => 'tx6'));
$res = tRpc('CancelTransaction', array('id' => 'tx6', 'reason' => 5));
checkEq(-31007, $res['error']['code'], 'cancel: paymeCanRefund false -> -31007');
checkEq(PAYME_STATE_PAID, paymeGetTransaction('tx6')->state, 'cancel: rad etilganda holat PAID qoladi');
$GLOBALS['can_refund_result'] = true;

// =============================================================================
//  CheckTransaction
// =============================================================================

echo "\nCheckTransaction\n";
resetState();

paymeDemoCreateOrder('ORD13', 500000);
tRpc('CreateTransaction', array('id' => 'tx7', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD13')));
$res = tRpc('CheckTransaction', array('id' => 'tx7'));
checkEq(PAYME_STATE_PENDING, $res['result']['state'], 'check: state=1');
checkEq(0, $res['result']['perform_time'], 'check: perform_time=0');
checkEq(0, $res['result']['cancel_time'], 'check: cancel_time=0');
checkEq(null, $res['result']['reason'], 'check: reason=null');

$res = tRpc('CheckTransaction', array('id' => 'yoq'));
checkEq(-31003, $res['error']['code'], 'check: topilmagan -> -31003');

// =============================================================================
//  GetStatement
// =============================================================================

echo "\nGetStatement\n";
resetState();

paymeDemoCreateOrder('ORD14', 500000);
paymeDemoCreateOrder('ORD15', 100000);
$t0 = tNowMs();
tRpc('CreateTransaction', array('id' => 'tx8', 'time' => tNowMs(), 'amount' => 500000, 'account' => array('order_id' => 'ORD14')));
tRpc('CreateTransaction', array('id' => 'tx9', 'time' => tNowMs(), 'amount' => 100000, 'account' => array('order_id' => 'ORD15')));
$t1 = tNowMs() + 1000;

// Diqqat: bu bitta PHP jarayonida ishlaydigan test skripti bo'lgani uchun
// xotiradagi baza avvalgi bo'limlarning tranzaksiyalarini ham saqlab
// turadi. Shuning uchun "aynan shu ikkitasi" emas, "shu ikkitasi RO'YXATDA
// bor" deb tekshiramiz — bu haqiqiy ishlatilishga ham to'g'ri keladi
// (GetStatement har doim faqat SIZning tranzaksiyalaringizni qaytarmaydi).
$res = tRpc('GetStatement', array('from' => $t0 - 1000, 'to' => $t1));
$ids = array_map(function ($t) { return $t['id']; }, $res['result']['transactions']);
check(in_array('tx8', $ids, true) && in_array('tx9', $ids, true), 'get-statement: ikkala tranzaksiya ro\'yxatda bor');

$res = tRpc('GetStatement', array('from' => 0, 'to' => 1));
checkEq(array(), $res['result']['transactions'], 'get-statement: bo\'sh oraliq (1970-yil)');

// =============================================================================
//  To'lov havolasi
// =============================================================================

echo "\nTO'LOV HAVOLASI\n";

$url = paymeCheckoutUrl(array('order_id' => 42), paymeSomToTiyin(5000));
check(strpos($url, 'https://checkout.paycom.uz/') === 0, 'havola to\'g\'ri manzildan boshlanadi');
$encoded = substr($url, strlen('https://checkout.paycom.uz/'));
$decoded = base64_decode($encoded);
checkEq('m=' . T_MERCHANT_ID . ';ac.order_id=42;a=500000', $decoded, 'havola tarkibi to\'g\'ri');
check(strpos($url, T_SECRET_KEY) === false, 'havolada secret_key YO\'Q');

checkEq(500000, paymeSomToTiyin(5000), 'som->tiyin: 5000 -> 500000');
checkEq(12345, paymeSomToTiyin('123.45'), 'som->tiyin: kasrli qiymat');

// =============================================================================

echo "\n";
echo "=====================================\n";
printf("  Jami: %d, xato: %d\n", $GLOBALS['tests_run'], $GLOBALS['tests_failed']);
echo "=====================================\n";

exit($GLOBALS['tests_failed'] > 0 ? 1 : 0);
