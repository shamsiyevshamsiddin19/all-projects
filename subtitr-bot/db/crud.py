"""Ma'lumotlar bazasi bilan ishlash uchun CRUD (Create, Read, Update, Delete) funksiyalari.

Barcha funksiyalar async/await orqali SQLAlchemy session'dan foydalanadi.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter

from sqlalchemy import func, select, update

from config import settings
from db.base import async_session
from db.models import Donation, Payment, Setting, User, Video, utcnow

# O'zbekiston vaqti (UTC+5) — kunlik limit chegarasini hisoblash uchun
_TASHKENT_OFFSET = dt.timedelta(hours=5)


def _today_start_utc() -> dt.datetime:
    """Bugungi kun boshini (Tashkent 00:00) UTC naive ko'rinishida qaytaradi."""
    now_utc = utcnow()
    now_tash = now_utc + _TASHKENT_OFFSET
    tash_midnight = dt.datetime(now_tash.year, now_tash.month, now_tash.day)
    return tash_midnight - _TASHKENT_OFFSET


def _month_start_utc() -> dt.datetime:
    """Joriy oy boshini (Tashkent 1-kun 00:00) UTC naive ko'rinishida qaytaradi."""
    now_tash = utcnow() + _TASHKENT_OFFSET
    first = dt.datetime(now_tash.year, now_tash.month, 1)
    return first - _TASHKENT_OFFSET


def effective_plan(user: User) -> str:
    """Amaldagi tarif: muddati o'tgan bo'lsa — free."""
    if user.plan != "free" and user.plan_until is not None:
        if user.plan_until < utcnow():
            return "free"
    return user.plan


async def get_user_by_tg(telegram_id: int) -> User | None:
    """Foydalanuvchini telegram_id bo'yicha topadi (o'zgartirmasdan; faqat
    last_active yangilanadi). Brauzer token auth uchun — username'ni o'chirmaydi."""
    async with async_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        if user is not None:
            user.last_active_at = utcnow()
            await session.commit()
            await session.refresh(user)
        return user


async def get_or_create_user(
    telegram_id: int, username: str | None, language: str | None = None
) -> User:
    async with async_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                language=language or "uz",
            )
            session.add(user)
        else:
            user.username = username
            user.last_active_at = utcnow()
            if language:
                user.language = language
        await session.commit()
        await session.refresh(user)
        return user


# Har muvaffaqiyatli taklif uchun bonus (referal qilgan VA qilingan ikkalasiga)
REFERRAL_BONUS = 5


async def apply_referral(
    new_tg_id: int, referrer_tg_id: int, bonus: int = REFERRAL_BONUS
) -> tuple[bool, int]:
    """Yangi foydalanuvchiga referal bonusini qo'llaydi.

    Qoidalar (suiiste'molni oldini olish):
      - Faqat referred_by hali yo'q bo'lsa (bir marta).
      - Yangi foydalanuvchi hali BIRORTA video qilmagan bo'lsa (eski faol
        foydalanuvchi do'st havolasini bosib bonus ololmasin).
      - O'zini o'zi taklif qilib bo'lmaydi.
    Qaytaradi: (qo'llandi, taklif_qilgan_telegram_id) — xabar berish uchun.
    """
    async with async_session() as session:
        new_user = await session.scalar(
            select(User).where(User.telegram_id == new_tg_id)
        )
        if new_user is None or new_user.referred_by is not None:
            return False, 0
        vcount = await session.scalar(
            select(func.count(Video.id)).where(Video.user_id == new_user.id)
        )
        if vcount and vcount > 0:
            return False, 0  # allaqachon faol — referal berilmaydi
        referrer = await session.scalar(
            select(User).where(User.telegram_id == referrer_tg_id)
        )
        if referrer is None or referrer.id == new_user.id:
            return False, 0
        new_user.referred_by = referrer.id
        new_user.bonus_videos = (new_user.bonus_videos or 0) + bonus
        referrer.bonus_videos = (referrer.bonus_videos or 0) + bonus
        await session.commit()
        return True, referrer.telegram_id


async def referral_stats(user_id: int) -> tuple[int, int]:
    """(taklif qilingan odamlar soni, jami bonus_videos)."""
    async with async_session() as session:
        n = await session.scalar(
            select(func.count(User.id)).where(User.referred_by == user_id)
        )
        user = await session.get(User, user_id)
        return int(n or 0), int(user.bonus_videos if user else 0)


