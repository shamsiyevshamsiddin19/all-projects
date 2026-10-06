#!/usr/bin/env python3
"""Guruhlarning vakillarini bitta katta rasmga joylaydi - belgilash uchun."""
import pickle, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from belgi_yig import guruhla

pool = pickle.load(open("data/namunalar.pkl", "rb"))
O, SCALE, PAD = 40, 3, 26
tile = O * SCALE

for tur, nechta in (("rank", 40), ("suit", 16)):
    gs = guruhla(pool, tur)[:nechta]
    cols = 8
    rows = (len(gs) + cols - 1) // cols
    img = Image.new("RGB", (cols * (tile + 8), rows * (tile + PAD)), (20, 20, 20))
    d = ImageDraw.Draw(img)
    for i, g in enumerate(gs):
        # Markazga eng yaqin a'zo - eng toza vakil
        vakil = max(g["azolar"], key=lambda p: float(np.dot(p["v"].ravel(), g["markaz"].ravel())))
        v = vakil["v"]
        v = (v - v.min()) / max(1e-6, v.max() - v.min())
        t = Image.fromarray((v * 255).astype(np.uint8)).resize((tile, tile), Image.NEAREST)
        cx, cy = (i % cols) * (tile + 8), (i // cols) * (tile + PAD)
        img.paste(t, (cx, cy + PAD))
        d.text((cx + 3, cy + 6), f"{i}:{len(g['azolar'])}", fill=(120, 255, 120))
    out = f"/tmp/claude-1000/-home-shamsiddin/7630cb26-2332-4b77-b6c4-60c17dfa98b2/scratchpad/guruh_{tur}.png"
    img.save(out)
    print(f"{out}  {len(gs)} guruh")
