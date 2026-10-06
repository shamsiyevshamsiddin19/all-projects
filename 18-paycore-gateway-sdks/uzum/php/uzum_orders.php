<?php
/**
 * =============================================================================
 *   SIZ FAQAT SHU FAYLNI TAHRIRLAYSIZ
 * =============================================================================
 *
 * Bu fayl Uzum Bank integratsiyasini SIZNING bazangiz bilan bog'laydi.
 * Qolgan fayllarga (uzum_methods.php, uzum_auth.php, uzum_config.php,
 * uzum_errors.php) tegish shart emas — ular o'zgarmaydi.
 *
 * Uzum Bank Payme'ga o'xshaydi: bitta "hisob" (sizning buyurtmangiz) va
 * bitta "tranzaksiya" (Uzum Bank ochadigan yozuv) bor. Farqi — holatlar
 * uchta (Payme'da to'rtta), timeout 30 daqiqa (Payme'da 12 soat), va eng
 * muhimi: TAKRORIY /create yoki /confirm so'rovida Uzum Bank aniq XATO
 * kutadi (idempotent muvaffaqiyat emas).
 *
 * Shuning uchun bu faylda IKKI GURUH funksiya bor:
 *
 *     HISOBINGIZGA ULANISH (siz yozasiz):
 *       1. uzumFindAccount($params)         -> buyurtmangizni toping
 *       2. uzumOnConfirmed($transaction)     -> to'lov o'tgach mahsulotni bering
 *       3. uzumOnReversed($transaction)      -> bekor qilinganda (ixtiyoriy)
 *       4. uzumCanReverse($transaction)      -> tasdiqlangandan keyin bekor
 *                                                qilish mumkinmi (ixtiyoriy)
 *
 *     TRANZAKSIYA KUNDALIGI (Uzum Bank talab qiladi, demo tayyor turibdi):
 *       Har bir tranzaksiyani vaqti va holati bilan saqlab turish — Uzum
 *       Bank'ning protokol talabi (/status shuni so'raydi). Hozir SQLite
 *       namunasi turibdi, production'da almashtirasiz (fayl oxiriga qarang).
 * =============================================================================
 */

require_once __DIR__ . '/uzum_config.php';

// --- Holatlar ------------------------------------------------------------
// Bu qiymatlarni Uzum Bank belgilagan (status maydonida aynan shu satrlar
// ishlatiladi) — o'zgartirmang.

define('UZUM_STATE_CREATED', 'CREATED');
define('UZUM_STATE_CONFIRMED', 'CONFIRMED');
define('UZUM_STATE_REVERSED', 'REVERSED');

// 30 daqiqa — shuncha vaqt ichida tasdiqlanmagan tranzaksiya "muvaffaqiyatsiz"
// hisoblanadi. Buni Uzum Bank alohida xabar bermaydi — o'zimiz kuzatamiz.
define('UZUM_TRANSACTION_TIMEOUT_MS', 30 * 60 * 1000);

/**
 * `uzumFindAccount()` qaytaradigan narsa — sizning buyurtmangiz haqida.
 */
class UzumAccount
{
    /** @var int|string */
    public $id;
    /** @var int summa TIYINDA */
    public $amount;
    /** @var bool */
    public $payable;
    /** @var array */
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
 * Uzum Bank tranzaksiya yozuvi — protokol talab qiladigan kundalik yozuvi.
 */
class UzumTransaction
{
    /** @var string Uzum Bank bergan UUID */
    public $transId;
    /** @var array foydalanuvchi kiritgan hisob maydonlari */
    public $params;
    /** @var int */
    public $amount;
    /** @var string CREATED|CONFIRMED|REVERSED */
    public $state;
    /** @var int */
    public $createTime;
    /** @var int */
    public $confirmTime = 0;
    /** @var int */
    public $reverseTime = 0;
    /** @var string */
    public $ourId;
    /** @var array */
    public $accountExtra = array();

