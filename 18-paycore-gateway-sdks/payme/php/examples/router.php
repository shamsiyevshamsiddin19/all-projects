<?php
/**
 * Front-controller (bitta kirish nuqtasi) bo'lgan loyihaga ulash.
 *
 * Sinash:
 *     php -S localhost:8000 examples/router.php
 *     curl -X POST "http://localhost:8000/payme" -H "Authorization: Basic ..." -d "..."
 */

require_once __DIR__ . '/../payme_methods.php';
require_once __DIR__ . '/../payme_utils.php';

// `payme_methods.php` ni `require` qilganingizda u o'zi hech narsa
// chiqarmaydi — faqat funksiyalarni e'lon qiladi. Javobni siz o'zingiz
// qaytarasiz.

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$path = rtrim($path, '/');

switch ($path) {
    case '/payme':
        $response = paymeHandleRequest(paymeRequestData(), paymeAuthorizationHeader());
        paymeSendJson($response);
        break;

    default:
        http_response_code(404);
        echo 'Not found';
}
