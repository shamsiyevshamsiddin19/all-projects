#!/usr/bin/env python3
"""Tanish aniqligini o'lchaydi - qo'lda belgilamasdan.

Uchta mezon:
  1. Kozir karta butun o'yin davomida o'zgarmaydi (bu videoda 8C).
  2. Bitta kadrda bir karta ikki marta chiqa olmaydi.
  3. Ishonchi past bo'lgan belgilar ulushi.
"""
import glob, sys, collections
import numpy as np
from PIL import Image
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from tanish import kartalar

HAQIQIY_KOZIR = "8C"

frames = sorted(glob.glob("data/frames/durak-3kishi-01/*.png"))
if len(sys.argv) > 1:
    frames = frames[::int(sys.argv[1])]

kozir_ok = kozir_xato = kozir_yoq = 0
takror = 0
jami_belgi = noma_lum = 0
ishonchlar = []
kozir_xatolari = collections.Counter()
zona_soni = collections.Counter()

for i, f in enumerate(frames):
    img = np.array(Image.open(f).convert("RGB"))
    ks = kartalar(img)
    jami_belgi += len(ks)
    kadr_kartalar = []
    kozir_topildi = False
    for k in ks:
        if k["karta"] is None:
            noma_lum += 1
            continue
        ishonchlar.append(k["ishonch"])
        zona_soni[k["zona"]] += 1
        if k["zona"] == "kozir":
            kozir_topildi = True
            if k["karta"] == HAQIQIY_KOZIR:
                kozir_ok += 1
            else:
                kozir_xato += 1
                kozir_xatolari[k["karta"]] += 1
        else:
            kadr_kartalar.append(k["karta"])
    if not kozir_topildi:
        kozir_yoq += 1
    c = collections.Counter(kadr_kartalar)
    takror += sum(v - 1 for v in c.values() if v > 1)
    if (i + 1) % 100 == 0:
        print(f"  {i+1}/{len(frames)}", flush=True)

n = len(frames)
print(f"\n=== {n} kadr ===")
print(f"Jami belgi: {jami_belgi}, noma'lum: {noma_lum} ({noma_lum/max(1,jami_belgi)*100:.1f}%)")
print(f"O'rtacha ishonch: {np.mean(ishonchlar):.3f}")
print(f"Zonalar: {dict(zona_soni)}")
print()
print(f"Kozir to'g'ri:   {kozir_ok}  ({kozir_ok/max(1,kozir_ok+kozir_xato)*100:.1f}% topilganlar ichida)")
print(f"Kozir xato:      {kozir_xato}  {dict(kozir_xatolari)}")
print(f"Kozir topilmadi: {kozir_yoq} kadr (zaxira tugagandan keyin normal)")
print()
print(f"Takrorlangan karta: {takror} ta ({takror/max(1,n):.2f} kadrga)")
