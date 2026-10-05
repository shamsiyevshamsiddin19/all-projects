#!/usr/bin/env python3
"""Kadrni kartalarga aylantiradi."""
import json, sys
import numpy as np
from PIL import Image
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from burchaklar import burchaklar, kozir_topish
from belgi_yig import namuna

def _profil(nom):
    """Shablon banki loyiha ichida saqlanadi - video bo'lmasa ham ishlasin."""
    import os
    yon = os.path.join(os.path.dirname(__file__), "..", "games", "durak", "profil", nom)
    return yon if os.path.exists(yon) else os.path.join("data", nom)


_sh = np.load(_profil("shablonlar.npz"))
_nom = json.load(open(_profil("shablon_nomlar.json")))
QIZIL_MASTLAR = {"D", "H"}


def _tanla(vektor, tur, ruxsat=None):
    """Eng mos shablonni topadi va ikkinchi o'rindagi BOSHQA nomdan farqini qaytaradi.

    Mutlaq o'xshashlik yetarli mezon emas: belgi kartadagi rasm bilan qisman
    yopishib qolsa ball tushadi, lekin baribir to'g'ri javobdan ancha oldinda
    turadi. Shuning uchun "qancha oldinda" ham hisobga olinadi.
    """
    if vektor is None:
        return None, 0.0, 0.0
    ball = _sh[tur] @ vektor.ravel()
    eng_nom = {}
    for i, b in enumerate(ball):
        nom = _nom[tur][i]
        if ruxsat is not None and nom not in ruxsat:
            continue
        eng_nom[nom] = max(eng_nom.get(nom, -1.0), float(b))
    if not eng_nom:
        return None, 0.0, 0.0
    tartib = sorted(eng_nom.items(), key=lambda x: -x[1])
    nom, ball1 = tartib[0]
    ball2 = tartib[1][1] if len(tartib) > 1 else 0.0
    return nom, ball1, ball1 - ball2


def _qabul(ball, farq, mutlaq=0.72, past=0.50, kerakli_farq=0.10):
    """Yuqori o'xshashlik, yoki pastroq bo'lsa ham raqobatchidan aniq oldinda."""
    return ball >= mutlaq or (ball >= past and farq >= kerakli_farq)


def kartalar(img):
    """Kadrdagi kartalar: [{karta, zona, ishonch}]"""
    natija = []
    h = img.shape[0]
    uchrashuv = [(t, img, "kadr") for t in burchaklar(img)]
    kz, bur = kozir_topish(img)
    if kz is not None:
        uchrashuv.append((kz, bur, "kozir"))

    for t, src, manba in uchrashuv:
        ruxsat = QIZIL_MASTLAR if t["rang"] == "qizil" else {"S", "C"}
        r, rb, rf = _tanla(namuna(src, t["rank"]), "rank")
        s, sb, sf = _tanla(namuna(src, t["suit"]), "suit", ruxsat)
        ishonch = min(rb, sb)
        if r is None or s is None or not (_qabul(rb, rf) and _qabul(sb, sf)):
            natija.append(dict(karta=None, zona=manba, ishonch=ishonch, box=t["box"]))
            continue
        yc = (t["box"]["y"] + t["box"]["h"] / 2) / src.shape[0]
        zona = "kozir" if manba == "kozir" else ("qol" if yc > 0.66 else "stol")
        natija.append(dict(karta=r + s, zona=zona, ishonch=round(ishonch, 3), box=t["box"]))
    return natija


if __name__ == "__main__":
    img = np.array(Image.open(sys.argv[1]).convert("RGB"))
    for k in kartalar(img):
        print(f"  {str(k['karta']):>5}  {k['zona']:>5}  ishonch {k['ishonch']:.2f}")
