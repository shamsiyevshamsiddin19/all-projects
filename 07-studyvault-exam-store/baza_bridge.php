<?php
/**
 * KO'PRIK — BAZA_ Click to'lovlarini ESKI serverdan YANGI serverga (shamsiyev) uzatadi.
 *
 * Eski click_prepare.php / click_complete.php ichidagi
 *   if (isBazaClickMerchantTransId($merchantTransId)) { ... }
 * blokining O'RNIGA quyidagicha chaqiriladi (boshqa hech narsa o'zgarmaydi):
 *
 *   if (isBazaClickMerchantTransId($merchantTransId)) {
 *       require_once __DIR__ . '/baza_bridge.php';
 *       bazaBridgeHandle('prepare', $requestData);   // prepare faylida
 *       // bazaBridgeHandle('complete', $requestData); // complete faylida
 *   }
 *
 * Bu fayl clickPrepareSuccessResponse / clickPrepareErrorResponse (functions.php)
 * funksiyalarini ishlatadi — ular javob qaytarib exit() qiladi.
 */

// >>> YANGI SERVER MANZILI VA SIRI (ikkalasi ham .env dagi INTERNAL_SECRET bilan bir xil) <<<
if (!defined('BAZA_BRIDGE_URL'))    define('BAZA_BRIDGE_URL', 'http://141.147.156.65/click/baza');
if (!defined('BAZA_BRIDGE_SECRET')) define('BAZA_BRIDGE_SECRET', 'PUT_SAME_SECRET_AS_NEW_SERVER');

function bazaBridgePost(string $action, array $requestData): array
{
    $payload = json_encode([
        'secret'              => BAZA_BRIDGE_SECRET,
        'merchant_trans_id'   => (string)($requestData['merchant_trans_id'] ?? ''),
        'merchant_prepare_id' => (int)($requestData['merchant_prepare_id'] ?? 0),
        'amount'              => $requestData['amount'] ?? 0,
        'click_trans_id'      => (string)($requestData['click_trans_id'] ?? ''),
        'click_error'         => (int)($requestData['error'] ?? 0),
    ]);

    $ch = curl_init(BAZA_BRIDGE_URL . '/' . $action);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        CURLOPT_CONNECTTIMEOUT => 8,
        CURLOPT_TIMEOUT        => 20,
    ]);
    $res  = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($res === false || $code >= 500) {
        return ['error' => -1, 'prepare_id' => null]; // system error -> Click qayta uradi
    }
    $decoded = json_decode($res, true);
    if (!is_array($decoded) || !array_key_exists('error', $decoded)) {
        return ['error' => -1, 'prepare_id' => null];
    }
    return $decoded;
}

function bazaBridgeHandle(string $action, array $requestData): void
{
    $resp            = bazaBridgePost($action, $requestData);
    $error           = (int)$resp['error'];
    $clickTransId    = (string)($requestData['click_trans_id'] ?? '');
    $merchantTransId = (string)($requestData['merchant_trans_id'] ?? '');
    $prepareId       = isset($resp['prepare_id']) ? (int)$resp['prepare_id'] : null;

    if ($action === 'complete') {
        if ($error === 0) {
            clickCompleteSuccessResponse($clickTransId, $merchantTransId, (int)$prepareId);
        }
        clickCompleteErrorResponse($error, 'Bridge xato: ' . $error, $requestData, $prepareId);
    } else {
        if ($error === 0) {
            clickPrepareSuccessResponse($clickTransId, $merchantTransId, (int)$prepareId);
        }
        clickPrepareErrorResponse($error, 'Bridge xato: ' . $error, $requestData, $prepareId);
    }
}
