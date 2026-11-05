"""AI Dublyaj va ko'p tilli audio treklar moduli (Cinema Studio Grade).

Videodagi gaplarni sun'iy intellekt (Microsoft Edge TTS) orqali o'zbekcha
(yoki boshqa tilda) ovozlashtiradi, kino darajasidagi mastering filtrlari
(Highpass, Warm EQ, De-esser, Kompressor, Micro-fade) bilan boyitadi,
original xorijiy nutqni fondan tozalaydi (AI Stem Separation / Demucs),
musiqa va tovush effektlarini 100% tiniq saqlaydi hamda ko'p tilli audio
yo'lakchalari bilan montajsiz birlashtiradi.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import sys
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

LANG_CHARACTERS: dict[str, dict[str, str]] = {
    "uz": {"male": "uz-UZ-SardorNeural", "female": "uz-UZ-MadinaNeural"},
    "ru": {"male": "ru-RU-DmitryNeural", "female": "ru-RU-SvetlanaNeural"},
    "en": {"male": "en-US-GuyNeural", "female": "en-US-JennyNeural"},
    "tr": {"male": "tr-TR-AhmetNeural", "female": "tr-TR-EmelNeural"},
    "kk": {"male": "kk-KZ-DauletNeural", "female": "kk-KZ-AigulNeural"},
}

VOICE_CATALOG: dict[str, list[dict[str, str]]] = {
    "uz": [
        {"id": "auto", "name": "Kino (Avto: Erkak + Ayol)", "gender": "multi", "lang": "O'zbekcha"},
        {"id": "uz-UZ-SardorNeural", "name": "Sardor", "gender": "male", "lang": "O'zbekcha"},
        {"id": "uz-UZ-MadinaNeural", "name": "Madina", "gender": "female", "lang": "O'zbekcha"},
    ],
    "ru": [
        {"id": "auto", "name": "Кино (Авто: Мужчина + Женщина)", "gender": "multi", "lang": "Ruscha"},
        {"id": "ru-RU-DmitryNeural", "name": "Dmitriy", "gender": "male", "lang": "Ruscha"},
        {"id": "ru-RU-SvetlanaNeural", "name": "Svetlana", "gender": "female", "lang": "Ruscha"},
    ],
    "en": [
        {"id": "auto", "name": "Cinema (Auto: Male + Female)", "gender": "multi", "lang": "Inglizcha"},
        {"id": "en-US-GuyNeural", "name": "Guy", "gender": "male", "lang": "Inglizcha"},
        {"id": "en-US-JennyNeural", "name": "Jenny", "gender": "female", "lang": "Inglizcha"},
    ],
    "tr": [
        {"id": "auto", "name": "Sinema (Otomatik: Erkek + Kadın)", "gender": "multi", "lang": "Turkcha"},
        {"id": "tr-TR-AhmetNeural", "name": "Ahmet", "gender": "male", "lang": "Turkcha"},
        {"id": "tr-TR-EmelNeural", "name": "Emel", "gender": "female", "lang": "Turkcha"},
    ],
    "kk": [
        {"id": "auto", "name": "Кино (Авто: Ер + Әйел)", "gender": "multi", "lang": "Qozoqcha"},
        {"id": "kk-KZ-DauletNeural", "name": "Daulet", "gender": "male", "lang": "Qozoqcha"},
        {"id": "kk-KZ-AigulNeural", "name": "Aigul", "gender": "female", "lang": "Qozoqcha"},
    ],
}

VOICES = {
    "auto": "auto",
    "multi": "auto",
    "kino": "auto",
    "sardor": "uz-UZ-SardorNeural",
    "madina": "uz-UZ-MadinaNeural",
    "dmitry": "ru-RU-DmitryNeural",
    "dmitriy": "ru-RU-DmitryNeural",
    "svetlana": "ru-RU-SvetlanaNeural",
    "guy": "en-US-GuyNeural",
    "jenny": "en-US-JennyNeural",
    "ahmet": "tr-TR-AhmetNeural",
    "emel": "tr-TR-EmelNeural",
    "daulet": "kk-KZ-DauletNeural",
    "aigul": "kk-KZ-AigulNeural",
}


def resolve_voice(voice_name: str | None, target_lang: str = "uz") -> str:
    """Ovoz nomini to'liq Edge TTS ovoz identifikatoriga aylantiradi."""
    code = (target_lang or "uz").split("-")[0].lower()
    if not voice_name:
        return DEFAULT_LANG_VOICES.get(code, DEFAULT_VOICE)

    key = voice_name.strip().lower()
    if key in {"auto", "multi", "kino"}:
        return "auto"
    if key in VOICES:
        return VOICES[key]
    if "neural" in key:
        return voice_name.strip()
    return DEFAULT_LANG_VOICES.get(code, DEFAULT_VOICE)


