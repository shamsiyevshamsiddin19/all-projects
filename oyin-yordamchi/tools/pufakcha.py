#!/usr/bin/env python3
"""O'yin hodisalarini o'qiydi: "I take", "Pass", "Done".

Pufakcha uch joydan birida chiqadi va joyi kimnikiligini bildiradi:
chapdagi raqib, o'ngdagi raqib, yoki o'zim. Rangi bilan matni esa
nima bo'lganini aytadi. Bu kuzatuv uchun eng ishonchli manba -
kartalar harakatidan taxmin qilish shart emas.
"""
import os, json, sys
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
from belgi_yig import namuna

# Nisbiy markazlar: (x, y) va kimga tegishli
JOYLAR = [("chap", 0.30, 0.105), ("ong", 0.70, 0.105), ("men", 0.50, 0.855)]
ENI = 0.30      # qidiruv oynasi kengligi (nisbiy)
BOYI = 0.075


def _maskalar(img):
    r, g, b = img[..., 0].astype(int), img[..., 1].astype(int), img[..., 2].astype(int)
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    oq = (r > 215) & (g > 215) & (b > 215) & ((mx - mn) < 25)
    sariq = (r > 180) & (g > 150) & (b < 120) & (r - b > 80) & (g - b > 60)
    qora = mx < 110
    return oq, sariq, qora


def nomzodlar(img):
    """Har joyda pufakcha bormi - matn bo'lagi bilan qaytaradi."""
    h, w = img.shape[:2]
    oq, sariq, qora = _maskalar(img)
    out = []
    for kim, cx, cy in JOYLAR:
        x0, x1 = int((cx - ENI / 2) * w), int((cx + ENI / 2) * w)
        y0, y1 = int((cy - BOYI / 2) * h), int((cy + BOYI / 2) * h)
        for rang, m in (("sariq", sariq), ("oq", oq)):
            sub = m[y0:y1, x0:x1]
            lab, n = ndimage.label(sub)
            for sl, i in zip(ndimage.find_objects(lab), range(1, n + 1)):
                ys, xs = sl
                bw, bh = int(xs.stop - xs.start), int(ys.stop - ys.start)
                area = int((lab[sl] == i).sum())
                if not (0.25 * (x1 - x0) < bw < 0.85 * (x1 - x0)
                        and 0.30 * (y1 - y0) < bh < 0.80 * (y1 - y0)
                        and area > 2000):
                    continue
                bx, by = x0 + int(xs.start), y0 + int(ys.start)
                # Pufakcha ichidagi qora matn. Chet qoldiriladi: pufakcha ostidagi
                # kartalar va pufakcha dumi matnga qo'shilib ketmasin.
                ix, iy = int(0.10 * bw), int(0.12 * bh)
                ich = qora[by + iy:by + bh - iy, bx + ix:bx + bw - ix]
                if ich.sum() < 150:
                    continue
                yss, xss = np.where(ich)
                matn = dict(x=bx + ix + int(xss.min()), y=by + iy + int(yss.min()),
                            w=int(xss.max() - xss.min()) + 1, h=int(yss.max() - yss.min()) + 1)
                out.append(dict(kim=kim, rang=rang, pufak=dict(x=bx, y=by, w=bw, h=bh), matn=matn))
                break
    return out


_BANK = None


def _bank():
    global _BANK
    if _BANK is None:
        yon = os.path.join(os.path.dirname(__file__), "..", "games", "durak", "profil")
        _BANK = (np.load(os.path.join(yon, "pufakcha.npz"))["v"],
                 json.load(open(os.path.join(yon, "pufakcha_nomlar.json"))))
    return _BANK


def hodisalar(img, min_ball=0.80):
    """[{kim, hodisa}] - hodisa: oldim / pas / bito"""
    vektorlar, nomlar = _bank()
    out = []
    for c in nomzodlar(img):
        v = namuna(img, c["matn"])
        if v is None:
            continue
        ball = vektorlar @ v.ravel()
        i = int(np.argmax(ball))
        if float(ball[i]) < min_ball or nomlar[i] == "?":
            continue
        out.append(dict(kim=c["kim"], hodisa=nomlar[i], ishonch=round(float(ball[i]), 3)))
    return out
