<?php
/**
 * =============================================================================
 *   SIZ FAQAT SHU FAYLNI TAHRIRLAYSIZ
 * =============================================================================
 *
 * Bu fayl Click integratsiyasini SIZNING bazangiz bilan bog'laydi.
 * Qolgan fayllarga (click_prepare.php, click_complete.php, click_signature.php,
 * click_config.php) tegish shart emas — ular o'zgarmaydi.
 *
 * Click integratsiyasi sizning tizimingiz haqida atigi 5 narsani bilishi kerak:
 *
 *     BAZA:
 *       1. clickFindOrder($merchantTransId)          -> buyurtmani toping
 *       2. clickMarkPaid($order, $clickTransId)      -> "to'landi" deb belgilang
 *       3. clickMarkCancelled($order, $clickTransId) -> "bekor qilindi" deb belgilang
 *
 *     HODISALAR:
 *       4. clickOnPaid($order)      -> to'lov o'tgach mahsulotni bering
 *       5. clickOnCancelled($order) -> to'lov bekor bo'lganda (ixtiyoriy)
 *
 * Hozir bu yerda SQLite bilan ishlaydigan NAMUNA turibdi — klon qilib darrov
 * sinab ko'rishingiz uchun. O'z bazangizga moslash uchun quyidagi 5 funksiyaning
 * ichini o'zgartiring, xolos.
 *
 * MySQL, Laravel (Eloquent) va mavjud PDO ulanishi uchun tayyor namunalar shu
 * faylning oxirida (izohda) berilgan — nusxa olib qo'yavering.
 * =============================================================================
 */

require_once __DIR__ . '/click_utils.php';
require_once __DIR__ . '/click_config.php';

// --- Holatlar ----------------------------------------------------------------
// Bazangizda boshqacha nomlangan bo'lsa (masalan 'pending_payment'),
// clickFindOrder() ichida shu uchtasiga o'girib bering.

define('CLICK_STATUS_PENDING', 'pending');      // to'lov kutilmoqda
define('CLICK_STATUS_PAID', 'paid');            // to'langan
define('CLICK_STATUS_CANCELLED', 'cancelled');  // bekor qilingan / amalga oshmagan

/**
 * Click integratsiyasi buyurtmangizdan kutadigan ma'lumot.
 */
class ClickOrder
{
    /**
     * Bazangizdagi raqamli id. Aynan shu qiymat Click'ga `merchant_prepare_id`
     * bo'lib ketadi va complete'da qaytib keladi.
     *
     * @var int
     */
    public $id;

    /**
     * To'lov havolasida `transaction_param` bo'lib ketadigan satr
     * (masalan "ORD42"). Bazangizda UNIKAL bo'lishi SHART.
     *
     * @var string
     */
    public $merchantTransId;

    /**
     * Kutilayotgan summa (so'mda). Click yuborgan summa shu bilan
     * solishtiriladi — mos kelmasa to'lov rad etiladi.
     *
     * @var float
     */
    public $amount;

    /**
     * CLICK_STATUS_PENDING | CLICK_STATUS_PAID | CLICK_STATUS_CANCELLED
     *
     * @var string
     */
    public $status;

    /**
     * Sizga kerak bo'ladigan ixtiyoriy ma'lumot (user_id, chat_id,
     * product_id...). Click bu bilan ishlamaydi — u faqat clickOnPaid()
     * ichida sizga kerak bo'ladi.
     *
     * @var array
     */
    public $extra = array();

    public function __construct($id, $merchantTransId, $amount, $status, array $extra = array())
    {
        $this->id = (int)$id;
        $this->merchantTransId = (string)$merchantTransId;
        $this->amount = (float)$amount;
        $this->status = (string)$status;
        $this->extra = $extra;
    }
}

// =============================================================================
//   1-3: BAZA BILAN ISHLASH
// =============================================================================

