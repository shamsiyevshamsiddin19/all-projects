<?php
/**
 * =============================================================================
 *   SIZ FAQAT SHU FAYLNI TAHRIRLAYSIZ
 * =============================================================================
 *
 * Bu fayl Payme integratsiyasini SIZNING bazangiz bilan bog'laydi.
 * Qolgan fayllarga (payme_methods.php, payme_auth.php, payme_checkout.php,
 * payme_config.php, payme_errors.php) tegish shart emas — ular o'zgarmaydi.
 *
 * Payme Click'dan farq qiladi: bu faylda IKKI GURUH funksiya bor.
 *
 *     HISOBINGIZGA ULANISH (siz yozasiz):
 *       1. paymeFindAccount($account)     -> buyurtmangizni toping
 *       2. paymeOnPaid($transaction)      -> to'lov o'tgach mahsulotni bering
 *       3. paymeOnCancelled($transaction) -> bekor qilinganda (ixtiyoriy)
 *       4. paymeCanRefund($transaction)   -> to'langandan keyin bekor qilish
 *                                             mumkinmi (ixtiyoriy, standart: true)
 *
 *     TRANZAKSIYA KUNDALIGI (Payme talab qiladi, demo tayyor turibdi):
 *       Payme protokoli CheckTransaction/GetStatement uchun har bir
 *       tranzaksiyani vaqti, holati va sababi bilan saqlab turishni talab
 *       qiladi. Hozir bu yerda SQLite bilan ishlaydigan NAMUNA turibdi.
 *       Production'da MySQL'ga o'tkazish uchun fayl oxiridagi namunaga qarang.
 * =============================================================================
 */

require_once __DIR__ . '/payme_config.php';

// --- Tranzaksiya holatlari -----------------------------------------------
// Bu qiymatlarni Payme belgilagan — o'zgartirmang.

define('PAYME_STATE_PENDING', 1);               // yaratilgan, hali to'lanmagan
define('PAYME_STATE_PAID', 2);                  // to'langan
define('PAYME_STATE_CANCELLED', -1);             // bekor qilingan (to'lanmasdan)
define('PAYME_STATE_CANCELLED_AFTER_PAID', -2);  // to'langandan keyin bekor (qaytarilgan)

// 12 soat — shuncha vaqt ichida to'lanmagan tranzaksiya avtomatik bekor bo'ladi.
define('PAYME_TRANSACTION_TIMEOUT_MS', 43200000);

// Bekor qilish sabablari (Payme yuboradi, biz faqat saqlaymiz).
define('PAYME_REASON_RECEIVER_NOT_FOUND', 1);
define('PAYME_REASON_DEBIT_OPERATION_ERROR', 2);
define('PAYME_REASON_TRANSACTION_ERROR', 3);
define('PAYME_REASON_TIMEOUT', 4); // avtomatik bekor qilinganda BIZ shu sababni qo'yamiz
define('PAYME_REASON_REFUND', 5);
define('PAYME_REASON_UNKNOWN', 10);

/**
 * `paymeFindAccount()` qaytaradigan narsa — sizning buyurtmangiz haqida.
 */
class PaymeAccount
{
    /** @var int|string bazangizdagi buyurtma id'si */
    public $id;
    /** @var int kutilayotgan summa TIYINDA (1 so'm = 100 tiyin) */
    public $amount;
    /** @var bool buyurtma hali to'lov kutyaptimi? */
    public $payable;
    /** @var array paymeOnPaid() ichida kerak bo'ladigan hamma narsa */
    public $extra;

    public function __construct($id, $amount, $payable = true, array $extra = array())
    {
        $this->id = $id;
        $this->amount = (int)$amount;
        $this->payable = (bool)$payable;
        $this->extra = $extra;
    }
}

/**
 * Payme tranzaksiya yozuvi — protokol talab qiladigan kundalik yozuvi.
 */
class PaymeTransaction
{
    /** @var string */
    public $paymeId;
    /** @var array */
    public $account;
    /** @var int TIYINDA */
    public $amount;
    /** @var int PAYME_STATE_* dan biri */
    public $state;
    /** @var int Payme yuborgan vaqt (ms) — 12 soatlik hisob uchun */
    public $paymeTime;
    /** @var int bizning serverimizdagi yaratilgan vaqt (ms) */
    public $createTime;
    /** @var int */
    public $performTime = 0;
    /** @var int */
    public $cancelTime = 0;
    /** @var int|null */
    public $reason;
    /** @var string */
    public $ourId;
    /** @var array paymeOnPaid()/paymeOnCancelled() uchun */
    public $accountExtra = array();

