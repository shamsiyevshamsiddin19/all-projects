"""Video va audio: yuklab olish, skanerlash, subtitr fayllari, ffprobe/ffmpeg."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable

from .core import FFMPEG, FFPROBE, KINO_DIR, ROOT, SUB_EXTS, Segment, TMP_DIR, VIDEO_EXTS, YTDLP, emit, ensure_dirs, is_url, require_tool, run, wrap_text


# Video sifati: foydalanuvchi tanlaydigan maksimal balandlik.
QUALITY_HEIGHTS = {"720": 720, "1080": 1080, "1440": 1440, "2160": 2160}
DEFAULT_QUALITY = os.getenv("SUB_QUALITY", "1080")


def quality_height(value: str | None) -> int:
    """Tanlangan sifatni piksel balandligiga aylantiradi."""
    return QUALITY_HEIGHTS.get(str(value or "").strip(), QUALITY_HEIGHTS[DEFAULT_QUALITY]
                               if DEFAULT_QUALITY in QUALITY_HEIGHTS else 1080)


# yt-dlp uchun JS dvigateli nomi, bir marta aniqlanadi.
#
# DIQQAT: bu o'zgaruvchi `js_runtime_args()` bilan BIR XIL modulda turishi
# shart — `global` e'loni faqat o'z modulining global nomiga qaraydi.
# Boshqa modulga ko'chirilsa, NameError bo'ladi va pyflakes buni ko'rmaydi.
_JS_RUNTIME_CACHE: str | None = None


def js_runtime_args() -> list[str]:
    """yt-dlp uchun JavaScript runtime argumenti.

    YouTube 2025 yildan beri format havolalarini JS "challenge" bilan yopadi:
    runtime bo'lmasa yt-dlp faqat 360p (format 18) ni ko'radi yoki umuman
    "This video is not available" deydi. Sukut bo'yicha faqat `deno` yoqilgan,
    shuning uchun tizimda topilgan runtime'ni o'zimiz ko'rsatamiz."""
    global _JS_RUNTIME_CACHE
    if _JS_RUNTIME_CACHE is None:
        for name in ("deno", "node", "bun"):
            if shutil.which(name):
                _JS_RUNTIME_CACHE = name
                break
        else:
            _JS_RUNTIME_CACHE = ""
    return ["--js-runtimes", _JS_RUNTIME_CACHE] if _JS_RUNTIME_CACHE else []


