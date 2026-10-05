#!/usr/bin/env python3
"""Kadrdagi barcha karta burchaklarini (raqam + mast juftligi) topadi.

G'oya: qaysi zona bo'lishidan qat'i nazar, har karta burchagida
toza oq fonda raqam turadi va uning TAGIDA mast belgisi turadi.
Shuning uchun zona bo'yicha emas, shu naqsh bo'yicha qidiramiz -
qo'l, stol va kozir uchun bitta mantiq yetadi.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage


def maskalar(img):
    r, g, b = img[..., 0].astype(int), img[..., 1].astype(int), img[..., 2].astype(int)
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    oq = (r > 170) & (g > 170) & (b > 170) & ((mx - mn) < 45)
    qora = mx < 120
    qizil = (r > 110) & (r - np.maximum(g, b) > 55)
    return oq, qora, qizil


def komponentlar(mask, min_area, max_area):
    lab, n = ndimage.label(mask)
    out = []
    for sl, idx in zip(ndimage.find_objects(lab), range(1, n + 1)):
        ys, xs = sl
        area = int((lab[sl] == idx).sum())
        if not (min_area <= area <= max_area):
            continue
        out.append(dict(x=int(xs.start), y=int(ys.start),
                        w=int(xs.stop - xs.start), h=int(ys.stop - ys.start), area=area))
    return out


def qoshni_birlashtir(parts, max_gap_ratio=0.45):
    """'10' kabi ikki bo'lakli raqamlarni birlashtiradi."""
    parts = sorted(parts, key=lambda p: p["x"])
    out = []
    for p in parts:
        merged = False
        for q in out:
            gap = p["x"] - (q["x"] + q["w"])
            yk = min(p["y"] + p["h"], q["y"] + q["h"]) - max(p["y"], q["y"])
            hmax = max(p["h"], q["h"])
            if -5 <= gap <= max_gap_ratio * hmax and yk > 0.55 * hmax:
                x0, y0 = min(p["x"], q["x"]), min(p["y"], q["y"])
                x1 = max(p["x"] + p["w"], q["x"] + q["w"])
                y1 = max(p["y"] + p["h"], q["y"] + q["h"])
                q.update(x=x0, y=y0, w=x1 - x0, h=y1 - y0, area=p["area"] + q["area"])
                merged = True
                break
        if not merged:
            out.append(dict(p))
    return out


def toza_fonmi(oq, box, chet=0.35):
    """Burchak belgisi atrofi oq bo'lishi kerak - rasm ichidagi qora chiziqlardan farqi shu."""
    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    dx, dy = int(w * chet) + 3, int(h * chet) + 3
    x0, y0 = max(0, x - dx), max(0, y - dy)
    x1, y1 = min(oq.shape[1], x + w + dx), min(oq.shape[0], y + h + dy)
    hudud = oq[y0:y1, x0:x1]
    if hudud.size == 0:
        return 0.0
    return float(hudud.mean())


def burchaklar(img, min_rank_h=40):
    h, w = img.shape[:2]
    oq, qora, qizil = maskalar(img)
    oq_keng = ndimage.binary_dilation(oq, iterations=8)

    topildi = []
    for rang, m in (("qora", qora), ("qizil", qizil)):
        ink = m & oq_keng
        parts = komponentlar(ink, min_area=100, max_area=12000)
        parts = qoshni_birlashtir(parts)
        # Raqam nomzodlari: baland, juda keng emas
        ranks = [p for p in parts if p["h"] >= min_rank_h and p["w"] <= 2.2 * p["h"]]
        for rk in ranks:
            # Mast belgisi: aynan tagida, kengligi o'xshash
            cx = rk["x"] + rk["w"] / 2
            nomzod = None
            for s in parts:
                if s is rk:
                    continue
                gap = s["y"] - (rk["y"] + rk["h"])
                scx = s["x"] + s["w"] / 2
                if (-0.15 * rk["h"] <= gap <= 0.75 * rk["h"]
                        and abs(scx - cx) <= 0.75 * rk["w"]
                        and 0.35 * rk["h"] <= s["h"] <= 1.15 * rk["h"]):
                    if nomzod is None or s["y"] < nomzod["y"]:
                        nomzod = s
            if nomzod is None:
                continue
            box = dict(
                x=min(rk["x"], nomzod["x"]), y=rk["y"],
                w=max(rk["x"] + rk["w"], nomzod["x"] + nomzod["w"]) - min(rk["x"], nomzod["x"]),
                h=nomzod["y"] + nomzod["h"] - rk["y"],
            )
            oqlik = toza_fonmi(oq, box)
            if oqlik < 0.55:
                continue
            topildi.append(dict(rang=rang, rank=rk, suit=nomzod, box=box, oqlik=oqlik))

    # Bir xil joydagi takrorlarni olib tashlaymiz
    topildi.sort(key=lambda t: -t["box"]["h"])
    natija = []
    for t in topildi:
        b = t["box"]
        if any(abs(b["x"] - n["box"]["x"]) < 0.6 * b["w"] and abs(b["y"] - n["box"]["y"]) < 0.6 * b["h"]
               for n in natija):
            continue
        natija.append(t)
    return sorted(natija, key=lambda t: (t["box"]["y"], t["box"]["x"]))


if __name__ == "__main__":
    path = sys.argv[1]
    img = np.array(Image.open(path).convert("RGB"))
    h, w = img.shape[:2]
    bs = burchaklar(img)
    print(f"{path}  {w}x{h}  burchak topildi: {len(bs)}")
    print(f"{'x':>5} {'y':>5} {'w':>4} {'h':>4} {'rang':>5} {'oqlik':>6}  zona")
    for t in bs:
        b = t["box"]
        yc = (b["y"] + b["h"] / 2) / h
        zona = "qo'l" if yc > 0.66 else ("stol" if yc > 0.25 else "yuqori")
        if b["x"] / w < 0.16 and 0.3 < yc < 0.6:
            zona = "kozir"
        print(f"{b['x']:5} {b['y']:5} {b['w']:4} {b['h']:4} {t['rang']:>5} {t['oqlik']:6.2f}  {zona}")
