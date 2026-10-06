#!/usr/bin/env python3
"""Shablon banklarini yangi material bilan qayta quradi.

Nom qo'lda berilmaydi: har namunaga hozirgi bank nom qo'yadi, keyin shu
nomlar bo'yicha qayta guruhlanadi. O'yin dizayni o'zgarganda yangi video
qo'shib shu buyruqni chopish kifoya - bank o'zi kengayadi.
"""
import glob, json, sys, struct
import numpy as np
from PIL import Image

sys.path.insert(0, "tools")
from belgi_yig import namuna, guruhla
from burchaklar import burchaklar, kozir_topish
from zaxira import raqam_bolaklari
from pufakcha import nomzodlar

YON = "games/durak/profil"


def eski_bank(nom):
    """Hozirgi bank - yangi namunalarga nom qo'yish uchun."""
    from bank import oqi
    return oqi(nom)


def nomla(vektor, v, nomlar, ruxsat=None):
    ball = v @ vektor.ravel()
    eng, eng_ball = None, -1.0
    for i, b in enumerate(ball):
        if ruxsat and nomlar[i] not in ruxsat:
            continue
        if b > eng_ball:
            eng, eng_ball = nomlar[i], float(b)
    return eng, eng_ball


def yig():
    """Har namuna uchun: (yangi vektor, eski vektor, tur, ruxsat)"""
    banklar = {k: eski_bank(f) for k, f in
               (("rank", "rank"), ("suit", "suit"), ("raqam", "raqam"), ("pufak", "pufakcha"))}
    yigindi = {k: [] for k in banklar}

    for i, f in enumerate(sorted(glob.glob("data/frames/durak-3kishi-01/*.png"))):
        img = np.array(Image.open(f).convert("RGB"))
        manbalar = [(t, img) for t in burchaklar(img)]
        kz, bur = kozir_topish(img)
        if kz:
            manbalar.append((kz, bur))
        for t, src in manbalar:
            ruxsat = {"D", "H"} if t["rang"] == "qizil" else {"S", "C"}
            for tur, quti, rx in (("rank", t["rank"], None), ("suit", t["suit"], ruxsat)):
                yangi = namuna(src, quti)
                if yangi is None:
                    continue
                v, nomlar = banklar[tur]
                nom, ball = nomla(yangi, v, nomlar, rx)
                if nom and ball >= 0.72:
                    yigindi[tur].append((yangi, nom))
        for b in raqam_bolaklari(img)[0]:
            yangi = namuna(img, b)
            if yangi is None:
                continue
            v, nomlar = banklar["raqam"]
            nom, ball = nomla(yangi, v, nomlar)
            if nom and ball >= 0.80:
                yigindi["raqam"].append((yangi, nom))
        for c in nomzodlar(img):
            yangi = namuna(img, c["matn"])
            if yangi is None:
                continue
            v, nomlar = banklar["pufak"]
            nom, ball = nomla(yangi, v, nomlar)
            if nom and ball >= 0.80:
                yigindi["pufak"].append((yangi, nom))
        if (i + 1) % 100 == 0:
            print(f"  {i+1} kadr", flush=True)
    return yigindi


def yoz(nom_fayl, namunalar):
    """Har nom ichida guruhlab, har guruhdan bitta shablon."""
    vektorlar, teglar = [], []
    nomlar = sorted({n for _, n in namunalar})
    for nom in nomlar:
        guruh = [dict(v=v, tur="x") for v, n in namunalar if n == nom]
        for g in guruhla(guruh, "x"):
            if len(g["azolar"]) < 2 and len(guruh) > 8:
                continue      # bitta namunali guruh - ehtimol tasodif
            vektorlar.append(g["markaz"].ravel().astype(np.float32))
            teglar.append(nom)
    v = np.array(vektorlar, dtype=np.float32)
    with open(f"{YON}/{nom_fayl}.bank", "wb") as f:
        f.write(struct.pack("<ii", v.shape[0], v.shape[1]))
        f.write(v.tobytes())
    json.dump(teglar, open(f"{YON}/{nom_fayl}.names.json", "w"))
    print(f"{nom_fayl}: {len(namunalar)} namuna -> {v.shape[0]} shablon, nomlar {sorted(set(teglar))}")


if __name__ == "__main__":
    y = yig()
    for tur, fayl in (("rank", "rank"), ("suit", "suit"), ("raqam", "raqam"), ("pufak", "pufakcha")):
        yoz(fayl, y[tur])
