<?php
/**
 * Uzum Bank Merchant API xato kodlari.
 *
 * Bu kodlarni Uzum Bank belgilagan (rasmiy hujjat: developer.uzumbank.uz,
 * "Коды ошибок" bo'limi) — o'zgartirmang.
 *
 * MUHIM: Uzum'da xato kodi SATR sifatida yuboriladi ("10007", raqam emas)
 * va javob HTTP 400 bilan qaytariladi (Click/Payme'da esa har doim 200).
 */

class UzumError extends RuntimeException
{
    /** @var string */
    public $code;

    public function __construct($code, $message)
    {
        parent::__construct($message);
        $this->code = $code;
    }

    public function toArray()
    {
        return array('errorCode' => $this->code);
    }
}

if (!function_exists('uzumAccessDenied')) {
    function uzumAccessDenied()
    {
        return new UzumError('10001', 'Access denied');
    }
}

if (!function_exists('uzumJsonParseError')) {
    function uzumJsonParseError()
    {
        return new UzumError('10002', 'JSON parsing error');
    }
}

if (!function_exists('uzumInvalidOperation')) {
    function uzumInvalidOperation()
    {
        return new UzumError('10003', 'Invalid operation (method must be POST)');
    }
}

if (!function_exists('uzumRequiredFieldMissing')) {
    function uzumRequiredFieldMissing()
    {
        return new UzumError('10005', 'Required parameter is missing');
    }
}

if (!function_exists('uzumInvalidServiceId')) {
    function uzumInvalidServiceId()
    {
        return new UzumError('10006', 'Invalid serviceId');
    }
}

if (!function_exists('uzumAccountNotFound')) {
    function uzumAccountNotFound()
    {
        return new UzumError('10007', 'Additional payment attribute not found');
    }
}

if (!function_exists('uzumAlreadyPaid')) {
    function uzumAlreadyPaid()
    {
        return new UzumError('10008', 'Payment already paid');
    }
}

if (!function_exists('uzumAlreadyCancelled')) {
    function uzumAlreadyCancelled()
    {
        return new UzumError('10009', 'Payment cancelled');
    }
}

if (!function_exists('uzumTransactionAlreadyCreated')) {
    /**
     * Shu `transId` bilan tranzaksiya allaqachon yaratilgan.
     *
     * DIQQAT: bu Click/Payme'dagidek "idempotent — bir xil natijani
     * qaytar" emas — Uzum Bank hujjati aniq shunday deydi: "Верните этот
     * код при повторном создании транзакции с тем же transId".
     */
    function uzumTransactionAlreadyCreated()
    {
        return new UzumError('10010', 'Transaction with this transId already created');
    }
}

if (!function_exists('uzumInvalidAmount')) {
    function uzumInvalidAmount()
    {
        return new UzumError('10011', 'Invalid amount');
    }
}

if (!function_exists('uzumAmountTooLow')) {
    function uzumAmountTooLow()
    {
        return new UzumError('10012', 'Amount is below the minimum');
    }
}

if (!function_exists('uzumAmountTooHigh')) {
    function uzumAmountTooHigh()
    {
        return new UzumError('10013', 'Amount is above the maximum');
    }
}

if (!function_exists('uzumTransactionNotFound')) {
    function uzumTransactionNotFound()
    {
        return new UzumError('10014', 'Transaction not found');
    }
}

if (!function_exists('uzumTransactionCancelled')) {
    /** Bekor qilingan tranzaksiyani tasdiqlab (confirm) bo'lmaydi. */
    function uzumTransactionCancelled()
    {
        return new UzumError('10015', 'Transaction is cancelled');
    }
}

if (!function_exists('uzumTransactionAlreadyConfirmed')) {
    /**
     * Takroriy /confirm so'rovi — Uzum Bank hujjati bo'yicha bu ham XATO,
     * idempotent muvaffaqiyat emas (10010 bilan bir xil mantiq).
     */
    function uzumTransactionAlreadyConfirmed()
    {
        return new UzumError('10016', 'Transaction already confirmed');
    }
}

if (!function_exists('uzumUnableToCancel')) {
    function uzumUnableToCancel()
    {
        return new UzumError('10017', 'Unable to cancel transaction in current state');
    }
}

if (!function_exists('uzumTransactionAlreadyCancelled')) {
    /** Takroriy /reverse so'rovi — xato qaytariladi (idempotent emas). */
    function uzumTransactionAlreadyCancelled()
    {
        return new UzumError('10018', 'Transaction already cancelled');
    }
}

if (!function_exists('uzumInternalError')) {
    function uzumInternalError()
    {
        return new UzumError('99999', 'Internal server error');
    }
}
