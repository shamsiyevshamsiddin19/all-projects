<?php
/**
 * Front-controller (bitta kirish nuqtasi) bo'lgan loyihaga ulash.
 *
 * Sinash:
 *     php -S localhost:8000 examples/router.php
 *     curl -X POST "http://localhost:8000/uzum/check" \
 *       -H "Authorization: Basic $(echo -n 'login:parol' | base64)" \
 *       -H "Content-Type: application/json" \
 *       -d '{"serviceId":101202,"timestamp":1,"params":{"account":"42"}}'
 *
 * Kabinetga yoziladigan bazaviy manzil:
 *     https://sizning-domen.uz/uzum
 * (Uzum Bank o'zi /check, /create va h.k. qo'shib chaqiradi.)
 */

require_once __DIR__ . '/../uzum_methods.php';

function uzumRequestJson()
{
    $raw = file_get_contents('php://input');
    $data = json_decode($raw, true);
    return is_array($data) ? $data : array();
}

function uzumSendJson($httpStatus, array $body)
{
    http_response_code($httpStatus);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
}

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$path = rtrim($path, '/');
$auth = uzumAuthorizationHeader();
$data = uzumRequestJson();

switch ($path) {
    case '/uzum/check':
        list($status, $body) = uzumHandleCheck($data, $auth);
        uzumSendJson($status, $body);
        break;

    case '/uzum/create':
        list($status, $body) = uzumHandleCreate($data, $auth);
        uzumSendJson($status, $body);
        break;

    case '/uzum/confirm':
        list($status, $body) = uzumHandleConfirm($data, $auth);
        uzumSendJson($status, $body);
        break;

    case '/uzum/reverse':
        list($status, $body) = uzumHandleReverse($data, $auth);
        uzumSendJson($status, $body);
        break;

    case '/uzum/status':
        list($status, $body) = uzumHandleStatus($data, $auth);
        uzumSendJson($status, $body);
        break;

    default:
        http_response_code(404);
        echo 'Not found';
}