async def videos_done_today(user_id: int) -> int:
    """Bugun muvaffaqiyatli tugagan videolar soni (kunlik limit uchun)."""
    async with async_session() as session:
        count = await session.scalar(
            select(func.count(Video.id)).where(
                Video.user_id == user_id,
                Video.status == "done",
                Video.created_at >= _today_start_utc(),
            )
        )
        return int(count or 0)


async def videos_done_this_month(user_id: int) -> int:
    """Shu oyda muvaffaqiyatli tugagan videolar soni (oylik limit uchun)."""
    async with async_session() as session:
        count = await session.scalar(
            select(func.count(Video.id)).where(
                Video.user_id == user_id,
                Video.status == "done",
                Video.created_at >= _month_start_utc(),
            )
        )
        return int(count or 0)


async def videos_in_month_by_mode(user_id: int, mode: str) -> int:
    """Shu oyda shu rejimda tugagan videolar soni (har rejimga oylik limit)."""
    async with async_session() as session:
        count = await session.scalar(
            select(func.count(Video.id)).where(
                Video.user_id == user_id,
                Video.mode == mode,
                Video.status == "done",
                Video.created_at >= _month_start_utc(),
            )
        )
        return int(count or 0)


async def create_video(
    user_id: int,
    mode: str,
    duration_seconds: int,
    source_type: str = "upload",
    target_lang: str | None = None,
) -> int:
    async with async_session() as session:
        video = Video(
            user_id=user_id,
            mode=mode,
            duration_seconds=duration_seconds,
            source_type=source_type,
            target_lang=target_lang,
            status="processing",
        )
        session.add(video)
        await session.commit()
        await session.refresh(video)
        return video.id


async def finish_video(
    video_id: int,
    status: str,
    error_step: str | None = None,
    error_message: str | None = None,
    translation_provider: str | None = None,
) -> None:
    async with async_session() as session:
        await session.execute(
            update(Video)
            .where(Video.id == video_id)
            .values(
                status=status,
                error_step=error_step,
                error_message=(error_message or "")[:500] or None,
                translation_provider=translation_provider,
                finished_at=utcnow(),
            )
        )
        await session.commit()


async def get_user_by_id(user_id: int) -> User | None:
    async with async_session() as session:
        return await session.get(User, user_id)


async def create_payment(
    user_id: int, plan: str, amount: int, meta: str | None = None
) -> int:
    async with async_session() as session:
        payment = Payment(
            user_id=user_id, plan=plan, amount=amount, status="pending", meta=meta
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment.id


async def get_payment(payment_id: int) -> Payment | None:
    async with async_session() as session:
        return await session.get(Payment, payment_id)


async def mark_payment_paid(payment_id: int, click_trans_id: str | None) -> None:
    async with async_session() as session:
        await session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(status="paid", click_trans_id=click_trans_id, paid_at=utcnow())
        )
        await session.commit()


async def get_dashboard_stats() -> dict:
    """Admin dashboard uchun asosiy ko'rsatkichlar (KPI)."""
    async with async_session() as session:
        now = utcnow()
        today = _today_start_utc()

        total_users = await session.scalar(select(func.count(User.id))) or 0
        new_users_today = await session.scalar(
            select(func.count(User.id)).where(User.created_at >= today)
        ) or 0
        active_subs = await session.scalar(
            select(func.count(User.id)).where(
                User.plan != "free",
                User.plan_until.is_not(None),
                User.plan_until > now,
            )
        ) or 0
        total_videos = await session.scalar(select(func.count(Video.id))) or 0
        videos_today = await session.scalar(
            select(func.count(Video.id)).where(Video.created_at >= today)
        ) or 0
        done_videos = await session.scalar(
            select(func.count(Video.id)).where(Video.status == "done")
        ) or 0
        error_videos = await session.scalar(
            select(func.count(Video.id)).where(Video.status == "error")
        ) or 0
        revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == "paid"
            )
        ) or 0
        return {
            "total_users": int(total_users),
            "new_users_today": int(new_users_today),
            "active_subs": int(active_subs),
            "total_videos": int(total_videos),
            "videos_today": int(videos_today),
            "done_videos": int(done_videos),
            "error_videos": int(error_videos),
            "revenue": int(revenue),
        }


