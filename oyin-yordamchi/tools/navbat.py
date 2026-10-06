#!/usr/bin/env python3
"""Kim himoyachi ekanini aniqlaydi.

Har o'yinchi avatarini rangli halqa o'rab turadi. O'lchov shuni ko'rsatdi:
har payt FAQAT BITTA o'yinchi yashil bo'ladi va u tur davomida o'zgarmaydi -
aynan o'sha kartani oladi yoki qoplaydi. Ya'ni yashil halqa = himoyachi,
qolganlari hujumchi.

Tekshirilgan: 2.0s da chap yashil edi va 9.5s da "oldim" dedi;
104.0s da men yashil edim va 134.0s da men oldim.
"""
import numpy as np

# Avatar hududlari (nisbiy): chap raqib, o'ng raqib, men
AVATARLAR = {
    "chap": (0.226, 0.086, 0.185, 0.083),
    "ong": (0.613, 0.086, 0.185, 0.083),
    "men": (0.417, 0.859, 0.185, 0.083),
}


def _halqa_ranglari(img, roi, qalinlik=0.09):
    h, w = img.shape[:2]
    x, y = int(roi[0] * w), int(roi[1] * h)
    bw, bh = int(roi[2] * w), int(roi[3] * h)
    sub = img[y:y + bh, x:x + bw].astype(int)
    if sub.size == 0:
        return 0.0, 0.0
    q = max(3, int(qalinlik * max(bw, bh)))
    chet = np.ones(sub.shape[:2], bool)
    if sub.shape[0] > 2 * q and sub.shape[1] > 2 * q:
        chet[q:-q, q:-q] = False
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    yashil = ((g > 140) & (g - r > 40) & (g - b > 60) & chet).sum()
    qizil = ((r > 170) & (r - g > 60) & (r - b > 40) & chet).sum()
    n = max(1, chet.sum())
    return yashil / n, qizil / n


def himoyachi(img, chegara=0.12):
    """Himoyachining nomi ("chap"/"ong"/"men") yoki None."""
    eng, eng_ball = None, chegara
    for kim, roi in AVATARLAR.items():
        yashil, qizil = _halqa_ranglari(img, roi)
        if yashil > eng_ball and yashil > qizil:
            eng, eng_ball = kim, yashil
    return eng
