<?php
/**
 * Payme JSON-RPC xato kodlari.
 *
 * Bu kodlarni Payme belgilagan — o'zgartirmang.
 *
 * Bu faylga tegishingiz shart emas.
 */

class PaymeError extends RuntimeException
{
    /** @var int */
    public $code;
    /** @var string */
    public $data;

    public function __construct($code, $message, $data = null)
    {
        parent::__construct($message);
        $this->code = (int)$code;
        $this->data = $data;
    }

    public function toArray()
    {
        $err = array('code' => $this->code, 'message' => $this->getMessage());
        if ($this->data !== null) {
            $err['data'] = $this->data;
        }
        return $err;
    }
}

// --- Umumiy JSON-RPC xatolari -------------------------------------------------

function paymeJsonParseError()
{
    return new PaymeError(-32700, 'JSON parsing exception', 'json');
}

function paymeRequiredFieldMissing($field = 'field')
{
    return new PaymeError(-32600, 'Required field not found', $field);
}

function paymeMethodNotFound()
{
    return new PaymeError(-32601, 'Method not found', 'method');
}

function paymeUnauthorized()
{
    return new PaymeError(-32504, 'Unauthorized request', 'authorization');
}

function paymeInternalError()
{
    return new PaymeError(-32400, 'Internal system error', null);
}

// --- Merchant API xatolari ------------------------------------------------

function paymeInvalidAmount()
{
    return new PaymeError(-31001, 'Invalid amount', 'amount');
}

function paymeTransactionNotFound()
{
    return new PaymeError(-31003, 'Transaction not found', 'transaction');
}

/** Order allaqachon yakunlangan (mahsulot berilgan) — bekor qilib bo'lmaydi. */
function paymeUnableToCancel()
{
    return new PaymeError(-31007, 'Unable to cancel transaction', 'transaction');
}

/** Holat nomos: allaqachon yakunlangan/bekor qilingan yoki muddati o'tgan. */
function paymeUnableToPerform()
{
    return new PaymeError(-31008, 'Unable to complete operation', 'transaction');
}

function paymeOrderNotFound()
{
    return new PaymeError(-31050, 'Order not found', 'order');
}

/** Order allaqachon to'langan yoki bekor qilingan — yangi to'lov bo'lmaydi. */
function paymeOrderNotPayable()
{
    return new PaymeError(-31099, 'Invoice already paid or cancelled', 'order');
}

/** Shu order uchun allaqachon boshqa (faol) tranzaksiya bor. */
function paymeTransactionAlreadyExists()
{
    return new PaymeError(-31099, 'Transaction already exists', 'transaction');
}
