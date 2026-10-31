"""Buyruq qatori interfeysi."""
from __future__ import annotations

import argparse
import traceback

from .cache import cache_usage, clear_cache
from .core import KINO_DIR, LOG_DIR, OUT_DIR, clean_orphan_tmp, current_log_file, emit, ensure_dirs, install_signal_handlers, log, redact, setup_logging
from .media import DEFAULT_QUALITY, QUALITY_HEIGHTS, download_video, playlist_entries, scan, update_ytdlp
from .pipeline import install_deps, prepare_session, preview_frame, process, render_session, retranslate_session_segment, subtitle_file


def main() -> int:
    ensure_dirs()
    setup_logging()
    install_signal_handlers()
    # Oldingi uzilgan ishlardan qolgan papkalar (SIGKILL yoki dastur tushishi)
    # shu yerda tozalanadi — ular keshda yuzlab megabayt egallab turardi.
    clean_orphan_tmp()
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
                 "softsub", "srt", "transcript", "reading", "vocabulary", "all"],
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
    p_process.add_argument("--subtitle", default=None, help="tashqi SRT/VTT/ASS/SSA fayl")
    p_process.add_argument("--subtitle-offset", type=float, default=0.0,
                           help="import qilingan subtitr uchun umumiy soniya siljishi")

    p_download = sub.add_parser("download")
    p_download.add_argument("--url", required=True)
    p_download.add_argument("--quality", default=DEFAULT_QUALITY, choices=list(QUALITY_HEIGHTS))

    p_playlist = sub.add_parser("playlist")
    p_playlist.add_argument("--url", required=True)
    p_playlist.add_argument("--limit", type=int, default=25)

    sub.add_parser("update-ytdlp")

    # Kesh ko'rinmas joyda (XDG kesh papkasi) o'sadi — ilovaga uni ko'rsatish
    # va tozalash imkonini beramiz.
    sub.add_parser("cache-info")
    sub.add_parser("log-path")
    p_clear = sub.add_parser("clear-cache")
    p_clear.add_argument(
        "--what", default="downloads",
        choices=["downloads", "work", "models", "transcripts", "all"],
    )

    # #1 — ikki bosqichli oqim: transkripsiya+tarjima (prepare) → tahrir → render.
    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("--video", required=True)
    p_prepare.add_argument(
        "--mode",
        default="dual_vocab",
        choices=["dual_vocab", "original_vocab", "dual", "original", "translated",
                 "softsub", "srt", "transcript", "reading", "vocabulary", "all"],
    )
    p_prepare.add_argument("--source-lang", default="auto")
    p_prepare.add_argument("--target-lang", default="uz")
    p_prepare.add_argument("--quality", default=DEFAULT_QUALITY, choices=list(QUALITY_HEIGHTS))
    p_prepare.add_argument("--subtitle", default=None)
    p_prepare.add_argument("--subtitle-offset", type=float, default=0.0)

    # Tahrirlash oynasi uchun: bitta kadr + ustida haqiqiy subtitr.
    p_prev = sub.add_parser("preview")
    p_prev.add_argument("--session", required=True)
    p_prev.add_argument("--segments", default=None)
    p_prev.add_argument("--at", type=float, required=True)
    p_prev.add_argument("--out", required=True)
    p_prev.add_argument("--render-mode", default=None)
    p_prev.add_argument("--font-scale", type=float, default=1.0)
    p_prev.add_argument("--position", default="bottom", choices=["bottom", "top"])
    p_prev.add_argument("--sub-color", default="#FFE680")
    p_prev.add_argument("--orig-style", default="box", choices=["box", "plain"])
    p_prev.add_argument("--preview-height", type=int, default=540)

    # Tahrirlash oynasidagi pleyer uchun: mpv shu ASS ni o'zi chizadi.
    p_sub = sub.add_parser("subtitle-file")
    p_sub.add_argument("--session", required=True)
    p_sub.add_argument("--segments", default=None)
    p_sub.add_argument("--out", required=True)
    p_sub.add_argument("--render-mode", default=None)
    p_sub.add_argument("--font-scale", type=float, default=1.0)
    p_sub.add_argument("--position", default="bottom", choices=["bottom", "top"])
    p_sub.add_argument("--sub-color", default="#FFE680")
    p_sub.add_argument("--orig-style", default="box", choices=["box", "plain"])

    p_render = sub.add_parser("render")
    p_render.add_argument("--session", required=True)
    p_render.add_argument("--segments", default=None)
    p_render.add_argument("--font-scale", type=float, default=1.0)
    p_render.add_argument("--position", default="bottom", choices=["bottom", "top"])
    p_render.add_argument("--sub-color", default="#FFE680")
    p_render.add_argument("--orig-style", default="box", choices=["box", "plain"])
    p_render.add_argument("--quality", default=DEFAULT_QUALITY, choices=list(QUALITY_HEIGHTS))
    p_render.add_argument("--upscale", action="store_true")
    p_retranslate = sub.add_parser("retranslate")
    p_retranslate.add_argument("--session", required=True)
    p_retranslate.add_argument("--segments", default=None)
    p_retranslate.add_argument("--index", required=True, type=int)

    args = parser.parse_args()
    # Hech qanday argument qiymati logga tushmaydi (`--video` yo'li tushadi,
    # lekin kalitlar faqat muhit o'zgaruvchilarida — ularga tegmaymiz).
    log.info("--- buyruq: %s ---", args.command)
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
        elif args.command == "playlist":
            emit("done", entries=playlist_entries(args.url, args.limit))
        elif args.command == "update-ytdlp":
            emit("done", **update_ytdlp())
        elif args.command == "cache-info":
            emit("done", **cache_usage())
        elif args.command == "log-path":
            emit("done", dir=str(LOG_DIR), file=str(current_log_file()))
        elif args.command == "clear-cache":
            emit("done", **clear_cache(args.what))
        elif args.command == "prepare":
            result = prepare_session(
                args.video, args.mode, args.source_lang, args.target_lang,
                quality=args.quality,
                subtitle_path=args.subtitle, subtitle_offset=args.subtitle_offset,
            )
            emit("done", **result)
        elif args.command == "preview":
            emit("done", **preview_frame(
                args.session, args.at, args.out,
                segments_path=args.segments, render_mode=args.render_mode,
                font_scale=args.font_scale, position=args.position,
                sub_color=args.sub_color, orig_style=args.orig_style,
                preview_height=args.preview_height,
            ))
        elif args.command == "subtitle-file":
            emit("done", **subtitle_file(
                args.session, args.out, segments_path=args.segments,
                render_mode=args.render_mode, font_scale=args.font_scale,
                position=args.position, sub_color=args.sub_color,
                orig_style=args.orig_style,
            ))
        elif args.command == "retranslate":
            emit("done", **retranslate_session_segment(
                args.session, args.index, segments_path=args.segments,
            ))
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
                upscale=args.upscale, subtitle_path=args.subtitle,
                subtitle_offset=args.subtitle_offset,
            )
            emit("done", **result)
        return 0
    except KeyboardInterrupt:
        # Ilova "Bekor qilish" bosganda SIGINT yuboradi — bu xato emas.
        log.info("foydalanuvchi bekor qildi")
        emit("error", message="Bekor qilindi")
        return 130
    except Exception as exc:
        # Traceback ilgari butunlay yo'qolardi: GUI faqat `str(exc)` ni
        # ko'rsatar, xato qaysi qatordan kelganini bilish imkoni yo'q edi.
        log.error("tushdi (%s):\n%s", args.command, redact(traceback.format_exc()))
        emit("error", message=str(exc), log=str(current_log_file()))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
