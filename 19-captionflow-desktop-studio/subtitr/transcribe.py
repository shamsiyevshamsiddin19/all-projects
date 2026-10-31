"""Transkripsiya uchun orqaga mos import nuqtasi.

Provider, VAD va rescan qatlamlari yangi modullarda ajratilgan. Eski
monkeypatch va private yordamchi importlarini ham buzmaslik uchun ushbu modul
import vaqtida eski engine obyektiga alias qilinadi.
"""
import sys

from . import _transcribe_engine as _engine

sys.modules[__name__] = _engine
