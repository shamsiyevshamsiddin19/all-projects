#!/usr/bin/env python3
"""Zaxirada qolgan karta sonini o'qiydi (chap chetdagi oq raqam)."""
import os, json, sys
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
from belgi_yig import namuna

ROI = (0.0, 0.305, 0.095, 0.040)   # nisbiy: chap chet, kozir kartasining tepasi


def _oq_matn(img):
    r, g, b = img[..., 0].astype(int), img[..., 1].astype(int), img[..., 2].astype(int)
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    return (r > 190) & (g > 190) & (b > 190) & ((mx - mn) < 35)


def raqam_bolaklari(img):
    """ROI ichidagi raqam bo'laklarini chapdan o'ngga qaytaradi."""
    h, w = img.shape[:2]
    x0, y0 = int(ROI[0] * w), int(ROI[1] * h)
    x1, y1 = int((ROI[0] + ROI[2]) * w), int((ROI[1] + ROI[3]) * h)
    sub = img[y0:y1, x0:x1]
    mask = _oq_matn(sub)
    lab, n = ndimage.label(mask)
    out = []
    for sl, i in zip(ndimage.find_objects(lab), range(1, n + 1)):
        ys, xs = sl
        bh, bw = ys.stop - ys.start, xs.stop - xs.start
        area = int((lab[sl] == i).sum())
        # Raqam: baland, tor, yetarlicha to'q
        if area < 80 or bh < 0.5 * (y1 - y0) or bw > 1.2 * bh:
            continue
        out.append(dict(x=int(xs.start) + x0, y=int(ys.start) + y0, w=int(bw), h=int(bh), area=area))
    return sorted(out, key=lambda d: d["x"]), sub


_BANK = None


def _bank():
    global _BANK
    if _BANK is None:
        from bank import oqi
        _BANK = oqi("raqam")
    return _BANK


def zaxira_soni(img, min_ball=0.80):
    """Zaxirada qolgan son. O'qib bo'lmasa None."""
    bolaklar, _ = raqam_bolaklari(img)
    if not bolaklar:
        return None
    vektorlar, nomlar = _bank()
    matn = ""
    for b in bolaklar:
        v = namuna(img, b)
        if v is None:
            return None
        ball = vektorlar @ v.ravel()
        i = int(np.argmax(ball))
        if float(ball[i]) < min_ball:
            return None
        matn += nomlar[i]
    try:
        return int(matn)
    except ValueError:
        return None
