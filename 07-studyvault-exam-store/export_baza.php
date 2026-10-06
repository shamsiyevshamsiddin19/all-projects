<?php
/**
 * tuityordam bazasini (users, settings, payments, products, referrals) JSON ga
 * eksport qiladi — yangi serverga (PostgreSQL) ko'chirish uchun.
 *
 * FOYDALANISH:
 *  1. Bu faylni ESKI hostingda mustaqilish1bot papkasiga yuklang.
 *  2. Brauzerда oching:  .../mustaqilish1bot/export_baza.php?key=KOCHIRISH2026
 *  3. baza_export.json yuklab olinadi — shu faylni menga bering.
 *  4. Ko'chirish tugagach bu faylni O'CHIRING (xavfsizlik uchun).
 */

if (($_GET['key'] ?? '') !== 'KOCHIRISH2026') {
    http_response_code(403);
    exit('Forbidden');
}

$configPath = __DIR__ . '/config.php';
if (!is_file($configPath)) {
    http_response_code(500);
    exit('config.php topilmadi');
}
$config = require $configPath;
$db = $config['baza_bot']['db'];

try {
    $pdo = new PDO(
        "mysql:host={$db['host']};port={$db['port']};dbname={$db['name']};charset={$db['charset']}",
        $db['user'], $db['pass'],
        [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
    );
} catch (Throwable $e) {
    http_response_code(500);
    exit('DB ulanish xatosi: ' . $e->getMessage());
}

$tables = ['users', 'settings', 'payments', 'products', 'referrals'];
$out = ['_db' => $db['name'], '_exported_at' => date('c')];
foreach ($tables as $t) {
    try {
        $out[$t] = $pdo->query("SELECT * FROM `{$t}`")->fetchAll(PDO::FETCH_ASSOC);
    } catch (Throwable $e) {
        $out[$t] = ['__error' => $e->getMessage()];
    }
}

header('Content-Type: application/json; charset=utf-8');
header('Content-Disposition: attachment; filename="baza_export.json"');
echo json_encode($out, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
