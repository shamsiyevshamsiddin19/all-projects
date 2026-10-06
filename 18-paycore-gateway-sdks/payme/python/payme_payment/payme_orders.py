"""
===============================================================================
  SIZ FAQAT SHU FAYLNI TAHRIRLAYSIZ
===============================================================================

Bu fayl Payme integratsiyasini SIZNING bazangiz bilan bog'laydi.
Qolgan fayllarga (payme_methods.py, payme_auth.py, payme_checkout.py,
payme_config.py, payme_errors.py) tegish shart emas — ular o'zgarmaydi.

Payme Click'dan farq qiladi: Click'da "to'lov" tushunchasi sizning
buyurtmangiz bilan bir xil, Payme'da esa ikkita alohida narsa bor:

    1. HISOB (account) — sizning buyurtmangiz/mahsulotingiz. Payme uni
       {"order_id": "42"} kabi maydonlar orqali topadi.
    2. TRANZAKSIYA (transaction) — Payme'ning o'zi CreateTransaction bilan
       ochadigan yozuv. Bitta hisobga (agar u muvaffaqiyatsiz urinishlar
       bo'lsa) bir nechta tranzaksiya urinishi bo'lishi mumkin, lekin faol
       (bekor qilinmagan) tranzaksiya har doim bittadan ko'p emas.

Shuning uchun bu faylda IKKI GURUH funksiya bor:

    HISOBINGIZGA ULANISH (siz yozasiz):
      1. find_account(account)        -> buyurtmangizni toping
      2. on_paid(transaction)         -> to'lov o'tgach mahsulotni bering
      3. on_cancelled(transaction)    -> bekor qilinganda (ixtiyoriy)
      4. can_refund(transaction)      -> to'langandan keyin bekor qilish
                                          mumkinmi (ixtiyoriy, standart: ha)

    TRANZAKSIYA KUNDALIGI (Payme talab qiladi, demo tayyor turibdi):
      Payme protokoli CheckTransaction/GetStatement uchun har bir
      tranzaksiyani vaqti, holati va sababi bilan saqlab turishni talab
      qiladi. Bu — sizning biznes qoidangiz emas, Payme'ning talabi.
      Hozir bu yerda SQLite bilan ishlaydigan NAMUNA turibdi. Production'da
      PostgreSQL/MySQL'ga o'tkazish uchun fayl oxiridagi namunaga qarang.
===============================================================================
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("payme")

# --- Tranzaksiya holatlari -----------------------------------------------
# Bu qiymatlarni Payme belgilagan (TransactionState) — o'zgartirmang.

STATE_PENDING = 1              # yaratilgan, hali to'lanmagan
STATE_PAID = 2                 # to'langan
STATE_CANCELLED = -1           # bekor qilingan (to'lanmasdan turib)
STATE_CANCELLED_AFTER_PAID = -2  # to'langandan keyin bekor qilingan (qaytarilgan)

# 12 soat — shuncha vaqt ichida to'lanmagan tranzaksiya avtomatik bekor bo'ladi.
TRANSACTION_TIMEOUT_MS = 43_200_000

# Bekor qilish sabablari (Payme yuboradi, biz faqat saqlaymiz).
REASON_RECEIVER_NOT_FOUND = 1
REASON_DEBIT_OPERATION_ERROR = 2
REASON_TRANSACTION_ERROR = 3
REASON_TIMEOUT = 4      # avtomatik bekor qilinganda BIZ shu sababni qo'yamiz
REASON_REFUND = 5
REASON_UNKNOWN = 10


@dataclass
class PaymeAccount:
    """`find_account()` qaytaradigan narsa — sizning buyurtmangiz haqida.

    id
        Bazangizdagi buyurtma id'si.

    amount
        Kutilayotgan summa TIYINDA (1 so'm = 100 tiyin). Payme yuborgan
        summa shu bilan solishtiriladi.

    payable
        Buyurtma hali to'lov kutyaptimi? Allaqachon to'langan yoki bekor
        qilingan bo'lsa `False` qiling — shunda Payme "-31099" oladi.

    extra
        `on_paid()` ichida kerak bo'ladigan hamma narsa (user_id, chat_id...).
    """

    id: int | str
    amount: int
    payable: bool = True
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PaymeTransaction:
    """Payme tranzaksiya yozuvi — protokol talab qiladigan kundalik yozuvi."""

    payme_id: str
    account: dict[str, Any]
    amount: int
    state: int
    payme_time: int
    create_time: int
    perform_time: int = 0
    cancel_time: int = 0
    reason: int | None = None
    our_id: str = ""
    account_extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.our_id:
            self.our_id = self.payme_id


# =============================================================================
#   HISOBINGIZGA ULANISH — shu 4 ta funksiyani o'zgartirasiz
# =============================================================================


def find_account(account: dict[str, Any]) -> PaymeAccount | None:
    """Payme yuborgan `account` maydonlari bo'yicha buyurtmani topadi.

    `account` — masalan `{"order_id": "42"}`. Payme buni checkout havolasiga
    qo'ygan `ac.order_id=42` dan oladi (payme_checkout.py`dagi
    `checkout_url()` ga qarang).

    Topilmasa `None` qaytaring — Payme "-31050 order not found" oladi.
    """
    order_id = account.get("order_id")
    if order_id is None:
        return None

    row = _demo_db().execute(
        "SELECT * FROM demo_orders WHERE id = ? LIMIT 1", (str(order_id),)
    ).fetchone()

    if row is None:
        return None

    return PaymeAccount(
        id=row["id"],
        amount=int(row["amount_tiyin"]),
        payable=(row["status"] == "pending"),
        extra={"product": row["product"]},
    )


def on_paid(transaction: PaymeTransaction) -> None:
    """To'lov tasdiqlangach BIR MARTA chaqiriladi. Mahsulotni shu yerda bering.

    Masalan:
        order_id = transaction.account["order_id"]
        db.orders.mark_paid(order_id)
        bot.send_message(transaction.account_extra["chat_id"], "To'landi!")

    Bu yerda uzoq ish qilmang — Payme javobni kutib turadi. Xato bersa,
    tranzaksiya baribir "to'langan" bo'lib qoladi (pul yechilgan-ku) va xato
    logga yoziladi — qo'lda tekshirasiz.
    """
    order_id = transaction.account.get("order_id")
    with _demo_write() as conn:
        conn.execute(
            "UPDATE demo_orders SET status = 'paid' WHERE id = ?", (str(order_id),)
        )
    logger.info(
        "TO'LANDI: order=%s, summa=%s tiyin, payme_id=%s",
        order_id,
        transaction.amount,
        transaction.payme_id,
    )


def on_cancelled(transaction: PaymeTransaction) -> None:
    """To'lov bekor qilinganda (yoki to'langandan keyin qaytarilganda) chaqiriladi.

    `transaction.state == STATE_CANCELLED_AFTER_PAID` bo'lsa — bu QAYTARISH
    (pul allaqachon berilgan edi, endi orqaga olinmoqda). Shu holatda
    mahsulotga ruxsatni bekor qiling.
    """
    order_id = transaction.account.get("order_id")
    is_refund = transaction.state == STATE_CANCELLED_AFTER_PAID
    with _demo_write() as conn:
        conn.execute(
            "UPDATE demo_orders SET status = 'cancelled' WHERE id = ?", (str(order_id),)
        )
    logger.info(
        "BEKOR QILINDI%s: order=%s, sabab=%s",
        " (qaytarish)" if is_refund else "",
        order_id,
        transaction.reason,
    )


def can_refund(transaction: PaymeTransaction) -> bool:
    """To'langan tranzaksiyani bekor qilish (qaytarish) mumkinmi?

    Standart: har doim mumkin. Agar mahsulot qaytarib bo'lmaydigan bo'lsa
    (masalan darhol yuklab olinadigan fayl), bu yerda `False` qaytaring —
    Payme "-31007 unable to cancel" oladi.
    """
    return True


# =============================================================================
#   TRANZAKSIYA KUNDALIGI — Payme talab qiladi, demo tayyor.
#   O'z bazangizga o'tganingizda pastdagi funksiyalarni almashtiring
#   (namunalar fayl oxirida).
# =============================================================================

_conn: sqlite3.Connection | None = None
_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS payme_transactions (
    payme_id      TEXT    PRIMARY KEY,
    our_id        TEXT    NOT NULL,
    account_json  TEXT    NOT NULL,
    amount        INTEGER NOT NULL,
    state         INTEGER NOT NULL,
    payme_time    INTEGER NOT NULL,
    create_time   INTEGER NOT NULL,
    perform_time  INTEGER NOT NULL DEFAULT 0,
    cancel_time   INTEGER NOT NULL DEFAULT 0,
    reason        INTEGER
);
CREATE INDEX IF NOT EXISTS idx_payme_tx_create_time ON payme_transactions(create_time);

CREATE TABLE IF NOT EXISTS demo_orders (
    id            TEXT    PRIMARY KEY,
    amount_tiyin  INTEGER NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'pending',
    product       TEXT
);
"""


