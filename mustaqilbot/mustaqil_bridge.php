<?php
/**
 * Talaba xizmatlari (mustaqil ish) boti KO'PRIGI — PHP 7.4 mos.
 *
 * Maqsad: BITTA Click xizmati (service_id) bilan bir nechta bot ishlashi.
 * Click har doim shu PHP hostingga (myxvest) callback yuboradi. Agar
 * merchant_trans_id "MUST" bilan boshlansa — bu mustaqil ish botiga tegishli,
 * shuning uchun so'rovni O'ZGARTIRMASDAN bot serveriga (shamsiyev, nginx)
 * uzatamiz va uning JSON javobini Click'ga aynan qaytaramiz.
 *
 * Bot o'z tomonida imzoni (md5 sign_string, bir xil secret_key) qayta
 * tekshiradi va o'z PostgreSQL bazasini yangilaydi. Ko'prik faqat "pochtachi".
 *
 * Ulanish: click_prepare.php va click_complete.php ichida, action
 * o'rnatilgandan keyin chaqiriladi:
 *     require_once $sharedFile('mustaqil_bridge.php');
 *     mustaqilBridgeMaybeForward($requestData, 'prepare');   // yoki 'complete'
 */

if (!defined('MUSTAQIL_BRIDGE_BASE_URL')) {
    // Shamsiyev serveri (nginx 80-port) → /mustaqil/click/... → 127.0.0.1:8092
    define('MUSTAQIL_BRIDGE_BASE_URL', 'http://141.147.156.65/mustaqil');
}

if (!defined('MUSTAQIL_BRIDGE_PREFIX')) {
    define('MUSTAQIL_BRIDGE_PREFIX', 'MUST');
}

if (!function_exists('mustaqilIsBridgeTxn')) {
    /**
     * merchant_trans_id mustaqil botga tegishlimi? ("MUST<payment_id>")
     */
    function mustaqilIsBridgeTxn($merchantTransId)
    {
        return strncmp((string)$merchantTransId, MUSTAQIL_BRIDGE_PREFIX, strlen(MUSTAQIL_BRIDGE_PREFIX)) === 0;
    }
}

if (!function_exists('mustaqilBridgeMaybeForward')) {
    /**
     * @param array  $requestData  Click'dan kelgan to'liq so'rov (action o'rnatilgan)
     * @param string $action       'prepare' yoki 'complete'
     *
     * Agar so'rov mustaqil botniki bo'lsa: uzatadi, javob beradi va exit qiladi.
     * Aks holda hech narsa qilmaydi — odatiy (talaba xizmatlari baza) oqim davom etadi.
     */
    function mustaqilBridgeMaybeForward(array $requestData, $action)
    {
        $mtid = isset($requestData['merchant_trans_id']) ? (string)$requestData['merchant_trans_id'] : '';

        // Bizniki emas — odatiy oqim davom etsin.
        if (!mustaqilIsBridgeTxn($mtid)) {
            return;
        }

        // Imzosiz GET (brauzer) — bu yerda hech narsa qilmaymiz. Click pay
        // URL'idagi return_url foydalanuvchini to'g'ridan bot Telegramiga oladi.
        if (empty($requestData['sign_string'])) {
            return;
        }

        $endpoint = ($action === 'complete') ? '/click/complete' : '/click/prepare';
        $url = rtrim(MUSTAQIL_BRIDGE_BASE_URL, '/') . $endpoint;

        $ch = curl_init($url);
        curl_setopt_array($ch, array(
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => http_build_query($requestData),
            CURLOPT_TIMEOUT        => 15,
            CURLOPT_CONNECTTIMEOUT => 6,
            CURLOPT_HTTPHEADER     => array('Content-Type: application/x-www-form-urlencoded'),
        ));

        $response = curl_exec($ch);
        $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlErr  = curl_error($ch);
        if (PHP_VERSION_ID < 80000) {
            curl_close($ch);
        }

        if (!headers_sent()) {
            header('Content-Type: application/json; charset=utf-8');
        }

        if ($response === false || $httpCode < 200 || $httpCode >= 300) {
            // Bot javob bermadi — Click qayta urinishi uchun -1 (System error).
            if (function_exists('logError')) {
                logError('Mustaqil bridge: bot javob bermadi', array(
                    'http_code'         => $httpCode,
                    'curl_error'        => $curlErr,
                    'merchant_trans_id' => $mtid,
                    'action'            => $action,
                ), 'click');
            }

            echo json_encode(array(
                'error'             => -1,
                'error_note'        => 'Bridge: mustaqil bot unreachable',
                'click_trans_id'    => isset($requestData['click_trans_id']) ? (int)$requestData['click_trans_id'] : 0,
                'merchant_trans_id' => $mtid,
            ));
            exit;
        }

        if (function_exists('logTolov')) {
            logTolov('Mustaqil bridge: javob uzatildi', array(
                'merchant_trans_id' => $mtid,
                'action'            => $action,
                'http_code'         => $httpCode,
            ));
        }

        // Bot JSON javobini Click'ga aynan qaytaramiz.
        echo $response;
        exit;
    }
}
