<?php
/**
 * Laravel loyihangizga ulash.
 *
 * 1) `uzum/php/` papkasini loyihaga ko'chiring, masalan `app/Uzum/`.
 *
 * 2) `uzum_orders.php` da o'z modelingizni ulang.
 *
 * 3) `routes/web.php` ga quyidagini qo'shing.
 */

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

require_once app_path('Uzum/uzum_methods.php');

// Sozlamani .env dan emas, Laravel config'idan bermoqchi bo'lsangiz:
//
//     uzumSetConfig([
//         'service_id'     => config('services.uzum.service_id'),
//         'webhook_login'  => config('services.uzum.webhook_login'),
//         'webhook_secret' => config('services.uzum.webhook_secret'),
//     ]);

// =============================================================================
//  DIQQAT — CSRF va auth
// =============================================================================
//
// Bu beshta manzil Uzum Bank SERVERIDAN keladi, foydalanuvchi brauzeridan
// emas. `web` middleware guruhiga QO'YMANG (CSRF talab qiladi) va `auth`
// middleware qo'ymang. Xavfsizlik HTTP Basic Auth orqali ta'minlanadi —
// uzumHandle*() funksiyalari ichida tekshiriladi.

function uzumLaravelRespond(array $pair)
{
    return response()->json($pair[1], $pair[0]);
}

Route::post('/uzum/check', function (Request $request) {
    return uzumLaravelRespond(uzumHandleCheck($request->json()->all(), $request->header('Authorization')));
})->withoutMiddleware(['web', 'auth']);

Route::post('/uzum/create', function (Request $request) {
    return uzumLaravelRespond(uzumHandleCreate($request->json()->all(), $request->header('Authorization')));
})->withoutMiddleware(['web', 'auth']);

Route::post('/uzum/confirm', function (Request $request) {
    return uzumLaravelRespond(uzumHandleConfirm($request->json()->all(), $request->header('Authorization')));
})->withoutMiddleware(['web', 'auth']);

Route::post('/uzum/reverse', function (Request $request) {
    return uzumLaravelRespond(uzumHandleReverse($request->json()->all(), $request->header('Authorization')));
})->withoutMiddleware(['web', 'auth']);

Route::post('/uzum/status', function (Request $request) {
    return uzumLaravelRespond(uzumHandleStatus($request->json()->all(), $request->header('Authorization')));
})->withoutMiddleware(['web', 'auth']);