async def recent_videos(limit: int = 10) -> list[dict]:
    """So'nggi videolar (foydalanuvchi nomi bilan)."""
    async with async_session() as session:
        rows = (
            await session.execute(
                select(Video, User.username, User.telegram_id)
                .join(User, Video.user_id == User.id)
                .order_by(Video.created_at.desc())
                .limit(limit)
            )
        ).all()
        return [
            {
                "id": v.id,
                "username": username,
                "telegram_id": tg_id,
                "source_type": v.source_type,
                "mode": v.mode,
                "target_lang": v.target_lang,
                "status": v.status,
                "duration": v.duration_seconds,
                "provider": v.translation_provider,
                "created_at": v.created_at,
                "error_message": v.error_message,
            }
            for v, username, tg_id in rows
        ]


async def recent_errors(limit: int = 10) -> list[dict]:
    """So'nggi xatolik bilan tugagan videolar."""
    async with async_session() as session:
        rows = (
            await session.execute(
                select(Video, User.username, User.telegram_id)
                .join(User, Video.user_id == User.id)
                .where(Video.status == "error")
                .order_by(Video.created_at.desc())
                .limit(limit)
            )
        ).all()
        return [
            {
                "id": v.id,
                "username": username,
                "telegram_id": tg_id,
                "mode": v.mode,
                "error_step": v.error_step,
                "error_message": v.error_message,
                "created_at": v.created_at,
            }
            for v, username, tg_id in rows
        ]


# --------------------------------------------------------- sozlamalar (settings)

# Admin paneldan tahrirlanadigan kalitlar va config'dagi standart qiymati
def _setting_defaults() -> dict[str, int]:
    return {
        "price_basic": settings.price_basic,
        "price_premium": settings.price_premium,
        "sub_days": settings.sub_days,
        "groq_monthly_minutes": settings.groq_monthly_minutes,
        "api_alert_threshold": settings.api_alert_threshold,
    }


async def get_settings_map() -> dict[str, str]:
    async with async_session() as session:
        rows = (await session.execute(select(Setting))).scalars().all()
        return {r.key: r.value for r in rows}


async def get_effective_settings() -> dict[str, int]:
    """DB dagi qiymat (bo'lsa) yoki config standarti — butun son sifatida."""
    db = await get_settings_map()
    out: dict[str, int] = {}
    for key, default in _setting_defaults().items():
        raw = db.get(key)
        try:
            out[key] = int(raw) if raw not in (None, "") else default
        except (ValueError, TypeError):
            out[key] = default
    return out


async def save_settings(items: dict[str, int]) -> None:
    async with async_session() as session:
        for key, value in items.items():
            row = await session.get(Setting, key)
            if row is None:
                session.add(Setting(key=key, value=str(value), updated_at=utcnow()))
            else:
                row.value = str(value)
                row.updated_at = utcnow()
        await session.commit()


# --------------------------------------------------------- tariflar (DB override)

# Admin tahrirlay oladigan barcha rejimlar (tartib bilan)
# tariffs._ALL_MODES bilan bitta manba — yangi rejim qo'shilса shu yerda ham
# avtomatik ko'rinadi (aks holda DB override filtri yangi rejimni o'chirardi).
from tariffs import _ALL_MODES as _ALL_MODE_KEYS  # noqa: E402


def _int_or(raw, default: int) -> int:
    try:
        return int(raw) if raw not in (None, "") else default
    except (ValueError, TypeError):
        return default


async def get_effective_tariffs() -> dict:
    """tariffs.py standartlari ustiga DB override (admin tahrirlasa).

    Setting kalitlari: tar_<plan>_daily, tar_<plan>_minutes, tar_<plan>_modes
    (modes — vergul bilan ajratilgan rejim kalitlari).
    """
    from tariffs import TARIFFS, Tariff

    db = await get_settings_map()
    out: dict[str, "Tariff"] = {}
    for plan, base in TARIFFS.items():
        daily = _int_or(db.get(f"tar_{plan}_daily"), base.daily_videos)
        minutes = _int_or(db.get(f"tar_{plan}_minutes"), base.max_minutes)
        monthly = _int_or(db.get(f"tar_{plan}_monthly"), base.monthly_videos)
        per_mode = _int_or(db.get(f"tar_{plan}_permode"), base.per_mode_monthly)
        modes_raw = db.get(f"tar_{plan}_modes")
        if modes_raw is not None and modes_raw.strip() != "":
            modes = tuple(m for m in modes_raw.split(",") if m in _ALL_MODE_KEYS)
        else:
            modes = base.modes
        out[plan] = Tariff(
            name=base.name, title=base.title,
            daily_videos=daily, max_minutes=minutes, modes=modes or base.modes,
            monthly_videos=monthly, per_mode_monthly=per_mode,
        )
    return out


