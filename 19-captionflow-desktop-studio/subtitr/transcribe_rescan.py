"""Yutilib qolgan nutqni topish va qayta o'qish qatlami."""
from __future__ import annotations

from typing import Any


def suspect_ranges(*args: Any, **kwargs: Any) -> Any:
    from ._transcribe_engine import suspect_ranges as _suspect_ranges

    return _suspect_ranges(*args, **kwargs)


def swallowed_gap_ranges(*args: Any, **kwargs: Any) -> Any:
    from ._transcribe_engine import swallowed_gap_ranges as _swallowed_gap_ranges

    return _swallowed_gap_ranges(*args, **kwargs)


def rescan_swallowed_speech(*args: Any, **kwargs: Any) -> Any:
    """Asosiy transkripsiyadagi shubhali oraliqlarni qayta o'qiydi."""
    from ._transcribe_engine import rescan_swallowed_speech as _rescan

    return _rescan(*args, **kwargs)