def update_ytdlp() -> dict[str, Any]:
    """yt-dlp'ni o'zini-o'zi yangilaydi (`yt-dlp -U`). Kino/video saytlar tez-tez
    o'zgargani uchun yuklovchini yangi tutish yuklashning ishlab turishini ta'minlaydi.
    Frozen exe yonidagi tools/yt-dlp.exe binarisi yangilanadi."""
    if not (os.path.isfile(YTDLP) or shutil.which(YTDLP)):
        return {"updated": False, "message": "yt-dlp topilmadi"}
    try:
        proc = subprocess.run(
            [YTDLP, "-U"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        out = ((proc.stdout or "") + (proc.stderr or "")).strip()
        low = out.lower()
        changed = "updating to" in low or "updated yt-dlp" in low
        return {"updated": changed, "message": out[-400:] if out else "yt-dlp allaqachon eng yangi"}
    except Exception as exc:  # noqa: BLE001 — yangilash majburiy emas, xatoni yumshoq qaytaramiz
        return {"updated": False, "message": f"Yangilab bo'lmadi: {exc}"}


def download_video(
    url: str,
    dest_dir: Path | None = None,
    use_cache: bool = True,
    progress_lo: float = 0.01,
    progress_hi: float = 0.05,
    quality: str | None = None,
    upscale: bool = False,
) -> Path:
    """yt-dlp qo'llab-quvvatlaydigan istalgan havoladan (YouTube, Instagram,
    kino saytlari va h.k.) videoni yuklab oladi.

    dest_dir=None bo'lsa — ishchi papkaga (qayta ishlash uchun, keshlanadi).
    Ko'rinadigan papka berilsa (masalan Videos/Yuklab olingan) — o'sha yerga toza
    nom bilan saqlaydi."""
    url = url.strip()
    if not (os.path.isfile(YTDLP) or shutil.which(YTDLP)):
        raise RuntimeError("yt-dlp topilmadi — havoladan yuklab bo'lmaydi.")

    dl_dir = dest_dir or (TMP_DIR / "yuklamalar")
    dl_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(url.encode("utf-8", "replace")).hexdigest()[:10]
    span = max(0.0, progress_hi - progress_lo)

    if use_cache:
        # Bir xil havola avval yuklangan bo'lsa — qaytadan yuklamaymiz.
        for existing in dl_dir.glob(f"*__{key}.*"):
            if existing.suffix.lower() in VIDEO_EXTS and existing.stat().st_size > 0:
                emit("progress", message="Video allaqachon yuklangan (keshdan)", progress=progress_lo)
                return existing
        out_tmpl = str(dl_dir / ("%(title).70s__" + key + ".%(ext)s"))
    else:
        out_tmpl = str(dl_dir / "%(title).120s.%(ext)s")

    emit("progress", message="Video havolasi tekshirilmoqda", progress=progress_lo)
    ffmpeg_dir = str(Path(FFMPEG).parent)
    max_height = quality_height(quality)

    def attempt(extra_args: list[str]) -> tuple[int, Path | None, list[str]]:
        cmd = [
            YTDLP, "--no-playlist", "--no-warnings", "--no-mtime",
            *js_runtime_args(),
            "-f", (
                f"bv*[height<={max_height}]+ba/b[height<={max_height}]/bv*+ba/b"
            ),
            "--merge-output-format", "mp4",
            "--ffmpeg-location", ffmpeg_dir,
            "--newline",
            "-o", out_tmpl,
            "--print", "after_move:filepath",
            *extra_args,
            url,
        ]
        # stderr'ni stdout'ga qo'shamiz — progress ba'zan stderr'da, ba'zan stdout'da
        # bo'ladi; bitta oqimda hammasini o'qib, ambiguity'dan qutulamiz.
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        tail: list[str] = []
        found: Path | None = None
        last_pct = -1
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip("\r\n")
            tail.append(line)
            if len(tail) > 40:
                tail.pop(0)
            m = re.search(r"\[download\]\s+([\d.]+)%", line)
            if m:
                try:
                    pct = int(float(m.group(1)))
                except ValueError:
                    pct = last_pct
                if pct != last_pct:
                    last_pct = pct
                    emit("progress", message=f"Video yuklab olinmoqda {pct}%",
                         progress=progress_lo + span * (pct / 100.0))
            elif line.strip() and not line.lstrip().startswith("[") and (
                line.strip().lower().endswith((".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi"))
            ):
                found = Path(line.strip())
        proc.wait()

        if found is None or not found.exists():
            # Zaxira: papkadagi eng yangi mos faylni topamiz.
            pattern = f"*__{key}.*" if use_cache else "*"
            candidates = [p for p in dl_dir.glob(pattern) if p.suffix.lower() in VIDEO_EXTS and p.stat().st_size > 0]
            found = max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None
        return proc.returncode, found, tail

    # YouTube vaqti-vaqti bilan ayrim "player client"larni bloklaydi va butunlay
    # ishlaydigan video uchun ham "This video is not available" deydi. Shu sababli
    # birinchi urinish muvaffaqiyatsiz bo'lsa, boshqa klientlar bilan qaytaramiz.
    attempts: list[list[str]] = [[]]
    if re.search(r"(youtube\.com|youtu\.be)", url, re.I):
        attempts += [
            ["--extractor-args", "youtube:player_client=android"],
            ["--extractor-args", "youtube:player_client=tv,web_safari,ios,mweb"],
        ]

    code, final_path, tail = 1, None, []
    for index, extra in enumerate(attempts):
        if index:
            emit("progress", message="Boshqa usul bilan qayta urinilmoqda", progress=progress_lo)
        code, final_path, tail = attempt(extra)
        if code == 0 and final_path is not None and final_path.exists():
            break

    if code != 0 or final_path is None or not final_path.exists():
        err = "\n".join(tail)[-600:] or "noma'lum"
        raise RuntimeError("Videoni yuklab bo'lmadi: " + err)
    emit("progress", message="Video yuklandi", progress=progress_hi)
    return final_path


def normalize_video_path(value: str, quality: str | None = None) -> Path:
    if is_url(value):
        return download_video(value, quality=quality)
    path = Path(value)
    if not path.is_absolute():
        local = (ROOT / value).resolve()
        if local.exists():
            path = local
        else:
            path = KINO_DIR / value
    path = path.resolve()
    if not path.exists():
        raise RuntimeError(f"Video topilmadi: {path}")
    if path.suffix.lower() not in VIDEO_EXTS:
        raise RuntimeError("Bu video formati qo'llab-quvvatlanmaydi")
    return path


def scan(target_dir: str | None = None) -> list[dict[str, Any]]:
    ensure_dirs()
    scan_path = Path(target_dir) if target_dir else KINO_DIR
    if not scan_path.exists() or not scan_path.is_dir():
        return []

    videos: list[dict[str, Any]] = []
    try:
        for path in sorted(scan_path.iterdir()):
            if path.is_dir():
                videos.append({
                    "name": path.name,
                    "path": str(path),
                    "size": 0,
                    "subtitle": "",
                    "subtitleName": "",
                    "isDir": True,
                })
            elif path.is_file() and path.suffix.lower() in VIDEO_EXTS:
                sidecar = find_sidecar_subtitle(path)
                videos.append({
                    "name": path.name,
                    "path": str(path),
                    "size": path.stat().st_size,
                    "subtitle": str(sidecar) if sidecar else "",
                    "subtitleName": sidecar.name if sidecar else "",
                    "isDir": False,
                })
    except Exception:
        pass
    return videos


def find_sidecar_subtitle(video: Path) -> Path | None:
    for ext in SUB_EXTS:
        candidate = video.with_suffix(ext)
        if candidate.exists():
            return candidate
    for candidate in video.parent.glob(video.stem + ".*"):
        if candidate.suffix.lower() in SUB_EXTS:
            return candidate
    return None


def strip_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("{\\an8}", "").replace("{\\an2}", "")
    return " ".join(text.split())


def srt_time_to_seconds(raw: str) -> float:
    raw = raw.strip().replace(",", ".")
    hms = raw.split(":")
    if len(hms) == 3:
        h, m, s = hms
        return int(h) * 3600 + int(m) * 60 + float(s)
    if len(hms) == 2:
        m, s = hms
        return int(m) * 60 + float(s)
    return float(raw)


def seconds_to_srt_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    m = (total_s // 60) % 60
    h = total_s // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def seconds_to_ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    cs = int(round(seconds * 100))
    total_s = cs // 100
    cs %= 100
    s = total_s % 60
    m = (total_s // 60) % 60
    h = total_s // 3600
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def read_subtitle_text(path: Path) -> str:
    """Read a subtitle file, guessing the encoding.

    Sidecar SRTs for Russian films are frequently Windows-1251 (cp1251), which
    is invalid UTF-8. We try UTF-8 first, then common single-byte code pages,
    and finally latin-1 (which never fails) so text is never garbled.
    """
    data = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1251", "cp1252", "cp1254"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")


def parse_srt(path: Path) -> list[Segment]:
    raw = read_subtitle_text(path)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", raw.strip())
    segments: list[Segment] = []
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        time_index = next((i for i, ln in enumerate(lines) if "-->" in ln), -1)
        if time_index < 0:
            continue
        start_raw, end_raw = [p.strip() for p in lines[time_index].split("-->", 1)]
        end_raw = end_raw.split()[0]
        text = strip_tags(" ".join(lines[time_index + 1:]))
        if not text:
            continue
        segments.append(Segment(srt_time_to_seconds(start_raw), srt_time_to_seconds(end_raw), text))
    return segments


def parse_vtt(path: Path) -> list[Segment]:
    raw = read_subtitle_text(path)
    raw = raw.replace("WEBVTT", "", 1)
    # Convert millisecond separators only inside timestamp lines so subtitle
    # text keeps its own periods (e.g. "Mr. Smith" stays intact).
    def _fix_timestamps(match: re.Match[str]) -> str:
        return match.group(0).replace(".", ",")

    raw = re.sub(r"\d{1,2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3}", _fix_timestamps, raw)
    tmp = TMP_DIR / (path.stem + "_from_vtt.srt")
    tmp.write_text(raw, encoding="utf-8")
    return parse_srt(tmp)


def write_srt(path: Path, segments: Iterable[Segment]) -> None:
    with path.open("w", encoding="utf-8-sig") as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{seconds_to_srt_time(seg.start)} --> {seconds_to_srt_time(seg.end)}\n")
            f.write(wrap_text(seg.text, 48) + "\n\n")


def probe_resolution(video: Path) -> tuple[int, int]:
    proc = run(
        [
            FFPROBE, "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x",
            str(video),
        ]
    )
    if proc.returncode == 0 and "x" in proc.stdout:
        try:
            w, h = proc.stdout.strip().split("x")[:2]
            return int(w), int(h)
        except Exception:
            pass
    return 1280, 720


def extract_embedded_subtitle(video: Path, tmp_dir: Path) -> Path | None:
    proc = run(
        [
            FFPROBE, "-v", "error",
            "-select_streams", "s",
            "-show_entries", "stream=index,codec_name",
            "-of", "json",
            str(video),
        ]
    )
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return None
    streams = data.get("streams") or []
    if not streams:
        return None
    out = tmp_dir / "embedded.srt"
    proc = run([FFMPEG, "-y", "-i", str(video), "-map", "0:s:0", str(out)])
    if proc.returncode == 0 and out.exists() and out.stat().st_size > 0:
        return out
    return None


def probe_duration_seconds(path: Path) -> float:
    proc = run(
        [
            FFPROBE, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    try:
        return float((proc.stdout or "").strip())
    except (TypeError, ValueError):
        return 0.0


def extract_audio(video: Path, audio_path: Path, lossless: bool = False) -> None:
    """Nutqni ajratib oladi (mono, 16 kHz).

    `lossless=False` — Groq'ga yuklash uchun kuchli siqilgan opus (tarmoq/limit).
    `lossless=True` — lokal Whisper uchun siqilmagan WAV: 12 kbit/s opus nutqni
    buzib, modelni yo'q so'zlarni "eshitish"ga majbur qiladi."""
    require_tool("ffmpeg")
    codec = ["-c:a", "pcm_s16le"] if lossless else ["-c:a", "libopus", "-b:a", "12k"]
    proc = run(
        [
            FFMPEG, "-y", "-i", str(video),
            "-vn", "-ac", "1", "-ar", "16000",
            *codec,
            str(audio_path),
        ]
    )
    if proc.returncode != 0:
        raise RuntimeError("Audio ajratishda xato: " + (proc.stderr[-700:] or "noma'lum"))
