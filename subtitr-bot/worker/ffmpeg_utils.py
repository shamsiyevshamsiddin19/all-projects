"""ffmpeg yordamida audio ajratish va subtitr yozish (burn).

Subtitr uslubi: TOZA KONTUR (arxitektura 5.5) — oq matn, qora kontur,
fonsiz, pastda markazda.
"""
from __future__ import annotations

import os
import subprocess

from config import settings


def _run(cmd: list[str], cwd: str | None = None) -> None:
    """ffmpeg ni ishga tushiradi; xato bo'lsa stderr bilan istisno tashlaydi."""
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "ignore").strip()
        tail = err[-600:] if err else "noma'lum xato"
        raise RuntimeError(f"ffmpeg xato (kod {proc.returncode}): {tail}")


def extract_audio(in_path: str, audio_path: str) -> None:
    """Videodan audio ajratadi (MP3, 16kHz mono, 64k — Whisper uchun optimal).

    MP3 (siqilgan) WAV o'rniga: hajmi ~30x kichik (1.9MB/daq -> 0.48MB/daq),
    shuning uchun uzun videolar (45 daq+) Groq fayl-hajm chegarasiga sig'adi
    va yuklash tezroq. Nutq aniqligi 64k da deyarli o'zgarmaydi.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", in_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "libmp3lame",
        "-b:a", "64k",
        audio_path,
    ]
    _run(cmd)
    if not os.path.exists(audio_path):
        raise RuntimeError("Audio ajratib bo'lmadi")


def extract_audio_hq(in_path: str, audio_path: str) -> None:
    """Videodan TINGLASH uchun sifatli MP3 ajratadi (stereo, 44.1kHz, 192k).

    extract_audio() dan farqi: u Whisper uchun (16kHz mono 64k — past sifat,
    kichik hajm); bu esa "audio" rejimi uchun — foydalanuvchi eshitadi,
    shuning uchun to'liq stereo va yuqori bitrate.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", in_path,
        "-vn",
        "-c:a", "libmp3lame",
        "-q:a", "2",           # ~190kbps VBR — yaxshi sifat
        "-ar", "44100",
        audio_path,
    ]
    _run(cmd)
    if not os.path.exists(audio_path):
        raise RuntimeError("Audio ajratib bo'lmadi")


def probe_resolution(in_path: str) -> tuple[int, int]:
    """Video kenglik va balandligini aniqlaydi (ffprobe). Xato bo'lsa 1280x720."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0:s=x",
        os.path.abspath(in_path),
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = proc.stdout.decode("utf-8", "ignore").strip()
        w_str, h_str = out.split("x")[:2]
        width, height = int(w_str), int(h_str)
        if width > 0 and height > 0:
            return width, height
    except Exception:
        pass
    return 1280, 720


def split_audio(audio_path: str, chunk_seconds: int) -> list[tuple[str, float]]:
    """Uzun audioni ~chunk_seconds bo'laklarga bo'ladi (mp3 nusxa — tez, qayta
    kodlashsiz). Qaytaradi: [(bo'lak_yo'li, boshlanish_ofseti_sek), ...].

    Bo'lish imkonsiz bo'lsa (davomiylik topilmadi) — bitta bo'lak (asl fayl)."""
    dur = probe_duration(audio_path)
    if dur <= 0 or chunk_seconds <= 0:
        return [(audio_path, 0.0)]
    base, ext = os.path.splitext(audio_path)
    chunks: list[tuple[str, float]] = []
    i = 0
    start = 0.0
    while start < dur - 1.0:  # oxirgi <1s qoldiqni yangi bo'lak qilmaymiz
        cp = f"{base}.part{i}{ext}"
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",
            "-i", audio_path,
            "-t", str(chunk_seconds),
            "-c", "copy",
            cp,
        ]
        try:
            _run(cmd)
        except RuntimeError:
            break
        if os.path.exists(cp) and os.path.getsize(cp) > 0:
            chunks.append((cp, start))
        start += chunk_seconds
        i += 1
    return chunks or [(audio_path, 0.0)]


def probe_duration(in_path: str) -> float:
    """Video davomiyligini sekundда aniqlaydi (ffprobe). Xato bo'lsa 0.0."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        os.path.abspath(in_path),
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = proc.stdout.decode("utf-8", "ignore").strip()
        return float(out) if out else 0.0
    except (ValueError, OSError):
        return 0.0


def burn_subtitles(
    in_path: str, ass_path: str, out_path: str, src_height: int | None = None
) -> None:
    """ASS subtitrni videoga yozadi (burn).

    src_height berilsa va u BURN_MAX_HEIGHT dan katta bo'lsa — video avval o'sha
    balandlikka tushiriladi (kodlash tezroq, fayl kichik; subtitr tiniq qoladi,
    chunki libass yangi kadr o'lchamiga moslab chizadi). Windows'da filtrdagi
    drive-harf (C:) muammosini chetlab o'tish uchun ffmpeg .ass papkasida
    ishga tushiriladi va faqat fayl nomi beriladi.
    """
    ass_dir = os.path.dirname(os.path.abspath(ass_path))
    ass_name = os.path.basename(ass_path)

    # Balandlikni kamaytirish (faqat kattaroq bo'lsa) — scale AVVAL, keyin ass:
    # shunda subtitr to'g'ridan-to'g'ri kichik kadrga chizilib tiniq chiqadi.
    max_h = settings.burn_max_height
    if src_height and max_h and src_height > max_h:
        vf = f"scale=-2:{max_h},ass={ass_name}"
    else:
        vf = f"ass={ass_name}"
    cmd = [
        "ffmpeg", "-y",
        "-i", os.path.abspath(in_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", settings.sub_preset,
        "-crf", str(settings.sub_crf),
        "-threads", "0",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        os.path.abspath(out_path),
    ]
    _run(cmd, cwd=ass_dir)
    if not os.path.exists(out_path):
        raise RuntimeError("Subtitr videoga yozilmadi")
