#!/usr/bin/env python3
"""Kadrda oq karta to'rtburchaklarini topadi.

Kartalar oq, fon ko'k-kulrang - shuning uchun oddiy chegaralash yetarli.
Maqsad: ROI larni ko'z bilan emas, o'lchov bilan aniqlash.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage


def oq_maska(img: np.ndarray) -> np.ndarray:
    r, g, b = img[..., 0].astype(int), img[..., 1].astype(int), img[..., 2].astype(int)
    yorqin = (r > 170) & (g > 170) & (b > 170)
    rangsiz = (np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)) < 45
    return yorqin & rangsiz


def kartalar(path, min_area=2000):
    img = np.array(Image.open(path).convert("RGB"))
    h, w = img.shape[:2]
    mask = oq_maska(img)
    lab, n = ndimage.label(mask)
    out = []
    for sl, idx in zip(ndimage.find_objects(lab), range(1, n + 1)):
        ys, xs = sl
        bh, bw = ys.stop - ys.start, xs.stop - xs.start
        area = (lab[sl] == idx).sum()
        if area < min_area:
            continue
        out.append(dict(x=xs.start, y=ys.start, w=bw, h=bh, area=int(area)))
    return img, mask, sorted(out, key=lambda d: (-d["area"]))


if __name__ == "__main__":
    path = sys.argv[1]
    img, mask, boxes = kartalar(path)
    h, w = img.shape[:2]
    print(f"{path}  {w}x{h}  oq piksel: {mask.mean()*100:.1f}%")
    print(f"{'x':>5} {'y':>5} {'w':>5} {'h':>5} {'area':>8}   nisbiy (x,y,w,h)")
    for b in boxes[:25]:
        print(f"{b['x']:5} {b['y']:5} {b['w']:5} {b['h']:5} {b['area']:8}   "
              f"({b['x']/w:.3f}, {b['y']/h:.3f}, {b['w']/w:.3f}, {b['h']/h:.3f})")
