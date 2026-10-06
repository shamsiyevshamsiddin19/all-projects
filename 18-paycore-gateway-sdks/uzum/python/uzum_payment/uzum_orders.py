"""
===============================================================================
  SIZ FAQAT SHU FAYLNI TAHRIRLAYSIZ
===============================================================================

Bu fayl Uzum Bank integratsiyasini SIZNING bazangiz bilan bog'laydi.
Qolgan fayllarga (uzum_methods.py, uzum_auth.py, uzum_config.py,
uzum_errors.py) tegish shart emas — ular o'zgarmaydi.

Uzum Bank Payme'ga o'xshaydi: bitta "hisob" (sizning buyurtmangiz) va bitta
"tranzaksiya" (Uzum Bank ochadigan yozuv) bor. Farqi — holatlar soni uchta
(Payme'da to'rtta: 1/2/-1/-2), timeout 30 daqiqa (Payme'da 12 soat), va eng
muhimi: TAKRORIY /create yoki /confirm so'rovida Uzum Bank aniq XATO kutadi
(idempotent muvaffaqiyat emas) — bu quyidagi funksiyalarda hisobga olingan.

Shuning uchun bu faylda IKKI GURUH funksiya bor:

    HISOBINGIZGA ULANISH (siz yozasiz):
      1. find_account(params)         -> buyurtmangizni toping
      2. on_confirmed(transaction)    -> to'lov o'tgach mahsulotni bering
      3. on_reversed(transaction)     -> bekor qilinganda (ixtiyoriy)
      4. can_reverse(transaction)     -> tasdiqlangandan keyin bekor qilish
                                          mumkinmi (ixtiyoriy, standart: ha)

    TRANZAKSIYA KUNDALIGI (Uzum Bank talab qiladi, demo tayyor turibdi):
      Har bir tranzaksiyani vaqti va holati bilan saqlab turish — Uzum
      Bank'ning protokol talabi (/status shuni so'raydi). Hozir SQLite
      namunasi turibdi, production'da almashtirasiz (fayl oxiriga qarang).
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

logger = logging.getLogger("uzum")

# --- Tranzaksiya holatlari -----------------------------------------------
# Bu qiymatlarni Uzum Bank belgilagan (status maydonida aynan shu satrlar
# ishlatiladi) — o'zgartirmang.

STATE_CREATED = "CREATED"      # yaratilgan, hali tasdiqlanmagan
STATE_CONFIRMED = "CONFIRMED"  # to'langan (mahsulot berilgan)
STATE_REVERSED = "REVERSED"    # bekor qilingan (to'lanmasdan turib YOKI qaytarilgan)

# 30 daqiqa — shuncha vaqt ichida tasdiqlanmagan (/confirm kelmagan)
# tranzaksiya "muvaffaqiyatsiz" hisoblanadi. Bu — Uzum Bank hujjatida aniq
# yozilgan qoida: BIZ o'zimiz shu muddatni kuzatishimiz kerak (Uzum Bank
# alohida "bekor qilish" so'rovi yubormaydi).
TRANSACTION_TIMEOUT_MS = 30 * 60 * 1000


@dataclass
class UzumAccount:
    """`find_account()` qaytaradigan narsa — sizning buyurtmangiz haqida.

    id
        Bazangizdagi buyurtma id'si.

    amount
        Kutilayotgan summa TIYINDA (1 so'm = 100 tiyin).

    payable
        Buyurtma hali to'lov kutyaptimi? Allaqachon to'langan/bekor
        qilingan bo'lsa `False` qiling.

    extra
        `on_confirmed()` ichida kerak bo'ladigan hamma narsa.
    """

    id: int | str
    amount: int
    payable: bool = True
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class UzumTransaction:
    """Uzum Bank tranzaksiya yozuvi — protokol talab qiladigan kundalik yozuvi."""

    trans_id: str                 # Uzum Bank bergan UUID
    params: dict[str, Any]        # foydalanuvchi kiritgan hisob maydonlari
    amount: int
    state: str
    create_time: int
    confirm_time: int = 0
    reverse_time: int = 0
    our_id: str = ""
    account_extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.our_id:
            self.our_id = self.trans_id


# =============================================================================
#   HISOBINGIZGA ULANISH — shu 4 ta funksiyani o'zgartirasiz
# =============================================================================


def find_account(params: dict[str, Any]) -> UzumAccount | None:
    """Uzum Bank yuborgan `params` maydonlari bo'yicha buyurtmani topadi.

    `params` — foydalanuvchi Uzum Bank ilovasida kiritgan qiymatlar,
    masalan `{"account": "42"}`. Aniq qaysi maydon ishlatilishi Uzum Bank
    kabinetida xizmatingizni sozlaganda siz belgilaysiz.

    Topilmasa `None` qaytaring — Uzum Bank "10007" oladi.
    """
    order_id = params.get("account")
    if order_id is None:
        return None

    row = _demo_db().execute(
        "SELECT * FROM demo_orders WHERE id = ? LIMIT 1", (str(order_id),)
    ).fetchone()

    if row is None:
        return None

    return UzumAccount(
        id=row["id"],
        amount=int(row["amount_tiyin"]),
        payable=(row["status"] == "pending"),
        extra={"product": row["product"]},
    )


def on_confirmed(transaction: UzumTransaction) -> None:
    """To'lov tasdiqlangach BIR MARTA chaqiriladi. Mahsulotni shu yerda bering.

    DIQQAT: Uzum Bank oqimida pul /confirm kelguncha ALLAQACHON yechilgan
    bo'ladi (Uzum foydalanuvchidan pulni /create dan keyin, /confirm dan
    OLDIN yechadi). Shuning uchun bu funksiya xato bersa ham, pul qaytarib
    berilmaydi — faqat mahsulot berish jarayoni chalasi qoladi. Xatoni
    logdan kuzatib, qo'lda hal qilasiz (yoki keyinroq /reverse orqali
    qaytarasiz).
    """
    order_id = transaction.params.get("account")
    with _demo_write() as conn:
        conn.execute(
            "UPDATE demo_orders SET status = 'paid' WHERE id = ?", (str(order_id),)
        )
    logger.info(
        "TASDIQLANDI: order=%s, summa=%s tiyin, trans_id=%s",
        order_id,
        transaction.amount,
        transaction.trans_id,
    )


def on_reversed(transaction: UzumTransaction) -> None:
    """Tranzaksiya bekor qilinganda (yoki tasdiqlangandan keyin qaytarilganda)
    chaqiriladi.

    Agar bekor qilish CONFIRMED holatidan bo'lsa — bu QAYTARISH (pul
    allaqachon berilgan edi). Shu holatda mahsulotga ruxsatni bekor qiling.
    """
    order_id = transaction.params.get("account")
    with _demo_write() as conn:
        conn.execute(
            "UPDATE demo_orders SET status = 'cancelled' WHERE id = ?", (str(order_id),)
        )
    logger.info("BEKOR QILINDI: order=%s, trans_id=%s", order_id, transaction.trans_id)


def can_reverse(transaction: UzumTransaction) -> bool:
    """Tasdiqlangan (CONFIRMED) tranzaksiyani bekor qilish (qaytarish) mumkinmi?

    Standart: har doim mumkin. Mahsulot qaytarib bo'lmaydigan bo'lsa,
    `False` qaytaring — Uzum Bank "10017" oladi.
    """
    return True


# =============================================================================
#   TRANZAKSIYA KUNDALIGI — Uzum Bank talab qiladi, demo tayyor.
#   O'z bazangizga o'tganingizda pastdagi funksiyalarni almashtiring
#   (namunalar fayl oxirida).
# =============================================================================

_conn: sqlite3.Connection | None = None
_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS uzum_transactions (
    trans_id      TEXT    PRIMARY KEY,
    our_id        TEXT    NOT NULL,
    params_json   TEXT    NOT NULL,
    amount        INTEGER NOT NULL,
    state         TEXT    NOT NULL,
    create_time   INTEGER NOT NULL,
    confirm_time  INTEGER NOT NULL DEFAULT 0,
    reverse_time  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_uzum_tx_create_time ON uzum_transactions(create_time);

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
        path = os.getenv("UZUM_DB_PATH", "uzum_demo.db")
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


def _row_to_transaction(row: sqlite3.Row) -> UzumTransaction:
    import json

    return UzumTransaction(
        trans_id=row["trans_id"],
        our_id=row["our_id"],
        params=json.loads(row["params_json"]),
        amount=int(row["amount"]),
        state=row["state"],
        create_time=int(row["create_time"]),
        confirm_time=int(row["confirm_time"]),
        reverse_time=int(row["reverse_time"]),
    )


def get_transaction(trans_id: str) -> UzumTransaction | None:
    """Uzum Bank'ning tranzaksiya id'si (`transId`) bo'yicha yozuvni topadi."""
    row = _demo_db().execute(
        "SELECT * FROM uzum_transactions WHERE trans_id = ? LIMIT 1", (trans_id,)
    ).fetchone()
    return _row_to_transaction(row) if row else None


