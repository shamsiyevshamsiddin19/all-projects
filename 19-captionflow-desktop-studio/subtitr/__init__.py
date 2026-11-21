"""Subtitr Desktop protsessori (modullar bo'yicha bo'lingan)."""
from __future__ import annotations

from .core import *  # noqa: F401,F403
from .media import *  # noqa: F401,F403
from .transcribe import *  # noqa: F401,F403
from .cache import *  # noqa: F401,F403
from .translate import *  # noqa: F401,F403
from .clean import *  # noqa: F401,F403
from .vocab import *  # noqa: F401,F403
from .subtitles import *  # noqa: F401,F403
from .documents import *  # noqa: F401,F403
from .pipeline import *  # noqa: F401,F403
from .cli import *  # noqa: F401,F403

__all__ = [
    # --- core: ma'lumot turlari ---
    "Segment", "Word", "ReadingBlock", "ReadingPair",
    # --- core: yo'llar va konstantalar ---
    "ROOT", "OUT_DIR", "TMP_DIR", "MODEL_DIR", "DICT_DIR", "CACHE_DIR",
    "LOG_DIR", "KINO_DIR", "ENV_FILE", "VENV_DIR", "REQUIREMENTS_FILE",
    "FFMPEG", "FFPROBE", "YTDLP",
    "VIDEO_EXTS", "IMAGE_EXTS", "MEDIA_EXTS", "SUB_EXTS",
    "TARGET_LANG_NAMES", "SOURCE_LANG_NAMES",
    "HELPERS", "POS_ORDER", "POS_UZ",
    "OFFLINE_WORDS", "OFFLINE_PHRASES",
    "USAGE", "AI_DISABLED",
    # --- core: funksiyalar ---
    "emit", "log", "redact", "setup_logging", "current_log_file",
    "ensure_dirs", "install_signal_handlers", "clean_orphan_tmp",
    "normalize_lang_code", "normalize_word", "pos_label",
    "run", "safe_stem", "is_url", "model_candidates", "words_from_segments",
    "wrap_lines", "wrap_text", "dialogue_parts",
    "require_disk_space", "require_tool", "resolve_tool", "venv_python",
    "secret", "error_kind", "disable_provider",
    "ai_throttle", "ai_retry_backoff", "reset_usage",
    "stop_child", "whisper_confidence", "low_confidence",
    "offline_words", "offline_phrases",
    # --- media ---
    "extract_audio", "extract_embedded_subtitle", "find_sidecar_subtitle",
    "download_video", "playlist_entries", "scan", "update_ytdlp",
    "probe_duration_seconds", "probe_resolution", "probe_audio_codec",
    "probe_audio_stream_count",
    "seconds_to_srt_time", "seconds_to_ass_time", "srt_time_to_seconds",
    "parse_srt", "parse_vtt", "parse_ass", "parse_srt_text", "parse_subtitle",
    "read_subtitle_text", "strip_tags",
    "hwaccel_args", "audio_args_for", "pick_video_encoder",
    "DEFAULT_QUALITY", "QUALITY_HEIGHTS", "quality_height",
    "normalize_video_path", "normalize_url_for_cache",
    "download_cache_key", "prune_download_cache",
    "is_pinterest_url", "download_pinterest_media",
    # --- transcribe ---
    "get_transcription",
    "transcribe_with_groq", "transcribe_with_faster_whisper",
    "transcribe_with_whisper_cli",
    "speech_seconds", "speech_regions", "gate_by_speech", "clamp_to_speech",
    "rescan_swallowed_speech", "suspect_ranges", "swallowed_gap_ranges",
    "WindowTranscriber",
    # --- cache ---
    "cache_dir_for", "load_transcription", "save_transcription",
    "transcription_signature", "cache_usage", "clear_cache",
    # --- translate ---
    "translate_segments", "translate_word_list",
    "translate_groq", "translate_openai", "translate_gemini", "translate_claude",
    "ai_translate_batch", "ai_providers", "ai_attempts", "try_providers",
    "offline_translate_word", "offline_translate_text",
    # --- clean ---
    "clean_transcription", "is_hallucination", "collapse_repeats",
    "polish_segments", "is_sound_annotation",
    # --- vocab ---
    "build_vocabulary", "dedupe_by_lemma", "is_translit_only",
    "build_glossary", "entry_helper", "helper_category",
    "filter_words", "sentence_for", "group_name_forms", "name_frequencies",
    # --- subtitles ---
    "write_srt", "write_ass", "ass_header", "ass_color", "ass_escape",
    "burn_subtitles", "attach_soft_subtitles",
    "enforce_reading_speed", "layout_for", "inline_color",
    "subtitle_font_name", "FONTS_DIR",
    # --- documents ---
    "write_txt_transcript", "write_txt_vocab",
    "write_docx_transcript", "write_docx_vocab", "write_csv_vocab",
    "write_md_reading", "write_txt_reading", "write_pdf_reading",
    "build_reading_blocks", "build_sentence_pairs",
    "reading_vocab_map", "reading_proper_nouns", "mark_vocab_words",
    "reading_title", "reading_meta",
    "PDF_FONT", "SPLIT_HEADING",
    # --- pipeline ---
    "process", "prepare_session", "render_session",
    "preview_frame", "subtitle_file", "retranslate_session_segment",
    "install_deps", "modes_for", "required_packages",
    "RenderData", "SESSION_VERSION", "ALL_MODE_OUTPUTS", "VIDEO_MODES",
    # --- cli ---
    "main", "build_parser",
]