if (!function_exists('clickFindOrder')) {
    /**
     * Buyurtmani `merchant_trans_id` bo'yicha topadi. Topilmasa null.
     *
     * Click prepare va complete so'rovlarida shu funksiya chaqiriladi.
     *
     * @return ClickOrder|null
     */
    function clickFindOrder($merchantTransId)
    {
        $stmt = clickDemoDb()->prepare(
            'SELECT * FROM orders WHERE merchant_trans_id = ? LIMIT 1'
        );
        $stmt->execute(array((string)$merchantTransId));
        $row = $stmt->fetch();

        if (!$row) {
            return null;
        }

        return new ClickOrder(
            $row['id'],
            $row['merchant_trans_id'],
            $row['amount'],
            $row['status'],
            // clickOnPaid() da nima kerak bo'lsa, shu yerga soling:
            array(
                'user_id' => $row['user_id'],
                'product' => $row['product'],
            )
        );
    }
}

if (!function_exists('clickMarkPaid')) {
    /**
     * Buyurtmani "to'langan" deb belgilaydi.
     *
     * +-----------------------------------------------------------------------+
     * |  DIQQAT — BU YERDA XATO QILISH OSON:                                  |
     * |                                                                       |
     * |  Faqat SHU chaqiruv holatni pending -> paid o'tkazgan bo'lsa `true`   |
     * |  qaytaring. Allaqachon to'langan bo'lsa `false` qaytaring.            |
     * |                                                                       |
     * |  Nega? Click javobni ololmasa complete'ni QAYTA yuboradi (ba'zan bir  |
     * |  vaqtda). `true` qaytgan chaqiruvda clickOnPaid() ishlaydi. Agar har  |
     * |  safar `true` qaytarsangiz — mahsulot ikki marta beriladi.            |
     * |                                                                       |
     * |  To'g'ri yo'l — shartni SQL'ning O'ZIGA qo'ying (atomar bo'ladi):     |
     * |      UPDATE ... SET status='paid' WHERE id=? AND status='pending'     |
     * |  va o'zgargan qatorlar sonini (rowCount) qaytaring.                   |
     * |                                                                       |
     * |  NOTO'G'RI (poyga bor — ikkalasi ham true olishi mumkin):             |
     * |      if ($order->status === 'pending') {    // <- avval o'qib         |
     * |          $pdo->exec("UPDATE ... SET status='paid'");  // <- keyin yozish
     * |          return true;                                                 |
     * |      }                                                                |
     * +-----------------------------------------------------------------------+
     *
     * @return bool
     */
    function clickMarkPaid(ClickOrder $order, $clickTransId)
    {
        $stmt = clickDemoDb()->prepare(
            'UPDATE orders
                SET status = ?, click_trans_id = ?, paid_at = ?
              WHERE id = ? AND status = ?'
        );
        $stmt->execute(array(
            CLICK_STATUS_PAID,
            (string)$clickTransId,
            gmdate('Y-m-d H:i:s'),
            $order->id,
            CLICK_STATUS_PENDING,
        ));

        return $stmt->rowCount() > 0;
    }
}

if (!function_exists('clickMarkCancelled')) {
    /**
     * Buyurtmani "bekor qilingan" deb belgilaydi.
     *
     * Click foydalanuvchi to'lovni bekor qilganini yoki xato bo'lganini
     * aytganda chaqiriladi.
     */
    function clickMarkCancelled(ClickOrder $order, $clickTransId)
    {
        $stmt = clickDemoDb()->prepare(
            'UPDATE orders
                SET status = ?, click_trans_id = ?, paid_at = NULL
              WHERE id = ? AND status = ?'
        );
        $stmt->execute(array(
            CLICK_STATUS_CANCELLED,
            (string)$clickTransId,
            $order->id,
            CLICK_STATUS_PENDING,
        ));
    }
}

// =============================================================================
//   4-5: HODISALAR — "to'langanda nima bo'lsin?"
// =============================================================================

