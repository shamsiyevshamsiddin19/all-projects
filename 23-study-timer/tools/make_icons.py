#!/usr/bin/env python3
"""
PWA ikonalarini yasaydi — faqat standart kutubxona (zlib + struct), tashqi paket yo'q.
Ishlatish: python3 tools/make_icons.py
"""
import math
import os
import struct
import zlib

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")
SIZES = (192, 512)
BG = (0, 0, 0)
FG = (255, 255, 255)
SS = 3  # supersampling — chiroyli qirralar uchun


def _coverage(size: int, inside) -> list[list[float]]:
    """Har bir piksel uchun 0..1 qoplama (supersampling bilan)."""
    cov = [[0.0] * size for _ in range(size)]
    step = 1.0 / SS
    for y in range(size):
        for x in range(size):
            hits = 0
            for sy in range(SS):
                for sx in range(SS):
                    px = x + (sx + 0.5) * step
                    py = y + (sy + 0.5) * step
                    if inside(px, py):
                        hits += 1
            cov[y][x] = hits / (SS * SS)
    return cov


def clock_shape(size: int, maskable: bool):
    """Soat glifi: halqa + ikki ko'rsatkich."""
    cx = cy = size / 2
    scale = 0.78 if maskable else 1.0
    r_outer = size * 0.40 * scale
    ring = size * 0.045 * scale
    hand_w = size * 0.038 * scale
    hour_len = size * 0.20 * scale
    minute_len = size * 0.29 * scale

    def on_segment(px, py, angle_deg, length):
        ang = math.radians(angle_deg - 90)
        ex, ey = cx + math.cos(ang) * length, cy + math.sin(ang) * length
        dx, dy = ex - cx, ey - cy
        seg_len2 = dx * dx + dy * dy
        if seg_len2 == 0:
            return False
        tproj = max(0.0, min(1.0, ((px - cx) * dx + (py - cy) * dy) / seg_len2))
        nx, ny = cx + dx * tproj, cy + dy * tproj
        return (px - nx) ** 2 + (py - ny) ** 2 <= (hand_w / 2) ** 2

    def inside(px, py):
        d = math.hypot(px - cx, py - cy)
        if r_outer - ring <= d <= r_outer:
            return True
        if on_segment(px, py, 0, hour_len):      # soat ko'rsatkichi — tepaga
            return True
        if on_segment(px, py, 105, minute_len):  # daqiqa ko'rsatkichi
            return True
        return False

    return inside


def write_png(path: str, size: int, maskable: bool = False) -> None:
    cov = _coverage(size, clock_shape(size, maskable))
    rows = bytearray()
    for y in range(size):
        rows.append(0)  # filtr turi: None
        for x in range(size):
            a = cov[y][x]
            rows.extend(bytes(round(BG[i] + (FG[i] - BG[i]) * a) for i in range(3)))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    header = struct.pack(">2I5B", size, size, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
           + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as handle:
        handle.write(png)


SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" fill="#000000"/>
  <g fill="none" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round">
    <circle cx="12" cy="12" r="9"/>
    <polyline points="12 7 12 12 15 15"/>
  </g>
</svg>
"""


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "icon.svg"), "w", encoding="utf-8") as handle:
        handle.write(SVG)
    for size in SIZES:
        write_png(os.path.join(OUT_DIR, f"icon-{size}.png"), size)
        print(f"icons/icon-{size}.png yasaldi")
    write_png(os.path.join(OUT_DIR, "icon-maskable-512.png"), 512, maskable=True)
    print("icons/icon-maskable-512.png yasaldi")
    print("icons/icon.svg yasaldi")


if __name__ == "__main__":
    main()
