<?php
/**
 * Payme'ning Basic Auth so'rovini tekshirish.
 *
 * Click'dan farqli o'laroq, Payme har bir so'rovni imzo bilan emas, oddiy
 * HTTP Basic Authentication bilan tasdiqlaydi:
 *
 *     Authorization: Basic base64("Paycom:MAXFIY_KALIT")
 *
 * Login har doim "Paycom" (yoki kabinetda o'zgartirilgan bo'lsa, shu qiymat).
 * Parol — kabinetdagi kassa uchun berilgan maxfiy kalit.
 *
 * Bu faylga tegishingiz shart emas.
 */

require_once __DIR__ . '/payme_config.php';

if (!function_exists('paymeCheckAuth')) {
    /**
     * `Authorization` sarlavhasini tekshiradi.
     *
     * Login va parol vaqt bo'yicha barqaror (timing-safe) solishtiriladi —
     * hash_equals() shu uchun ishlatiladi.
     */
    function paymeCheckAuth($authorizationHeader)
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

        $expectedLogin = (string)paymeConfig('merchant_login');
        $expectedPassword = (string)paymeConfig('secret_key');

        return hash_equals($expectedLogin, $login) && hash_equals($expectedPassword, $password);
    }
}

if (!function_exists('paymeAuthorizationHeader')) {
    /**
     * Turli server konfiguratsiyalarida `Authorization` sarlavhasini topadi.
     *
     * Ba'zi hosting'larda Apache uni $_SERVER['HTTP_AUTHORIZATION'] ga
     * qo'ymaydi (mod_php cheklovi) — shuning uchun bir necha manbadan
     * qidiramiz.
     */
    function paymeAuthorizationHeader()
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
