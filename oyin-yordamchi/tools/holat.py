#!/usr/bin/env python3
"""Bitta kadrdan to'liq o'yin holatini yig'adi.

Kuzatuvchi (keyingi bosqich) aynan shu holatlar ketma-ketligidan
o'yin oqimini tiklaydi: kim nima qildi, qaysi kartalar bitoga ketdi.
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from tanish import kartalar
from zaxira import zaxira_soni
from pufakcha import hodisalar


def holat(img):
    ks = kartalar(img)
    return dict(
        qol=sorted(k["karta"] for k in ks if k["zona"] == "qol" and k["karta"]),
        stol=sorted(k["karta"] for k in ks if k["zona"] == "stol" and k["karta"]),
        kozir=next((k["karta"] for k in ks if k["zona"] == "kozir" and k["karta"]), None),
        zaxira=zaxira_soni(img),
        hodisalar=hodisalar(img),
        oqilmagan=sum(1 for k in ks if k["karta"] is None),
    )


def chiz(h):
    qism = [f"qo'l: {' '.join(h['qol']) or '-'}",
            f"stol: {' '.join(h['stol']) or '-'}",
            f"kozir: {h['kozir'] or '-'}",
            f"zaxira: {h['zaxira'] if h['zaxira'] is not None else '-'}"]
    if h["hodisalar"]:
        qism.append("hodisa: " + ", ".join(f"{e['kim']}={e['hodisa']}" for e in h["hodisalar"]))
    if h["oqilmagan"]:
        qism.append(f"o'qilmagan: {h['oqilmagan']}")
    return " | ".join(qism)


if __name__ == "__main__":
    from PIL import Image
    import glob
    yollar = sys.argv[1:] or sorted(glob.glob("data/frames/durak-3kishi-01/*.png"))[::20]
    for y in yollar:
        img = np.array(Image.open(y).convert("RGB"))
        print(f"{os.path.basename(y)}: {chiz(holat(img))}")