    public function __construct($paymeId, array $account, $amount, $state, $paymeTime, $createTime)
    {
        $this->paymeId = $paymeId;
        $this->ourId = $paymeId;
        $this->account = $account;
        $this->amount = (int)$amount;
        $this->state = (int)$state;
        $this->paymeTime = (int)$paymeTime;
        $this->createTime = (int)$createTime;
    }
}

// =============================================================================
//   HISOBINGIZGA ULANISH — shu 4 ta funksiyani o'zgartirasiz
// =============================================================================

if (!function_exists('paymeFindAccount')) {
    /**
     * Payme yuborgan `account` maydonlari bo'yicha buyurtmani topadi.
     *
     * `$account` — masalan ['order_id' => '42']. Payme buni checkout
     * havolasiga qo'ygan `ac.order_id=42` dan oladi (payme_checkout.php
     * dagi paymeCheckoutUrl()ga qarang).
     *
     * Topilmasa null qaytaring — Payme "-31050 order not found" oladi.
     *
     * @return PaymeAccount|null
     */
    function paymeFindAccount(array $account)
    {
        if (!isset($account['order_id'])) {
            return null;
        }

        $stmt = paymeDemoDb()->prepare('SELECT * FROM demo_orders WHERE id = ? LIMIT 1');
        $stmt->execute(array((string)$account['order_id']));
        $row = $stmt->fetch();

        if (!$row) {
            return null;
        }

        return new PaymeAccount(
            $row['id'],
            (int)$row['amount_tiyin'],
            $row['status'] === 'pending',
            array('product' => $row['product'])
        );
    }
}

if (!function_exists('paymeOnPaid')) {
    /**
     * To'lov tasdiqlangach BIR MARTA chaqiriladi. Mahsulotni shu yerda bering.
     *
     * Bu yerda uzoq ish qilmang — Payme javobni kutib turadi. Xato bersa,
     * tranzaksiya baribir "to'langan" bo'lib qoladi va xato logga yoziladi.
     */
    function paymeOnPaid(PaymeTransaction $transaction)
    {
        $orderId = isset($transaction->account['order_id']) ? $transaction->account['order_id'] : null;

        $stmt = paymeDemoDb()->prepare("UPDATE demo_orders SET status = 'paid' WHERE id = ?");
        $stmt->execute(array((string)$orderId));

        paymeLog('info', "TO'LANDI", array(
            'order_id' => $orderId,
            'summa_tiyin' => $transaction->amount,
            'payme_id' => $transaction->paymeId,
        ));
    }
}

if (!function_exists('paymeOnCancelled')) {
    /**
     * To'lov bekor qilinganda (yoki to'langandan keyin qaytarilganda) chaqiriladi.
     *
     * `$transaction->state === PAYME_STATE_CANCELLED_AFTER_PAID` bo'lsa —
     * bu QAYTARISH. Shu holatda mahsulotga ruxsatni bekor qiling.
     */
    function paymeOnCancelled(PaymeTransaction $transaction)
    {
        $orderId = isset($transaction->account['order_id']) ? $transaction->account['order_id'] : null;
        $isRefund = $transaction->state === PAYME_STATE_CANCELLED_AFTER_PAID;

        $stmt = paymeDemoDb()->prepare("UPDATE demo_orders SET status = 'cancelled' WHERE id = ?");
        $stmt->execute(array((string)$orderId));

        paymeLog('info', 'BEKOR QILINDI' . ($isRefund ? ' (qaytarish)' : ''), array(
            'order_id' => $orderId,
            'sabab' => $transaction->reason,
        ));
    }
}

if (!function_exists('paymeCanRefund')) {
    /**
     * To'langan tranzaksiyani bekor qilish (qaytarish) mumkinmi?
     *
     * Standart: har doim mumkin. Mahsulot qaytarib bo'lmaydigan bo'lsa
     * `false` qaytaring — Payme "-31007 unable to cancel" oladi.
     */
    function paymeCanRefund(PaymeTransaction $transaction)
    {
        return true;
    }
}

// =============================================================================
//   TRANZAKSIYA KUNDALIGI — Payme talab qiladi, demo tayyor.
//   O'z bazangizga o'tganingizda pastdagi funksiyalarni almashtiring
//   (namunalar fayl oxirida).
// =============================================================================

