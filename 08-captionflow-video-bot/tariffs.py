"""Tariflar ta'rifi (arxitektura 9-bo'lim).

daily_videos = -1  -> cheksiz (yumshoq chegara)
modes        -> shu tarifda ruxsat etilgan rejimlar
"""
from __future__ import annotations
from dataclasses import dataclass


_ALL_MODES = (
    "original", "translate", "dual", "dual_vocab", "srt",
    "transcript", "vocabulary", "audio",
)


@dataclass(frozen=True)
class Tariff:
    name: str
    title: str
    daily_videos: int           # -1 = kunlik chek yo'q; >0 = kunlik chek
    max_minutes: int
    modes: tuple[str, ...]
    monthly_videos: int = 0     # 0 = oylik chek yo'q; >0 = oyiga jami chek
    per_mode_monthly: int = 0   # 0 = chek yo'q; >0 = har rejimga oyiga chek


TARIFFS: dict[str, Tariff] = {
    "free": Tariff(
        name="free",
        title="BEPUL",
        daily_videos=-1,         # kunlik emas — oylik tizim
        max_minutes=5,
        modes=_ALL_MODES,        # hamma rejim ochiq (lekin oyiga 3 tadan)
        monthly_videos=10,       # oyiga jami 10 video
        per_mode_monthly=3,      # har rejimga oyiga 3 ta
    ),
    "basic": Tariff(
        name="basic",
        title="BASIC",
        daily_videos=10,
        max_minutes=30,
        modes=_ALL_MODES,
    ),
    "premium": Tariff(
        name="premium",
        title="PREMIUM",
        daily_videos=-1,  # cheksiz (adolatli foydalanish)
        max_minutes=30,
        modes=_ALL_MODES,
    ),
}


def get_tariff(plan: str) -> Tariff:
    return TARIFFS.get(plan, TARIFFS["free"])
