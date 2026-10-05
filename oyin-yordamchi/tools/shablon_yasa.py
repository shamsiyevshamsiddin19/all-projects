#!/usr/bin/env python3
"""Guruhlarga berilgan nomlardan shablon banki yasaydi.

Har guruhning markazi - bitta shablon. Tanish = eng o'xshash shablonni topish.
Axlat guruhlar ataylab tashlab ketiladi: ularga tushgan belgi "noma'lum" bo'ladi.
"""
import pickle, json
import numpy as np
import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from belgi_yig import guruhla

# Guruh raqami -> nom. Qo'lda bir marta ko'rib belgilangan.
RANK_NOM = {0:"K", 1:"J", 2:"8", 3:"6", 4:"J", 5:"Q", 6:"K", 7:"Q", 8:"10", 9:"J",
            10:"J", 11:"10", 12:"9", 13:"7", 14:"A", 15:"Q", 16:"8", 17:"9", 18:"10",
            19:"K", 20:"7", 21:"A", 22:"10", 23:"A", 24:"10", 26:"J", 27:"7", 28:"10",
            30:"7", 31:"6", 32:"10", 33:"8", 35:"7", 36:"8", 38:"6", 39:"K"}
SUIT_NOM = {0:"C", 1:"H", 2:"S", 3:"D", 4:"C", 5:"D", 6:"H", 7:"S", 8:"H",
            9:"H", 10:"D", 11:"C", 12:"D", 13:"S", 14:"C"}
pool = pickle.load(open("data/namunalar.pkl", "rb"))
banк = {}
meta = {}
for tur, nomlar in (("rank", RANK_NOM), ("suit", SUIT_NOM)):
    gs = guruhla(pool, tur)
    vektorlar, teglar, ogirlik = [], [], []
    for i, g in enumerate(gs):
        nom = nomlar.get(i)
        if nom is None:
            continue
        vektorlar.append(g["markaz"].ravel())
        teglar.append(nom)
        ogirlik.append(len(g["azolar"]))
    banк[tur] = np.array(vektorlar, dtype=np.float32)
    meta[tur] = teglar
    qamrov = sum(ogirlik) / sum(len(g["azolar"]) for g in gs)
    print(f"{tur}: {len(teglar)} shablon, namunalarning {qamrov*100:.1f}% i qamralgan")
    print(f"   darajalar: {sorted(set(teglar))}")

np.savez("games/durak/profil/shablonlar.npz", rank=banк["rank"], suit=banк["suit"])
json.dump(meta, open("games/durak/profil/shablon_nomlar.json", "w"), ensure_ascii=False, indent=1)
print("games/durak/profil/shablonlar.npz saqlandi")
