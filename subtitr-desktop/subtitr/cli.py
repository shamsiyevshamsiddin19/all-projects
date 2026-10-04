"""Buyruq qatori interfeysi."""
from __future__ import annotations

import argparse

from .core import KINO_DIR, OUT_DIR, emit, ensure_dirs
from .media import DEFAULT_QUALITY, QUALITY_HEIGHTS, download_video, scan, update_ytdlp
from .pipeline import install_deps, prepare_session, process, render_session


def main() -> int:
    ensure_dirs()
    parser = argparse.ArgumentParser(description="Subtitr desktop local processor")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--dir", default=None)
    sub.add_parser("install-deps")

    p_process = sub.add_parser("process")
    p_process.add_argument("--video", required=True)
    p_process.add_argument(
        "--mode",
        default="dual_vocab",
        choices=["dual_vocab", "original_vocab", "dual", "original", "translated",
                 "srt", "transcript", "reading", "vocabulary", "all"],
    )
    p_process.add_argument("--source-lang", default="auto")
    p_process.add_argument("--target-lang", default="uz")
    p_process.add_argument("--font-scale", type=float, default=1.0)
    p_process.add_argument("--position", default="bottom", choices=["bottom", "top"])
    p_process.add_argument("--sub-color", default="#FFE680")
    p_process.add_argument("--orig-style", default="box", choices=["box", "plain"])
    p_process.add_argument("--quality", default=DEFAULT_QUALITY, choices=list(QUALITY_HEIGHTS))
    p_process.add_argument("--upscale", action="store_true",
                           help="manba past sifatli bo'lsa ham tanlangan o'lchamga kattalashtirish")

    p_download = sub.add_parser("download")
    p_download.add_argument("--url", required=True)
    p_download.add_argument("--quality", default=DEFAULT_QUALITY, choices=list(QUALITY_HEIGHTS))

    sub.add_parser("update-ytdlp")

    # #1 — ikki bosqichli oqim: transkripsiya+tarjima (prepare) → tahrir → render.
    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("--video", required=True)
    p_prepare.add_argument(
        "--mode",
        default="dual_vocab",
        choices=["dual_vocab", "original_vocab", "dual", "original", "translated",
                 "srt", "transcript", "reading", "vocabulary", "all"],
    )
    p_prepare.add_argument("--source-lang", default="auto")
    p_prepare.add_argument("--target-lang", default="uz")
    p_prepare.add_argument("--quality", default=DEFAULT_QUALITY, choices=list(QUALITY_HEIGHTS))

    p_render = sub.add_parser("render")
    p_render.add_argument("--session", required=True)
    p_render.add_argument("--segments", default=None)
    p_render.add_argument("--font-scale", type=float, default=1.0)
    p_render.add_argument("--position", default="bottom", choices=["bottom", "top"])
    p_render.add_argument("--sub-color", default="#FFE680")
    p_render.add_argument("--orig-style", default="box", choices=["box", "plain"])
    p_render.add_argument("--quality", default=DEFAULT_QUALITY, choices=list(QUALITY_HEIGHTS))
    p_render.add_argument("--upscale", action="store_true")

    args = parser.parse_args()
    try:
        if args.command == "scan":
            emit("done", videos=scan(args.dir), kinoDir=str(KINO_DIR), outDir=str(OUT_DIR))
        elif args.command == "install-deps":
            install_deps()
        elif args.command == "download":
            dest = KINO_DIR / "Yuklab olingan"
            path = download_video(
                args.url, dest_dir=dest, use_cache=False,
                progress_lo=0.0, progress_hi=1.0, quality=args.quality,
            )
            emit("done", path=str(path), name=path.name, dir=str(dest))
        elif args.command == "update-ytdlp":
            emit("done", **update_ytdlp())
        elif args.command == "prepare":
            result = prepare_session(
                args.video, args.mode, args.source_lang, args.target_lang,
                quality=args.quality,
            )
            emit("done", **result)
        elif args.command == "render":
            result = render_session(
                args.session, segments_path=args.segments,
                font_scale=args.font_scale, position=args.position, sub_color=args.sub_color,
                orig_style=args.orig_style, quality=args.quality,
                upscale=args.upscale,
            )
            emit("done", **result)
        elif args.command == "process":
            result = process(
                args.video, args.mode, args.source_lang, args.target_lang,
                font_scale=args.font_scale, position=args.position, sub_color=args.sub_color,
                orig_style=args.orig_style, quality=args.quality,
                upscale=args.upscale,
            )
            emit("done", **result)
        return 0
    except Exception as exc:
        emit("error", message=str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