def _demo_db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        path = os.getenv("PAYME_DB_PATH", "payme_demo.db")
        _conn = sqlite3.connect(path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        if path != ":memory:":
            _conn.execute("PRAGMA journal_mode=WAL")
        _conn.executescript(SCHEMA)
        _conn.commit()
    return _conn


class _demo_write:
    """Yozish tranzaksiyasi (bir vaqtda bitta yozuvchi)."""

    def __enter__(self) -> sqlite3.Connection:
        _lock.acquire()
        self.conn = _demo_db()
        self.conn.execute("BEGIN IMMEDIATE")
        return self.conn

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            _lock.release()


def _row_to_transaction(row: sqlite3.Row) -> PaymeTransaction:
    import json

    return PaymeTransaction(
        payme_id=row["payme_id"],
        our_id=row["our_id"],
        account=json.loads(row["account_json"]),
        amount=int(row["amount"]),
        state=int(row["state"]),
        payme_time=int(row["payme_time"]),
        create_time=int(row["create_time"]),
        perform_time=int(row["perform_time"]),
        cancel_time=int(row["cancel_time"]),
        reason=row["reason"],
    )


def get_transaction(payme_id: str) -> PaymeTransaction | None:
    """Payme'ning tranzaksiya id'si bo'yicha yozuvni topadi."""
    row = _demo_db().execute(
        "SELECT * FROM payme_transactions WHERE payme_id = ? LIMIT 1", (payme_id,)
    ).fetchone()
    return _row_to_transaction(row) if row else None


def get_active_transaction_for_account(account: dict[str, Any]) -> PaymeTransaction | None:
    """Shu hisob uchun hali bekor qilinmagan tranzaksiya bormi?

    CreateTransaction bitta buyurtmaga ikkita PARALLEL faol tranzaksiya
    ochilishining oldini olish uchun ishlatadi.
    """
    import json

    order_id = account.get("order_id")
    rows = _demo_db().execute(
        "SELECT * FROM payme_transactions WHERE state IN (?, ?)",
        (STATE_PENDING, STATE_PAID),
    ).fetchall()
    for row in rows:
        acc = json.loads(row["account_json"])
        if acc.get("order_id") == order_id:
            return _row_to_transaction(row)
    return None


def create_transaction(
    payme_id: str,
    payme_time: int,
    amount: int,
    account: dict[str, Any],
) -> PaymeTransaction:
    """Yangi tranzaksiya yozuvini yaratadi (state=PENDING).

    `create_time` sizning serveringizning HOZIRGI vaqti bo'ladi — Payme
    yuborgan `payme_time` esa faqat 12-soatlik muddatni hisoblash uchun
    saqlanadi. Bu ikkalasi doim bir xil emas.
    """
    import json

    now = int(datetime.now(timezone.utc).timestamp() * 1000)

    with _demo_write() as conn:
        conn.execute(
            """INSERT INTO payme_transactions
                   (payme_id, our_id, account_json, amount, state,
                    payme_time, create_time)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (payme_id, payme_id, json.dumps(account), amount, STATE_PENDING, payme_time, now),
        )

    return PaymeTransaction(
        payme_id=payme_id,
        our_id=payme_id,
        account=account,
        amount=amount,
        state=STATE_PENDING,
        payme_time=payme_time,
        create_time=now,
    )


def mark_performed(payme_id: str) -> PaymeTransaction | None:
    """Tranzaksiyani "to'langan" qiladi (state: PENDING -> PAID).

    Faqat HAQIQATAN o'tkazgan chaqiruv yangilangan yozuvni qaytaradi — aks
    holda (allaqachon PAID bo'lsa yoki topilmasa) `None` qaytadi.
    Bu — takroriy so'rovda `on_paid()` qayta chaqirilmasligi uchun MUHIM.
    """
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    with _demo_write() as conn:
        cur = conn.execute(
            """UPDATE payme_transactions
               SET state = ?, perform_time = ?
               WHERE payme_id = ? AND state = ?""",
            (STATE_PAID, now, payme_id, STATE_PENDING),
        )
        if cur.rowcount == 0:
            return None
    return get_transaction(payme_id)


def mark_cancelled(payme_id: str, reason: int) -> PaymeTransaction | None:
    """Tranzaksiyani bekor qiladi.

    PENDING -> CANCELLED, PAID -> CANCELLED_AFTER_PAID. Allaqachon bekor
    qilingan bo'lsa `None` qaytaradi (chaqiruvchi buni "idempotent — o'zgarish
    yo'q" deb tushunadi va mavjud yozuvni qaytaradi).
    """
    now = int(datetime.now(timezone.utc).timestamp() * 1000)

    current = get_transaction(payme_id)
    if current is None or current.state in (STATE_CANCELLED, STATE_CANCELLED_AFTER_PAID):
        return None

    new_state = STATE_CANCELLED_AFTER_PAID if current.state == STATE_PAID else STATE_CANCELLED

    with _demo_write() as conn:
        conn.execute(
            """UPDATE payme_transactions
               SET state = ?, cancel_time = ?, reason = ?
               WHERE payme_id = ?""",
            (new_state, now, reason, payme_id),
        )

    return get_transaction(payme_id)


def list_transactions(from_ms: int, to_ms: int) -> list[PaymeTransaction]:
    """`create_time` bo'yicha [from_ms, to_ms] oralig'idagi tranzaksiyalar."""
    rows = _demo_db().execute(
        "SELECT * FROM payme_transactions WHERE create_time BETWEEN ? AND ? "
        "ORDER BY create_time",
        (from_ms, to_ms),
    ).fetchall()
    return [_row_to_transaction(r) for r in rows]


def demo_create_order(order_id: str, amount_tiyin: int, product: str = "") -> None:
    """Namuna uchun buyurtma yaratadi (demo_orders jadvaliga)."""
    with _demo_write() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO demo_orders (id, amount_tiyin, status, product) "
            "VALUES (?, ?, 'pending', ?)",
            (order_id, amount_tiyin, product),
        )


def reset_db_for_tests() -> None:
    """Testlar uchun ulanishni tozalaydi."""
    global _conn
    if _conn is not None:
        _conn.close()
    _conn = None


# =============================================================================
#   O'Z BAZANGIZ UCHUN NAMUNA — nusxa oling va yuqoridagi tranzaksiya
#   kundaligi funksiyalari o'rniga qo'ying (PostgreSQL, psycopg misolida).
# =============================================================================
#
#   import psycopg
#   from psycopg.rows import dict_row
#
#   def _pg():
#       return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
#
#   def get_transaction(payme_id):
#       with _pg() as c, c.cursor() as cur:
#           cur.execute("SELECT * FROM payme_transactions WHERE payme_id=%s", (payme_id,))
#           row = cur.fetchone()
#       if not row:
#           return None
#       return PaymeTransaction(
#           payme_id=row["payme_id"], our_id=row["our_id"],
#           account=row["account_json"], amount=row["amount"], state=row["state"],
#           payme_time=row["payme_time"], create_time=row["create_time"],
#           perform_time=row["perform_time"], cancel_time=row["cancel_time"],
#           reason=row["reason"],
#       )
#
#   def mark_performed(payme_id):
#       with _pg() as c, c.cursor() as cur:
#           cur.execute(
#               "UPDATE payme_transactions SET state=2, perform_time=%s "
#               "WHERE payme_id=%s AND state=1",
#               (now_ms(), payme_id),
#           )
#           if cur.rowcount == 0:      # <- atomar, poyga yo'q
#               return None
#       return get_transaction(payme_id)
#
#   find_account(), on_paid(), on_cancelled() — bularni O'ZGARTIRMAYSIZ (ular
#   ledger emas, sizning biznesingiz) — faqat ichlarida o'z ORM/SQL'ingizni
#   ishlatasiz (Click'dagi click_orders.py bilan bir xil naqsh).
# =============================================================================