async def get_effective_tariff(plan: str):
    """Bitta tarif (DB override bilan). Noma'lum bo'lsa — free."""
    tariffs = await get_effective_tariffs()
    return tariffs.get(plan) or tariffs["free"]


async def save_tariffs(values: dict) -> None:
    """Tarif sozlamalarini Setting jadvaliga (matn) yozadi."""
    async with async_session() as session:
        for key, value in values.items():
            row = await session.get(Setting, key)
            if row is None:
                session.add(Setting(key=key, value=str(value), updated_at=utcnow()))
            else:
                row.value = str(value)
                row.updated_at = utcnow()
        await session.commit()


async def set_setting(key: str, value: str) -> None:
    """Bitta sozlama (matn) yozadi (masalan promo rasm file_id)."""
    async with async_session() as session:
        row = await session.get(Setting, key)
        if row is None:
            session.add(Setting(key=key, value=str(value), updated_at=utcnow()))
        else:
            row.value = str(value)
            row.updated_at = utcnow()
        await session.commit()


# --------------------------------------------------------------- navbat (jobs)

async def get_queue() -> dict:
    """Navbat holati: ishlanayotgan + kutayotgan videolar va bugungi yakunlar."""
    async with async_session() as session:
        active = (
            await session.execute(
                select(Video, User.username, User.telegram_id)
                .join(User, Video.user_id == User.id)
                .where(Video.status.in_(("processing", "pending")))
                .order_by(Video.created_at.asc())
            )
        ).all()
        today = _today_start_utc()
        done_today = await session.scalar(
            select(func.count(Video.id)).where(
                Video.status == "done", Video.created_at >= today
            )
        ) or 0
        error_today = await session.scalar(
            select(func.count(Video.id)).where(
                Video.status == "error", Video.created_at >= today
            )
        ) or 0
        return {
            "active": [
                {
                    "id": v.id,
                    "username": username,
                    "telegram_id": tg_id,
                    "source_type": v.source_type,
                    "mode": v.mode,
                    "target_lang": v.target_lang,
                    "status": v.status,
                    "created_at": v.created_at,
                }
                for v, username, tg_id in active
            ],
            "done_today": int(done_today),
            "error_today": int(error_today),
        }


async def cancel_video(video_id: int) -> bool:
    """Bitta faol (processing/pending) videoni to'xtatadi (status -> error)."""
    async with async_session() as session:
        v = await session.get(Video, video_id)
        if v is None or v.status not in ("processing", "pending"):
            return False
        v.status = "error"
        v.error_message = "Admin tomonidan to'xtatildi"
        v.finished_at = utcnow()
        await session.commit()
        return True


async def cancel_stuck_videos(minutes: int = 60) -> int:
    """`minutes` daqiqadan ortiq processing'da turgan videolarni to'xtatadi."""
    cutoff = utcnow() - dt.timedelta(minutes=minutes)
    async with async_session() as session:
        rows = (await session.execute(
            select(Video).where(
                Video.status == "processing", Video.created_at < cutoff
            )
        )).scalars().all()
        for v in rows:
            v.status = "error"
            v.error_message = f"Tiqilib qolgan ({minutes}+ daqiqa) — to'xtatildi"
            v.finished_at = utcnow()
        await session.commit()
        return len(rows)


async def cancel_all_active_videos() -> int:
    """Barcha faol (processing/pending) videolarni to'xtatadi."""
    async with async_session() as session:
        rows = (await session.execute(
            select(Video).where(Video.status.in_(("processing", "pending")))
        )).scalars().all()
        for v in rows:
            v.status = "error"
            v.error_message = "Admin tomonidan to'xtatildi"
            v.finished_at = utcnow()
        await session.commit()
        return len(rows)


