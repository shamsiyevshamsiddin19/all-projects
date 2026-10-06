#!/usr/bin/env python3
"""Topilgan burchaklarni kadr ustiga chizadi - xatoni ko'z bilan ko'rish uchun."""
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from burchaklar import burchaklar

path, out = sys.argv[1], sys.argv[2]
img = Image.open(path).convert("RGB")
bs = burchaklar(np.array(img))
d = ImageDraw.Draw(img)
for i, t in enumerate(bs):
    b, rk, st = t["box"], t["rank"], t["suit"]
    d.rectangle([b["x"]-2, b["y"]-2, b["x"]+b["w"]+2, b["y"]+b["h"]+2], outline=(0,255,0), width=4)
    d.rectangle([rk["x"], rk["y"], rk["x"]+rk["w"], rk["y"]+rk["h"]], outline=(255,255,0), width=2)
    d.rectangle([st["x"], st["y"], st["x"]+st["w"], st["y"]+st["h"]], outline=(0,200,255), width=2)
    d.text((b["x"], max(0, b["y"]-22)), f"{i}", fill=(0,255,0))
img.save(out)
print(f"{out} saqlandi, {len(bs)} ta belgilandi")
