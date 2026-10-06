<?php
/**
 * Laravel loyihangizga ulash.
 *
 * 1) `click/php/` papkasini loyihaga ko'chiring, masalan `app/Click/`.
 *
 * 2) `click_orders.php` da o'z modelingizni ulang (fayl oxiridagi Laravel
 *    namunasiga qarang).
 *
 * 3) `routes/web.php` ga quyidagini qo'shing.
 */

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

require_once app_path('Click/click_prepare.php');
require_once app_path('Click/click_complete.php');

// Sozlamani .env dan emas, Laravel config'idan bermoqchi bo'lsangiz:
//
//     clickSetConfig([
//         'service_id'       => config('services.click.service_id'),
//         'merchant_id'      => config('services.click.merchant_id'),
//         'secret_key'       => config('services.click.secret_key'),
//         'merchant_user_id' => config('services.click.merchant_user_id'),
//     ]);
//
// Aks holda click_config.php loyihangizning `.env` faylini o'zi topib o'qiydi.

// =============================================================================
//  DIQQAT — CSRF va auth
// =============================================================================
//
// Bu ikkala manzil Click SERVERIDAN keladi, foydalanuvchi brauzeridan emas.
// Click sizning tizimingizga login qila olmaydi va CSRF token yubormaydi.
//
//  - `web` middleware guruhiga QO'YMANG (u CSRF talab qiladi) yoki
//    `VerifyCsrfToken::$except` ga 'click/*' ni qo'shing.
//  - `auth` middleware qo'ymang.
//
// Xavfsizlik imzo (sign_string) orqali ta'minlanadi — clickHandlePrepare()
// va clickHandleComplete() ichida tekshiriladi.

Route::post('/click/prepare', function (Request $request) {
    return response()->json(clickHandlePrepare($request->all()));
})->withoutMiddleware(['web', 'auth']);

Route::post('/click/complete', function (Request $request) {
    return response()->json(clickHandleComplete($request->all()));
})->withoutMiddleware(['web', 'auth']);

// =============================================================================
//  To'lov havolasi
// =============================================================================

Route::get('/checkout/{order}', function ($orderId) {
    $order = \App\Models\Order::findOrFail($orderId);

    // Buyurtmaga unikal merchant_trans_id beramiz (bir marta)
    if (!$order->merchant_trans_id) {
        $order->merchant_trans_id = 'ORD' . $order->id;
        $order->save();
    }

    return redirect(clickPaymentUrl($order->merchant_trans_id, $order->price));
})->middleware('auth');
