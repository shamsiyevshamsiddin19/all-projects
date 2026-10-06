#!/usr/bin/env python3
"""Barcha kadrlardan raqam va mast belgilarini yig'ib, guruhlarga ajratadi.

Maqsad: 36 ta kartani qo'lda belgilash o'rniga, o'xshashlarini guruhlab,
har guruhga bitta nom berish. Shunda belgilash ishi o'nlab marta kamayadi.
"""
import sys, glob, pickle
import numpy as np
from PIL import Image
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from burchaklar import burchaklar, kozir_topish

O = 40  # namuna o'lchami
_USUL = "maydon"


def _namuna(img, box, usul):
    global _USUL
    eski, _USUL = _USUL, usul
    try:
        return namuna(img, box)
    finally:
        _USUL = eski


def maydon_kichiklashtir(kvadrat, yangi=40):
    """Maydon bo'yicha o'rtachalash - Kotlin tarafdagi bilan aynan bir xil.

    Ilgari LANCZOS ishlatilgandi; Kotlin'da uni takrorlash qiyin va chegaradagi
    belgilar ikki tarafda har xil chiqardi. Shuning uchun ikkala taraf ham
    shu oddiy va aniq takrorlanadigan usulga o'tdi.
    """
    tomon = kvadrat.shape[0]
    nisbat = tomon / yangi
    out = np.empty((yangi, yangi), np.float64)
    for y in range(yangi):
        sy0, sy1 = y * nisbat, (y + 1) * nisbat
        y0, y1 = int(np.floor(sy0)), min(tomon, int(np.ceil(sy1)))
        wy = np.minimum(sy1, np.arange(y0, y1) + 1) - np.maximum(sy0, np.arange(y0, y1))
        for x in range(yangi):
            sx0, sx1 = x * nisbat, (x + 1) * nisbat
            x0, x1 = int(np.floor(sx0)), min(tomon, int(np.ceil(sx1)))
            wx = np.minimum(sx1, np.arange(x0, x1) + 1) - np.maximum(sx0, np.arange(x0, x1))
            blok = kvadrat[y0:y1, x0:x1]
            ogirlik = np.outer(wy, wx)
            jami = ogirlik.sum()
            out[y, x] = (blok * ogirlik).sum() / jami if jami > 0 else 255.0
    return out


def namuna_lanczos(img, box):
    """Eski usul - faqat bankni qayta qurishda nom berish uchun kerak."""
    return _namuna(img, box, "lanczos")


def namuna(img, box):
    """Belgini kesib, kvadratga to'ldirib, bir xil o'lchamga keltiradi."""
    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    pad = 2
    y0, y1 = max(0, y - pad), min(img.shape[0], y + h + pad)
    x0, x1 = max(0, x - pad), min(img.shape[1], x + w + pad)
    kesim = img[y0:y1, x0:x1]
    if kesim.size == 0:
        return None
    g = np.array(Image.fromarray(kesim).convert("L"), dtype=np.float32)
    # Kvadratga to'ldirish - nisbat buzilmasin ('1' va '0' farqlansin)
    hh, ww = g.shape
    side = max(hh, ww)
    kvadrat = np.full((side, side), 255.0, np.float32)
    kvadrat[(side - hh) // 2:(side - hh) // 2 + hh, (side - ww) // 2:(side - ww) // 2 + ww] = g
    kichik = (np.array(Image.fromarray(kvadrat).resize((O, O), Image.LANCZOS), dtype=np.float64)
              if _USUL == "lanczos" else maydon_kichiklashtir(kvadrat, O)).astype(np.float32)
    kichik -= kichik.mean()
    n = np.linalg.norm(kichik)
    return kichik / n if n > 1e-6 else None


def yig(frames):
    pool = []
    for i, f in enumerate(frames):
        img = np.array(Image.open(f).convert("RGB"))
        h = img.shape[0]
        uchrashuv = [(t, "kadr") for t in burchaklar(img)]
        kz, bur = kozir_topish(img)
        if kz:
            uchrashuv.append((kz, "kozir"))
        for t, manba in uchrashuv:
            src = bur if manba == "kozir" else img
            yc = (t["box"]["y"] + t["box"]["h"] / 2) / (src.shape[0])
            zona = "kozir" if manba == "kozir" else ("qol" if yc > 0.66 else "stol")
            for tur in ("rank", "suit"):
                v = namuna(src, t[tur])
                if v is not None:
                    pool.append(dict(v=v, tur=tur, rang=t["rang"], zona=zona, kadr=f.split("/")[-1]))
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(frames)} kadr, {len(pool)} namuna", flush=True)
    return pool


def guruhla(pool, tur, chegara=0.88):
    """Ochko'z guruhlash: o'xshashlik chegaradan yuqori bo'lsa bitta guruhga."""
    items = [p for p in pool if p["tur"] == tur]
    guruhlar = []
    for p in items:
        joylashdi = False
        for g in guruhlar:
            if float(np.dot(p["v"].ravel(), g["markaz"].ravel())) > chegara:
                g["azolar"].append(p)
                g["markaz"] = g["markaz"] + (p["v"] - g["markaz"]) / len(g["azolar"])
                g["markaz"] /= np.linalg.norm(g["markaz"])
                joylashdi = True
                break
        if not joylashdi:
            guruhlar.append(dict(markaz=p["v"].copy(), azolar=[p]))
    return sorted(guruhlar, key=lambda g: -len(g["azolar"]))


if __name__ == "__main__":
    frames = sorted(glob.glob("data/frames/durak-3kishi-01/*.png"))
    if len(sys.argv) > 1:
        frames = frames[::int(sys.argv[1])]
    print(f"{len(frames)} kadr qayta ishlanadi")
    pool = yig(frames)
    print(f"\nJami namuna: {len(pool)}")
    for tur in ("rank", "suit"):
        gs = guruhla(pool, tur)
        kattalar = [len(g["azolar"]) for g in gs[:10]]
        soni = sum(1 for p in pool if p["tur"] == tur)
        print(f"  {tur}: {soni} namuna -> {len(gs)} guruh, eng kattalari: {kattalar}")
    with open("data/namunalar.pkl", "wb") as f:
        pickle.dump(pool, f)
    print("data/namunalar.pkl saqlandi")
