"""Pinterest media extractor and downloader for CaptionFlow / Subtitr Desktop.

Supports:
- Pinterest Videos (MP4 in highest available resolution: 1080p, 720p, etc.)
- Pinterest Animated GIFs (.gif)
- Pinterest High-Res Images (.jpg, .png, .webp in original uncompressed quality)
- Both standard URLs (pinterest.com/pin/...) and shortlinks (pin.it/...)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .core import TMP_DIR, emit


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|\r\n\t]', "_", name).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "pinterest_media"


PINTEREST_DOMAIN_RE = re.compile(r"(?:pinterest\.[a-z.]+|pin\.it)", re.I)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,uz;q=0.8,ru;q=0.7",
}


def is_pinterest_url(url: str) -> bool:
    """Tekshiradi: havola Pinterest yoki pin.it domeniga tegishlimi."""
    if not url or not isinstance(url, str):
        return False
    clean = url.strip()
    return bool(PINTEREST_DOMAIN_RE.search(clean))


def resolve_pinterest_url(url: str, timeout: float = 12.0) -> str:
    """pin.it qisqa havolalarini asl to'liq pinterest.com/pin/... manziliga ochadi."""
    clean = url.strip()
    if not clean.startswith(("http://", "https://")):
        clean = "https://" + clean

    req = urllib.request.Request(clean, headers=DEFAULT_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.geturl()
    except Exception:
        # Agar tarmoqda xato bersa, asl URL bilan davom etamiz
        return clean


def _extract_title(html: str, default_id: str = "media") -> str:
    """Pinterest sahifasidan post sarlavhasini oladi."""
    # 1. JSON ichidan title
    tm = re.search(r'"title":\s*"([^"]+)"', html)
    if tm:
        val = tm.group(1).encode("utf-8").decode("unicode_escape", errors="ignore").strip()
        if val and val.lower() != "null":
            return _clean_title(val)

    # 2. OpenGraph og:title
    og = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html, re.I)
    if not og:
        og = re.search(r'<meta\s+name=["\']title["\']\s+content=["\']([^"\']+)["\']', html, re.I)
    if og:
        val = og.group(1).strip()
        if val:
            return _clean_title(val)

    # 3. HTML title tegi
    t = re.search(r'<title>(.*?)</title>', html, re.I | re.DOTALL)
    if t:
        val = t.group(1).strip()
        if val:
            return _clean_title(val)

    return f"pinterest_{default_id}"


def _clean_title(title: str) -> str:
    """Sarlavhadan Pinterest qo'shimchalarini tozalaydi."""
    title = re.sub(r"\s*\|\s*Pinterest.*$", "", title, flags=re.I)
    title = re.sub(r"\s*-\s*Pinterest.*$", "", title, flags=re.I)
    title = re.sub(r"\s+on\s+Pinterest.*$", "", title, flags=re.I)
    cleaned = sanitize_filename(title.strip())
    return cleaned[:70] if cleaned else "pinterest_media"


