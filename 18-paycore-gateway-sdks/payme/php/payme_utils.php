<?php
/**
 * Kichik yordamchilar: so'rovni o'qish, javob yuborish, endpoint aniqlash.
 *
 * Bu faylga tegishingiz shart emas.
 */

if (!function_exists('paymeRequestData')) {
    /**
     * Payme so'rovining tanasini (body) massiv qilib o'qiydi.
     *
     * Payme har doim `application/json` POST yuboradi.
     */
    function paymeRequestData()
    {
        $raw = file_get_contents('php://input');
        if ($raw === false || $raw === '') {
            return array();
        }

        $decoded = json_decode($raw, true);
        return is_array($decoded) ? $decoded : array();
    }
}

if (!function_exists('paymeSendJson')) {
    /** Javobni Payme'ga JSON qilib yuboradi. Har doim HTTP 200 bilan. */
    function paymeSendJson(array $response)
    {
        if (!headers_sent()) {
            header('Content-Type: application/json; charset=utf-8');
        }
        http_response_code(200);
        echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }
}

if (!function_exists('paymeIsDirectRequest')) {
    /**
     * Shu fayl web-server orqali TO'G'RIDAN-TO'G'RI chaqirilganmi?
     *
     * payme.php ikki xil ishlatiladi:
     *   1. Oddiy hosting'da — Payme to'g'ridan-to'g'ri
     *      https://domen.uz/payme.php ga uradi.
     *   2. Framework'da — fayl `require` qilinadi va paymeHandleRequest()
     *      qo'lda chaqiriladi.
     */
    function paymeIsDirectRequest($file)
    {
        if (PHP_SAPI === 'cli') {
            return false;
        }

        $script = isset($_SERVER['SCRIPT_FILENAME']) ? $_SERVER['SCRIPT_FILENAME'] : '';
        if ($script === '') {
            return false;
        }

        $scriptPath = realpath($script);
        $filePath = realpath($file);

        return $scriptPath !== false && $filePath !== false && $scriptPath === $filePath;
    }
}
