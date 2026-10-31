"""VAD (nutq faolligini aniqlash) qatlamining ochiq adapterlari."""
from __future__ import annotations

from pathlib import Path


def speech_seconds(media: Path, start: float, duration: float) -> float:
    """Berilgan oraliqdagi nutq davomiyligini qaytaradi."""
    from ._transcribe_engine import speech_seconds as _speech_seconds

    return _speech_seconds(media, start, duration)


def speech_regions(audio_path: Path) -> list[tuple[float, float]]:
    """Audio ichidagi nutq oraliqlarini qaytaradi."""
    from ._transcribe_engine import speech_regions as _speech_regions

    return _speech_regions(audio_path)


def gate_by_speech(*args: object, **kwargs: object) -> object:
    """Nutq bo'lmagan joydagi taxminiy matnni filtrlash adapteri."""
    from ._transcribe_engine import gate_by_speech as _gate_by_speech

    return _gate_by_speech(*args, **kwargs)
