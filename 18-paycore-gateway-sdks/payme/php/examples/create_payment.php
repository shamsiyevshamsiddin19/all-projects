<?php
/**
 * To'lov havolasini yasash — oddiy PHP namunasi.
 *
 * Sinash (loyiha ildizidan):
 *     php examples/create_payment.php
 */

require_once __DIR__ . '/../payme_checkout.php';
require_once __DIR__ . '/../payme_orders.php';

// --- 1. Buyurtma yaratamiz ---------------------------------------------------
//
// O'z tizimingizda buyurtma allaqachon bazangizda bo'ladi:
//
//     $stmt = db()->prepare('INSERT INTO orders (product, price_som) VALUES (?, ?)');
//     $stmt->execute(array('Kitob', 5000));
//     $orderId = db()->lastInsertId();

$orderId = 'ORD' . time();
paymeDemoCreateOrder($orderId, paymeSomToTiyin(5000), 'Kitob');

// --- 2. To'lov havolasini yasaymiz -------------------------------------------

$url = paymeCheckoutUrl(array('order_id' => $orderId), paymeSomToTiyin(5000));

// Ixtiyoriy: qaytish manzili va til
// $url = paymeCheckoutUrl(['order_id' => $orderId], paymeSomToTiyin(5000), 'https://domen.uz/rahmat', 'uz');

// --- 3. Foydalanuvchini yuboramiz --------------------------------------------

if (PHP_SAPI === 'cli') {
    echo "Buyurtma:  {$orderId}\n";
    echo "Summa:     5000 so'm (" . paymeSomToTiyin(5000) . " tiyin)\n";
    echo "Havola:    {$url}\n";
} else {
    header('Location: ' . $url);
    exit;
}