if (!function_exists('clickOnPaid')) {
    /**
     * To'lov tasdiqlangach BIR MARTA chaqiriladi. Mahsulotni shu yerda bering.
     *
     * Masalan:
     *     sendTelegramMessage($order->extra['chat_id'], "To'lovingiz qabul qilindi!");
     *     grantAccess($order->extra['user_id'], $order->extra['product']);
     *
     * Ikki muhim eslatma:
     *
     *  1. Bu yerda UZOQ ish qilmang — Click javobni kutib turadi va kechiksangiz
     *     so'rovni qayta yuboradi. Og'ir ishni navbatga qo'ying.
     *
     *  2. Bu funksiya xato bersa, to'lov baribir "paid" bo'lib qoladi (pul
     *     yechilgan-ku) va xato logga yoziladi. Click'ga xato qaytarish foyda
     *     bermaydi: u qayta urganda buyurtma allaqachon "paid" bo'lgani uchun
     *     bu funksiya qayta ishlamaydi. Shuning uchun loglarni kuzatib boring.
     */
    function clickOnPaid(ClickOrder $order)
    {
        clickLog('info', "TO'LANDI", array(
            'merchant_trans_id' => $order->merchantTransId,
            'amount'            => $order->amount,
            'user_id'           => isset($order->extra['user_id']) ? $order->extra['user_id'] : null,
            'product'           => isset($order->extra['product']) ? $order->extra['product'] : null,
        ));
    }
}

if (!function_exists('clickOnCancelled')) {
    /**
     * To'lov bekor qilinganda chaqiriladi (ixtiyoriy — bo'sh qoldirsangiz ham bo'ladi).
     */
    function clickOnCancelled(ClickOrder $order)
    {
        clickLog('info', 'BEKOR QILINDI', array(
            'merchant_trans_id' => $order->merchantTransId,
        ));
    }
}

// =============================================================================
//   Quyidagisi — faqat yuqoridagi SQLite NAMUNASI uchun kerak.
//   O'z bazangizga o'tganingizda bu qismni o'chirib tashlang.
// =============================================================================

if (!function_exists('clickDemoDb')) {
    /**
     * Namuna SQLite bazasi.
     *
     * O'z loyihangizda buning o'rniga mavjud PDO ulanishingizni qaytaring:
     *     function clickDemoDb() { return db(); }
     */
    function clickDemoDb()
    {
        static $pdo = null;

        if ($pdo === null) {
            $path = clickEnv('CLICK_DB_PATH', __DIR__ . '/click_demo.sqlite');

            $pdo = new PDO('sqlite:' . $path);
            $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

            $pdo->exec(
                "CREATE TABLE IF NOT EXISTS orders (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    merchant_trans_id TEXT    NOT NULL UNIQUE,
                    amount            TEXT    NOT NULL,
                    status            TEXT    NOT NULL DEFAULT 'pending',
                    click_trans_id    TEXT,
                    paid_at           TEXT,
                    created_at        TEXT    NOT NULL,
                    user_id           INTEGER,
                    product           TEXT
                )"
            );
        }

        return $pdo;
    }
}

if (!function_exists('clickDemoCreateOrder')) {
    /**
     * Namuna uchun buyurtma yaratadi.
     *
     * O'z tizimingizda buyurtma allaqachon bazangizda bo'ladi — bu funksiya
     * kerak emas. Faqat `merchant_trans_id` ustunini qo'shib qo'ying.
     *
     * @return ClickOrder
     */
    function clickDemoCreateOrder($merchantTransId, $amount, $userId = null, $product = null)
    {
        $stmt = clickDemoDb()->prepare(
            'INSERT INTO orders (merchant_trans_id, amount, status, created_at, user_id, product)
             VALUES (?, ?, ?, ?, ?, ?)'
        );
        $stmt->execute(array(
            (string)$merchantTransId,
            (string)$amount,
            CLICK_STATUS_PENDING,
            gmdate('Y-m-d H:i:s'),
            $userId,
            $product,
        ));

        return new ClickOrder(
            (int)clickDemoDb()->lastInsertId(),
            $merchantTransId,
            $amount,
            CLICK_STATUS_PENDING,
            array('user_id' => $userId, 'product' => $product)
        );
    }
}

