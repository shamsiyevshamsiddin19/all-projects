<?php
/**
 * Uzum Bank sozlamalari — hammasi .env dan o'qiladi.
 *
 * Qaysi qiymat kerakligi `.env.example` da yozilgan.
 * Bu faylga tegishingiz shart emas.
 *
 * .env fayli quyidagi joylardan qidiriladi (birinchi topilgani olinadi):
 *   1. shu papka                    (uzum/php/.env)
 *   2. bir daraja yuqori            (loyihangiz ildizi)
 *   3. ikki daraja yuqori
 */

if (!function_exists('uzumEnvLoad')) {
    function uzumEnvLoad()
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

if (!function_exists('uzumEnv')) {
    function uzumEnv($name, $default = null)
    {
        $value = getenv($name);
        if ($value !== false && $value !== '') {
            return $value;
        }

        if (isset($_SERVER[$name]) && $_SERVER[$name] !== '') {
            return $_SERVER[$name];
        }

        $vars = uzumEnvLoad();
        if (isset($vars[$name]) && $vars[$name] !== '') {
            return $vars[$name];
        }

        return $default;
    }
}

if (!function_exists('uzumEnvRequire')) {
    function uzumEnvRequire($name)
    {
        $value = uzumEnv($name);

        if ($value === null || trim((string)$value) === '') {
            throw new RuntimeException(
                "{$name} .env da yo'q. `.env.example` dan `.env` yasang va "
                . "qiymatlarni Uzum Bank kabinetidan (merchants.uzumbank.uz) to'ldiring."
            );
        }

        return trim((string)$value);
    }
}

if (!function_exists('uzumConfigStore')) {
    /**
     * Ichki: sozlamani saqlab turadi (bir marta o'qish uchun kesh).
     *
     * @param array|null|false $config false -> o'qish, array -> yozish,
     *                                 null  -> tozalash (testlar uchun)
     */
    function uzumConfigStore($config = false)
    {
        static $stored = null;

        if ($config !== false) {
            $stored = $config;
        }

        return $stored;
    }
}

if (!function_exists('uzumResetConfig')) {
    function uzumResetConfig()
    {
        uzumConfigStore(null);
    }
}

if (!function_exists('uzumConfig')) {
    /**
     * Sozlamani oladi.
     *
     * Kalitlar: service_id, webhook_login, webhook_secret
     */
    function uzumConfig($key)
    {
        $config = uzumConfigStore();

        if ($config === null) {
            $config = array(
                'service_id'     => (int)uzumEnvRequire('UZUM_SERVICE_ID'),
                'webhook_login'  => uzumEnvRequire('UZUM_WEBHOOK_LOGIN'),
                'webhook_secret' => uzumEnvRequire('UZUM_WEBHOOK_SECRET'),
            );
            uzumConfigStore($config);
        }

        if (!array_key_exists($key, $config)) {
            throw new RuntimeException("Uzum Bank: noma'lum sozlama '{$key}'");
        }

        return $config[$key];
    }
}

if (!function_exists('uzumSetConfig')) {
    /**
     * Sozlamani qo'lda o'rnatish — .env ishlatmasangiz yoki testlarda.
     */
    function uzumSetConfig(array $values)
    {
        uzumConfigStore($values);
    }
}