def resolve_voice_for_segment(
    voice_choice: str | None,
    target_lang: str = "uz",
    gender: str = "male",
    seg_index: int = 0,
) -> tuple[str, str]:
    """Segment uchun mos ovoz ID va nozik pitch parametrini qaytaradi."""
    code = (target_lang or "uz").split("-")[0].lower()
    resolved = resolve_voice(voice_choice, target_lang=code)

    if resolved == "auto":
        char_map = LANG_CHARACTERS.get(code, LANG_CHARACTERS["uz"])
        chosen_voice = char_map.get(gender, char_map["male"])
        return chosen_voice, "+0Hz"

    return resolved, "+0Hz"


def estimate_natural_speech_duration(text: str, chars_per_second: float = 14.5) -> float:
    """O'rtacha gapirish sur'atidan kelib chiqib tabiiy davomiylikni baholaydi."""
    clean = " ".join((text or "").split())
    if not clean:
        return 0.5
    return max(0.5, len(clean) / max(8.0, chars_per_second))


def compute_speech_rate(text: str, target_duration: float) -> str:
    """Matn hajmi va ajratilgan vaqtga qarab Edge TTS rate parametrini hisoblaydi."""
    if target_duration <= 0.1:
        return "+0%"
    natural_dur = estimate_natural_speech_duration(text)
    ratio = natural_dur / target_duration
    if ratio > 1.08:
        pct = min(35, max(5, int((ratio - 1.0) * 100)))
        return f"+{pct}%"
    elif ratio < 0.70 and natural_dur >= 0.8:
        pct = max(-15, min(-5, int((ratio - 1.0) * 100)))
        return f"{pct}%"
    return "+0%"


