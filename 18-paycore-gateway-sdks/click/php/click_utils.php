<?php
/**
 * Kichik yordamchilar. Bu faylga tegishingiz shart emas.
 */

// Summalarni solishtirishda ruxsat etilgan farq (tiyin yaxlitlashlari uchun).
define('CLICK_AMOUNT_TOLERANCE', 0.01);

if (!function_exists('clickRequestData')) {
    /**
     * Click so'rovidan maydonlarni oladi.
     *
     * Click odatda form-encoded POST yuboradi, lekin sozlamaga qarab JSON
     * ham kelishi mumkin. Oxirida query parametrlariga tushamiz.
     */
    function clickRequestData()
    {
        if (!empty($_POST)) {
            return $_POST;
        }

        $raw = file_get_contents('php://input');
        if ($raw !== false && $raw !== '') {
            $decoded = json_decode($raw, true);
            if (is_array($decoded) && !empty($decoded)) {
                return $decoded;
            }
        }

        if (!empty($_REQUEST)) {
            return $_REQUEST;
        }

        return array();
    }
}

if (!function_exists('clickMissingFields')) {
    /**
     * So'rovda yetishmayotgan majburiy maydonlar ro'yxati.
     */
    function clickMissingFields(array $data, array $required)
    {
        $missing = array();

        foreach ($required as $field) {
            if (!array_key_exists($field, $data) || $data[$field] === '' || $data[$field] === null) {
                $missing[] = $field;
            }
        }

        return $missing;
    }
}

if (!function_exists('clickAsInt')) {
    /**
     * Xavfsiz int'ga o'girish — bo'lmasa 0.
     */
    function clickAsInt($value)
    {
        if (is_int($value)) {
            return $value;
        }

        $value = trim((string)$value);

        if ($value === '' || !is_numeric($value)) {
            return 0;
        }

        return (int)$value;
    }
}

if (!function_exists('clickAmountsMatch')) {
    /**
     * Click yuborgan summa bazadagiga mos keladimi?
     *
     * Click "5000", "5000.00" yoki "5000.0" yuborishi mumkin — hammasi bir xil
     * summa. Shuning uchun kichik farq bilan solishtiramiz.
     */
    function clickAmountsMatch($received, $expected)
    {
        if (!is_numeric($received)) {
            return false;
        }

        return abs((float)$received - (float)$expected) < CLICK_AMOUNT_TOLERANCE;
    }
}

if (!function_exists('clickSendJson')) {
    /**
     * Javobni Click'ga JSON qilib yuboradi.
     */
    function clickSendJson(array $response)
    {
        if (!headers_sent()) {
            header('Content-Type: application/json; charset=utf-8');
        }

        echo json_encode($response, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }
}

if (!function_exists('clickIsDirectRequest')) {
    /**
     * Shu fayl web-server orqali TO'G'RIDAN-TO'G'RI chaqirilganmi?
     *
     * click_prepare.php / click_complete.php ikki xil ishlatiladi:
     *
     *   1. Oddiy hosting'da — Click to'g'ridan-to'g'ri
     *      https://domen.uz/click_prepare.php ga uradi. Shunda fayl o'zi
     *      javob berishi kerak.
     *
     *   2. Framework'da (Laravel, Slim, Symfony...) — fayl `require` qilinadi
     *      va clickHandlePrepare() qo'lda chaqiriladi. Bunda fayl o'zi hech
     *      narsa chiqarmasligi kerak.
     *
     * Shu funksiya ikkalasini ajratadi.
     */
    function clickIsDirectRequest($file)
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

if (!function_exists('clickLog')) {
    /**
     * Click hodisalarini loglaydi.
     *
     * Odatiy holda PHP'ning error_log() iga yozadi. Loyihangizda o'z
     * loggeringiz bo'lsa, shu funksiyani o'zgartiring — masalan:
     *
     *     function clickLog($level, $message, array $context = array())
     *     {
     *         logYozish($level, $message, $context, 'click');
     *     }
     *
     * @param string $level 'info' | 'warning' | 'error'
     */
    function clickLog($level, $message, array $context = array())
    {
        $line = '[click] [' . strtoupper($level) . '] ' . $message;

        if (!empty($context)) {
            $line .= ' ' . json_encode($context, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        }

        error_log($line);
    }
}
