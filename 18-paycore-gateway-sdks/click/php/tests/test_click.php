<?php
/**
 * click_prepare.php va click_complete.php testlari.
 *
 * Ishga tushirish (loyiha ildizidan):
 *
 *     php tests/test_click.php
 *
 * PHPUnit kerak emas — oddiy skript.
 */

// --- Hodisalarni kuzatish ----------------------------------------------------
// MUHIM: bularni click_orders.php dan OLDIN e'lon qilamiz. click_orders.php
// dagi funksiyalar `if (!function_exists(...))` bilan o'ralgani uchun bizniki
// kuchda qoladi. Siz ham o'z loyihangizda shu usulda ustidan yozishingiz mumkin.

$GLOBALS['paid_calls'] = array();
$GLOBALS['cancelled_calls'] = array();
$GLOBALS['on_paid_throws'] = false;

function clickOnPaid(ClickOrder $order)
{
    if ($GLOBALS['on_paid_throws']) {
        throw new RuntimeException('baza yiqildi');
    }
    $GLOBALS['paid_calls'][] = $order->merchantTransId;
}

function clickOnCancelled(ClickOrder $order)
{
    $GLOBALS['cancelled_calls'][] = $order->merchantTransId;
}

// Namuna bazani xotirada ishlatamiz — fayl qoldirmaydi.
putenv('CLICK_DB_PATH=:memory:');

require_once __DIR__ . '/../click_prepare.php';
require_once __DIR__ . '/../click_complete.php';

clickSetConfig(array(
    'service_id'       => '12345',
    'merchant_id'      => '54321',
    'secret_key'       => 'test_secret_key',
    'merchant_user_id' => '67890',
));

define('T_SERVICE_ID', '12345');
define('T_SECRET_KEY', 'test_secret_key');
define('T_SIGN_TIME', '2026-07-17 12:00:00');
define('T_CLICK_TRANS_ID', '987654321');

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
        echo "  XATO {$name}";
        if ($info !== '') {
            echo " -> {$info}";
        }
        echo "\n";
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

// --- Yordamchilar ------------------------------------------------------------

/** Imzoni "qo'lda" hisoblaymiz — kutubxona kodidan mustaqil tekshirish uchun. */
function tSign()
{
    return md5(implode('', func_get_args()));
}

function tPrepareReq($merchantTransId, $amount, array $over = array())
{
    $data = array(
        'click_trans_id'    => T_CLICK_TRANS_ID,
        'service_id'        => T_SERVICE_ID,
        'merchant_trans_id' => $merchantTransId,
        'amount'            => $amount,
        'action'            => '0',
        'sign_time'         => T_SIGN_TIME,
        'sign_string'       => tSign(
            T_CLICK_TRANS_ID, T_SERVICE_ID, T_SECRET_KEY, $merchantTransId,
            $amount, '0', T_SIGN_TIME
        ),
    );

    return array_merge($data, $over);
}

function tCompleteReq($merchantTransId, $amount, $prepareId, array $over = array())
{
    $data = array(
        'click_trans_id'      => T_CLICK_TRANS_ID,
        'service_id'          => T_SERVICE_ID,
        'merchant_trans_id'   => $merchantTransId,
        'merchant_prepare_id' => (string)$prepareId,
        'amount'              => $amount,
        'action'              => '1',
        'error'               => '0',
        'sign_time'           => T_SIGN_TIME,
        'sign_string'         => tSign(
            T_CLICK_TRANS_ID, T_SERVICE_ID, T_SECRET_KEY, $merchantTransId,
            (string)$prepareId, $amount, '1', T_SIGN_TIME
        ),
    );

    return array_merge($data, $over);
}

// =============================================================================
//  PREPARE
// =============================================================================

echo "\nPREPARE\n";

$order = clickDemoCreateOrder('ORD1', 5000);
$res = clickHandlePrepare(tPrepareReq('ORD1', '5000'));
checkEq(CLICK_SUCCESS, $res['error'], 'prepare muvaffaqiyatli');
checkEq($order->id, $res['merchant_prepare_id'], 'prepare merchant_prepare_id qaytaradi');
checkEq('ORD1', $res['merchant_trans_id'], 'prepare merchant_trans_id qaytaradi');

clickDemoCreateOrder('ORD2', 5000);
$res = clickHandlePrepare(tPrepareReq('ORD2', '5000.00'));
checkEq(CLICK_SUCCESS, $res['error'], 'prepare "5000.00" kasrli summani qabul qiladi');

