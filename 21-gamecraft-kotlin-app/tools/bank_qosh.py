#!/usr/bin/env python3
"""Bankka yangi qurilmaning belgilarini qo'shadi.

Nega kerak: shablonlar bitta qurilmaning chizmasidan o'rgatilgan. Boshqa
telefonda shrift biroz boshqacha chiziladi va bank xato nom qo'yishi mumkin -
bunda xato JIM bo'ladi, chunki o'z-o'zini tekshirish (karta ikkilanmasin,
yo'qolmasin) bunday xatoni ko'rmaydi: almashtirilgan nom ham izchil.

Shuning uchun nom qo'lda beriladi. Ishlatish ikki qadamda:

    python3 tools/bank_qosh.py data/telefon rank
        -> guruhlarni rasmga chiqaradi va bank nima deyishini aytadi

    python3 tools/bank_qosh.py data/telefon rank --qosh 0=8 19=6
        -> ko'rsatilgan guruhlarni o'sha nom bilan bankka qo'shadi
"""
import glob
import json
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bank import oqi as bank_oqi, YON
from belgi_yig import namuna, guruhla
from burchaklar import burchaklar, kozir_topish

FAYL = {"rank": "rank", "suit": "suit"}


def belgilarni_yig(papka, tur):
    pool = []
    for f in sorted(glob.glob(os.path.join(papka, "*.png"))):
        img = np.array(Image.open(f).convert("RGB"))
        manbalar = [(t, img) for t in burchaklar(img)]
        kz, bur = kozir_topish(img)
        if kz:
            manbalar.append((kz, bur))
        for t, src in manbalar:
            v = namuna(src, t[tur])
            if v is not None:
                pool.append(dict(v=v, tur=tur, src=src, box=t[tur], fayl=f))
    return pool


def bank_nomi(V, N, v):
    ball = V @ v.ravel()
    eng = {}
    for i, b in enumerate(ball):
        if N[i] not in eng or b > eng[N[i]]:
            eng[N[i]] = float(b)
    t = sorted(eng.items(), key=lambda kv: -kv[1])
    return t[0], (t[1] if len(t) > 1 else ("-", 0.0))


def varaq(guruhlar, V, N, chiqish):
    """Guruh vakillarini bitta rasmga yig'adi - odam o'qiy olishi uchun."""
    K, USTUN = 110, 10
    qator = (len(guruhlar) + USTUN - 1) // USTUN
    tuval = Image.new("RGB", (USTUN * (K + 10), qator * (K + 46)), (255, 255, 255))
    d = ImageDraw.Draw(tuval)
    for j, g in enumerate(guruhlar):
        p = g["azolar"][0]
        b, im = p["box"], p["src"]
        kes = im[max(0, b["y"] - 2):b["y"] + b["h"] + 2, max(0, b["x"] - 2):b["x"] + b["w"] + 2]
        cx, cy = (j % USTUN) * (K + 10), (j // USTUN) * (K + 46)
        tuval.paste(Image.fromarray(kes).resize((K, K)), (cx, cy + 16))
        (n1, b1), _ = bank_nomi(V, N, g["markaz"])
        d.text((cx + 3, cy + 2), f"#{j} ({len(g['azolar'])})", fill=(0, 0, 200))
        d.text((cx + 3, cy + K + 20), f"bank:{n1} {b1:.2f}", fill=(200, 0, 0))
    tuval.save(chiqish)


def saqla(tur, V, N):
    yol = os.path.join(YON, f"{FAYL[tur]}.bank")
    with open(yol, "wb") as f:
        f.write(struct.pack("<ii", V.shape[0], V.shape[1]))
        f.write(V.astype("<f4").tobytes())
    with open(os.path.join(YON, f"{FAYL[tur]}.names.json"), "w") as f:
        json.dump(N, f, ensure_ascii=False)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    papka, tur = sys.argv[1], sys.argv[2]
    qosh = {}
    if "--qosh" in sys.argv:
        for juft in sys.argv[sys.argv.index("--qosh") + 1:]:
            g, nom = juft.split("=")
            qosh[int(g)] = nom

    V, N = bank_oqi(FAYL[tur])
    pool = belgilarni_yig(papka, tur)
    guruhlar = guruhla(pool, tur, chegara=0.88)
    print(f"{len(pool)} ta '{tur}' belgisi -> {len(guruhlar)} guruh")

    chiqish = os.path.join(papka, f"guruhlar-{tur}.png")
    varaq(guruhlar, V, N, chiqish)
    print(f"rasm: {chiqish}")

    for j, g in enumerate(guruhlar):
        (n1, b1), (n2, b2) = bank_nomi(V, N, g["markaz"])
        belgi = f"  -> QO'SHILADI nomi '{qosh[j]}'" if j in qosh else ""
        print(f"  #{j:2d} a'zo={len(g['azolar']):3d}  bank: {n1}={b1:.3f}  "
              f"ikkinchi: {n2}={b2:.3f}{belgi}")

    if not qosh:
        print("\nQo'shish uchun: --qosh <guruh>=<nom> ...")
        return 0

    # Guruhning markazi emas, bir nechta a'zosi qo'shiladi: markaz silliqlangan
    # o'rtacha, a'zolar esa haqiqiy ko'rinishlar - turlichaligi foydali.
    yangiV, yangiN = list(V), list(N)
    for j, nom in sorted(qosh.items()):
        azolar = guruhlar[j]["azolar"]
        tanlangan = azolar[:: max(1, len(azolar) // 3)][:3]
        for p in tanlangan:
            yangiV.append(p["v"].ravel().astype(np.float32))
            yangiN.append(nom)
        print(f"  #{j}: '{nom}' nomi bilan {len(tanlangan)} ta shablon qo'shildi")

    saqla(tur, np.array(yangiV), yangiN)
    print(f"bank yangilandi: {len(N)} -> {len(yangiN)} shablon")
    return 0


if __name__ == "__main__":
    sys.exit(main())
