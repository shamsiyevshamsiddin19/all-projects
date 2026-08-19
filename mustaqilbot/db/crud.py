from __future__ import annotations
import datetime as dt
from sqlalchemy import select, func, update, desc, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import async_session, engine, Base
from db.models import User, Order, Payment, Referral, Setting, Rating

# Mavjud jadvallarga yangi ustunlar (create_all ustun qo'shmaydi)
_MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS otm VARCHAR(256)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS source VARCHAR(32)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS marketing_ok BOOLEAN DEFAULT TRUE",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS source_text TEXT",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS revisions INTEGER DEFAULT 0",
]


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in _MIGRATIONS:
            try:
                await conn.execute(sa_text(stmt))
            except Exception:
                pass


# ─────────────────── USER ───────────────────

async def get_or_create_user(
    user_id: int, username: str | None = None,
    full_name: str | None = None, referred_by: int | None = None,
) -> User:
    async with async_session() as s:
        u = await s.get(User, user_id)
        if u is None:
            u = User(
                id=user_id,
                username=username,
                full_name=full_name,
                referral_code=User.make_code(),
                referred_by=referred_by,
            )
            s.add(u)
            if referred_by:
                ref = Referral(referrer_id=referred_by, referee_id=user_id)
                s.add(ref)
                ref_user = await s.get(User, referred_by)
                if ref_user:
                    ref_user.referral_count += 1
            await s.commit()
            await s.refresh(u)
            u._is_new = True  # start handler welcome-bonus uchun
        else:
            u.last_active = dt.datetime.utcnow()
            if username:
                u.username = username
            if full_name:
                u.full_name = full_name
            await s.commit()
            await s.refresh(u)
        return u


async def get_user(user_id: int) -> User | None:
    async with async_session() as s:
        return await s.get(User, user_id)


async def get_user_by_code(code: str) -> User | None:
    async with async_session() as s:
        result = await s.execute(select(User).where(User.referral_code == code))
        return result.scalar_one_or_none()


async def update_balance(user_id: int, delta: int) -> int:
    async with async_session() as s:
        u = await s.get(User, user_id)
        if u is None:
            return 0
        u.balance = max(0, u.balance + delta)
        await s.commit()
        return u.balance


async def get_balance(user_id: int) -> int:
    async with async_session() as s:
        u = await s.get(User, user_id)
        return u.balance if u else 0


async def ban_user(user_id: int, banned: bool = True):
    async with async_session() as s:
        u = await s.get(User, user_id)
        if u:
            u.is_banned = banned
            await s.commit()


# ─────────────────── ORDER ───────────────────

async def create_order(
    user_id: int, doc_type: str, topic: str,
    details: dict, language: str, page_count: int,
    price: int, paid_from: str,
) -> Order:
    async with async_session() as s:
        o = Order(
            user_id=user_id, doc_type=doc_type, topic=topic,
            details=details, language=language, page_count=page_count,
            price=price, paid_from=paid_from,
        )
        s.add(o)
        await s.commit()
        await s.refresh(o)
        return o


async def get_order(order_id: int) -> Order | None:
    async with async_session() as s:
        return await s.get(Order, order_id)


async def set_order_status(order_id: int, status: str, **kwargs):
    async with async_session() as s:
        o = await s.get(Order, order_id)
        if o:
            o.status = status
            for k, v in kwargs.items():
                setattr(o, k, v)
            if status == "done":
                o.completed_at = dt.datetime.utcnow()
            await s.commit()


async def get_user_orders(user_id: int, limit: int = 20) -> list[dict]:
    async with async_session() as s:
        rows = (await s.execute(
            select(Order).where(Order.user_id == user_id)
            .order_by(desc(Order.created_at)).limit(limit)
        )).scalars().all()
        return [_order_dict(r) for r in rows]


def _order_dict(o: Order) -> dict:
    return {
        "id": o.id, "doc_type": o.doc_type, "topic": o.topic,
        "status": o.status, "price": o.price, "file_format": o.file_format,
        "tg_file_id": o.tg_file_id, "created_at": o.created_at,
        "completed_at": o.completed_at, "ai_provider": o.ai_provider,
        "page_count": o.page_count, "language": o.language,
    }


