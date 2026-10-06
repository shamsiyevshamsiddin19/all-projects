#!/usr/bin/env python3
"""O'tkazib yuborishni o'lchaydi: karta yo'qolib keyin qaytib kelsa - bu xato.

Kartalar o'yin davomida o'z-o'zidan g'oyib bo'lmaydi. Agar N-kadrda bor,
N+1 da yo'q, N+2 da yana bor bo'lsa - o'rtadagi kadrda o'tkazib yuborilgan.
"""
import glob, sys, collections
import numpy as np
from PIL import Image
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from tanish import kartalar

frames = sorted(glob.glob("data/frames/durak-3kishi-01/*.png"))
if len(sys.argv) > 1:
    frames = frames[::int(sys.argv[1])]

ketma = []
for i, f in enumerate(frames):
    img = np.array(Image.open(f).convert("RGB"))
    ks = kartalar(img)
    ketma.append({
        "qol": {k["karta"] for k in ks if k["zona"] == "qol" and k["karta"]},
        "stol": {k["karta"] for k in ks if k["zona"] == "stol" and k["karta"]},
    })
    if (i + 1) % 100 == 0:
        print(f"  {i+1}/{len(frames)}", flush=True)

for zona in ("qol", "stol"):
    miltillash = 0
    jami = 0
    for i in range(1, len(ketma) - 1):
        oldin, hozir, keyin = ketma[i-1][zona], ketma[i][zona], ketma[i+1][zona]
        yoqolgan = (oldin & keyin) - hozir   # oldin ham, keyin ham bor - lekin hozir yo'q
        miltillash += len(yoqolgan)
        jami += len(oldin & keyin)
    print(f"{zona}: {jami} ta barqaror karta-kadr, {miltillash} ta miltilladi "
          f"({miltillash/max(1,jami)*100:.2f}% o'tkazib yuborilgan)")

sonlar = collections.Counter(len(k["qol"]) for k in ketma)
print("\nQo'ldagi karta soni taqsimoti:", dict(sorted(sonlar.items())))