if (!function_exists('paymeDemoDb')) {
    function paymeDemoDb()
    {
        static $pdo = null;

        if ($pdo === null) {
            $path = paymeEnv('PAYME_DB_PATH', __DIR__ . '/payme_demo.sqlite');

            $pdo = new PDO('sqlite:' . $path);
            $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

            $pdo->exec(
                "CREATE TABLE IF NOT EXISTS payme_transactions (
                    payme_id     TEXT PRIMARY KEY,
                    our_id       TEXT NOT NULL,
                    account_json TEXT NOT NULL,
                    amount       INTEGER NOT NULL,
                    state        INTEGER NOT NULL,
                    payme_time   INTEGER NOT NULL,
                    create_time  INTEGER NOT NULL,
                    perform_time INTEGER NOT NULL DEFAULT 0,
                    cancel_time  INTEGER NOT NULL DEFAULT 0,
                    reason       INTEGER
                )"
            );
            $pdo->exec('CREATE INDEX IF NOT EXISTS idx_payme_tx_create_time ON payme_transactions(create_time)');
            $pdo->exec(
                "CREATE TABLE IF NOT EXISTS demo_orders (
                    id           TEXT PRIMARY KEY,
                    amount_tiyin INTEGER NOT NULL,
                    status       TEXT NOT NULL DEFAULT 'pending',
                    product      TEXT
                )"
            );
        }

        return $pdo;
    }
}

if (!function_exists('paymeNowMs')) {
    function paymeNowMs()
    {
        return (int)round(microtime(true) * 1000);
    }
}

if (!function_exists('paymeRowToTransaction')) {
    function paymeRowToTransaction(array $row)
    {
        $tx = new PaymeTransaction(
            $row['payme_id'],
            json_decode($row['account_json'], true),
            $row['amount'],
            $row['state'],
            $row['payme_time'],
            $row['create_time']
        );
        $tx->ourId = $row['our_id'];
        $tx->performTime = (int)$row['perform_time'];
        $tx->cancelTime = (int)$row['cancel_time'];
        $tx->reason = $row['reason'] !== null ? (int)$row['reason'] : null;
        return $tx;
    }
}

if (!function_exists('paymeGetTransaction')) {
    /** Payme'ning tranzaksiya id'si bo'yicha yozuvni topadi. */
    function paymeGetTransaction($paymeId)
    {
        $stmt = paymeDemoDb()->prepare('SELECT * FROM payme_transactions WHERE payme_id = ? LIMIT 1');
        $stmt->execute(array($paymeId));
        $row = $stmt->fetch();
        return $row ? paymeRowToTransaction($row) : null;
    }
}

if (!function_exists('paymeGetActiveTransactionForAccount')) {
    /**
     * Shu hisob uchun hali bekor qilinmagan tranzaksiya bormi?
     *
     * CreateTransaction bitta buyurtmaga ikkita PARALLEL faol tranzaksiya
     * ochilishining oldini olish uchun ishlatadi.
     */
    function paymeGetActiveTransactionForAccount(array $account)
    {
        $orderId = isset($account['order_id']) ? $account['order_id'] : null;

        $stmt = paymeDemoDb()->prepare(
            'SELECT * FROM payme_transactions WHERE state IN (?, ?)'
        );
        $stmt->execute(array(PAYME_STATE_PENDING, PAYME_STATE_PAID));

        while ($row = $stmt->fetch()) {
            $acc = json_decode($row['account_json'], true);
            if (isset($acc['order_id']) && $acc['order_id'] == $orderId) {
                return paymeRowToTransaction($row);
            }
        }

        return null;
    }
}

if (!function_exists('paymeCreateTransaction')) {
    /**
     * Yangi tranzaksiya yozuvini yaratadi (state=PENDING).
     *
     * `create_time` sizning serveringizning HOZIRGI vaqti bo'ladi — Payme
     * yuborgan `$paymeTime` esa faqat 12-soatlik muddatni hisoblash uchun
     * saqlanadi.
     */
    function paymeCreateTransaction($paymeId, $paymeTime, $amount, array $account)
    {
        $now = paymeNowMs();

        $stmt = paymeDemoDb()->prepare(
            'INSERT INTO payme_transactions
                (payme_id, our_id, account_json, amount, state, payme_time, create_time)
             VALUES (?, ?, ?, ?, ?, ?, ?)'
        );
        $stmt->execute(array(
            $paymeId, $paymeId, json_encode($account), (int)$amount,
            PAYME_STATE_PENDING, (int)$paymeTime, $now,
        ));

        $tx = new PaymeTransaction($paymeId, $account, $amount, PAYME_STATE_PENDING, $paymeTime, $now);
        return $tx;
    }
}

