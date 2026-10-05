#!/usr/bin/env python3
"""Kadrgacha o'yinni kuzatib, dvigatelga yuboriladigan buyruqni yasaydi.

Ishlatish:  python3 tools/maslahat_ber.py 160 hujum
Natija:     ./gradlew :games:durak:maslahat --args="..." buyrug'i
"""
import glob, sys, subprocess
import numpy as np
from PIL import Image

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from holat import holat
from kuzatuv import Kuzatuv


def holatgacha(kadr_raqami, papka="data/frames/durak-3kishi-01"):
    k = Kuzatuv(raqiblar=2)
    for f in sorted(glob.glob(f"{papka}/*.png"))[:kadr_raqami]:
        img = np.array(Image.open(f).convert("RGB"))
        k.qadam(holat(img), vaqt=int(f[-8:-4]) / 2)
    return k


def buyruq(d, rol):
    def ro(x):
        return ",".join(x) if x else "-"
    return (f'--kozir {d["kozir"]} --qol {ro(d["qol"])} '
            f'--hujum {ro(d["hujumlar"])} '
            f'--qopla {",".join(c if c else "-" for c in d["qoplaganlar"]) or "-"} '
            f'--zaxira {d["zaxira"]} --bito {ro(d["bitoga"])} '
            f'--raqiblar {",".join(str(x) for x in d["raqiblar"])} --rol {rol}')


if __name__ == "__main__":
    kadr = int(sys.argv[1]) if len(sys.argv) > 1 else 160
    rol = sys.argv[2] if len(sys.argv) > 2 else "hujum"
    k = holatgacha(kadr)
    d = k.dvigatel_uchun()
    print(f"# {kadr}-kadrgacha kuzatildi, bitoga ketgan: {len(d['bitoga'])} karta")
    print(buyruq(d, rol))