// =============================================================================
//   O'Z BAZANGIZ UCHUN NAMUNALAR — nusxa oling va yuqoridagi funksiyalar
//   o'rniga qo'ying.
// =============================================================================
//
// --- MySQL (mavjud PDO ulanishingiz bilan) -----------------------------------
//
//   Loyihangizda db() kabi PDO qaytaradigan funksiya bo'lsa, o'shani ishlating.
//
//   function clickFindOrder($merchantTransId)
//   {
//       $stmt = db()->prepare(
//           'SELECT id, merchant_trans_id, price, status, user_id, telegram_id
//              FROM orders WHERE merchant_trans_id = ? LIMIT 1'
//       );
//       $stmt->execute(array($merchantTransId));
//       $row = $stmt->fetch();
//
//       if (!$row) {
//           return null;
//       }
//
//       // Bazangizdagi holatni bizning uchta holatga o'giring:
//       $map = array(
//           'new'             => CLICK_STATUS_PENDING,
//           'pending_payment' => CLICK_STATUS_PENDING,
//           'paid'            => CLICK_STATUS_PAID,
//           'queue_waiting'   => CLICK_STATUS_PAID,   // allaqachon bajarilgan
//           'done'            => CLICK_STATUS_PAID,
//       );
//       $status = isset($map[$row['status']]) ? $map[$row['status']] : CLICK_STATUS_CANCELLED;
//
//       return new ClickOrder(
//           $row['id'],
//           $row['merchant_trans_id'],
//           $row['price'],              // narx qaysi ustunda bo'lsa
//           $status,
//           array('user_id' => $row['user_id'], 'telegram_id' => $row['telegram_id'])
//       );
//   }
//
//   function clickMarkPaid(ClickOrder $order, $clickTransId)
//   {
//       $stmt = db()->prepare(
//           "UPDATE orders
//               SET status = 'paid', click_trans_id = ?, paid_at = NOW()
//             WHERE id = ? AND status = 'pending_payment'"
//       );
//       $stmt->execute(array($clickTransId, $order->id));
//
//       return $stmt->rowCount() > 0;   // <- atomar, poyga yo'q
//   }
//
//   function clickMarkCancelled(ClickOrder $order, $clickTransId)
//   {
//       $stmt = db()->prepare(
//           "UPDATE orders
//               SET status = 'cancelled', click_trans_id = ?
//             WHERE id = ? AND status = 'pending_payment'"
//       );
//       $stmt->execute(array($clickTransId, $order->id));
//   }
//
//   function clickOnPaid(ClickOrder $order)
//   {
//       // loyihangizdagi mavjud funksiyani chaqiring:
//       sendMessage($order->extra['telegram_id'], "To'lovingiz qabul qilindi!");
//       notifyAdminsNewOrder($order->id);
//   }
//
//
// --- Laravel (Eloquent) ------------------------------------------------------
//
//   function clickFindOrder($merchantTransId)
//   {
//       $o = \App\Models\Order::where('merchant_trans_id', $merchantTransId)->first();
//       if (!$o) {
//           return null;
//       }
//       return new ClickOrder($o->id, $o->merchant_trans_id, $o->price,
//                             $o->status, array('user_id' => $o->user_id));
//   }
//
//   function clickMarkPaid(ClickOrder $order, $clickTransId)
//   {
//       // ->update() atomar UPDATE yasaydi — poyga yo'q
//       $updated = \App\Models\Order::where('id', $order->id)
//           ->where('status', 'pending')
//           ->update(array(
//               'status'         => 'paid',
//               'click_trans_id' => $clickTransId,
//               'paid_at'        => now(),
//           ));
//
//       return $updated > 0;
//   }
//
// =============================================================================
