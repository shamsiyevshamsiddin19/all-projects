"""Transkripsiya oqimini muvofiqlashtiruvchi yupqa facade.

Provider, VAD va rescan implementatsiyalari alohida modullarda yashaydi.
Bu modul hamda :mod:`subtitr.transcribe` eski import va monkeypatch nuqtalarini
saqlaydi.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from .core import FFMPEG, Segment, Word, emit, model_candidates, secret, words_from_segments, run
from .media import extract_audio, extract_embedded_subtitle, find_sidecar_subtitle, parse_srt, parse_vtt, probe_duration_seconds
from .transcribe_providers import (
    _groq_transcribe_file, _groq_window_transcriber, _local_window_transcriber,
    transcribe_with_faster_whisper, transcribe_with_groq as _provider_transcribe_with_groq, value,
)
from .transcribe_rescan import (
    WindowTranscriber, _rescan_one, pick_best_segments, ranges_within_budget, rescan_swallowed_speech,
    rescan_windows, seg_density, suspect_ranges, swallowed_gap_ranges,
)


def transcribe_with_groq(audio_path: Path, language: str, source_media: Path | None = None):
    """Providerga eski monkeypatch nuqtalarini uzatadigan moslik adapteri."""
    from . import transcribe_providers as providers
    from . import transcribe_rescan as rescans
    providers.model_candidates = model_candidates
    providers._groq_transcribe_file = _groq_transcribe_file
    providers.run = run
    providers.probe_duration_seconds = probe_duration_seconds
    providers.rescan_swallowed_speech = rescan_swallowed_speech
    providers.emit = emit
    rescans._rescan_one = _rescan_one
    rescans.emit = emit
    return _provider_transcribe_with_groq(audio_path, language, source_media)
from .transcribe_vad import (
    _pcm_window, _speech_seconds_ffmpeg, _speech_seconds_vad, clamp_to_speech,
    gate_by_speech, speech_regions, speech_seconds,
)


def transcribe_with_whisper_cli(audio_path: Path, tmp_dir: Path, language: str) -> tuple[list[Segment], list[Word], str]:
    exe = shutil.which("whisper")
    if not exe:
        raise RuntimeError("whisper CLI topilmadi")
    model = os.getenv("WHISPER_MODEL", "small")
    cmd = [exe, str(audio_path), "--model", model, "--output_format", "srt", "--output_dir", str(tmp_dir)]
    if language and language != "auto":
        cmd += ["--language", language]
    proc = run(cmd)
    if proc.returncode != 0:
        raise RuntimeError("whisper CLI xato: " + (proc.stderr[-700:] or "noma'lum"))
    srt = tmp_dir / (audio_path.stem + ".srt")
    segments = parse_srt(srt)
    return segments, words_from_segments(segments), language if language != "auto" else ""


def get_transcription(video: Path, tmp_dir: Path, source_lang: str) -> tuple[list[Segment], list[Word], str, str]:
    sidecar = find_sidecar_subtitle(video)
    if sidecar:
        emit("progress", message=f"SRT topildi: {sidecar.name}", progress=0.12)
        segments = parse_vtt(sidecar) if sidecar.suffix.lower() == ".vtt" else parse_srt(sidecar)
        return segments, words_from_segments(segments), source_lang if source_lang != "auto" else "", "sidecar_srt"
    embedded = extract_embedded_subtitle(video, tmp_dir)
    if embedded:
        emit("progress", message="Ichki subtitr ajratildi", progress=0.16)
        segments = parse_srt(embedded)
        return segments, words_from_segments(segments), source_lang if source_lang != "auto" else "", "embedded_srt"
    cache: dict[str, Path] = {}
    def audio_for(lossless: bool) -> Path:
        key = "wav" if lossless else "opus"
        if key not in cache:
            path = tmp_dir / ("audio.wav" if lossless else "audio.webm")
            emit("progress", message="Audio ajratilmoqda" if lossless else "Audio ajratilmoqda (yuqori siqilishda)", progress=0.18)
            extract_audio(video, path, lossless=lossless)
            cache[key] = path
        return cache[key]
    errors: list[str] = []
    def try_groq():
        if secret("GROQ_API_KEY").strip():
            try:
                emit("progress", message="Groq Whisper transkripsiya qilmoqda", progress=0.30)
                segments, words, detected = transcribe_with_groq(audio_for(False), source_lang, video)
                segments, words = gate_by_speech(segments, words, audio_for(False))
                if not segments: raise RuntimeError("nutq topilmadi")
                return segments, words or words_from_segments(segments), detected, "groq"
            except Exception as exc: errors.append(f"Groq: {exc}")
        return None
    def try_faster_whisper():
        try:
            emit("progress", message="Lokal faster-whisper tekshirilmoqda", progress=0.30)
            segments, words, detected = transcribe_with_faster_whisper(audio_for(True), source_lang, video)
            return segments, words or words_from_segments(segments), detected, "faster_whisper"
        except Exception as exc: errors.append(f"faster-whisper: {exc}")
        return None
    def try_whisper_cli():
        try:
            emit("progress", message="Lokal whisper CLI tekshirilmoqda", progress=0.30)
            segments, words, detected = transcribe_with_whisper_cli(audio_for(True), tmp_dir, source_lang)
            return segments, words, detected, "whisper_cli"
        except Exception as exc: errors.append(f"whisper CLI: {exc}")
        return None
    order = ([try_faster_whisper, try_whisper_cli, try_groq] if os.getenv("PREFERRED_TRANSCRIBER", "").strip().lower() in {"faster_whisper", "local", "offline"} else [try_groq, try_faster_whisper, try_whisper_cli])
    for fn in order:
        result = fn()
        if result is not None: return result
    detail = " | ".join(errors[-3:])
    raise RuntimeError("Subtitr topilmadi va transkripsiya ishlamadi. Video yoniga .srt qo'ying yoki GROQ_API_KEY / faster-whisper / whisper CLI sozlang. " + detail)
