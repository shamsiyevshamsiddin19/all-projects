<?php
/**
 * MySQL -> JSON EKSPORT (PHP 7.0+)
 * ---------------------------------
 * Eski kino bot bazasini JSON ga eksport qiladi. Chiqgan `kino_export.json`
 * faylini Python migratsiyasiga beriladi (migrate_from_json.py).
 *
 * ISHLATISH:
 *   1. Shu faylni hosting'ga (bot papkasiga) yuklang.
 *   2. Brauzerda oching:  https://SIZNING-DOMEN/bot/kino/export.php?key=CHANGE_THIS_SECRET
 *      (yoki ?key=...&download=1 — to'g'ridan-to'g'ri yuklab olish)
 *   3. Ishlagach shu faylni O'CHIRIB tashlang (xavfsizlik uchun).
 */

// ------- SOZLAMALAR (eski config.php dagi qiymatlar) -------
$DB_HOST = 'localhost';
$DB_NAME = 'your_db_name';
$DB_USER = 'your_db_name';
$DB_PASS = 'CHANGE_ME';

$SECRET  = 'CHANGE_THIS_SECRET'; // ?key= bilan mos kelishi shart

// ------- HIMOYA -------
if (($_GET['key'] ?? '') !== $SECRET) {
    http_response_code(403);
    exit('Kirish taqiqlangan. To\'g\'ri ?key= bering.');
}

header('Content-Type: application/json; charset=utf-8');

try {
    $pdo = new PDO(
        "mysql:host=$DB_HOST;dbname=$DB_NAME;charset=utf8mb4",
        $DB_USER,
        $DB_PASS,
        [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]
    );
} catch (Throwable $e) {
    http_response_code(500);
    exit(json_encode(['error' => 'DB ulanmadi: ' . $e->getMessage()]));
}

// Eksport qilinadigan jadvallar
$tables = ['users', 'movies', 'series', 'episodes', 'channels', 'settings', 'social_links'];

$out = [
    'exported_at' => date('c'),
    'source_db'   => $DB_NAME,
    'tables'      => [],
];

foreach ($tables as $t) {
    try {
        $rows = $pdo->query("SELECT * FROM `$t`")->fetchAll();
        $out['tables'][$t] = $rows;
    } catch (Throwable $e) {
        // Jadval yo'q bo'lsa — bo'sh
        $out['tables'][$t] = [];
    }
}

// Statistika (tekshirish uchun)
$out['counts'] = [];
foreach ($out['tables'] as $name => $rows) {
    $out['counts'][$name] = count($rows);
}

$json = json_encode($out, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);

if (($_GET['download'] ?? '') === '1') {
    header('Content-Disposition: attachment; filename="kino_export.json"');
}

echo $json;
