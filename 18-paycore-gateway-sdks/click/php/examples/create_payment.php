<?php
/**
 * To'lov havolasini yasash — oddiy PHP namunasi.
 *
 * Foydalanuvchi "sotib olaman" bosganda shu kod ishlaydi.
 *
 * Sinash (loyiha ildizidan):
 *     php examples/create_payment.php
 */

require_once __DIR__ . '/../click_config.php';
require_once __DIR__ . '/../click_orders.php';

// --- 1. Buyurtma yaratamiz ---------------------------------------------------
//
// O'z tizimingizda buyurtma allaqachon bazangizda bo'ladi — siz faqat unga
// unikal `merchant_trans_id` berasiz:
//
//     $merchantTransId = 'ORD' . $order['id'];
//     $stmt = db()->prepare('UPDATE orders SET merchant_trans_id = ? WHERE id = ?');
//     $stmt->execute(array($merchantTransId, $order['id']));

$order = clickDemoCreateOrder(
    'ORD' . time(),   // unikal bo'lishi SHART
    5000,             // summa, so'mda
    7,                // user_id
    'Kitob'           // mahsulot
);

// --- 2. To'lov havolasini yasaymiz -------------------------------------------

$url = clickPaymentUrl($order->merchantTransId, $order->amount);

// Ixtiyoriy: qaytish manzilini shu yerda ham berish mumkin
// $url = clickPaymentUrl($order->merchantTransId, $order->amount, 'https://domen.uz/rahmat');

// --- 3. Foydalanuvchini yuboramiz --------------------------------------------

if (PHP_SAPI === 'cli') {
    echo "Buyurtma:  {$order->merchantTransId}\n";
    echo "Summa:     {$order->amount} so'm\n";
    echo "Havola:    {$url}\n";
} else {
    // Web'da:
    header('Location: ' . $url);
    exit;

    // Telegram botda:
    //   tugma sifatida yuborasiz: array('text' => "To'lash", 'url' => $url)
}