# ─────────────────── RATING / OTM / STATISTIKA ───────────────────

async def add_rating(order_id: int, user_id: int, stars: int) -> None:
    async with async_session() as s:
        r = (await s.execute(
            select(Rating).where(Rating.order_id == order_id))).scalar_one_or_none()
        if r is None:
            s.add(Rating(order_id=order_id, user_id=user_id, stars=stars))
        else:
            r.stars = stars
        await s.commit()


async def set_rating_comment(order_id: int, comment: str) -> None:
    async with async_session() as s:
        r = (await s.execute(
            select(Rating).where(Rating.order_id == order_id))).scalar_one_or_none()
        if r:
            r.comment = comment[:1000]
            await s.commit()


async def save_user_otm(user_id: int, otm: str) -> None:
    async with async_session() as s:
        u = await s.get(User, user_id)
        if u:
            u.otm = otm[:256]
            await s.commit()


async def increment_revisions(order_id: int) -> int:
    async with async_session() as s:
        o = await s.get(Order, order_id)
        if not o:
            return 0
        o.revisions = (o.revisions or 0) + 1
        await s.commit()
        return o.revisions


async def recover_stuck_orders() -> list[dict]:
    """Restart paytida 'generating' holatida osilib qolgan buyurtmalarni topib,
    narxni foydalanuvchi balansiga qaytaradi va 'refunded' qiladi.
    Qaytarilganlar ro'yxatini beradi (foydalanuvchini ogohlantirish uchun)."""
    async with async_session() as s:
        rows = (await s.execute(
            select(Order).where(Order.status == "generating")
        )).scalars().all()
        recovered = []
        for o in rows:
            u = await s.get(User, o.user_id)
            if u and o.price > 0:
                u.balance += o.price
                if u.total_spent >= o.price:
                    u.total_spent -= o.price
            o.status = "refunded"
            o.error_msg = "Server qayta ishga tushdi — avtomatik qaytarildi"
            recovered.append({"user_id": o.user_id, "order_id": o.id,
                              "price": o.price, "topic": o.topic,
                              "doc_type": o.doc_type})
        await s.commit()
        return recovered


async def public_stats() -> dict:
    """Foydalanuvchiga ko'rsatiladigan jonli statistika (halol raqamlar)."""
    async with async_session() as s:
        done = await s.scalar(
            select(func.count(Order.id)).where(Order.status == "done")) or 0
        users = await s.scalar(select(func.count(User.id))) or 0
        return {"done_orders": done, "users": users}


async def avg_rating() -> tuple[float, int]:
    """(o'rtacha yulduz, jami baho soni) — ishonch signali uchun."""
    async with async_session() as s:
        cnt = await s.scalar(select(func.count(Rating.id))) or 0
        if cnt == 0:
            return 0.0, 0
        avg = await s.scalar(select(func.avg(Rating.stars))) or 0
        return round(float(avg), 1), cnt


async def get_setting(key: str) -> str | None:
    """Bitta sozlamani (string) o'qish — masalan namuna fayl tg_file_id si."""
    async with async_session() as s:
        obj = await s.get(Setting, key)
        return obj.value if obj else None


async def set_setting(key: str, value: str) -> None:
    async with async_session() as s:
        obj = await s.get(Setting, key)
        if obj is None:
            s.add(Setting(key=key, value=value))
        else:
            obj.value = value
            obj.updated_at = dt.datetime.utcnow()
        await s.commit()


# ─────────────────── PAYMENT ───────────────────

