"""
===============================================================================
  SIZ FAQAT SHU FAYLNI TAHRIRLAYSIZ
===============================================================================

Bu fayl Click integratsiyasini SIZNING bazangiz bilan bog'laydi.
Qolgan fayllarga (click_prepare.py, click_complete.py, click_signature.py,
click_config.py) tegish shart emas — ular o'zgarmaydi.

Click integratsiyasi sizning tizimingiz haqida atigi 5 narsani bilishi kerak:

    BAZA:
      1. find_order(merchant_trans_id)         -> buyurtmani toping
      2. mark_paid(order, click_trans_id)      -> "to'landi" deb belgilang
      3. mark_cancelled(order, click_trans_id) -> "bekor qilindi" deb belgilang

    HODISALAR:
      4. on_paid(order)      -> to'lov o'tgach mahsulotni bering
      5. on_cancelled(order) -> to'lov bekor bo'lganda (ixtiyoriy)

Hozir bu yerda SQLite bilan ishlaydigan NAMUNA turibdi — klon qilib darrov
sinab ko'rishingiz uchun. O'z bazangizga moslash uchun quyidagi 5 funksiyaning
ichini o'zgartiring, xolos.

PostgreSQL, MySQL, Django ORM va SQLAlchemy uchun tayyor namunalar shu
faylning oxirida (izohda) berilgan — nusxa olib qo'yavering.
===============================================================================
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

logger = logging.getLogger("click")


# --- Holatlar ----------------------------------------------------------------
# Bazangizda boshqacha nomlangan bo'lsa (masalan "pending_payment"), find_order
# ichida shu uchtasiga o'girib bering.

STATUS_PENDING = "pending"      # to'lov kutilmoqda
STATUS_PAID = "paid"            # to'langan
STATUS_CANCELLED = "cancelled"  # bekor qilingan / amalga oshmagan


@dataclass
class Order:
    """Click integratsiyasi buyurtmangizdan kutadigan ma'lumot.

    id
        Bazangizdagi raqamli id. Aynan shu qiymat Click'ga
        `merchant_prepare_id` bo'lib ketadi va complete'da qaytib keladi.

    merchant_trans_id
        To'lov havolasida `transaction_param` bo'lib ketadigan satr
        (masalan "ORD42"). Bazangizda UNIKAL bo'lishi SHART.

    amount
        Kutilayotgan summa (so'mda). Click yuborgan summa shu bilan
        solishtiriladi — mos kelmasa to'lov rad etiladi.

    status
        Yuqoridagi STATUS_* qiymatlaridan biri.

    extra
        Sizga kerak bo'ladigan ixtiyoriy ma'lumot (user_id, chat_id,
        product_id...). Click bu bilan ishlamaydi — u faqat on_paid()
        ichida sizga kerak bo'ladi.
    """

    id: int
    merchant_trans_id: str
    amount: Decimal
    status: str
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Pulni har doim Decimal'da ushlaymiz — float bilan hisoblash
        # yaxlitlash xatolariga olib keladi.
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))


# =============================================================================
#  1-3: BAZA BILAN ISHLASH
# =============================================================================


def find_order(merchant_trans_id: str) -> Order | None:
    """Buyurtmani `merchant_trans_id` bo'yicha topadi. Topilmasa None.

    Click prepare va complete so'rovlarida shu funksiya chaqiriladi.
    """
    row = _db().execute(
        "SELECT * FROM orders WHERE merchant_trans_id = ? LIMIT 1",
        (str(merchant_trans_id),),
    ).fetchone()

    if row is None:
        return None

    return Order(
        id=int(row["id"]),
        merchant_trans_id=str(row["merchant_trans_id"]),
        amount=Decimal(str(row["amount"])),
        status=str(row["status"]),
        # on_paid() da nima kerak bo'lsa, shu yerga soling:
        extra={"user_id": row["user_id"], "product": row["product"]},
    )


def mark_paid(order: Order, click_trans_id: str) -> bool:
    """Buyurtmani "to'langan" deb belgilaydi.

    ┌───────────────────────────────────────────────────────────────────────┐
    │  DIQQAT — BU YERDA XATO QILISH OSON:                                  │
    │                                                                       │
    │  Faqat SHU chaqiruv holatni pending -> paid o'tkazgan bo'lsa `True`   │
    │  qaytaring. Allaqachon to'langan bo'lsa `False` qaytaring.            │
    │                                                                       │
    │  Nega? Click javobni ololmasa complete'ni QAYTA yuboradi (ba'zan bir  │
    │  vaqtda). `True` qaytgan chaqiruvda on_paid() ishlaydi. Agar har      │
    │  safar `True` qaytarsangiz — mahsulot ikki marta beriladi.            │
    │                                                                       │
    │  To'g'ri yo'l — shartni SQL'ning O'ZIGA qo'ying (atomar bo'ladi):     │
    │      UPDATE ... SET status='paid' WHERE id=? AND status='pending'     │
    │  va o'zgargan qatorlar sonini (rowcount) qaytaring.                   │
    │                                                                       │
    │  NOTO'G'RI (poyga bor — ikkalasi ham True olishi mumkin):             │
    │      if order.status == 'pending':      # <- avval o'qib             │
    │          UPDATE ... SET status='paid'   # <- keyin yozish            │
    │          return True                                                  │
    └───────────────────────────────────────────────────────────────────────┘
    """
    with _write() as conn:
        cur = conn.execute(
            """UPDATE orders
               SET status = ?, click_trans_id = ?, paid_at = ?
               WHERE id = ? AND status = ?""",
            (
                STATUS_PAID,
                str(click_trans_id),
                datetime.now(timezone.utc).isoformat(),
                int(order.id),
                STATUS_PENDING,
            ),
        )
        return cur.rowcount > 0


def mark_cancelled(order: Order, click_trans_id: str) -> None:
    """Buyurtmani "bekor qilingan" deb belgilaydi.

    Click foydalanuvchi to'lovni bekor qilganini yoki xato bo'lganini
    aytganda chaqiriladi.
    """
    with _write() as conn:
        conn.execute(
            """UPDATE orders
               SET status = ?, click_trans_id = ?, paid_at = NULL
               WHERE id = ? AND status = ?""",
            (STATUS_CANCELLED, str(click_trans_id), int(order.id), STATUS_PENDING),
        )


# =============================================================================
#  4-5: HODISALAR — "to'langanda nima bo'lsin?"
# =============================================================================


def on_paid(order: Order) -> None:
    """To'lov tasdiqlangach BIR MARTA chaqiriladi. Mahsulotni shu yerda bering.

    Masalan:
        bot.send_message(order.extra["chat_id"], "To'lovingiz qabul qilindi!")
        give_access(order.extra["user_id"], order.extra["product"])

    Ikki muhim eslatma:

    1. Bu yerda UZOQ ish qilmang — Click javobni kutib turadi va kechiksangiz
       so'rovni qayta yuboradi. Og'ir ishni navbatga (queue/celery) qo'ying.

    2. Bu funksiya xato bersa, to'lov baribir "paid" bo'lib qoladi (pul
       yechilgan-ku) va xato logga yoziladi. Click'ga xato qaytarish foyda
       bermaydi: u qayta urganda buyurtma allaqachon "paid" bo'lgani uchun
       bu funksiya qayta ishlamaydi. Shuning uchun loglarni kuzatib boring.
    """
    logger.info(
        "TO'LANDI: %s, summa=%s, user_id=%s, mahsulot=%s",
        order.merchant_trans_id,
        order.amount,
        order.extra.get("user_id"),
        order.extra.get("product"),
    )


def on_cancelled(order: Order) -> None:
    """To'lov bekor qilinganda chaqiriladi (ixtiyoriy — bo'sh qoldirsangiz ham bo'ladi)."""
    logger.info("BEKOR QILINDI: %s", order.merchant_trans_id)


# =============================================================================
#  Quyidagisi — faqat yuqoridagi SQLite NAMUNASI uchun kerak.
#  O'z bazangizga o'tganingizda bu qismni o'chirib tashlang.
# =============================================================================

_conn: sqlite3.Connection | None = None
_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_trans_id TEXT    NOT NULL UNIQUE,
    amount            TEXT    NOT NULL,
    status            TEXT    NOT NULL DEFAULT 'pending',
    click_trans_id    TEXT,
    paid_at           TEXT,
    created_at        TEXT    NOT NULL,
    -- o'z ustunlaringiz:
    user_id           INTEGER,
    product           TEXT
);
"""


def _db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        path = os.getenv("CLICK_DB_PATH", "click_demo.db")
        _conn = sqlite3.connect(path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        if path != ":memory:":
            # WAL — webhook'lar parallel kelganda o'qish/yozish bloklanmasin.
            _conn.execute("PRAGMA journal_mode=WAL")
        _conn.executescript(SCHEMA)
        _conn.commit()
    return _conn


class _write:
    """Yozish tranzaksiyasi (bir vaqtda bitta yozuvchi)."""

    def __enter__(self) -> sqlite3.Connection:
        _lock.acquire()
        self.conn = _db()
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


def create_order(
    merchant_trans_id: str,
    amount: Decimal | int | float | str,
    user_id: int | None = None,
    product: str | None = None,
) -> Order:
    """Namuna uchun buyurtma yaratadi.

    O'z tizimingizda buyurtma allaqachon bazangizda bo'ladi — bu funksiya
    kerak emas. Faqat `merchant_trans_id` ustunini qo'shib qo'ying.
    """
    with _write() as conn:
        cur = conn.execute(
            """INSERT INTO orders
                   (merchant_trans_id, amount, status, created_at, user_id, product)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                str(merchant_trans_id),
                str(Decimal(str(amount))),
                STATUS_PENDING,
                datetime.now(timezone.utc).isoformat(),
                user_id,
                product,
            ),
        )
        new_id = int(cur.lastrowid or 0)

    return Order(
        id=new_id,
        merchant_trans_id=str(merchant_trans_id),
        amount=Decimal(str(amount)),
        status=STATUS_PENDING,
        extra={"user_id": user_id, "product": product},
    )


