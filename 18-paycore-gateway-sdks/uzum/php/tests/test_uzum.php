<?php
/**
 * uzumHandle* funksiyalari uchun testlar.
 *
 * Ishga tushirish (loyiha ildizidan):
 *
 *     php tests/test_uzum.php
 *
 * PHPUnit kerak emas — oddiy skript.
 */

// --- Hodisalarni kuzatish ----------------------------------------------------
// MUHIM: bularni uzum_orders.php dan OLDIN e'lon qilamiz. U yerdagi
// funksiyalar `if (!function_exists(...))` bilan o'ralgani uchun bizniki
// kuchda qoladi.

$GLOBALS['confirmed_calls'] = array();
$GLOBALS['reversed_calls'] = array();

function uzumOnConfirmed(UzumTransaction $tx)
{
    $GLOBALS['confirmed_calls'][] = $tx->transId;
}

function uzumOnReversed(UzumTransaction $tx)
{
    $GLOBALS['reversed_calls'][] = $tx->transId;
}

putenv('UZUM_DB_PATH=:memory:');
require_once __DIR__ . '/../uzum_methods.php';

const SERVICE_ID = 101202;
const LOGIN = 'myLogin';
const SECRET = 'myPassword';

uzumSetConfig(array('service_id' => SERVICE_ID, 'webhook_login' => LOGIN, 'webhook_secret' => SECRET));

function tAuth()
{
    return 'Basic ' . base64_encode(LOGIN . ':' . SECRET);
}

function tBadAuth()
{
    return 'Basic ' . base64_encode('wrong:wrong');
}

function tCheckReq($account = '42', array $over = array())
{
    $data = array('serviceId' => SERVICE_ID, 'timestamp' => 1, 'params' => array('account' => $account));
    return array_merge($data, $over);
}

function tCreateReq($transId, $account = '42', $amount = 2500000, array $over = array())
{
    $data = array(
        'serviceId' => SERVICE_ID, 'timestamp' => 1, 'transId' => $transId,
        'params' => array('account' => $account), 'amount' => $amount,
    );
    return array_merge($data, $over);
}

function tConfirmReq($transId, array $over = array())
{
    $data = array(
        'serviceId' => SERVICE_ID, 'timestamp' => 1, 'transId' => $transId,
        'paymentSource' => 'UZCARD', 'phone' => '998901234567',
    );
    return array_merge($data, $over);
}

function tReverseReq($transId, array $over = array())
{
    $data = array('serviceId' => SERVICE_ID, 'timestamp' => 1, 'transId' => $transId);
    return array_merge($data, $over);
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
    check($expected === $actual, $name, 'kutilgan: ' . var_export($expected, true) . ', kelgan: ' . var_export($actual, true));
}

// =============================================================================
//  AUTH
// =============================================================================

echo "\nAUTH\n";
uzumDemoCreateOrder('42', 2500000);

list($status, $body) = uzumHandleCheck(tCheckReq(), tBadAuth());
checkEq(400, $status, 'soxta auth -> HTTP 400');
checkEq('10001', $body['errorCode'], 'soxta auth -> 10001');

list($status, $body) = uzumHandleCheck(tCheckReq(), null);
checkEq(400, $status, "auth yo'q -> HTTP 400");
checkEq('10001', $body['errorCode'], "auth yo'q -> 10001");

// =============================================================================
//  /check
// =============================================================================

echo "\n/check\n";

list($status, $body) = uzumHandleCheck(tCheckReq(), tAuth());
checkEq(200, $status, 'check muvaffaqiyatli');
checkEq('OK', $body['status'], 'check status OK');

list($status, $body) = uzumHandleCheck(tCheckReq('999'), tAuth());
checkEq(400, $status, 'check topilmagan');
checkEq('10007', $body['errorCode'], 'check topilmagan -> 10007');

list($status, $body) = uzumHandleCheck(tCheckReq('42', array('serviceId' => 555)), tAuth());
checkEq('10006', $body['errorCode'], "check noto'g'ri serviceId -> 10006");

$req = tCheckReq();
unset($req['timestamp']);
list($status, $body) = uzumHandleCheck($req, tAuth());
checkEq('10005', $body['errorCode'], "check timestamp yo'q -> 10005");

// =============================================================================
//  /create
// =============================================================================

echo "\n/create\n";

list($status, $body) = uzumHandleCreate(tCreateReq('t1'), tAuth());
checkEq(200, $status, 'create muvaffaqiyatli');
checkEq('CREATED', $body['status'], 'create status CREATED');
checkEq('t1', $body['transId'], "create transId to'g'ri");

list($status, $body) = uzumHandleCreate(tCreateReq('t1'), tAuth());
checkEq(400, $status, 'takroriy create -> HTTP 400');
checkEq('10010', $body['errorCode'], 'takroriy create -> 10010 (idempotent EMAS)');

list($status, $body) = uzumHandleCreate(tCreateReq('t2', '42', 100), tAuth());
checkEq('10011', $body['errorCode'], "create noto'g'ri summa -> 10011");

list($status, $body) = uzumHandleCreate(tCreateReq('t3', '999'), tAuth());
checkEq('10007', $body['errorCode'], "create topilmagan hisob -> 10007");