# ------------------------------------------------------------ donatlar (donations)

async def create_donation(user_id: int, amount: int, comment: str | None) -> int:
    async with async_session() as session:
        d = Donation(user_id=user_id, amount=amount, comment=(comment or None))
        session.add(d)
        await session.commit()
        await session.refresh(d)
        return d.id


async def get_donation(donation_id: int) -> Donation | None:
    async with async_session() as session:
        return await session.get(Donation, donation_id)


async def mark_donation_paid(donation_id: int, click_trans_id: str | None) -> None:
    # is_public=True: to'langan donat darrov minnatdorchilik devorida ko'rinadi
    # (Mini App profil pasti). Admin panel "Devorda" tugmasi bilan yashirsa bo'ladi;
    # izoh matni esa faqat tasdiqlangach (is_approved) ko'rinadi.
    async with async_session() as session:
        await session.execute(
            update(Donation)
            .where(Donation.id == donation_id)
            .values(
                status="paid", click_trans_id=click_trans_id,
                paid_at=utcnow(), is_public=True,
            )
        )
        await session.commit()


async def list_donations(limit: int = 60) -> list[dict]:
    async with async_session() as session:
        rows = (
            await session.execute(
                select(Donation, User.username, User.telegram_id)
                .join(User, Donation.user_id == User.id)
                .order_by(Donation.created_at.desc())
                .limit(limit)
            )
        ).all()
        return [
            {
                "id": d.id,
                "username": username,
                "telegram_id": tg_id,
                "amount": d.amount,
                "comment": d.comment,
                "status": d.status,
                "is_approved": d.is_approved,
                "is_public": d.is_public,
                "created_at": d.created_at,
            }
            for d, username, tg_id in rows
        ]


async def count_active_videos() -> int:
    """Navbatdagi (pending/processing) videolar soni — navbat o'rni uchun.

    2 soatlik oyna: yakunlanmay qolib ketgan eski yozuvlar (worker o'lgan
    holatlar) navbatni sun'iy katta ko'rsatmasin.
    """
    cutoff = utcnow() - dt.timedelta(hours=2)
    async with async_session() as session:
        n = await session.scalar(
            select(func.count(Video.id)).where(
                Video.status.in_(("pending", "processing")),
                Video.created_at >= cutoff,
            )
        )
        return int(n or 0)


async def list_wall_donations(limit: int = 30) -> list[dict]:
    """Minnatdorchilik devori (Mini App) — to'langan va ko'rsatishga ruxsatli
    donatlar. Izoh faqat moderatsiyadan o'tgan bo'lsa (is_approved) qaytadi."""
    async with async_session() as session:
        rows = (
            await session.execute(
                select(Donation, User.username)
                .join(User, Donation.user_id == User.id)
                .where(Donation.status == "paid", Donation.is_public.is_(True))
                .order_by(Donation.paid_at.desc().nulls_last(), Donation.id.desc())
                .limit(limit)
            )
        ).all()
        return [
            {
                "name": (f"@{username}" if username else "Homiy"),
                "amount": d.amount,
                "comment": (d.comment or None) if d.is_approved else None,
                "date": (d.paid_at or d.created_at).strftime("%d.%m.%Y"),
            }
            for d, username in rows
        ]


async def donations_total() -> int:
    async with async_session() as session:
        total = await session.scalar(
            select(func.coalesce(func.sum(Donation.amount), 0)).where(
                Donation.status == "paid"
            )
        )
        return int(total or 0)


async def set_donation_approved(donation_id: int, approved: bool) -> None:
    async with async_session() as session:
        await session.execute(
            update(Donation)
            .where(Donation.id == donation_id)
            .values(is_approved=approved)
        )
        await session.commit()


async def set_donation_public(donation_id: int, public: bool) -> None:
    async with async_session() as session:
        await session.execute(
            update(Donation).where(Donation.id == donation_id).values(is_public=public)
        )
        await session.commit()