def reset_db_for_tests() -> None:
    """Testlar uchun ulanishni tozalaydi."""
    global _conn
    if _conn is not None:
        _conn.close()
    _conn = None


# =============================================================================
#  O'Z BAZANGIZ UCHUN NAMUNALAR — nusxa oling va yuqoridagi funksiyalar
#  o'rniga qo'ying.
# =============================================================================
#
# ─── PostgreSQL (psycopg 3) ──────────────────────────────────────────────────
#
#   import psycopg
#   from psycopg.rows import dict_row
#
#   def _conn():
#       return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
#
#   def find_order(merchant_trans_id):
#       with _conn() as c, c.cursor() as cur:
#           cur.execute(
#               "SELECT id, merchant_trans_id, price, status, user_id "
#               "FROM orders WHERE merchant_trans_id = %s",
#               (merchant_trans_id,),
#           )
#           row = cur.fetchone()
#       if row is None:
#           return None
#       return Order(
#           id=row["id"],
#           merchant_trans_id=row["merchant_trans_id"],
#           amount=row["price"],
#           # bazangizdagi holatni bizning uchta holatga o'giring:
#           status={"new": STATUS_PENDING, "pending_payment": STATUS_PENDING,
#                   "paid": STATUS_PAID}.get(row["status"], STATUS_CANCELLED),
#           extra={"user_id": row["user_id"]},
#       )
#
#   def mark_paid(order, click_trans_id):
#       with _conn() as c, c.cursor() as cur:
#           cur.execute(
#               "UPDATE orders SET status='paid', click_trans_id=%s, paid_at=NOW() "
#               "WHERE id=%s AND status='pending_payment'",
#               (click_trans_id, order.id),
#           )
#           return cur.rowcount > 0        # <- atomar, poyga yo'q
#
#   def mark_cancelled(order, click_trans_id):
#       with _conn() as c, c.cursor() as cur:
#           cur.execute(
#               "UPDATE orders SET status='cancelled', click_trans_id=%s "
#               "WHERE id=%s AND status='pending_payment'",
#               (click_trans_id, order.id),
#           )
#
#
# ─── MySQL (mysql-connector / PyMySQL) ───────────────────────────────────────
#
#   Yuqoridagi PostgreSQL namunasi bilan bir xil, faqat:
#     - `%s` o'rniga ham `%s` ishlatiladi (PyMySQL) — o'zgarish yo'q
#     - NOW() o'rniga NOW() (bir xil)
#     - cur.rowcount ham xuddi shunday ishlaydi
#
#
# ─── Django ORM ──────────────────────────────────────────────────────────────
#
#   from myapp.models import Order as OrderModel
#
#   def find_order(merchant_trans_id):
#       o = OrderModel.objects.filter(merchant_trans_id=merchant_trans_id).first()
#       if o is None:
#           return None
#       return Order(id=o.id, merchant_trans_id=o.merchant_trans_id,
#                    amount=o.price, status=o.status,
#                    extra={"user_id": o.user_id})
#
#   def mark_paid(order, click_trans_id):
#       # .update() atomar — poyga yo'q
#       updated = OrderModel.objects.filter(id=order.id, status="pending").update(
#           status="paid", click_trans_id=click_trans_id, paid_at=timezone.now()
#       )
#       return updated > 0
#
#
# ─── SQLAlchemy ──────────────────────────────────────────────────────────────
#
#   def mark_paid(order, click_trans_id):
#       with Session() as s:
#           result = s.execute(
#               update(OrderModel)
#               .where(OrderModel.id == order.id, OrderModel.status == "pending")
#               .values(status="paid", click_trans_id=click_trans_id)
#           )
#           s.commit()
#           return result.rowcount > 0
#
# =============================================================================
