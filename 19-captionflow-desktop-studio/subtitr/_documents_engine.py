"""Hujjat eksporti uchun orqaga mos facade."""
from .documents_text import *  # noqa: F401,F403
from .documents_markdown import *  # noqa: F401,F403
from .documents_pdf import *  # noqa: F401,F403
from .documents_markdown import (  # private legacy helpers deliberately re-exported
    _READ_MD_MAX_MARKS,
    _read_implicit_break,
    _read_sentence_spans,
)