    public function __construct($transId, array $params, $amount, $state, $createTime)
    {
        $this->transId = $transId;
        $this->ourId = $transId;
        $this->params = $params;
        $this->amount = (int)$amount;
        $this->state = $state;
        $this->createTime = (int)$createTime;
    }
}

// =============================================================================
//   HISOBINGIZGA ULANISH — shu 4 ta funksiyani o'zgartirasiz
// =============================================================================

if (!function_exists('uzumFindAccount')) {
    /**
     * Uzum Bank yuborgan `params` maydonlari bo'yicha buyurtmani topadi.
     *
     * `params` — foydalanuvchi Uzum Bank ilovasida kiritgan qiymatlar,
     * masalan `array('account' => '42')`.
     *
     * Topilmasa `null` qaytaring — Uzum Bank "10007" oladi.
     *
     * @return UzumAccount|null
     */
    function uzumFindAccount(array $params)
    {
        if (!isset($params['account'])) {
            return null;
        }
        $orderId = (string)$params['account'];

        $stmt = uzumDemoDb()->prepare('SELECT * FROM demo_orders WHERE id = ? LIMIT 1');
        $stmt->execute(array($orderId));
        $row = $stmt->fetch();

        if (!$row) {
            return null;
        }

        return new UzumAccount(
            $row['id'],
            $row['amount_tiyin'],
            $row['status'] === 'pending',
            array('product' => $row['product'])
        );
    }
}

if (!function_exists('uzumOnConfirmed')) {
    /**
     * To'lov tasdiqlangach BIR MARTA chaqiriladi. Mahsulotni shu yerda bering.
     *
     * DIQQAT: Uzum Bank oqimida pul /confirm kelguncha ALLAQACHON
     * yechilgan bo'ladi. Shuning uchun bu funksiya xato bersa ham, pul
     * qaytarib berilmaydi — faqat mahsulot berish jarayoni chalasi qoladi.
     * Xatoni logdan kuzatib, qo'lda hal qilasiz.
     */
    function uzumOnConfirmed(UzumTransaction $transaction)
    {
        $orderId = isset($transaction->params['account']) ? $transaction->params['account'] : null;

        $stmt = uzumDemoDb()->prepare("UPDATE demo_orders SET status = 'paid' WHERE id = ?");
        $stmt->execute(array((string)$orderId));

        uzumLog('info', 'TASDIQLANDI', array(
            'order_id' => $orderId,
            'amount'   => $transaction->amount,
            'trans_id' => $transaction->transId,
        ));
    }
}

if (!function_exists('uzumOnReversed')) {
    /**
     * Tranzaksiya bekor qilinganda (yoki qaytarilganda) chaqiriladi.
     */
    function uzumOnReversed(UzumTransaction $transaction)
    {
        $orderId = isset($transaction->params['account']) ? $transaction->params['account'] : null;

        $stmt = uzumDemoDb()->prepare("UPDATE demo_orders SET status = 'cancelled' WHERE id = ?");
        $stmt->execute(array((string)$orderId));

        uzumLog('info', 'BEKOR QILINDI', array('order_id' => $orderId, 'trans_id' => $transaction->transId));
    }
}

if (!function_exists('uzumCanReverse')) {
    /**
     * Tasdiqlangan (CONFIRMED) tranzaksiyani bekor qilish (qaytarish)
     * mumkinmi? Standart: har doim mumkin.
     */
    function uzumCanReverse(UzumTransaction $transaction)
    {
        return true;
    }
}

if (!function_exists('uzumLog')) {
    function uzumLog($level, $message, array $context = array())
    {
        $line = '[uzum] [' . strtoupper($level) . '] ' . $message;
        if (!empty($context)) {
            $line .= ' ' . json_encode($context, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        }
        error_log($line);
    }
}

// =============================================================================
//   TRANZAKSIYA KUNDALIGI — Uzum Bank talab qiladi, demo tayyor.
//   O'z bazangizga o'tganingizda pastdagi funksiyalarni almashtiring
//   (namunalar fayl oxirida).
// =============================================================================

if (!function_exists('uzumDemoDb')) {
    function uzumDemoDb()
    {
        static $pdo = null;

        if ($pdo === null) {
            $path = uzumEnv('UZUM_DB_PATH', __DIR__ . '/uzum_demo.sqlite');

            $pdo = new PDO('sqlite:' . $path);
            $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

            $pdo->exec(
                "CREATE TABLE IF NOT EXISTS uzum_transactions (
                    trans_id     TEXT PRIMARY KEY,
                    our_id       TEXT NOT NULL,
                    params_json  TEXT NOT NULL,
                    amount       INTEGER NOT NULL,
                    state        TEXT NOT NULL,
                    create_time  INTEGER NOT NULL,
                    confirm_time INTEGER NOT NULL DEFAULT 0,
                    reverse_time INTEGER NOT NULL DEFAULT 0
                )"
            );
            $pdo->exec('CREATE INDEX IF NOT EXISTS idx_uzum_tx_create_time ON uzum_transactions(create_time)');
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

if (!function_exists('uzumNowMs')) {
    function uzumNowMs()
    {
        return (int)round(microtime(true) * 1000);
    }
}

if (!function_exists('uzumRowToTransaction')) {
    function uzumRowToTransaction(array $row)
    {
        $tx = new UzumTransaction(
            $row['trans_id'],
            json_decode($row['params_json'], true),
            $row['amount'],
            $row['state'],
            $row['create_time']
        );
        $tx->ourId = $row['our_id'];
        $tx->confirmTime = (int)$row['confirm_time'];
        $tx->reverseTime = (int)$row['reverse_time'];

        return $tx;
    }
}

if (!function_exists('uzumGetTransaction')) {
    /**
     * Uzum Bank'ning tranzaksiya id'si (`transId`) bo'yicha yozuvni topadi.
     *
     * @return UzumTransaction|null
     */
    function uzumGetTransaction($transId)
    {
        $stmt = uzumDemoDb()->prepare('SELECT * FROM uzum_transactions WHERE trans_id = ? LIMIT 1');
        $stmt->execute(array($transId));
        $row = $stmt->fetch();

        return $row ? uzumRowToTransaction($row) : null;
    }
}

if (!function_exists('uzumGetActiveTransactionForAccount')) {
    /**
     * Shu hisob uchun hali bekor qilinmagan tranzaksiya bormi?
     *
     * /create bitta buyurtmaga ikkita PARALLEL faol tranzaksiya
     * ochilishining oldini olish uchun ishlatadi.
     *
     * @return UzumTransaction|null
     */
    function uzumGetActiveTransactionForAccount(array $params)
    {
        $orderId = isset($params['account']) ? $params['account'] : null;

        $stmt = uzumDemoDb()->prepare(
            'SELECT * FROM uzum_transactions WHERE state IN (?, ?)'
        );
        $stmt->execute(array(UZUM_STATE_CREATED, UZUM_STATE_CONFIRMED));

        while ($row = $stmt->fetch()) {
            $p = json_decode($row['params_json'], true);
            $pAccount = isset($p['account']) ? $p['account'] : null;
            if ($pAccount == $orderId) {
                return uzumRowToTransaction($row);
            }
        }

        return null;
    }
}

if (!function_exists('uzumCreateTransaction')) {
    /**
     * Yangi tranzaksiya yozuvini yaratadi (state=CREATED).
     *
     * @return UzumTransaction
     */
    function uzumCreateTransaction($transId, $amount, array $params)
    {
        $now = uzumNowMs();

        $stmt = uzumDemoDb()->prepare(
            'INSERT INTO uzum_transactions
                 (trans_id, our_id, params_json, amount, state, create_time)
             VALUES (?, ?, ?, ?, ?, ?)'
        );
        $stmt->execute(array(
            $transId,
            $transId,
            json_encode($params),
            (int)$amount,
            UZUM_STATE_CREATED,
            $now,
        ));

        return new UzumTransaction($transId, $params, $amount, UZUM_STATE_CREATED, $now);
    }
}

if (!function_exists('uzumMarkConfirmed')) {
    /**
     * Tranzaksiyani "tasdiqlangan" qiladi (state: CREATED -> CONFIRMED).
     *
     * Faqat HAQIQATAN o'tkazgan chaqiruv yangilangan yozuvni qaytaradi —
     * aks holda `null`.
     *
     * @return UzumTransaction|null
     */
    function uzumMarkConfirmed($transId)
    {
        $now = uzumNowMs();

        $stmt = uzumDemoDb()->prepare(
            "UPDATE uzum_transactions
                SET state = ?, confirm_time = ?
              WHERE trans_id = ? AND state = ?"
        );
        $stmt->execute(array(UZUM_STATE_CONFIRMED, $now, $transId, UZUM_STATE_CREATED));

        if ($stmt->rowCount() === 0) {
            return null;
        }

        return uzumGetTransaction($transId);
    }
}

if (!function_exists('uzumMarkReversed')) {
    /**
     * Tranzaksiyani bekor qiladi (CREATED yoki CONFIRMED -> REVERSED).
     *
     * Allaqachon REVERSED bo'lsa `null` qaytaradi.
     *
     * @return UzumTransaction|null
     */
    function uzumMarkReversed($transId)
    {
        $now = uzumNowMs();

        $current = uzumGetTransaction($transId);
        if ($current === null || $current->state === UZUM_STATE_REVERSED) {
            return null;
        }

        $stmt = uzumDemoDb()->prepare(
            "UPDATE uzum_transactions SET state = ?, reverse_time = ? WHERE trans_id = ?"
        );
        $stmt->execute(array(UZUM_STATE_REVERSED, $now, $transId));

        return uzumGetTransaction($transId);
    }
}

if (!function_exists('uzumDemoCreateOrder')) {
    /**
     * Namuna uchun buyurtma yaratadi (demo_orders jadvaliga).
     */
    function uzumDemoCreateOrder($orderId, $amountTiyin, $product = '')
    {
        $stmt = uzumDemoDb()->prepare(
            "INSERT OR REPLACE INTO demo_orders (id, amount_tiyin, status, product)
             VALUES (?, ?, 'pending', ?)"
        );
        $stmt->execute(array((string)$orderId, (int)$amountTiyin, $product));
    }
}

// =============================================================================
//   O'Z BAZANGIZ UCHUN NAMUNA — nusxa oling va yuqoridagi tranzaksiya
//   kundaligi funksiyalari o'rniga qo'ying (MySQL misolida).
// =============================================================================
//
//   function uzumGetTransaction($transId)
//   {
//       $stmt = db()->prepare('SELECT * FROM uzum_transactions WHERE trans_id = ?');
//       $stmt->execute(array($transId));
//       $row = $stmt->fetch();
//       if (!$row) return null;
//       // ... uzumRowToTransaction($row) bilan bir xil qaytaring
//   }
//
//   function uzumMarkConfirmed($transId)
//   {
//       $stmt = db()->prepare(
//           "UPDATE uzum_transactions SET state='CONFIRMED', confirm_time=?
//             WHERE trans_id=? AND state='CREATED'"
//       );
//       $stmt->execute(array(uzumNowMs(), $transId));
//       if ($stmt->rowCount() === 0) {    // <- atomar, poyga yo'q
//           return null;
//       }
//       return uzumGetTransaction($transId);
//   }
//
//   uzumFindAccount(), uzumOnConfirmed(), uzumOnReversed() — bularni
//   O'ZGARTIRMAYSIZ (ular ledger emas, sizning biznesingiz) — faqat
//   ichlarida o'z SQL'ingizni ishlatasiz.
// =============================================================================
