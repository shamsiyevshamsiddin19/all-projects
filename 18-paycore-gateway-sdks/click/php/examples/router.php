<?php
/**
 * Front-controller (bitta kirish nuqtasi) bo'lgan loyihaga ulash.
 *
 * Loyihangizda hamma so'rov index.php dan o'tsa (o'z routeringiz, Slim,
 * CodeIgniter va h.k.), click_prepare.php ni to'g'ridan-to'g'ri ochib qo'yish
 * shart emas — shu usulda chaqirasiz.
 *
 * Sinash:
 *     php -S localhost:8000 examples/router.php
 *     curl -X POST "http://localhost:8000/click/prepare" -d "..."
 */

require_once __DIR__ . '/../click_prepare.php';
require_once __DIR__ . '/../click_complete.php';

// Bu fayllarni `require` qilganingizda ular o'zi hech narsa chiqarmaydi —
// faqat funksiyalarni e'lon qiladi. Javobni siz o'zingiz qaytarasiz.

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$path = rtrim($path, '/');

switch ($path) {
    case '/click/prepare':
        clickSendJson(clickHandlePrepare(clickRequestData()));
        break;

    case '/click/complete':
        clickSendJson(clickHandleComplete(clickRequestData()));
        break;

    default:
        http_response_code(404);
        echo 'Not found';
}