clickDemoCreateOrder('ORD3', 5000);
$res = clickHandlePrepare(tPrepareReq('ORD3', '5000', array('sign_string' => str_repeat('a', 32))));
checkEq(CLICK_SIGN_CHECK_FAILED, $res['error'], 'prepare soxta imzoni rad etadi');

clickDemoCreateOrder('ORD4', 5000);
$res = clickHandlePrepare(tPrepareReq('ORD4', '5000', array('service_id' => '99999')));
checkEq(CLICK_SIGN_CHECK_FAILED, $res['error'], 'prepare boshqa service_id ni rad etadi');

clickDemoCreateOrder('ORD5', 5000);
$req = tPrepareReq('ORD5', '5000');
unset($req['sign_time']);
$res = clickHandlePrepare($req);
checkEq(CLICK_BAD_REQUEST, $res['error'], 'prepare to\'liqmas so\'rovni rad etadi');

clickDemoCreateOrder('ORD6', 5000);
$res = clickHandlePrepare(tPrepareReq('ORD6', '100'));
checkEq(CLICK_INCORRECT_AMOUNT, $res['error'], 'prepare noto\'g\'ri summani rad etadi');

$res = clickHandlePrepare(tPrepareReq('YOQ404', '5000'));
checkEq(CLICK_USER_NOT_FOUND, $res['error'], 'prepare topilmagan buyurtma -5 qaytaradi');

$paidOrder = clickDemoCreateOrder('ORD7', 5000);
clickMarkPaid($paidOrder, T_CLICK_TRANS_ID);
$res = clickHandlePrepare(tPrepareReq('ORD7', '5000'));
checkEq(CLICK_ALREADY_PAID, $res['error'], 'prepare to\'langan buyurtmaga -4 qaytaradi');

$cancelledOrder = clickDemoCreateOrder('ORD8', 5000);
clickMarkCancelled($cancelledOrder, T_CLICK_TRANS_ID);
$res = clickHandlePrepare(tPrepareReq('ORD8', '5000'));
checkEq(CLICK_TRANSACTION_CANCELLED, $res['error'], 'prepare bekor qilinganga -9 qaytaradi');

// =============================================================================
//  COMPLETE
// =============================================================================

echo "\nCOMPLETE\n";

$GLOBALS['paid_calls'] = array();
$o = clickDemoCreateOrder('C1', 5000, 7, 'Kitob');
clickHandlePrepare(tPrepareReq('C1', '5000'));
$res = clickHandleComplete(tCompleteReq('C1', '5000', $o->id));
checkEq(CLICK_SUCCESS, $res['error'], 'complete muvaffaqiyatli');
checkEq($o->id, $res['merchant_confirm_id'], 'complete merchant_confirm_id qaytaradi');
checkEq(CLICK_STATUS_PAID, clickFindOrder('C1')->status, 'complete bazada "paid" qiladi');
checkEq(array('C1'), $GLOBALS['paid_calls'], 'complete clickOnPaid() ni chaqiradi');

$GLOBALS['paid_calls'] = array();
$o = clickDemoCreateOrder('C2', 5000);
clickHandlePrepare(tPrepareReq('C2', '5000'));
$first = clickHandleComplete(tCompleteReq('C2', '5000', $o->id));
$second = clickHandleComplete(tCompleteReq('C2', '5000', $o->id));
checkEq(CLICK_SUCCESS, $first['error'], 'takroriy: birinchi callback OK');
checkEq(CLICK_SUCCESS, $second['error'], 'takroriy: ikkinchi callback ham OK');
checkEq(array('C2'), $GLOBALS['paid_calls'], 'takroriy: clickOnPaid FAQAT BIR MARTA chaqiriladi');

$GLOBALS['paid_calls'] = array();
$o = clickDemoCreateOrder('C3', 5000);
clickHandlePrepare(tPrepareReq('C3', '5000'));
$res = clickHandleComplete(tCompleteReq('C3', '5000', $o->id, array('sign_string' => str_repeat('b', 32))));
checkEq(CLICK_SIGN_CHECK_FAILED, $res['error'], 'complete soxta imzoni rad etadi');
checkEq(CLICK_STATUS_PENDING, clickFindOrder('C3')->status, 'soxta imzo bazani o\'zgartirmaydi');
checkEq(array(), $GLOBALS['paid_calls'], 'soxta imzo clickOnPaid ni chaqirmaydi');

$o = clickDemoCreateOrder('C4', 5000);
$prepareSign = tPrepareReq('C4', '5000');
$res = clickHandleComplete(tCompleteReq('C4', '5000', $o->id, array(
    'sign_string' => $prepareSign['sign_string'],
)));
checkEq(CLICK_SIGN_CHECK_FAILED, $res['error'], 'prepare imzosi complete\'da ishlamaydi');

