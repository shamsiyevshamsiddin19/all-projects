"""AI Dublyaj va ko'p tilli audio treklar moduli.

Videodagi gaplarni sun'iy intellekt (Microsoft Edge TTS) orqali o'zbekcha
(yoki boshqa tilda) ovozlashtiradi, vaqtga (start/end) moslab tezlashtiradi,
asl fon musiqasini pasaytiradi (ducking) va bitta videoga bir nechta audio
treklarni muxlaydi (Asl inglizcha ovoz + O'zbekcha dublyaj).
"""
from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import wave
from pathlib import Path
from typing import Any, Callable

try:
    import edge_tts
except ImportError:
    edge_tts = None  # type: ignore

from subtitr.core import emit, log, require_tool, run
from subtitr.media import (
    extract_audio, probe_audio_codec, probe_audio_stream_count,
    probe_duration_seconds,
)

DEFAULT_VOICE = "uz-UZ-SardorNeural"

DEFAULT_LANG_VOICES = {
    "uz": "uz-UZ-SardorNeural",
    "ru": "ru-RU-DmitryNeural",
    "tr": "tr-TR-AhmetNeural",
    "en": "en-US-GuyNeural",
    "kk": "kk-KZ-DauletNeural",
    "tg": "ru-RU-DmitryNeural",
    "ky": "ru-RU-DmitryNeural",
}

VOICES = {
    "sardor": "uz-UZ-SardorNeural",
    "madina": "uz-UZ-MadinaNeural",
}


def resolve_voice(voice_name: str | None, target_lang: str = "uz") -> str:
    """Ovoz nomini to'liq Edge TTS ovoz identifikatoriga aylantiradi."""
    code = (target_lang or "uz").split("-")[0].lower()
    if not voice_name:
        return DEFAULT_LANG_VOICES.get(code, DEFAULT_VOICE)

    key = voice_name.strip().lower()
    if key in VOICES:
        return VOICES[key]
    if "neural" in key:
        return voice_name.strip()
    return DEFAULT_LANG_VOICES.get(code, DEFAULT_VOICE)


async def _generate_single_clip(text: str, voice: str, out_path: Path) -> None:
    """Bitta gapni TTS orqali MP3 faylga aylantiradi."""
    if edge_tts is None:
        raise RuntimeError("edge-tts kutubxonasi o'rnatilmagan ('pip install edge-tts')")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))


def generate_clip_sync(text: str, voice: str, out_path: Path) -> None:
    """Sinxron oqimdan TTS chaqirish uchun wrapper."""
    asyncio.run(_generate_single_clip(text, voice, out_path))


def adjust_audio_tempo(
    in_path: Path,
    out_wav: Path,
    target_duration: float,
    sample_rate: int = 24000,
) -> float:
    """TTS ovozini berilgan vaqt oralig'iga (atempo) moslab WAV formatiga o'tkazadi."""
    require_tool("ffmpeg")
    actual_dur = probe_duration_seconds(in_path)
    if actual_dur <= 0.05:
        actual_dur = target_duration

    # Agar ovoz berilgan vaqtdan uzunroq bo'lsa, tezlashtiramiz (maksimal 2.0x)
    ratio = actual_dur / max(0.1, target_duration)
    # `atempo` 2x bilan cheklangan: juda uzun gaplar hali ham oraliqdan
    # chiqishi mumkin. Chiqish davomiyligini qat'iy cheklash keyingi gaplarni
    # siljitib yuborishining oldini oladi.
    output_limit = f"{max(0.1, target_duration):.3f}"
    if ratio > 1.05:
        speed = min(2.0, ratio)
        cmd = [
            "ffmpeg", "-y", "-i", str(in_path),
            "-filter:a", f"atempo={speed:.3f}",
            "-ar", str(sample_rate), "-ac", "1",
            "-t", output_limit,
            str(out_wav),
        ]
    elif ratio < 0.70 and actual_dur >= 0.3:
        # Agar juda kalta bo'lsa, biroz sekinlashtirish mumkin (minimum 0.75x)
        speed = max(0.75, ratio)
        cmd = [
            "ffmpeg", "-y", "-i", str(in_path),
            "-filter:a", f"atempo={speed:.3f}",
            "-ar", str(sample_rate), "-ac", "1",
            "-t", output_limit,
            str(out_wav),
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-i", str(in_path),
            "-ar", str(sample_rate), "-ac", "1",
            "-t", output_limit,
            str(out_wav),
        ]

    res = run(cmd)
    if res.returncode != 0:
        log.warning("atempo xatosi: %s", res.stderr)
        # Zaxira: filtrlarsiz oddiy WAV ga o'tkazamiz
        run([
            "ffmpeg", "-y", "-i", str(in_path),
            "-ar", str(sample_rate), "-ac", "1",
            "-t", output_limit,
            str(out_wav),
        ])

    return probe_duration_seconds(out_wav)