def get_active_transaction_for_account(params: dict[str, Any]) -> UzumTransaction | None:
    """Shu hisob uchun hali bekor qilinmagan tranzaksiya bormi?

    /create bitta buyurtmaga ikkita PARALLEL faol tranzaksiya ochilishining
    oldini olish uchun ishlatadi.
    """
    import json

    order_id = params.get("account")
    rows = _demo_db().execute(
        "SELECT * FROM uzum_transactions WHERE state IN (?, ?)",
        (STATE_CREATED, STATE_CONFIRMED),
    ).fetchall()
    for row in rows:
        p = json.loads(row["params_json"])
        if p.get("account") == order_id:
            return _row_to_transaction(row)
    return None


def create_transaction(trans_id: str, amount: int, params: dict[str, Any]) -> UzumTransaction:
    """Yangi tranzaksiya yozuvini yaratadi (state=CREATED)."""
    import json

    now = int(datetime.now(timezone.utc).timestamp() * 1000)

    with _demo_write() as conn:
        conn.execute(
            """INSERT INTO uzum_transactions
                   (trans_id, our_id, params_json, amount, state, create_time)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (trans_id, trans_id, json.dumps(params), amount, STATE_CREATED, now),
        )

    return UzumTransaction(
        trans_id=trans_id,
        our_id=trans_id,
        params=params,
        amount=amount,
        state=STATE_CREATED,
        create_time=now,
    )


def mark_confirmed(trans_id: str) -> UzumTransaction | None:
    """Tranzaksiyani "tasdiqlangan" qiladi (state: CREATED -> CONFIRMED).

    Faqat HAQIQATAN o'tkazgan chaqiruv yangilangan yozuvni qaytaradi — aks
    holda `None`. Bu — takroriy so'rovda `on_confirmed()` qayta
    chaqirilmasligi uchun MUHIM (garchi Uzum Bank protokoli bo'yicha
    takroriy /confirm asosan xato bilan rad etilsa ham, himoya ortiqcha
    emas — masalan parallel so'rov holatida).
    """
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    with _demo_write() as conn:
        cur = conn.execute(
            """UPDATE uzum_transactions
               SET state = ?, confirm_time = ?
               WHERE trans_id = ? AND state = ?""",
            (STATE_CONFIRMED, now, trans_id, STATE_CREATED),
        )
        if cur.rowcount == 0:
            return None
    return get_transaction(trans_id)


def mark_reversed(trans_id: str) -> UzumTransaction | None:
    """Tranzaksiyani bekor qiladi (CREATED yoki CONFIRMED -> REVERSED).

    Allaqachon REVERSED bo'lsa `None` qaytaradi.
    """
    now = int(datetime.now(timezone.utc).timestamp() * 1000)

    current = get_transaction(trans_id)
    if current is None or current.state == STATE_REVERSED:
        return None

    with _demo_write() as conn:
        conn.execute(
            """UPDATE uzum_transactions
               SET state = ?, reverse_time = ?
               WHERE trans_id = ?""",
            (STATE_REVERSED, now, trans_id),
        )

    return get_transaction(trans_id)


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
#   def get_transaction(trans_id):
#       with _pg() as c, c.cursor() as cur:
#           cur.execute("SELECT * FROM uzum_transactions WHERE trans_id=%s", (trans_id,))
#           row = cur.fetchone()
#       if not row:
#           return None
#       return UzumTransaction(
#           trans_id=row["trans_id"], our_id=row["our_id"], params=row["params_json"],
#           amount=row["amount"], state=row["state"], create_time=row["create_time"],
#           confirm_time=row["confirm_time"], reverse_time=row["reverse_time"],
#       )
#
#   def mark_confirmed(trans_id):
#       with _pg() as c, c.cursor() as cur:
#           cur.execute(
#               "UPDATE uzum_transactions SET state='CONFIRMED', confirm_time=%s "
#               "WHERE trans_id=%s AND state='CREATED'",
#               (now_ms(), trans_id),
#           )
#           if cur.rowcount == 0:      # <- atomar, poyga yo'q
#               return None
#       return get_transaction(trans_id)
#
#   find_account(), on_confirmed(), on_reversed() — bularni O'ZGARTIRMAYSIZ
#   (ular ledger emas, sizning biznesingiz) — faqat ichlarida o'z
#   ORM/SQL'ingizni ishlatasiz (Click/Payme'dagi bilan bir xil naqsh).
# =============================================================================
