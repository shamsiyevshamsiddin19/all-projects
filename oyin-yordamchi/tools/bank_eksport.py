#!/usr/bin/env python3
"""Shablon banklarini Kotlin o'qiydigan sodda formatga chiqaradi.

Format (.bank): 4 bayt soni, 4 bayt o'lchami, keyin float32 vektorlar (little-endian).
Nomlar yonidagi .json da.
"""
import json, struct, os
import numpy as np

YON = "games/durak/profil"
MANBA = [("shablonlar.npz", "rank", "shablon_nomlar.json", "rank", "rank.bank"),
         ("shablonlar.npz", "suit", "shablon_nomlar.json", "suit", "suit.bank"),
         ("raqamlar.npz", "v", "raqam_nomlar.json", None, "raqam.bank"),
         ("pufakcha.npz", "v", "pufakcha_nomlar.json", None, "pufakcha.bank")]

for npz, kalit, nomfayl, nomkalit, chiqish in MANBA:
    v = np.load(os.path.join(YON, npz))[kalit].astype(np.float32)
    nomlar = json.load(open(os.path.join(YON, nomfayl)))
    if nomkalit:
        nomlar = nomlar[nomkalit]
    assert len(nomlar) == v.shape[0], f"{chiqish}: {len(nomlar)} nom, {v.shape[0]} vektor"
    yol = os.path.join(YON, chiqish)
    with open(yol, "wb") as f:
        f.write(struct.pack("<ii", v.shape[0], v.shape[1]))
        f.write(v.tobytes())
    json.dump(nomlar, open(yol.replace(".bank", ".names.json"), "w"))
    print(f"{chiqish}: {v.shape[0]} shablon x {v.shape[1]} o'lcham")