async def create_payment(
    user_id: int, amount: int,
    order_id: int | None = None, payment_type: str = "click",
) -> Payment:
    """Payment yozuvini yaratadi. merchant_trans_id avval bo'sh, keyin MUST<id>."""
    async with async_session() as s:
        p = Payment(
            user_id=user_id, order_id=order_id,
            merchant_trans_id=None,  # flush'dan keyin MUST<id> bilan to'ldiriladi
            amount=amount, payment_type=payment_type,
        )
        s.add(p)
        await s.flush()
        from config import settings as _st
        p.merchant_trans_id = f"{_st.click_tx_prefix}{p.id}"
        await s.commit()
        await s.refresh(p)
        return p


async def get_payment(payment_id: int) -> Payment | None:
    async with async_session() as s:
        return await s.get(Payment, payment_id)


async def mark_payment_paid(payment_id: int, click_trans_id: str) -> Payment | None:
    async with async_session() as s:
        p = await s.get(Payment, payment_id)
        if p and p.status != "paid":
            p.status = "paid"
            p.click_trans_id = click_trans_id
            p.paid_at = dt.datetime.utcnow()
            # Foydalanuvchi statistikasi
            u = await s.get(User, p.user_id)
            if u and p.order_id:  # buyurtma to'lovi
                u.total_spent += p.amount
                u.orders_count += 1
            await s.commit()
            await s.refresh(p)
        return p


# ─────────────────── REFERRAL BONUS ───────────────────

async def award_referral_bonus(referee_id: int, doc_type: str, bonus: int) -> int | None:
    """Birinchi to'lovda referral bonusini beradi. Referrer ID qaytaradi."""
    async with async_session() as s:
        r = await s.execute(
            select(Referral).where(
                Referral.referee_id == referee_id,
                Referral.bonus_awarded == False,
            )
        )
        ref = r.scalar_one_or_none()
        if ref is None:
            return None
        ref.bonus_awarded = True
        ref.bonus_amount = bonus
        ref.bonus_at = dt.datetime.utcnow()
        referrer = await s.get(User, ref.referrer_id)
        if referrer:
            referrer.balance += bonus
            referrer.referral_earned += bonus
        await s.commit()
        return ref.referrer_id


async def get_referral_stats(user_id: int) -> dict:
    async with async_session() as s:
        refs = (await s.execute(
            select(Referral).where(Referral.referrer_id == user_id)
        )).scalars().all()
        paid = sum(1 for r in refs if r.bonus_awarded)
        earned = sum(r.bonus_amount for r in refs if r.bonus_awarded)
        return {"total": len(refs), "paid": paid, "earned": earned}


# ─────────────────── ADMIN ───────────────────

async def admin_list_users(search: str = "", limit: int = 100) -> list[dict]:
    async with async_session() as s:
        q = select(User).order_by(desc(User.created_at)).limit(limit)
        if search:
            if search.startswith("@"):
                q = q.where(User.username == search[1:])
            elif search.isdigit():
                q = q.where(User.id == int(search))
            else:
                q = q.where(User.username.ilike(f"%{search}%"))
        rows = (await s.execute(q)).scalars().all()
        return [_user_dict(u) for u in rows]


def _user_dict(u: User) -> dict:
    return {
        "id": u.id, "username": u.username, "full_name": u.full_name,
        "balance": u.balance, "referral_count": u.referral_count,
        "referral_earned": u.referral_earned, "total_spent": u.total_spent,
        "orders_count": u.orders_count, "is_banned": u.is_banned,
        "created_at": u.created_at, "last_active": u.last_active,
        "referral_code": u.referral_code,
    }


async def admin_get_user(user_id: int) -> dict | None:
    async with async_session() as s:
        u = await s.get(User, user_id)
        if not u:
            return None
        orders = (await s.execute(
            select(Order).where(Order.user_id == user_id)
            .order_by(desc(Order.created_at)).limit(20)
        )).scalars().all()
        payments = (await s.execute(
            select(Payment).where(Payment.user_id == user_id)
            .order_by(desc(Payment.created_at)).limit(20)
        )).scalars().all()
        d = _user_dict(u)
        d["orders"] = [_order_dict(o) for o in orders]
        d["payments"] = [_payment_dict(p) for p in payments]
        return d


