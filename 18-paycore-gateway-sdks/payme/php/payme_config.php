<?php
/**
 * Payme sozlamalari — hammasi .env dan o'qiladi.
 *
 * Qaysi qiymat kerakligi `.env.example` da yozilgan.
 * Bu faylga tegishingiz shart emas.
 *
 * .env fayli quyidagi joylardan qidiriladi (birinchi topilgani olinadi):
 *   1. shu papka                    (payme/php/.env)
 *   2. bir daraja yuqori            (loyihangiz ildizi)
 *   3. ikki daraja yuqori
 */

if (!function_exists('paymeEnvLoad')) {
    function paymeEnvLoad()
    {
        static $vars = null;

        if ($vars !== null) {
            return $vars;
        }

        $vars = array();

        $candidates = array(
            __DIR__ . '/.env',
            dirname(__DIR__) . '/.env',
            dirname(dirname(__DIR__)) . '/.env',
        );

        $path = null;
        foreach ($candidates as $candidate) {
            if (is_file($candidate) && is_readable($candidate)) {
                $path = $candidate;
                break;
            }
        }

        if ($path === null) {
            return $vars;
        }

        $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        if ($lines === false) {
            return $vars;
        }

        foreach ($lines as $line) {
            $line = trim($line);

            if ($line === '' || strpos($line, '#') === 0) {
                continue;
            }

            $pos = strpos($line, '=');
            if ($pos === false) {
                continue;
            }

            $key = trim(substr($line, 0, $pos));
            $value = trim(substr($line, $pos + 1));

            $len = strlen($value);
            if ($len >= 2) {
                $first = $value[0];
                $last = $value[$len - 1];
                if (($first === '"' && $last === '"') || ($first === "'" && $last === "'")) {
                    $value = substr($value, 1, -1);
                }
            }

            if ($key !== '') {
                $vars[$key] = $value;
            }
        }

        return $vars;
    }
}

if (!function_exists('paymeEnv')) {
    function paymeEnv($name, $default = null)
    {
        $value = getenv($name);
        if ($value !== false && $value !== '') {
            return $value;
        }

        if (isset($_SERVER[$name]) && $_SERVER[$name] !== '') {
            return $_SERVER[$name];
        }

        $vars = paymeEnvLoad();
        if (isset($vars[$name]) && $vars[$name] !== '') {
            return $vars[$name];
        }

        return $default;
    }
}

if (!function_exists('paymeEnvRequire')) {
    function paymeEnvRequire($name)
    {
        $value = paymeEnv($name);

        if ($value === null || trim((string)$value) === '') {
            throw new RuntimeException(
                "{$name} .env da yo'q. `.env.example` dan `.env` yasang va "
                . "qiymatlarni Payme kabinetidan (business.payme.uz) to'ldiring."
            );
        }

        return trim((string)$value);
    }
}

if (!function_exists('paymeConfigStore')) {
    /**
     * Ichki: sozlamani saqlab turadi (bir marta o'qish uchun kesh).
     *
     * @param array|null|false $config false -> o'qish, array -> yozish,
     *                                 null  -> tozalash (testlar uchun)
     */
    function paymeConfigStore($config = false)
    {
        static $stored = null;

        if ($config !== false) {
            $stored = $config;
        }

        return $stored;
    }
}

if (!function_exists('paymeResetConfig')) {
    function paymeResetConfig()
    {
        paymeConfigStore(null);
    }
}

if (!function_exists('paymeConfig')) {
    /**
     * Sozlamani oladi.
     *
     * Kalitlar: merchant_id, secret_key, merchant_login, checkout_base_url
     */
    function paymeConfig($key)
    {
        $config = paymeConfigStore();

        if ($config === null) {
            $config = array(
                'merchant_id'        => paymeEnvRequire('PAYME_MERCHANT_ID'),
                'secret_key'         => paymeEnvRequire('PAYME_SECRET_KEY'),
                'merchant_login'     => paymeEnv('PAYME_MERCHANT_LOGIN', 'Paycom'),
                'checkout_base_url'  => paymeEnv('PAYME_CHECKOUT_BASE_URL', 'https://checkout.paycom.uz'),
            );
            paymeConfigStore($config);
        }

        if (!array_key_exists($key, $config)) {
            throw new RuntimeException("Payme: noma'lum sozlama '{$key}'");
        }

        return $config[$key];
    }
}

if (!function_exists('paymeSetConfig')) {
    /**
     * Sozlamani qo'lda o'rnatish — .env ishlatmasangiz yoki testlarda.
     */
    function paymeSetConfig(array $values)
    {
        $defaults = array(
            'merchant_login'    => 'Paycom',
            'checkout_base_url' => 'https://checkout.paycom.uz',
        );

        paymeConfigStore(array_merge($defaults, $values));
    }
}