// =============================================================================
//  /confirm
// =============================================================================

echo "\n/confirm\n";

uzumDemoCreateOrder('50', 1000000, 'Daftar');
uzumHandleCreate(tCreateReq('c1', '50', 1000000), tAuth());

list($status, $body) = uzumHandleConfirm(tConfirmReq('c1'), tAuth());
checkEq(200, $status, 'confirm muvaffaqiyatli');
checkEq('CONFIRMED', $body['status'], 'confirm status CONFIRMED');
check(in_array('c1', $GLOBALS['confirmed_calls']), 'confirm uzumOnConfirmed() ni chaqiradi');

list($status, $body) = uzumHandleConfirm(tConfirmReq('c1'), tAuth());
checkEq(400, $status, 'takroriy confirm -> HTTP 400');
checkEq('10016', $body['errorCode'], 'takroriy confirm -> 10016 (idempotent EMAS)');
checkEq(1, count(array_keys($GLOBALS['confirmed_calls'], 'c1')), 'takroriy confirm uzumOnConfirmed ni QAYTA chaqirmaydi');

list($status, $body) = uzumHandleConfirm(tConfirmReq('yoq-id'), tAuth());
checkEq('10014', $body['errorCode'], 'confirm topilmagan -> 10014');

$req = tConfirmReq('c1');
unset($req['paymentSource']);
list($status, $body) = uzumHandleConfirm($req, tAuth());
checkEq('10005', $body['errorCode'], "confirm paymentSource yo'q -> 10005");

// =============================================================================
//  /reverse
// =============================================================================

echo "\n/reverse\n";

uzumDemoCreateOrder('60', 500000, 'Ruchka');
uzumHandleCreate(tCreateReq('r1', '60', 500000), tAuth());

list($status, $body) = uzumHandleReverse(tReverseReq('r1'), tAuth());
checkEq(200, $status, 'CREATED holatidan reverse');
checkEq('REVERSED', $body['status'], 'reverse status REVERSED');
check(in_array('r1', $GLOBALS['reversed_calls']), 'reverse uzumOnReversed() ni chaqiradi');

list($status, $body) = uzumHandleConfirm(tConfirmReq('r1'), tAuth());
checkEq('10015', $body['errorCode'], 'bekor qilingandan keyin confirm -> 10015');

list($status, $body) = uzumHandleReverse(tReverseReq('r1'), tAuth());
checkEq('10018', $body['errorCode'], 'takroriy reverse -> 10018');

// refund (CONFIRMED holatidan reverse)
uzumDemoCreateOrder('70', 700000, 'Qalam');
uzumHandleCreate(tCreateReq('r2', '70', 700000), tAuth());
uzumHandleConfirm(tConfirmReq('r2'), tAuth());

list($status, $body) = uzumHandleReverse(tReverseReq('r2'), tAuth());
checkEq(200, $status, 'CONFIRMED holatidan reverse (refund)');
checkEq('REVERSED', $body['status'], 'refund status REVERSED');
check(in_array('r2', $GLOBALS['reversed_calls']), 'refund uzumOnReversed() ni chaqiradi');

list($status, $body) = uzumHandleReverse(tReverseReq('yoq-id'), tAuth());
checkEq('10014', $body['errorCode'], 'reverse topilmagan -> 10014');

// =============================================================================
//  /status
// =============================================================================

echo "\n/status\n";

uzumDemoCreateOrder('80', 200000, 'Marker');
uzumHandleCreate(tCreateReq('s1', '80', 200000), tAuth());

list($status, $body) = uzumHandleStatus(tReverseReq('s1'), tAuth());
checkEq(200, $status, 'status CREATED');
checkEq('CREATED', $body['status'], 'status CREATED qiymati');
check(!isset($body['confirmTime']), 'status CREATED holatida confirmTime yo\'q');

uzumHandleConfirm(tConfirmReq('s1'), tAuth());
list($status, $body) = uzumHandleStatus(tReverseReq('s1'), tAuth());
checkEq('CONFIRMED', $body['status'], 'status CONFIRMED qiymati');
check(isset($body['confirmTime']), 'status CONFIRMED holatida confirmTime bor');

list($status, $body) = uzumHandleStatus(tReverseReq('yoq-id'), tAuth());
checkEq('10014', $body['errorCode'], 'status topilmagan -> 10014');

// =============================================================================
//  Poyga himoyasi — eng muhim shart
// =============================================================================

echo "\nPOYGA HIMOYASI\n";

uzumDemoCreateOrder('90', 300000, 'Flomaster');
uzumHandleCreate(tCreateReq('p1', '90', 300000), tAuth());

check(uzumMarkConfirmed('p1') !== null, 'uzumMarkConfirmed birinchi marta yozuv qaytaradi');
check(uzumMarkConfirmed('p1') === null, "uzumMarkConfirmed ikkinchi marta NULL qaytaradi (mahsulot ikki marta berilmaydi)");

// =============================================================================

echo "\n";
echo "=====================================\n";
printf("  Jami: %d, xato: %d\n", $GLOBALS['tests_run'], $GLOBALS['tests_failed']);
echo "=====================================\n";

exit($GLOBALS['tests_failed'] > 0 ? 1 : 0);