$o = clickDemoCreateOrder('C5', 5000);
clickHandlePrepare(tPrepareReq('C5', '5000'));
$res = clickHandleComplete(tCompleteReq('C5', '5000', $o->id + 777));
checkEq(CLICK_TRANSACTION_NOT_FOUND, $res['error'], 'complete noto\'g\'ri merchant_prepare_id ni rad etadi');

$o = clickDemoCreateOrder('C6', 5000);
clickHandlePrepare(tPrepareReq('C6', '5000'));
$res = clickHandleComplete(tCompleteReq('C6', '1', $o->id));
checkEq(CLICK_INCORRECT_AMOUNT, $res['error'], 'complete noto\'g\'ri summani rad etadi');
checkEq(CLICK_STATUS_PENDING, clickFindOrder('C6')->status, 'noto\'g\'ri summa bazani o\'zgartirmaydi');

$GLOBALS['paid_calls'] = array();
$GLOBALS['cancelled_calls'] = array();
$o = clickDemoCreateOrder('C7', 5000);
clickHandlePrepare(tPrepareReq('C7', '5000'));
$res = clickHandleComplete(tCompleteReq('C7', '5000', $o->id, array('error' => '-5017')));
checkEq(CLICK_TRANSACTION_CANCELLED, $res['error'], 'complete Click xatosida -9 qaytaradi');
checkEq(CLICK_STATUS_CANCELLED, clickFindOrder('C7')->status, 'Click xatosi bazada "cancelled" qiladi');
checkEq(array(), $GLOBALS['paid_calls'], 'bekor qilinganda clickOnPaid chaqirilmaydi');
checkEq(array('C7'), $GLOBALS['cancelled_calls'], 'bekor qilinganda clickOnCancelled chaqiriladi');

$res = clickHandleComplete(tCompleteReq('YOQ404', '5000', 1));
checkEq(CLICK_USER_NOT_FOUND, $res['error'], 'complete topilmagan buyurtma -5 qaytaradi');

// clickOnPaid xato bersa — Click'ga baribir SUCCESS ketadi
$GLOBALS['on_paid_throws'] = true;
$o = clickDemoCreateOrder('C8', 5000);
clickHandlePrepare(tPrepareReq('C8', '5000'));
$res = clickHandleComplete(tCompleteReq('C8', '5000', $o->id));
checkEq(CLICK_SUCCESS, $res['error'], 'clickOnPaid xatosi javobni buzmaydi');
checkEq(CLICK_STATUS_PAID, clickFindOrder('C8')->status, 'clickOnPaid xatosida to\'lov "paid" qoladi');
$GLOBALS['on_paid_throws'] = false;

// =============================================================================
//  Poyga himoyasi — eng muhim shart
// =============================================================================

echo "\nPOYGA HIMOYASI\n";

$o = clickDemoCreateOrder('R1', 5000);
check(clickMarkPaid($o, '111') === true, 'clickMarkPaid birinchi marta true qaytaradi');
check(clickMarkPaid($o, '111') === false, 'clickMarkPaid ikkinchi marta FALSE qaytaradi (mahsulot ikki marta berilmaydi)');

// =============================================================================
//  To'lov havolasi
// =============================================================================

echo "\nTO'LOV HAVOLASI\n";

$url = clickPaymentUrl('ORD1', 5000, 'https://a.uz/ok');
check(strpos($url, 'https://my.click.uz/services/pay?') === 0, 'havola to\'g\'ri manzildan boshlanadi');
check(strpos($url, 'service_id=12345') !== false, 'havolada service_id bor');
check(strpos($url, 'merchant_id=54321') !== false, 'havolada merchant_id bor');
check(strpos($url, 'amount=5000') !== false, 'havolada amount bor');
check(strpos($url, 'transaction_param=ORD1') !== false, 'havolada transaction_param bor');
check(strpos($url, 'merchant_user_id=67890') !== false, 'havolada merchant_user_id bor');
check(strpos($url, 'return_url=' . urlencode('https://a.uz/ok')) !== false, 'havolada return_url bor');
check(strpos($url, T_SECRET_KEY) === false, 'havolada secret_key YO\'Q (juda muhim)');

// =============================================================================

echo "\n";
echo "=====================================\n";
printf("  Jami: %d, xato: %d\n", $GLOBALS['tests_run'], $GLOBALS['tests_failed']);
echo "=====================================\n";

exit($GLOBALS['tests_failed'] > 0 ? 1 : 0);