def _payment_dict(p: Payment) -> dict:
    return {
        "id": p.id, "amount": p.amount, "status": p.status,
        "payment_type": p.payment_type, "merchant_trans_id": p.merchant_trans_id,
        "click_trans_id": p.click_trans_id, "order_id": p.order_id,
        "created_at": p.created_at, "paid_at": p.paid_at,
    }


async def admin_list_orders(status: str | None = None, limit: int = 100) -> list[dict]:
    async with async_session() as s:
        q = (select(Order, User.username)
             .join(User, Order.user_id == User.id, isouter=True)
             .order_by(desc(Order.created_at)).limit(limit))
        if status:
            q = q.where(Order.status == status)
        rows = (await s.execute(q)).all()
        result = []
        for o, uname in rows:
            d = _order_dict(o)
            d["username"] = uname
            d["user_id"] = o.user_id
            result.append(d)
        return result


async def admin_list_payments(limit: int = 100) -> list[dict]:
    async with async_session() as s:
        rows = (await s.execute(
            select(Payment, User.username)
            .join(User, Payment.user_id == User.id, isouter=True)
            .order_by(desc(Payment.created_at)).limit(limit)
        )).all()
        result = []
        for p, uname in rows:
            d = _payment_dict(p)
            d["username"] = uname
            d["user_id"] = p.user_id
            result.append(d)
        return result


async def admin_dashboard() -> dict:
    async with async_session() as s:
        total_users = await s.scalar(select(func.count(User.id))) or 0
        today = dt.datetime.utcnow().date()
        today_dt = dt.datetime(today.year, today.month, today.day)
        new_today = await s.scalar(
            select(func.count(User.id)).where(User.created_at >= today_dt)
        ) or 0
        total_orders = await s.scalar(select(func.count(Order.id))) or 0
        orders_today = await s.scalar(
            select(func.count(Order.id)).where(Order.created_at >= today_dt)
        ) or 0
        done_orders = await s.scalar(
            select(func.count(Order.id)).where(Order.status == "done")
        ) or 0
        revenue = await s.scalar(
            select(func.sum(Payment.amount)).where(Payment.status == "paid")
        ) or 0
        revenue_today = await s.scalar(
            select(func.sum(Payment.amount)).where(
                Payment.status == "paid", Payment.paid_at >= today_dt
            )
        ) or 0
        return {
            "total_users": total_users, "new_today": new_today,
            "total_orders": total_orders, "orders_today": orders_today,
            "done_orders": done_orders, "revenue": revenue, "revenue_today": revenue_today,
        }


async def admin_add_balance(user_id: int, amount: int):
    async with async_session() as s:
        u = await s.get(User, user_id)
        if u:
            u.balance += amount
            await s.commit()


# ─────────────────── SETTINGS (admin sozlamalari) ───────────────────

async def load_settings() -> dict[str, str]:
    """Barcha sozlamalarni o'qiydi (key→value)."""
    async with async_session() as s:
        rows = (await s.execute(select(Setting))).scalars().all()
        return {r.key: r.value for r in rows if r.value is not None}


async def save_settings_bulk(data: dict[str, str]) -> None:
    """Bir nechta sozlamani saqlaydi (mavjudini yangilaydi)."""
    async with async_session() as s:
        for k, v in data.items():
            obj = await s.get(Setting, k)
            if obj is None:
                s.add(Setting(key=k, value=str(v)))
            else:
                obj.value = str(v)
                obj.updated_at = dt.datetime.utcnow()
        await s.commit()


async def admin_refund_order(order_id: int) -> bool:
    """Buyurtmani qaytaradi: narxni foydalanuvchi balansiga qaytaradi,
    statusni 'refunded' qiladi. Faqat to'langan/bajarilgan/xato uchun."""
    async with async_session() as s:
        o = await s.get(Order, order_id)
        if o is None or o.status == "refunded":
            return False
        u = await s.get(User, o.user_id)
        if u and o.price > 0:
            u.balance += o.price
            if u.total_spent >= o.price:
                u.total_spent -= o.price
        o.status = "refunded"
        await s.commit()
        return True
