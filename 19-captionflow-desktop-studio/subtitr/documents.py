"""Hujjat eksporti uchun orqaga mos import nuqtasi.

TXT/DOCX/CSV, Markdown va PDF qatlamlari alohida modullarda. Eski ichki
yordamchi importlari ham ishlashi uchun bu nom engine moduliga alias qilinadi.
"""
import sys

from . import _documents_engine as _engine

sys.modules[__name__] = _engine