async def get_daily_stats(days: int = 14) -> list[dict]:
    """Oxirgi N kun: har kuni video soni va yangi foydalanuvchilar (Tashkent kun)."""
    async with async_session() as session:
        start = _today_start_utc() - dt.timedelta(days=days - 1)
        vid_dates = (
            await session.execute(
                select(Video.created_at).where(Video.created_at >= start)
            )
        ).scalars().all()
        usr_dates = (
            await session.execute(
                select(User.created_at).where(User.created_at >= start)
            )
        ).scalars().all()

    def tash_date(value: dt.datetime) -> dt.date:
        return (value + _TASHKENT_OFFSET).date()

    vc = Counter(tash_date(d) for d in vid_dates)
    uc = Counter(tash_date(d) for d in usr_dates)
    today_tash = (utcnow() + _TASHKENT_OFFSET).date()
    out: list[dict] = []
    for i in range(days):
        day = today_tash - dt.timedelta(days=days - 1 - i)
        out.append({"date": day, "videos": vc.get(day, 0), "users": uc.get(day, 0)})
    return out


async def get_distributions() -> dict:
    """Taqsimotlar: rejim, manba, tarif (raw plan), holat bo'yicha sonlar."""
    async with async_session() as session:
        async def grouped(column):
            rows = (await session.execute(select(column, func.count()).group_by(column))).all()
            return {k: int(v) for k, v in rows if k is not None}

        return {
            "modes": await grouped(Video.mode),
            "sources": await grouped(Video.source_type),
            "plans": await grouped(User.plan),
            "statuses": await grouped(Video.status),
        }


async def get_api_usage_stats() -> dict:
    """API sarfi (taxminiy): Groq audio daqiqalari + tarjima provayderlari.

    Token darajasidagi aniq kvota hozircha saqlanmaydi — Groq sarfi video
    davomiyligidan, tarjima esa provayder bo'yicha video sonidan hisoblanadi.
    """
    async with async_session() as session:
        month0 = _month_start_utc()
        groq_sec_month = await session.scalar(
            select(func.coalesce(func.sum(Video.duration_seconds), 0)).where(
                Video.created_at >= month0
            )
        ) or 0
        groq_sec_total = await session.scalar(
            select(func.coalesce(func.sum(Video.duration_seconds), 0))
        ) or 0
        prov_month = dict(
            (
                await session.execute(
                    select(Video.translation_provider, func.count())
                    .where(
                        Video.created_at >= month0,
                        Video.translation_provider.is_not(None),
                    )
                    .group_by(Video.translation_provider)
                )
            ).all()
        )
        prov_total = dict(
            (
                await session.execute(
                    select(Video.translation_provider, func.count())
                    .where(Video.translation_provider.is_not(None))
                    .group_by(Video.translation_provider)
                )
            ).all()
        )
        return {
            "groq_min_month": round(groq_sec_month / 60),
            "groq_min_total": round(groq_sec_total / 60),
            "prov_month": {k: int(v) for k, v in prov_month.items()},
            "prov_total": {k: int(v) for k, v in prov_total.items()},
        }


async def list_users(search: str = "", limit: int = 60) -> list[dict]:
    """Foydalanuvchilar ro'yxati (video soni bilan). search: username yoki ID."""
    async with async_session() as session:
        q = (
            select(User, func.count(Video.id))
            .outerjoin(Video, Video.user_id == User.id)
            .group_by(User.id)
            .order_by(User.created_at.desc())
            .limit(limit)
        )
        s = (search or "").strip().lstrip("@")
        if s:
            if s.isdigit():
                q = q.where(User.telegram_id == int(s))
            else:
                q = q.where(User.username.ilike(f"%{s}%"))
        rows = (await session.execute(q)).all()
        return [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "username": u.username,
                "plan": effective_plan(u),
                "raw_plan": u.plan,
                "plan_until": u.plan_until,
                "is_blocked": u.is_blocked,
                "videos": int(vcount),
                "created_at": u.created_at,
                "last_active_at": u.last_active_at,
            }
            for u, vcount in rows
        ]


async def list_payments(limit: int = 60) -> list[dict]:
    """To'lovlar ro'yxati (foydalanuvchi nomi bilan)."""
    async with async_session() as session:
        rows = (
            await session.execute(
                select(Payment, User.username, User.telegram_id)
                .join(User, Payment.user_id == User.id)
                .order_by(Payment.created_at.desc())
                .limit(limit)
            )
        ).all()
        return [
            {
                "id": p.id,
                "username": username,
                "telegram_id": tg_id,
                "plan": p.plan,
                "amount": p.amount,
                "status": p.status,
                "provider": p.provider,
                "created_at": p.created_at,
                "paid_at": p.paid_at,
            }
            for p, username, tg_id in rows
        ]


