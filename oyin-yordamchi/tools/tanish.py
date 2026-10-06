#!/usr/bin/env python3
"""Kadrni kartalarga aylantiradi."""
import json, sys
import numpy as np
from PIL import Image
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from burchaklar import burchaklar, kozir_topish, KOZIR_ROI
from belgi_yig import namuna

from bank import oqi as _bank_oqi

_rank_v, _rank_n = _bank_oqi("rank")
_suit_v, _suit_n = _bank_oqi("suit")
_sh = {"rank": _rank_v, "suit": _suit_v}
_nom = {"rank": _rank_n, "suit": _suit_n}
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
    # Kozir kartasi yonboshlab yotadi va alohida, burilgan holda o'qiladi.
    # Asosiy qidiruv o'sha hududga tegmasligi kerak - aks holda bitta karta
    # ikki marta, ustiga stol kartasi deb yoziladi.
    kx0, ky0 = KOZIR_ROI[0] * img.shape[1], KOZIR_ROI[1] * img.shape[0]
    kx1, ky1 = (KOZIR_ROI[0] + KOZIR_ROI[2]) * img.shape[1], (KOZIR_ROI[1] + KOZIR_ROI[3]) * img.shape[0]

    def kozir_hududida(t):
        cx = t["box"]["x"] + t["box"]["w"] / 2
        cy = t["box"]["y"] + t["box"]["h"] / 2
        return kx0 <= cx <= kx1 and ky0 <= cy <= ky1

    uchrashuv = [(t, img, "kadr") for t in burchaklar(img) if not kozir_hududida(t)]
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
    return _takrorni_tozala(natija)


def _takrorni_tozala(natija):
    """Bitta karta ikki joyda bo'la olmaydi.

    Shunday bo'lsa - biri albatta xato. Ishonchi pastrog'i "noma'lum" ga
    chiqariladi: maslahatchiga xato karta berishdan ko'ra, bilmaslik xavfsiz.
    """
    eng_yaxshi = {}
    for k in natija:
        if k["karta"] is None:
            continue
        oldingi = eng_yaxshi.get(k["karta"])
        if oldingi is None or k["ishonch"] > oldingi["ishonch"]:
            eng_yaxshi[k["karta"]] = k
    for k in natija:
        if k["karta"] is not None and eng_yaxshi[k["karta"]] is not k:
            k["karta"] = None
    return natija


if __name__ == "__main__":
    img = np.array(Image.open(sys.argv[1]).convert("RGB"))
    for k in kartalar(img):
        print(f"  {str(k['karta']):>5}  {k['zona']:>5}  ishonch {k['ishonch']:.2f}")
