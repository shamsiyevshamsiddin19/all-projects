<?php
/**
 * Laravel loyihangizga ulash.
 *
 * 1) `payme/php/` papkasini loyihaga ko'chiring, masalan `app/Payme/`.
 *
 * 2) `payme_orders.php` da o'z modelingizni ulang.
 *
 * 3) `routes/web.php` ga quyidagini qo'shing.
 */

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

require_once app_path('Payme/payme_methods.php');
require_once app_path('Payme/payme_checkout.php');

// Sozlamani .env dan emas, Laravel config'idan bermoqchi bo'lsangiz:
//
//     paymeSetConfig([
//         'merchant_id' => config('services.payme.merchant_id'),
//         'secret_key'  => config('services.payme.secret_key'),
//     ]);

// =============================================================================
//  DIQQAT — CSRF va auth
// =============================================================================
//
// Payme'ning yagona endpointi SERVERIDAN keladi, foydalanuvchi brauzeridan
// emas. Payme sizning tizimingizga login qila olmaydi va CSRF token
// yubormaydi.
//
//  - `web` middleware guruhiga QO'YMANG (CSRF talab qiladi) yoki
//    `VerifyCsrfToken::$except` ga 'payme' ni qo'shing.
//  - `auth` middleware qo'ymang.
//
// Xavfsizlik HTTP Basic Auth orqali ta'minlanadi — paymeHandleRequest()
// ichida tekshiriladi.

Route::post('/payme', function (Request $request) {
    $body = json_decode($request->getContent(), true) ?: array();
    $auth = $request->header('Authorization');
    return response()->json(paymeHandleRequest($body, $auth));
})->withoutMiddleware(['web', 'auth']);

// =============================================================================
//  To'lov havolasi
// =============================================================================

Route::get('/checkout/{order}', function ($orderId) {
    $order = \App\Models\Order::findOrFail($orderId);

    return redirect(paymeCheckoutUrl(
        array('order_id' => $order->id),
        paymeSomToTiyin($order->price)
    ));
})->middleware('auth');
