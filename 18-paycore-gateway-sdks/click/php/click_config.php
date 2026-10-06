<?php
/**
 * Click sozlamalari — hammasi .env dan o'qiladi.
 *
 * Qaysi qiymat kerakligi `.env.example` da yozilgan.
 * Bu faylga tegishingiz shart emas.
 *
 * .env fayli quyidagi joylardan qidiriladi (birinchi topilgani olinadi):
 *   1. shu papka                    (click/php/.env)
 *   2. bir daraja yuqori            (loyihangiz ildizi)
 *   3. ikki daraja yuqori
 *
 * Hosting'ingiz haqiqiy muhit o'zgaruvchilarini bersa (getenv), ular
 * .env fayldan ustun turadi.
 */

if (!function_exists('clickEnvLoad')) {
    /**
     * .env faylini o'qiydi (bir marta) va massiv qilib qaytaradi.
     * Composer yoki tashqi kutubxona kerak emas.
     */
    function clickEnvLoad()
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

            // Izoh yoki bo'sh qator
            if ($line === '' || strpos($line, '#') === 0) {
                continue;
            }

            $pos = strpos($line, '=');
            if ($pos === false) {
                continue;
            }

            $key = trim(substr($line, 0, $pos));
            $value = trim(substr($line, $pos + 1));

            // "qiymat" yoki 'qiymat' -> qiymat
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

if (!function_exists('clickEnv')) {
    /**
     * Muhit o'zgaruvchisini oladi: getenv -> $_SERVER -> .env fayl -> default.
     */
    function clickEnv($name, $default = null)
    {
        $value = getenv($name);
        if ($value !== false && $value !== '') {
            return $value;
        }

        if (isset($_SERVER[$name]) && $_SERVER[$name] !== '') {
            return $_SERVER[$name];
        }

        $vars = clickEnvLoad();
        if (isset($vars[$name]) && $vars[$name] !== '') {
            return $vars[$name];
        }

        return $default;
    }
}

if (!function_exists('clickConfig')) {
    /**
     * Sozlamani oladi.
     *
     * Kalitlar: service_id, merchant_id, secret_key, merchant_user_id,
     *           pay_base_url, return_url
     *
     * @throws RuntimeException majburiy qiymat .env da bo'lmasa
     */
    function clickConfig($key)
    {
        $config = clickConfigStore();

        if ($config === null) {
            $config = array(
                'service_id'       => clickEnvRequire('CLICK_SERVICE_ID'),
                'merchant_id'      => clickEnvRequire('CLICK_MERCHANT_ID'),
                'secret_key'       => clickEnvRequire('CLICK_SECRET_KEY'),
                'merchant_user_id' => clickEnvRequire('CLICK_MERCHANT_USER_ID'),
                'pay_base_url'     => clickEnv('CLICK_PAY_BASE_URL', 'https://my.click.uz/services/pay'),
                'return_url'       => clickEnv('CLICK_RETURN_URL', ''),
            );
            clickConfigStore($config);
        }

        if (!array_key_exists($key, $config)) {
            throw new RuntimeException("Click: noma'lum sozlama '{$key}'");
        }

        return $config[$key];
    }
}

if (!function_exists('clickEnvRequire')) {
    function clickEnvRequire($name)
    {
        $value = clickEnv($name);

        if ($value === null || trim((string)$value) === '') {
            throw new RuntimeException(
                "{$name} .env da yo'q. `.env.example` dan `.env` yasang va "
                . "qiymatlarni Click kabinetidan (merchant.click.uz) to'ldiring."
            );
        }

        return trim((string)$value);
    }
}

if (!function_exists('clickSetConfig')) {
    /**
     * Sozlamani qo'lda o'rnatish — .env ishlatmasangiz yoki testlarda.
     *
     * Namuna (Laravel/Symfony config'idan berish):
     *     clickSetConfig([
     *         'service_id'       => config('click.service_id'),
     *         'merchant_id'      => config('click.merchant_id'),
     *         'secret_key'       => config('click.secret_key'),
     *         'merchant_user_id' => config('click.merchant_user_id'),
     *     ]);
     */
    function clickSetConfig(array $values)
    {
        $defaults = array(
            'pay_base_url' => 'https://my.click.uz/services/pay',
            'return_url'   => '',
        );

        clickConfigStore(array_merge($defaults, $values));
    }
}

if (!function_exists('clickConfigStore')) {
    /**
     * Ichki: sozlamani saqlab turadi (bir marta o'qish uchun kesh).
     *
     * @param array|null|false $config false -> o'qish, array -> yozish,
     *                                 null  -> tozalash (testlar uchun)
     */
    function clickConfigStore($config = false)
    {
        static $stored = null;

        if ($config !== false) {
            $stored = $config;
        }

        return $stored;
    }
}

if (!function_exists('clickResetConfig')) {
    /**
     * Sozlama keshini tozalaydi — testlarda .env yoki clickSetConfig()
     * o'zgarganda kerak.
     */
    function clickResetConfig()
    {
        clickConfigStore(null);
    }
}

if (!function_exists('clickFormatAmount')) {
    /**
     * Summani to'lov havolasi uchun chiqaradi (5000.00 -> "5000").
     *
     * Bu faqat HAVOLA uchun — imzo hisoblashda Click yuborgan xom satr
     * ishlatiladi (click_signature.php izohiga qarang).
     */
    function clickFormatAmount($amount)
    {
        $value = (float)$amount;

        if (abs($value - round($value)) < 0.00001) {
            return (string)(int)round($value);
        }

        return number_format($value, 2, '.', '');
    }
}

if (!function_exists('clickPaymentUrl')) {
    /**
     * Foydalanuvchi yuboriladigan Click to'lov havolasini quradi.
     *
     * `$merchantTransId` — sizning to'lov identifikatoringiz (masalan "ORD42").
     * Click uni prepare/complete so'rovlarida aynan shu holda qaytarib yuboradi.
     *
     * Namuna:
     *     $url = clickPaymentUrl('ORD42', 5000);
     *     header('Location: ' . $url);
     */
    function clickPaymentUrl($merchantTransId, $amount, $returnUrl = null)
    {
        $params = array(
            'service_id'        => clickConfig('service_id'),
            'merchant_id'       => clickConfig('merchant_id'),
            'amount'            => clickFormatAmount($amount),
            'transaction_param' => (string)$merchantTransId,
            'merchant_user_id'  => clickConfig('merchant_user_id'),
        );

        $finalReturnUrl = $returnUrl !== null ? $returnUrl : clickConfig('return_url');
        if ($finalReturnUrl !== '') {
            $params['return_url'] = $finalReturnUrl;
        }

        return clickConfig('pay_base_url') . '?' . http_build_query($params);
    }
}
