"""Rejim kartalari (preview rasmlar) generatsiyasi — bot mode-carousel uchun.

Har bir rejim uchun 960x540 PNG: video-freym mockup + rejimga xos vizual
belgi (subtitr qatorlari / fayl ikonkasi / lug'at ustuni / audio to'lqin).
Ishga tushirish: python gen_mode_cards.py <chiqish_papka>
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 960, 540
FONT_DIR = "/usr/share/fonts/truetype/noto"
F_BOLD = os.path.join(FONT_DIR, "NotoSans-Bold.ttf")
F_REG = os.path.join(FONT_DIR, "NotoSans-Regular.ttf")
F_SEMI = os.path.join(FONT_DIR, "NotoSans-SemiBold.ttf")


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def bg_gradient(accent: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (W, H), (10, 14, 24))
    top = (13, 18, 30)
    bottom = (7, 10, 18)
    for y in range(H):
        t = y / H
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        ImageDraw.Draw(img).line([(0, y), (W, y)], fill=(r, g, b))
    # Yumshoq accent nur (yuqori chap burchak)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-260, -260, 420, 380], fill=accent)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.blend(img, glow, 0.35)
    return img


def rounded(draw: ImageDraw.ImageDraw, box, radius, **kw):
    draw.rounded_rectangle(box, radius=radius, **kw)


def video_frame(draw: ImageDraw.ImageDraw, x, y, w, h):
    """Video freym mockup: ekran + play belgisi."""
    rounded(draw, [x, y, x + w, y + h], 18, fill=(20, 26, 41), outline=(48, 58, 82), width=2)
    cx, cy = x + w // 2, y + h // 2 - 30
    draw.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=(255, 255, 255, 40), outline=(210, 220, 235), width=2)
    draw.polygon([(cx - 10, cy - 18), (cx - 10, cy + 18), (cx + 18, cy)], fill=(230, 235, 245))


def sub_bar(draw: ImageDraw.ImageDraw, cx, y, text, fnt, fg, bg, pad_x=16, pad_y=8):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x0 = cx - tw // 2 - pad_x
    x1 = cx + tw // 2 + pad_x
    y0 = y - pad_y
    y1 = y + th + pad_y
    rounded(draw, [x0, y0, x1, y1], 10, fill=bg)
    draw.text((cx - tw // 2, y - bbox[1]), text, font=fnt, fill=fg)
    return y1


def tag(draw: ImageDraw.ImageDraw, text: str, accent):
    fnt = font(F_SEMI, 26)
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    x0, y0 = 48, 44
    rounded(draw, [x0, y0, x0 + tw + 40, y0 + 52], 26, fill=accent)
    draw.text((x0 + 20, y0 + 10), text, font=fnt, fill=(12, 14, 20))


FRAME = dict(x=140, y=118, w=680, h=340)


def make_original(accent):
    img = bg_gradient(accent)
    d = ImageDraw.Draw(img)
    tag(d, "ORIGINAL", accent)
    video_frame(d, **FRAME)
    cx = FRAME["x"] + FRAME["w"] // 2
    sub_bar(d, cx, FRAME["y"] + FRAME["h"] - 62, "We don't have much time left.",
            font(F_SEMI, 28), (18, 22, 30), (240, 244, 250))
    return img


def make_translate(accent):
    img = bg_gradient(accent)
    d = ImageDraw.Draw(img)
    tag(d, "TARJIMA", accent)
    video_frame(d, **FRAME)
    cx = FRAME["x"] + FRAME["w"] // 2
    sub_bar(d, cx, FRAME["y"] + FRAME["h"] - 62, "Vaqtimiz ko'p qolmadi.",
            font(F_SEMI, 28), (255, 255, 255), accent)
    return img


def make_dual(accent):
    img = bg_gradient(accent)
    d = ImageDraw.Draw(img)
    tag(d, "IKKI QATLAM", accent)
    video_frame(d, **FRAME)
    cx = FRAME["x"] + FRAME["w"] // 2
    y = FRAME["y"] + FRAME["h"] - 118
    y = sub_bar(d, cx, y, "We don't have much time left.", font(F_SEMI, 24), (18, 22, 30), (240, 244, 250))
    sub_bar(d, cx, y + 10, "Vaqtimiz ko'p qolmadi.", font(F_SEMI, 24), (255, 255, 255), accent)
    return img


def make_dual_vocab(accent):
    img = bg_gradient(accent)
    d = ImageDraw.Draw(img)
    tag(d, "LUG'AT BILAN", accent)
    frame = dict(FRAME); frame["w"] = 520
    video_frame(d, **frame)
    cx = frame["x"] + frame["w"] // 2
    y = frame["y"] + frame["h"] - 118
    y = sub_bar(d, cx, y, "We don't have much time.", font(F_SEMI, 22), (18, 22, 30), (240, 244, 250))
    sub_bar(d, cx, y + 10, "Vaqtimiz ko'p qolmadi.", font(F_SEMI, 22), (255, 255, 255), accent)
    # Suzuvchi lug'at ustuni (o'ngda)
    vx = frame["x"] + frame["w"] + 30
    vy = frame["y"] + 10
    words = [("time", "vaqt"), ("much", "ko'p"), ("left", "qoldi")]
    fw = font(F_REG, 22); fwt = font(F_SEMI, 22)
    for i, (w1, w2) in enumerate(words):
        yy = vy + i * 70
        rounded(d, [vx, yy, vx + 150, yy + 54], 12, fill=(20, 26, 41), outline=accent, width=2)
        d.text((vx + 14, yy + 6), w1, font=fwt, fill=(240, 244, 250))
        d.text((vx + 14, yy + 28), w2, font=fw, fill=accent)
    return img


def make_srt(accent):
    img = bg_gradient(accent)
    d = ImageDraw.Draw(img)
    tag(d, ".SRT FAYL", accent)
    fx, fy, fw_, fh = 330, 110, 300, 360
    rounded(d, [fx, fy, fx + fw_, fy + fh], 20, fill=(20, 26, 41), outline=accent, width=3)
    d.polygon([(fx + fw_ - 70, fy), (fx + fw_, fy + 70), (fx + fw_ - 70, fy + 70)], fill=accent)
    fnt = font(F_SEMI, 22); fnt2 = font(F_REG, 18)
    lines = [("1", "00:00:01,200 --> 00:00:03,400"), ("We don't have much time left.", ""),
             ("2", "00:00:03,600 --> 00:00:05,900"), ("We have to leave right now.", "")]
    yy = fy + 60
    for i, (a, b) in enumerate(lines):
        c = accent if not b else (225, 230, 240)
        f = fnt if b or a.isdigit() and not b else fnt2
        d.text((fx + 26, yy), a, font=(fnt if a.isdigit() else fnt2), fill=(accent if b else (225, 230, 240)))
        yy += 34
        if b:
            d.text((fx + 26, yy), b, font=font(F_REG, 16), fill=(140, 150, 170))
            yy += 40
    return img


def make_transcript(accent):
    img = bg_gradient(accent)
    d = ImageDraw.Draw(img)
    tag(d, "MATN (PDF)", accent)
    fx, fy, fw_, fh = 330, 100, 300, 380
    rounded(d, [fx, fy, fx + fw_, fy + fh], 20, fill=(250, 250, 252))
    d.rectangle([fx, fy, fx + fw_, fy + 70], fill=accent)
    fnt_b = font(F_SEMI, 22)
    d.text((fx + 24, fy + 22), "Videodagi matn", font=fnt_b, fill=(20, 22, 30))
    fnt = font(F_REG, 16)
    yy = fy + 100
    widths = [230, 260, 180, 250, 200, 240, 150]
    for w_ in widths:
        d.rounded_rectangle([fx + 24, yy, fx + 24 + w_, yy + 14], 6, fill=(210, 214, 224))
        yy += 30
    return img


def make_vocabulary(accent):
    img = bg_gradient(accent)
    d = ImageDraw.Draw(img)
    tag(d, "LUG'AT", accent)
    fx, fy, fw_, fh = 300, 100, 360, 380
    rounded(d, [fx, fy, fx + fw_, fy + fh], 20, fill=(20, 26, 41), outline=accent, width=3)
    fnt_b = font(F_SEMI, 24); fnt = font(F_REG, 20)
    words = [("time", "vaqt", "x12"), ("leave", "ketmoq", "x8"),
             ("much", "ko'p", "x15"), ("change", "o'zgarmoq", "x6")]
    yy = fy + 30
    for w1, w2, cnt in words:
        d.text((fx + 24, yy), w1, font=fnt_b, fill=(240, 244, 250))
        d.text((fx + 24, yy + 30), "→ " + w2, font=fnt, fill=accent)
        bbox = d.textbbox((0, 0), cnt, font=fnt)
        d.text((fx + fw_ - 24 - (bbox[2] - bbox[0]), yy + 8), cnt, font=fnt, fill=(140, 150, 170))
        yy += 82
    return img


def make_audio(accent):
    img = bg_gradient(accent)
    d = ImageDraw.Draw(img)
    tag(d, "AUDIO (MP3)", accent)
    cx, cy = W // 2, H // 2 + 20
    d.ellipse([cx - 90, cy - 90, cx + 90, cy + 90], fill=accent)
    d.polygon([(cx - 24, cy - 40), (cx - 24, cy + 40), (cx + 44, cy)], fill=(15, 18, 26))
    import random
    random.seed(7)
    bar_x = cx - 260
    for i in range(30):
        bh = random.randint(14, 90)
        d.rounded_rectangle([bar_x, cy - bh // 2, bar_x + 10, cy + bh // 2], 4, fill=accent)
        bar_x += 18
        if bar_x > cx - 120:
            break
    bar_x = cx + 150
    for i in range(30):
        bh = random.randint(14, 90)
        d.rounded_rectangle([bar_x, cy - bh // 2, bar_x + 10, cy + bh // 2], 4, fill=accent)
        bar_x += 18
        if bar_x > cx + 300:
            break
    return img


MODES = {
    "original": (make_original, (167, 139, 250)),
    "translate": (make_translate, (96, 165, 250)),
    "dual": (make_dual, (52, 211, 153)),
    "dual_vocab": (make_dual_vocab, (250, 204, 21)),
    "srt": (make_srt, (248, 113, 113)),
    "transcript": (make_transcript, (203, 213, 225)),
    "vocabulary": (make_vocabulary, (244, 114, 182)),
    "audio": (make_audio, (129, 230, 217)),
}


def main() -> None:
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out_dir, exist_ok=True)
    for name, (fn, accent) in MODES.items():
        img = fn(accent)
        path = os.path.join(out_dir, f"{name}.png")
        img.save(path, "PNG", optimize=True)
        print("yozildi:", path)


if __name__ == "__main__":
    main()