def synthesize_all_segments(
    segments: list[dict[str, Any]],
    voice: str,
    work_dir: Path,
    progress_cb: Callable[[float, str], None] | None = None,
    progress_lo: float = 0.70,
    progress_hi: float = 0.88,
) -> list[tuple[float, Path]]:
    """Barcha tarjima qilingan segmentlarni parallel ravishda TTS ovoziga aylantiradi."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    work_dir.mkdir(parents=True, exist_ok=True)
    results_dict: dict[int, tuple[float, Path]] = {}
    failures = 0
    total = len(segments)

    tasks_to_run: list[tuple[int, float, float, str]] = []
    for i, seg in enumerate(segments):
        start = float(getattr(seg, "start", None) if hasattr(seg, "start") else seg.get("start", 0.0))
        end = float(getattr(seg, "end", None) if hasattr(seg, "end") else seg.get("end", start + 2.0))
        if hasattr(seg, "translated"):
            text = str(getattr(seg, "translated", "") or getattr(seg, "text", "") or getattr(seg, "original", "")).strip()
        elif hasattr(seg, "text"):
            text = str(getattr(seg, "text", "")).strip()
        else:
            text = str(seg.get("translated") or seg.get("text") or seg.get("original") or "").strip()
        if text:
            tasks_to_run.append((i, start, end, text))

    def process_item(item: tuple[int, float, float, str]) -> tuple[int, float, Path]:
        idx, start, end, text = item
        raw_mp3 = work_dir / f"seg_{idx:04d}_raw.mp3"
        out_wav = work_dir / f"seg_{idx:04d}_tempo.wav"
        generate_clip_sync(text, voice, raw_mp3)
        target_dur = max(0.2, end - start)
        adjust_audio_tempo(raw_mp3, out_wav, target_duration=target_dur)
        return idx, start, out_wav

    completed = 0
    max_workers = min(6, max(1, len(tasks_to_run))) if tasks_to_run else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(process_item, item): item for item in tasks_to_run}
        for future in as_completed(future_map):
            item = future_map[future]
            try:
                idx, start, out_wav = future.result()
                results_dict[idx] = (start, out_wav)
            except Exception as exc:
                failures += 1
                log.warning("Segment %d ovozlashtirishda xato: %s", item[0], exc)
            completed += 1
            if progress_cb and total:
                pct = progress_lo + (progress_hi - progress_lo) * (completed / total)
                progress_cb(pct, f"AI Ovozlashtirilmoqda ({completed}/{total}): {item[3][:35]}...")

    results = [results_dict[item[0]] for item in tasks_to_run if item[0] in results_dict]
    if total and not results:
        raise RuntimeError(
            "AI Dublyaj uchun birorta ovoz qatori yaratilolmadi. "
            "Internet, Edge-TTS va tanlangan ovozni tekshiring."
        )
    if failures:
        emit(
            "progress",
            message=f"Diqqat: {failures} qator ovozlashtirilmadi",
            progress=progress_hi,
        )
    return results


def build_speech_timeline_wav(
    placed_clips: list[tuple[float, Path]],
    total_duration: float,
    out_wav_path: Path,
    sample_rate: int = 24000,
) -> Path:
    """Barcha ovoz bo'laklarini aniq millisekund vaqtlari bo'yicha yagona WAV trekka joylaydi."""
    channels = 1
    sample_width = 2  # 16-bit PCM
    current_sample = 0

    with wave.open(str(out_wav_path), "wb") as out_f:
        out_f.setnchannels(channels)
        out_f.setsampwidth(sample_width)
        out_f.setframerate(sample_rate)

        ordered_clips = sorted(placed_clips, key=lambda x: x[0])
        target_total = max(0, int(total_duration * sample_rate))
        for index, (start_time, clip_path) in enumerate(ordered_clips):
            target_sample = max(0, int(start_time * sample_rate))
            # Bir segment keyingisining boshlanishidan oshmasin. Aks holda
            # eski kod uni ketma-ket yozib, keyingi ovozni noto'g'ri vaqtga
            # surib yuborardi.
            next_sample = target_total
            if index + 1 < len(ordered_clips):
                next_sample = max(0, int(ordered_clips[index + 1][0] * sample_rate))
            clip_end = min(target_total, next_sample)
            if target_sample > current_sample:
                gap = target_sample - current_sample
                out_f.writeframes(b"\x00" * (gap * sample_width))
                current_sample = target_sample

            if clip_path.exists():
                try:
                    with wave.open(str(clip_path), "rb") as clip_f:
                        available_frames = max(0, clip_end - current_sample)
                        frames = clip_f.readframes(available_frames)
                        out_f.writeframes(frames)
                        current_sample += len(frames) // sample_width
                except Exception as exc:
                    log.warning("Klipni ulab bo'lmadi %s: %s", clip_path, exc)

        # Video oxirigacha sukunat bilan to'ldirish
        if target_total > current_sample:
            rem = target_total - current_sample
            out_f.writeframes(b"\x00" * (rem * sample_width))

    return out_wav_path


def mix_dubbed_soundtrack(
    video_path: Path,
    speech_timeline_wav: Path,
    out_audio_path: Path,
    ducking_volume: float = 0.18,
) -> Path:
    """Asl video audiosi bilan yangi dublyaj ovozini aralashtiradi (Ducking)."""
    require_tool("ffmpeg")
    ducking_volume = max(0.0, min(1.0, float(ducking_volume)))
    has_audio = probe_audio_codec(video_path) != ""

    if not has_audio or ducking_volume <= 0.01:
        # Original ovoz yo'q yoki fon ovozi butunlay o'chirilgan
        cmd = [
            "ffmpeg", "-y",
            "-i", str(speech_timeline_wav),
            "-c:a", "aac", "-b:a", "192k",
            str(out_audio_path),
        ]
    else:
        # Asl audioni ducking_volume ga pasaytirib, dublyaj bilan qorishtirish
        filter_str = (
            f"[0:a:0]aformat=channel_layouts=stereo,volume={ducking_volume:.2f}[bg]; "
            "[1:a]aformat=channel_layouts=stereo[fg]; "
            "[bg][fg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[out]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(speech_timeline_wav),
            "-filter_complex", filter_str,
            "-map", "[out]",
            "-c:a", "aac", "-b:a", "192k",
            str(out_audio_path),
        ]

    res = run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"Audioni aralashtirishda ffmpeg xatosi: {res.stderr}")

    return out_audio_path


def create_dubbed_video(
    video_path: Path,
    dubbed_audio_path: Path,
    out_video_path: Path,
    ass_subtitle_path: Path | None = None,
    target_lang: str = "uz",
    source_lang: str = "en",
    multi_track: bool = True,
) -> Path:
    """Videoni qayta kodlamasdan (-c:v copy) ko'p tilli audio yo'laklar bilan yig'adi."""
    require_tool("ffmpeg")
    has_orig_audio = probe_audio_codec(video_path) != ""
    original_track_count = probe_audio_stream_count(video_path) if has_orig_audio else 0
    dub_title = "O'zbekcha AI Dublyaj" if target_lang.startswith("uz") else f"AI Dublyaj ({target_lang.upper()})"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(dubbed_audio_path),
    ]

    has_sub = ass_subtitle_path is not None and ass_subtitle_path.exists()
    if has_sub:
        cmd.extend(["-i", str(ass_subtitle_path)])

    # Video oqimi qayta kodlanmaydi — bir lahzada tayyor bo'ladi
    cmd.extend(["-map", "0:v", "-c:v", "copy"])

    if has_orig_audio and multi_track:
        # Bitta videoda ikkala audio yo'lagi ham bo'ladi:
        # 1-trek: Asl ovoz (Original)
        # 2-trek: O'zbekcha AI Dublyaj (Standart faol)
        cmd.extend([
            # Barcha asl audio treklar yo'qolmasdan saqlanadi. Dublyajning
            # chiqish indeksi ular sonidan keyin keladi.
            "-map", "0:a?",
            "-map", "1:a:0",
            "-c:a", "copy",
            "-metadata:s:a:0", f"language={source_lang}",
            "-metadata:s:a:0", "title=Asl ovoz (Original)",
            "-disposition:s:a:0", "0",
            f"-metadata:s:a:{max(1, original_track_count)}", f"language={target_lang}",
            f"-metadata:s:a:{max(1, original_track_count)}", f"title={dub_title}",
            f"-disposition:s:a:{max(1, original_track_count)}", "default",
        ])
    else:
        cmd.extend([
            "-map", "1:a",
            "-c:a", "copy",
            "-metadata:s:a:0", f"language={target_lang}",
            "-metadata:s:a:0", f"title={dub_title}",
            "-disposition:s:a:0", "default",
        ])

    if has_sub:
        sub_input_idx = 2
        is_mkv = out_video_path.suffix.lower() == ".mkv"
        cmd.extend([
            "-map", f"{sub_input_idx}:0",
            "-c:s", "copy" if is_mkv else "mov_text",
            "-metadata:s:s:0", f"language={target_lang}",
            "-metadata:s:s:0", "title=O'zbekcha subtitr",
        ])

    cmd.append(str(out_video_path))
    res = run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"Dublyajli videoni muxlashda xato: {res.stderr}")

    return out_video_path
