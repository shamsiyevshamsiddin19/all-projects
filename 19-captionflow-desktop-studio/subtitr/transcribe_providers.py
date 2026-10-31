"""Transkripsiya providerlari uchun barqaror qatlam.

Bu modul providerga xos yordamchilarni bitta nom ostida beradi.  Asosiy
orchestrator hali ``_transcribe_engine`` da turadi; shu orqali eski
``subtitr.transcribe`` importlari ham buzilmaydi.
"""
from __future__ import annotations

from typing import Any


def groq_file(*args: Any, **kwargs: Any) -> Any:
    """Groq fayl transkripsiyasini provider qatlamidan chaqiradi."""
    from ._transcribe_engine import _groq_transcribe_file

    return _groq_transcribe_file(*args, **kwargs)


def groq_window_transcriber(*args: Any, **kwargs: Any) -> Any:
    """Groq uchun qayta o'qish oynasi transcriberini beradi."""
    from ._transcribe_engine import _groq_window_transcriber

    return _groq_window_transcriber(*args, **kwargs)


def local_window_transcriber(*args: Any, **kwargs: Any) -> Any:
    """Faster-Whisper uchun qayta o'qish oynasi transcriberini beradi."""
    from ._transcribe_engine import _local_window_transcriber

    return _local_window_transcriber(*args, **kwargs)