if (!function_exists('paymeMarkPerformed')) {
    /**
     * Tranzaksiyani "to'langan" qiladi (state: PENDING -> PAID).
     *
     * Faqat HAQIQATAN o'tkazgan chaqiruv yangilangan yozuvni qaytaradi —
     * aks holda null qaytadi. Bu — takroriy so'rovda paymeOnPaid() qayta
     * chaqirilmasligi uchun MUHIM.
     */
    function paymeMarkPerformed($paymeId)
    {
        $now = paymeNowMs();

        $stmt = paymeDemoDb()->prepare(
            'UPDATE payme_transactions SET state = ?, perform_time = ?
             WHERE payme_id = ? AND state = ?'
        );
        $stmt->execute(array(PAYME_STATE_PAID, $now, $paymeId, PAYME_STATE_PENDING));

        if ($stmt->rowCount() === 0) {
            return null;
        }

        return paymeGetTransaction($paymeId);
    }
}

if (!function_exists('paymeMarkCancelled')) {
    /**
     * Tranzaksiyani bekor qiladi.
     *
     * PENDING -> CANCELLED, PAID -> CANCELLED_AFTER_PAID. Allaqachon bekor
     * qilingan bo'lsa null qaytaradi (idempotentlik).
     */
    function paymeMarkCancelled($paymeId, $reason)
    {
        $current = paymeGetTransaction($paymeId);
        if ($current === null ||
            in_array($current->state, array(PAYME_STATE_CANCELLED, PAYME_STATE_CANCELLED_AFTER_PAID), true)
        ) {
            return null;
        }

        $newState = $current->state === PAYME_STATE_PAID
            ? PAYME_STATE_CANCELLED_AFTER_PAID
            : PAYME_STATE_CANCELLED;

        $now = paymeNowMs();

        $stmt = paymeDemoDb()->prepare(
            'UPDATE payme_transactions SET state = ?, cancel_time = ?, reason = ?
             WHERE payme_id = ?'
        );
        $stmt->execute(array($newState, $now, (int)$reason, $paymeId));

        return paymeGetTransaction($paymeId);
    }
}

if (!function_exists('paymeListTransactions')) {
    /** `create_time` bo'yicha [from, to] oralig'idagi tranzaksiyalar. */
    function paymeListTransactions($fromMs, $toMs)
    {
        $stmt = paymeDemoDb()->prepare(
            'SELECT * FROM payme_transactions WHERE create_time BETWEEN ? AND ?
             ORDER BY create_time'
        );
        $stmt->execute(array((int)$fromMs, (int)$toMs));

        $result = array();
        while ($row = $stmt->fetch()) {
            $result[] = paymeRowToTransaction($row);
        }
        return $result;
    }
}

if (!function_exists('paymeDemoCreateOrder')) {
    /** Namuna uchun buyurtma yaratadi (demo_orders jadvaliga). */
    function paymeDemoCreateOrder($orderId, $amountTiyin, $product = '')
    {
        $stmt = paymeDemoDb()->prepare(
            "INSERT OR REPLACE INTO demo_orders (id, amount_tiyin, status, product)
             VALUES (?, ?, 'pending', ?)"
        );
        $stmt->execute(array((string)$orderId, (int)$amountTiyin, $product));
    }
}

if (!function_exists('paymeLog')) {
    function paymeLog($level, $message, array $context = array())
    {
        $line = '[payme] [' . strtoupper($level) . '] ' . $message;
        if (!empty($context)) {
            $line .= ' ' . json_encode($context, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        }
        error_log($line);
    }
}

// =============================================================================
//   O'Z BAZANGIZ UCHUN NAMUNA — nusxa oling va yuqoridagi tranzaksiya
//   kundaligi funksiyalari o'rniga qo'ying (MySQL misolida).
// =============================================================================
//
//   function paymeGetTransaction($paymeId)
//   {
//       $stmt = db()->prepare('SELECT * FROM payme_transactions WHERE payme_id = ?');
//       $stmt->execute(array($paymeId));
//       $row = $stmt->fetch();
//       return $row ? paymeRowToTransaction($row) : null;
//   }
//
//   function paymeMarkPerformed($paymeId)
//   {
//       $stmt = db()->prepare(
//           "UPDATE payme_transactions SET state = 2, perform_time = ?
//             WHERE payme_id = ? AND state = 1"
//       );
//       $stmt->execute(array(paymeNowMs(), $paymeId));
//
//       if ($stmt->rowCount() === 0) {   // <- atomar, poyga yo'q
//           return null;
//       }
//       return paymeGetTransaction($paymeId);
//   }
//
//   paymeFindAccount(), paymeOnPaid(), paymeOnCancelled() — bularni
//   o'zgartirmaysiz (ular ledger emas, sizning biznesingiz) — faqat
//   ichlarida o'z SQL'ingizni ishlatasiz (Click'dagi click_orders.php
//   bilan bir xil naqsh).
// =============================================================================