def extract_pinterest_media(url: str, timeout: float = 14.0) -> dict[str, Any]:
    """Pinterest havolasidan rasm, video yoki gif URL manzilini ajratib oladi."""
    final_url = resolve_pinterest_url(url, timeout=timeout)
    pin_id_match = re.search(r"/pin/(\d+)", final_url)
    pin_id = pin_id_match.group(1) if pin_id_match else "media"

    req = urllib.request.Request(final_url, headers=DEFAULT_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        raise RuntimeError(f"Pinterest sahifasini ochib bo'lmadi: {e}") from e

    title = _extract_title(html, default_id=pin_id)

    # --- 1. Video tekshiruvi ---
    mp4_urls = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', html)
    if mp4_urls:
        unique_vids = list(dict.fromkeys(mp4_urls))
        # Sifatiga ko'ra saralash: 1080p > 720p > 480p > boshqa
        def video_rank(u: str) -> int:
            u_low = u.lower()
            if "1080p" in u_low: return 4
            if "720p" in u_low: return 3
            if "480p" in u_low: return 2
            if "mobile" in u_low: return 1
            return 0

        best_video = sorted(unique_vids, key=video_rank, reverse=True)[0]
        return {
            "type": "video",
            "url": best_video,
            "title": title,
            "ext": ".mp4",
            "pin_id": pin_id,
        }

    # --- 2. GIF tekshiruvi ---
    gif_urls = re.findall(r'https?://[^\s"\'<>]+\.gif[^\s"\'<>]*', html)
    if gif_urls:
        best_gif = gif_urls[0]
        # Agar 736x yoki 564x bo'lsa, originals ga o'tkazish
        best_gif = re.sub(r"/(?:736x|564x|474x|236x)/", "/originals/", best_gif)
        return {
            "type": "gif",
            "url": best_gif,
            "title": title,
            "ext": ".gif",
            "pin_id": pin_id,
        }

    # --- 3. Rasm (Image) tekshiruvi ---
    # Asl sifatdagi rasmlar: i.pinimg.com/originals/...
    orig_imgs = re.findall(
        r'https?://i\.pinimg\.com/originals/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)',
        html,
        re.I,
    )
    if orig_imgs:
        best_img = orig_imgs[0]
        ext = "." + best_img.split(".")[-1].split("?")[0].lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            ext = ".jpg"
        return {
            "type": "image",
            "url": best_img,
            "title": title,
            "ext": ext,
            "pin_id": pin_id,
        }

    # Zaxira: 736x yoki boshqa sifatdagi rasmni originals ga o'tkazish
    other_imgs = re.findall(
        r'https?://i\.pinimg\.com/(?:736x|564x|474x|236x)/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)',
        html,
        re.I,
    )
    if other_imgs:
        transformed = re.sub(r"/(?:736x|564x|474x|236x)/", "/originals/", other_imgs[0])
        ext = "." + transformed.split(".")[-1].split("?")[0].lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            ext = ".jpg"
        return {
            "type": "image",
            "url": transformed,
            "title": title,
            "ext": ext,
            "pin_id": pin_id,
        }

    raise RuntimeError("Pinterest havolasidan rasm, video yoki gif topilmadi.")


def download_pinterest_media(
    url: str,
    dest_dir: Path | None = None,
    use_cache: bool = True,
    progress_lo: float = 0.01,
    progress_hi: float = 0.99,
    quality: str | None = None,
) -> Path:
    """Pinterest havolasidagi rasm, video yoki gifni to'g'ridan-to'g'ri yuklab oladi.

    Yuklab olingan fayl `dest_dir` ga saqlanadi va uning Path obyekti qaytariladi.
    """
    emit("progress", message="Pinterest havolasi tahlil qilinmoqda", progress=progress_lo)
    media_info = extract_pinterest_media(url)

    media_type = media_info["type"]
    media_url = media_info["url"]
    title = media_info["title"]
    ext = media_info["ext"]

    type_label = "video" if media_type == "video" else ("gif" if media_type == "gif" else "rasm")
    emit("progress", message=f"Pinterest {type_label} topildi: {title}", progress=progress_lo + 0.05)

    target_dir = dest_dir or (TMP_DIR / "yuklamalar")
    target_dir.mkdir(parents=True, exist_ok=True)

    cache_key = hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:12]

    if use_cache:
        # Agar avval yuklangan bo'lsa, mavjud faylni qaytarish
        for existing in target_dir.glob(f"*__{cache_key}.*"):
            if existing.stat().st_size > 0:
                emit("progress", message=f"Pinterest {type_label} keshdan olindi", progress=progress_hi)
                return existing

        out_name = f"{title}__{cache_key}{ext}"
    else:
        out_name = f"{title}{ext}"

    out_path = target_dir / out_name
    # Nom takrorlanishining oldini olish
    counter = 1
    while not use_cache and out_path.exists():
        out_path = target_dir / f"{title}_{counter}{ext}"
        counter += 1

    temp_path = out_path.with_suffix(out_path.suffix + ".part")
    if temp_path.exists():
        temp_path.unlink()

    req = urllib.request.Request(media_url, headers=DEFAULT_HEADERS)
    span = max(0.01, progress_hi - (progress_lo + 0.05))

    try:
        with urllib.request.urlopen(req, timeout=30) as resp, open(temp_path, "wb") as f:
            total_size = int(resp.headers.get("Content-Length") or 0)
            downloaded = 0
            chunk_size = 64 * 1024  # 64 KB
            last_reported_pct = -1

            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)

                if total_size > 0:
                    pct = int((downloaded / total_size) * 100)
                    if pct != last_reported_pct and pct % 5 == 0:
                        last_reported_pct = pct
                        emit(
                            "progress",
                            message=f"Pinterest {type_label} yuklanmoqda {pct}%",
                            progress=progress_lo + 0.05 + span * (downloaded / total_size),
                        )

        temp_path.replace(out_path)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise RuntimeError(f"Pinterest {type_label}ni yuklab bo'lmadi: {e}") from e

    emit("progress", message=f"Pinterest {type_label} muvaffaqiyatli yuklandi", progress=progress_hi)
    return out_path
