<?php
/**
 * Uzum Bank'ning Basic Auth so'rovini tekshirish.
 *
 * Payme'ga o'xshab, Uzum Bank ham har bir webhook so'rovini oddiy HTTP Basic
 * Authentication bilan tasdiqlaydi:
 *
 *     Authorization: Basic base64("login:parol")
 *
 * Farqi: Payme'da login doim "Paycom", Uzum'da esa LOGIN HAM, PAROL HAM siz
 * kabinetda o'zingiz belgilaysiz (ikkalasi ham `.env` da).
 *
 * Bu faylga tegishingiz shart emas.
 */

require_once __DIR__ . '/uzum_config.php';

if (!function_exists('uzumCheckAuth')) {
    /**
     * `Authorization` sarlavhasini tekshiradi.
     *
     * Login va parol vaqt bo'yicha barqaror (timing-safe) solishtiriladi.
     */
    function uzumCheckAuth($authorizationHeader)
    {
        if (empty($authorizationHeader) || strpos($authorizationHeader, 'Basic ') !== 0) {
            return false;
        }

        $token = trim(substr($authorizationHeader, strlen('Basic ')));
        $decoded = base64_decode($token, true);

        if ($decoded === false) {
            return false;
        }

        $pos = strpos($decoded, ':');
        if ($pos === false) {
            return false;
        }

        $login = substr($decoded, 0, $pos);
        $password = substr($decoded, $pos + 1);

        if ($password === '') {
            return false;
        }

        $expectedLogin = (string)uzumConfig('webhook_login');
        $expectedPassword = (string)uzumConfig('webhook_secret');

        return hash_equals($expectedLogin, $login) && hash_equals($expectedPassword, $password);
    }
}

if (!function_exists('uzumAuthorizationHeader')) {
    /**
     * Turli server konfiguratsiyalarida `Authorization` sarlavhasini topadi.
     *
     * Ba'zi hosting'larda Apache uni $_SERVER['HTTP_AUTHORIZATION'] ga
     * qo'ymaydi (mod_php cheklovi) — shuning uchun bir necha manbadan
     * qidiramiz.
     */
    function uzumAuthorizationHeader()
    {
        if (!empty($_SERVER['HTTP_AUTHORIZATION'])) {
            return $_SERVER['HTTP_AUTHORIZATION'];
        }

        if (!empty($_SERVER['REDIRECT_HTTP_AUTHORIZATION'])) {
            return $_SERVER['REDIRECT_HTTP_AUTHORIZATION'];
        }

        if (function_exists('apache_request_headers')) {
            $headers = apache_request_headers();
            if (isset($headers['Authorization'])) {
                return $headers['Authorization'];
            }
        }

        return null;
    }
}