async def list_videos(status: str | None = None, limit: int = 60) -> list[dict]:
    """Videolar ro'yxati. status berilsa — shu holatdagilar (done/error/...)."""
    async with async_session() as session:
        q = (
            select(Video, User.username, User.telegram_id)
            .join(User, Video.user_id == User.id)
            .order_by(Video.created_at.desc())
            .limit(limit)
        )
        if status:
            q = q.where(Video.status == status)
        rows = (await session.execute(q)).all()
        return [
            {
                "id": v.id,
                "username": username,
                "telegram_id": tg_id,
                "source_type": v.source_type,
                "mode": v.mode,
                "target_lang": v.target_lang,
                "status": v.status,
                "duration": v.duration_seconds,
                "provider": v.translation_provider,
                "created_at": v.created_at,
                "error_message": v.error_message,
            }
            for v, username, tg_id in rows
        ]


async def get_user_detail(user_id: int) -> dict | None:
    """Bitta foydalanuvchi: profil + so'nggi videolari + to'lovlari (admin detal)."""
    async with async_session() as session:
        u = await session.get(User, user_id)
        if u is None:
            return None
        vcount = await session.scalar(
            select(func.count(Video.id)).where(Video.user_id == user_id)
        ) or 0
        videos = (
            await session.execute(
                select(Video)
                .where(Video.user_id == user_id)
                .order_by(Video.created_at.desc())
                .limit(10)
            )
        ).scalars().all()
        payments = (
            await session.execute(
                select(Payment)
                .where(Payment.user_id == user_id)
                .order_by(Payment.created_at.desc())
                .limit(10)
            )
        ).scalars().all()
        return {
            "id": u.id,
            "telegram_id": u.telegram_id,
            "username": u.username,
            "plan": effective_plan(u),
            "raw_plan": u.plan,
            "plan_until": u.plan_until,
            "is_blocked": u.is_blocked,
            "videos_count": int(vcount),
            "created_at": u.created_at,
            "last_active_at": u.last_active_at,
            "videos": [
                {
                    "id": v.id,
                    "username": u.username,
                    "telegram_id": u.telegram_id,
                    "source_type": v.source_type,
                    "mode": v.mode,
                    "target_lang": v.target_lang,
                    "status": v.status,
                    "duration": v.duration_seconds,
                    "provider": v.translation_provider,
                    "created_at": v.created_at,
                    "error_message": v.error_message,
                }
                for v in videos
            ],
            "payments": [
                {
                    "id": p.id,
                    "username": u.username,
                    "telegram_id": u.telegram_id,
                    "plan": p.plan,
                    "amount": p.amount,
                    "status": p.status,
                    "provider": p.provider,
                    "created_at": p.created_at,
                    "paid_at": p.paid_at,
                }
                for p in payments
            ],
        }


async def admin_set_blocked(user_id: int, blocked: bool) -> bool:
    """Foydalanuvchini bloklaydi/blokdan chiqaradi (id bo'yicha). True = topildi."""
    async with async_session() as session:
        result = await session.execute(
            update(User).where(User.id == user_id).values(is_blocked=blocked)
        )
        await session.commit()
        return result.rowcount > 0


async def admin_set_plan(user_id: int, plan: str, days: int) -> bool:
    """Foydalanuvchiga tarif beradi (id bo'yicha — admin paneldan). True = topildi."""
    until = utcnow() + dt.timedelta(days=days) if plan != "free" else None
    async with async_session() as session:
        result = await session.execute(
            update(User).where(User.id == user_id).values(plan=plan, plan_until=until)
        )
        await session.commit()
        return result.rowcount > 0


async def set_plan(telegram_id: int, plan: str, days: int) -> bool:
    """Foydalanuvchiga tarif beradi (admin/to'lov uchun). True = topildi."""
    until = utcnow() + dt.timedelta(days=days) if plan != "free" else None
    async with async_session() as session:
        result = await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(plan=plan, plan_until=until)
        )
        await session.commit()
        return result.rowcount > 0