async def _generate_single_clip(
    text: str,
    voice: str,
    out_path: Path,
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> None:
    """Bitta gapni TTS orqali MP3 faylga aylantiradi."""
    if edge_tts is None:
        raise RuntimeError("edge-tts kutubxonasi o'rnatilmagan ('pip install edge-tts')")
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(str(out_path))


def generate_clip_sync(
    text: str,
    voice: str,
    out_path: Path,
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> None:
    """Sinxron oqimdan TTS chaqirish uchun wrapper."""
    asyncio.run(_generate_single_clip(text, voice, out_path, rate=rate, pitch=pitch))


def estimate_speaker_gender(audio_path: Path, start: float, end: float) -> str:
    """Audio segmentidagi aktyor ovozi chastotasi (F0) orqali jinsini aniqlaydi.

    Erkak ovozi F0: 80Hz - 165Hz
    Ayol ovozi F0: 165Hz - 260Hz
    """
    if not audio_path.exists() or end <= start:
        return "male"
    mid = (start + end) / 2.0
    dur = min(0.4, max(0.12, end - start))
    start_cut = max(0.0, mid - dur / 2.0)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        tmp_wav = Path(tf.name)
    try:
        res = run([
            "ffmpeg", "-y", "-ss", f"{start_cut:.3f}", "-t", f"{dur:.3f}",
            "-i", str(audio_path),
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            str(tmp_wav),
        ])
        if res.returncode != 0 or not tmp_wav.exists() or tmp_wav.stat().st_size < 200:
            return "male"

        with wave.open(str(tmp_wav), "rb") as wf:
            frames = wf.readframes(wf.getnframes())

        if len(frames) < 1600:
            return "male"

        import numpy as np
        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
        rms = np.sqrt(np.mean(samples ** 2))
        if rms < 250:
            return "male"

        min_lag = int(16000 / 340)
        max_lag = int(16000 / 75)
        corr = np.correlate(samples, samples, mode="full")
        corr = corr[len(corr) // 2:]
        if len(corr) < max_lag:
            return "male"

        peak_idx = min_lag + int(np.argmax(corr[min_lag:max_lag]))
        f0 = 16000.0 / peak_idx if peak_idx > 0 else 120.0
        return "female" if f0 > 165.0 else "male"
    except Exception as exc:
        log.debug("Ovoz jinsini aniqlashda ogohlantirish: %s", exc)
        return "male"
    finally:
        if tmp_wav.exists():
            tmp_wav.unlink(missing_ok=True)


def separate_audio_stems(
    video_or_audio_path: Path,
    work_dir: Path,
    model_name: str = "htdemucs",
    progress_cb: Callable[[float, str], None] | None = None,
    progress_lo: float = 0.45,
    progress_hi: float = 0.65,
) -> tuple[Path, Path]:
    """Videodagi asl audioni 2 yo'lakka ajratadi:
    1. `bg_track`: BGM + SFX (musiqa, portlashlar, atrof-muhit shovqini - toza fon)
    2. `vocals_track`: Asl chet tili aktyor ovozi (o'chirilishi yoki tahlil uchun)

    Agar tizimda Demucs bo'lsa, AI Stem Separation modelidan foydalanadi.
    Aks holda FFmpeg ning center-channel vocal reduction filtri orqali tezkor ajratadi.
    """
    require_tool("ffmpeg")
    work_dir.mkdir(parents=True, exist_ok=True)
    bg_track = work_dir / "bg_music_sfx.wav"
    vocals_track = work_dir / "original_vocals.wav"

    if not video_or_audio_path.exists() or video_or_audio_path.stat().st_size < 500:
        bg_track.touch()
        vocals_track.touch()
        return bg_track, vocals_track

    raw_audio = work_dir / "orig_extracted.wav"
    run([
        "ffmpeg", "-y", "-i", str(video_or_audio_path),
        "-vn", "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le",
        str(raw_audio),
    ])
    if not raw_audio.exists() or raw_audio.stat().st_size < 100:
        bg_track.touch()
        vocals_track.touch()
        return bg_track, vocals_track

    use_demucs = os.getenv("DUBBING_USE_DEMUCS", "1").strip().lower() not in {"0", "false", "no"}
    if use_demucs:
        try:
            import demucs  # noqa: F401
            if progress_cb:
                progress_cb(progress_lo, "AI Vokal izolyatsiyasi (Demucs: musiqa va nutq ajratilmoqda)...")
            demucs_out = work_dir / "demucs_stems"
            demucs_out.mkdir(parents=True, exist_ok=True)
            cmd = [
                sys.executable, "-m", "demucs.separate",
                "-n", model_name,
                "--two-stems", "vocals",
                "-d", "cpu",
                "-j", "4",
                "-o", str(demucs_out),
                str(raw_audio),
            ]
            res = run(cmd)
            stem_dir = demucs_out / model_name / raw_audio.stem
            d_no_vocals = stem_dir / "no_vocals.wav"
            d_vocals = stem_dir / "vocals.wav"
            if res.returncode == 0 and d_no_vocals.exists() and d_vocals.exists():
                shutil.copy(str(d_no_vocals), str(bg_track))
                shutil.copy(str(d_vocals), str(vocals_track))
                log.info("Demucs AI vokal ajratish muvaffaqiyatli yakunlandi")
                return bg_track, vocals_track
            else:
                log.warning("Demucs stem topilmadi, FFmpeg zaxira filtriga o'tilmoqda: %s", res.stderr)
        except Exception as exc:
            log.warning("Demucs chaqirishda xato (%s), FFmpeg zaxirasiga o'tilmoqda", exc)

    if progress_cb:
        progress_cb(progress_lo + (progress_hi - progress_lo) * 0.5, "Kino filtrlari: markaziy vokal tozalash...")

    flt_bg = (
        "[0:a]aformat=channel_layouts=stereo,"
        "stereotools=mlev=0.08:slev=1.2,"
        "equalizer=f=1200:t=q:w=1.0:g=-12,"
        "highpass=f=45[bg]"
    )
    run([
        "ffmpeg", "-y", "-i", str(raw_audio),
        "-filter_complex", flt_bg,
        "-map", "[bg]",
        "-ar", "44100", "-c:a", "pcm_s16le",
        str(bg_track),
    ])
    shutil.copy(str(raw_audio), str(vocals_track))
    return bg_track, vocals_track


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

    ratio = actual_dur / max(0.1, target_duration)
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
    target_lang: str = "uz",
    reference_audio: Path | None = None,
) -> list[tuple[float, Path]]:
    """Barcha tarjima qilingan segmentlarni parallel ravishda TTS ovoziga aylantiradi."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    work_dir.mkdir(parents=True, exist_ok=True)
    results_dict: dict[int, tuple[float, Path]] = {}
    failures = 0
    total = len(segments)

    tasks_to_run: list[tuple[int, float, float, str, str, str]] = []
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
            gender = "male"
            if reference_audio and (voice in {"auto", "multi"} or "neural" not in voice.lower()):
                gender = estimate_speaker_gender(reference_audio, start, end)
            seg_voice, seg_pitch = resolve_voice_for_segment(voice, target_lang=target_lang, gender=gender, seg_index=i)
            tasks_to_run.append((i, start, end, text, seg_voice, seg_pitch))

    def process_item(item: tuple[int, float, float, str, str, str]) -> tuple[int, float, Path]:
        idx, start, end, text, seg_voice, seg_pitch = item
        raw_mp3 = work_dir / f"seg_{idx:04d}_raw.mp3"
        out_wav = work_dir / f"seg_{idx:04d}_tempo.wav"
        target_dur = max(0.2, end - start)
        rate_str = compute_speech_rate(text, target_dur)
        generate_clip_sync(text, seg_voice, raw_mp3, rate=rate_str, pitch=seg_pitch)
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

        if target_total > current_sample:
            rem = target_total - current_sample
            out_f.writeframes(b"\x00" * (rem * sample_width))

    return out_wav_path


def mix_dubbed_soundtrack(
    video_path: Path,
    speech_timeline_wav: Path,
    out_audio_path: Path,
    ducking_volume: float = 0.18,
    dynamic: bool = False,
    isolated_bg_wav: Path | None = None,
) -> Path:
    """Asl video audiosi bilan yangi dublyaj ovozini aralashtiradi.

    `isolated_bg_wav` berilganda (AI Stem Separation orqali tozalangan fon),
    original xorijiy aktyor nutqi 0% eshitiladi, orqa fondagi musiqa va ovoz effektlari
    esa 100% toza va tiniq qoladi!
    `dynamic=True` bo'lganda sidechaincompress orqali dublyaj nutqi paytida fon musiqasi
    mayin pasayadi (ducking), nutq yo'q paytda esa to'liq jarangdorlik saqlanadi.
    """
    require_tool("ffmpeg")
    ducking_volume = max(0.0, min(1.0, float(ducking_volume)))

    vocal_chain = (
        "highpass=f=80,"
        "equalizer=f=250:t=q:w=1.2:g=1.5,"
        "equalizer=f=3400:t=q:w=1.8:g=-2.5,"
        "acompressor=threshold=-16dB:ratio=3.5:attack=15:release=120:makeup=2,"
        "volume=1.15,"
        "alimiter=limit=0.95"
    )

    if ducking_volume <= 0.01:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(speech_timeline_wav),
            "-af", vocal_chain,
            "-c:a", "aac", "-b:a", "192k",
            str(out_audio_path),
        ]
        res = run(cmd)
        if res.returncode != 0:
            raise RuntimeError(f"Audioni saqlashda ffmpeg xatosi: {res.stderr}")
        return out_audio_path

    bg_input = isolated_bg_wav if (isolated_bg_wav and isolated_bg_wav.exists()) else video_path
    has_audio = probe_audio_codec(bg_input) != ""

    if not has_audio:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(speech_timeline_wav),
            "-af", vocal_chain,
            "-c:a", "aac", "-b:a", "192k",
            str(out_audio_path),
        ]
        res = run(cmd)
        if res.returncode != 0:
            raise RuntimeError(f"Audioni saqlashda ffmpeg xatosi: {res.stderr}")
        return out_audio_path

    is_stem = (isolated_bg_wav is not None and isolated_bg_wav.exists())
    bg_vol = min(1.0, max(0.20, ducking_volume * 3.0)) if is_stem else ducking_volume

    if dynamic:
        compress_ratio = max(3.0, min(10.0, (1.0 - ducking_volume) * 8.0))
        sc_thresh = 0.035
        filter_dynamic = (
            f"[1:a]aformat=channel_layouts=stereo,{vocal_chain},asplit[sc][fg]; "
            f"[0:a]aformat=channel_layouts=stereo,volume={bg_vol:.2f}[bg]; "
            f"[bg][sc]sidechaincompress=threshold={sc_thresh:.3f}:ratio={compress_ratio:.1f}:attack=20:release=280[ducked_bg]; "
            "[ducked_bg][fg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[out]"
        )
        cmd_dyn = [
            "ffmpeg", "-y",
            "-i", str(bg_input),
            "-i", str(speech_timeline_wav),
            "-filter_complex", filter_dynamic,
            "-map", "[out]",
            "-c:a", "aac", "-b:a", "192k",
            str(out_audio_path),
        ]
        res_dyn = run(cmd_dyn)
        if res_dyn.returncode == 0:
            return out_audio_path
        log.warning("Dinamik sidechaincompress ishlamadi, statik aralashtirishga o'tilmoqda: %s", res_dyn.stderr)

    filter_str = (
        f"[0:a]aformat=channel_layouts=stereo,volume={bg_vol:.2f}[bg]; "
        f"[1:a]aformat=channel_layouts=stereo,{vocal_chain}[fg]; "
        "[bg][fg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[out]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(bg_input),
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


def preview_voice_sample(voice: str, out_wav: Path, sample_text: str | None = None) -> Path:
    """Ovoz namunasini eshitish uchun qisqa audio fayl yaratadi."""
    require_tool("ffmpeg")
    text = sample_text or "Assalomu alaykum! Men sun'iy intellekt orqali videolaringizni professional ovozlashtirib beraman."
    raw_mp3 = out_wav.with_suffix(".mp3")
    resolved_voice = "uz-UZ-SardorNeural" if voice in {"auto", "multi"} else resolve_voice(voice)
    generate_clip_sync(text, resolved_voice, raw_mp3, rate="+0%")
    run([
        "ffmpeg", "-y", "-i", str(raw_mp3),
        "-ar", "24000", "-ac", "1",
        str(out_wav),
    ])
    if raw_mp3.exists():
        raw_mp3.unlink(missing_ok=True)
    return out_wav


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

    cmd.extend(["-map", "0:v", "-c:v", "copy"])

    if has_orig_audio and multi_track:
        cmd.extend([
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
            "-metadata:s:s:0", f"title=O'zbekcha subtitr",
        ])

    cmd.append(str(out_video_path))
    res = run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"Dublyajli videoni muxlashda xato: {res.stderr}")

    return out_video_path
