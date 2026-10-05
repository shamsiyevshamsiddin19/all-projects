#!/usr/bin/env python3
"""Kadrdagi barcha karta burchaklarini (raqam + mast juftligi) topadi.

G'oya: qaysi zona bo'lishidan qat'i nazar, har karta burchagida
toza oq fonda raqam turadi va uning TAGIDA mast belgisi turadi.
Shuning uchun zona bo'yicha emas, shu naqsh bo'yicha qidiramiz -
qo'l, stol va kozir uchun bitta mantiq yetadi.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage


def maskalar(img):
    r, g, b = img[..., 0].astype(int), img[..., 1].astype(int), img[..., 2].astype(int)
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    oq = (r > 170) & (g > 170) & (b > 170) & ((mx - mn) < 45)
    qora = mx < 120
    qizil = (r > 110) & (r - np.maximum(g, b) > 55)
    return oq, qora, qizil


def komponentlar(mask, min_area, max_area):
    lab, n = ndimage.label(mask)
    out = []
    for sl, idx in zip(ndimage.find_objects(lab), range(1, n + 1)):
        ys, xs = sl
        area = int((lab[sl] == idx).sum())
        if not (min_area <= area <= max_area):
            continue
        out.append(dict(x=int(xs.start), y=int(ys.start),
                        w=int(xs.stop - xs.start), h=int(ys.stop - ys.start), area=area))
    return out


def qoshni_birlashtir(parts):
    """Faqat '10' ning ikki bo'lagini birlashtiradi.

    Ilgari har qanday yonma-yon bo'lakni birlashtirardi va mast belgilarini
    bir-biriga yopishtirib yuborardi - shuning uchun shart qattiq:
    chapdagisi ingichka tayoq ('1'), o'ngdagisi shunga teng balandlikda ('0').
    """
    parts = sorted(parts, key=lambda p: p["x"])
    ishlatilgan = set()
    out = []
    for i, p in enumerate(parts):
        if i in ishlatilgan:
            continue
        birlashdi = False
        for j in range(i + 1, len(parts)):
            if j in ishlatilgan:
                continue
            q = parts[j]
            gap = q["x"] - (p["x"] + p["w"])
            # '10' da ikki raqam deyarli yopishib turadi; qo'shni KARTA belgisi
            # esa karta cheti bilan ajralgan - shuning uchun oraliq juda kichik bo'lsin.
            if gap > 0.18 * p["h"]:
                break
            ingichka = p["w"] <= 0.45 * p["h"]
            bir_xil_balandlik = 0.8 * p["h"] <= q["h"] <= 1.25 * p["h"]
            yk = min(p["y"] + p["h"], q["y"] + q["h"]) - max(p["y"], q["y"])
            if ingichka and bir_xil_balandlik and gap >= -4 and yk > 0.7 * max(p["h"], q["h"]):
                x0, y0 = min(p["x"], q["x"]), min(p["y"], q["y"])
                x1 = max(p["x"] + p["w"], q["x"] + q["w"])
                y1 = max(p["y"] + p["h"], q["y"] + q["h"])
                out.append(dict(x=x0, y=y0, w=x1 - x0, h=y1 - y0, area=p["area"] + q["area"]))
                ishlatilgan.add(i); ishlatilgan.add(j)
                birlashdi = True
                break
        if not birlashdi:
            out.append(dict(p))
    return out


def _botiq(profil, min_orin):
    """Cho'qqidan keyingi birinchi botiqni (local minimum) topadi.

    Belgi va unga yopishgan rasm orasida siyoh soni kamayadi, lekin nolga
    tushmaydi - ingichka ko'prik qoladi. Shuning uchun nol emas, botiq qidiriladi.
    """
    if len(profil) == 0:
        return None
    cho_qqi = int(np.argmax(profil))
    i = cho_qqi
    while i + 1 < len(profil) and profil[i + 1] <= profil[i]:
        i += 1
    # i - pasayish tugagan joy; shu botiq bo'lsa va yetarlicha pastda bo'lsa
    if i > min_orin and i + 1 < len(profil) and profil[i] < 0.6 * profil[cho_qqi]:
        return i + 1
    return None


def mast_kes(suit, rank, m):
    """Mast belgisi kartadagi rasm bilan yopishib ketgan bo'lsa, ortig'ini kesadi.

    Yopishish ko'pincha pastdan bo'ladi (yurak -> qirolning qizil kiyimi).
    Me'yorda mast raqam balandligining yarmicha bo'ladi; undan oshsa kesiladi.
    """
    me_yor_h = 0.72 * rank["h"]
    me_yor_w = 0.85 * rank["h"]
    if suit["h"] <= me_yor_h and suit["w"] <= me_yor_w:
        return suit

    x, y, w, h = suit["x"], suit["y"], suit["w"], suit["h"]
    kesim = m[y:y + h, x:x + w]
    if kesim.size == 0:
        return suit

    yangi = dict(suit)
    if h > me_yor_h:
        kes = _botiq(kesim.sum(axis=1).astype(float), int(0.25 * h))
        if kes:
            yangi["h"] = kes
    if w > me_yor_w:
        ustun = m[y:y + yangi["h"], x:x + w].sum(axis=0).astype(float)
        kes = _botiq(ustun, int(0.25 * w))
        if kes:
            yangi["w"] = kes

    if yangi["h"] < 0.25 * rank["h"] or yangi["w"] < 0.2 * rank["h"]:
        return suit
    return yangi


def toza_fonmi(oq, box, chet=0.35):
    """Burchak belgisi atrofi oq bo'lishi kerak.

    Kartaning o'rtasidagi rasm ichida ham qora chiziqlar bor, lekin ular
    atrofi rang-barang; burchakdagi raqam esa toza oq fonda turadi.
    """
    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    dx, dy = int(w * chet) + 3, int(h * chet) + 3
    x0, y0 = max(0, x - dx), max(0, y - dy)
    x1, y1 = min(oq.shape[1], x + w + dx), min(oq.shape[0], y + h + dy)
    hudud = oq[y0:y1, x0:x1]
    if hudud.size == 0:
        return 0.0
    return float(hudud.mean())


def burchaklar(img, min_rank_h=40, min_oqlik=0.48, ochish=0):
    h, w = img.shape[:2]
    oq, qora, qizil = maskalar(img)
    oq_keng = ndimage.binary_dilation(oq, iterations=8)

    topildi = []
    for rang, m in (("qora", qora), ("qizil", qizil)):
        ink = m & oq_keng
        # Belgilar ba'zan kartadagi rasm bilan ingichka ko'prik orqali yopishadi
        # (masalan yurak qirolning qizil kiyimiga). Ochish shu ko'prikni uzadi.
        if ochish:
            ink = ndimage.binary_opening(ink, iterations=ochish)
        parts = komponentlar(ink, min_area=100, max_area=12000)
        parts = qoshni_birlashtir(parts)
        # Raqam nomzodlari: baland, juda keng emas
        ranks = [p for p in parts if p["h"] >= min_rank_h and 0.9 * p["h"] >= p["w"]]
        for rk in ranks:
            # Mast belgisi: aynan tagida, kengligi o'xshash
            cx = rk["x"] + rk["w"] / 2
            nomzod = None
            for s in parts:
                if s is rk:
                    continue
                gap = s["y"] - (rk["y"] + rk["h"])
                scx = s["x"] + s["w"] / 2
                if (-0.15 * rk["h"] <= gap <= 0.70 * rk["h"]
                        and abs(scx - cx) <= 0.70 * rk["w"]
                        and 0.30 * rk["h"] <= s["h"] <= 0.90 * rk["h"]
                        and s["w"] <= 0.95 * rk["h"]):
                    if nomzod is None or s["y"] < nomzod["y"]:
                        nomzod = s
            if nomzod is None:
                continue
            nomzod = mast_kes(nomzod, rk, m)
            box = dict(
                x=min(rk["x"], nomzod["x"]), y=rk["y"],
                w=max(rk["x"] + rk["w"], nomzod["x"] + nomzod["w"]) - min(rk["x"], nomzod["x"]),
                h=nomzod["y"] + nomzod["h"] - rk["y"],
            )
            oqlik = toza_fonmi(oq, box)
            if oqlik < min_oqlik:
                continue
            topildi.append(dict(rang=rang, rank=rk, suit=nomzod, box=box, oqlik=oqlik))

    # Bir xil joydagi takrorlarni olib tashlaymiz
    topildi.sort(key=lambda t: -t["box"]["h"])
    natija = []
    for t in topildi:
        b = t["box"]
        if any(abs(b["x"] - n["box"]["x"]) < 0.6 * b["w"] and abs(b["y"] - n["box"]["y"]) < 0.6 * b["h"]
               for n in natija):
            continue
        natija.append(t)
    natija = olcham_filtri(natija, h)
    return sorted(natija, key=lambda t: (t["box"]["y"], t["box"]["x"]))


def olcham_filtri(topildi, kadr_balandligi, chidam=0.18):
    """Bitta zonadagi kartalar bir xil o'lchamda bo'ladi -
    o'rtachadan keskin farq qilgani soxta (kartalar orasidagi tirqish va h.k.)."""
    zonalar = {}
    for t in topildi:
        yc = (t["box"]["y"] + t["box"]["h"] / 2) / kadr_balandligi
        z = "qol" if yc > 0.66 else ("stol" if yc > 0.25 else "yuqori")
        zonalar.setdefault(z, []).append(t)

    out = []
    for z, ts in zonalar.items():
        if len(ts) < 3:
            out.extend(ts)
            continue
        hs = sorted(t["box"]["h"] for t in ts)
        orta = hs[len(hs) // 2]
        out.extend(t for t in ts if abs(t["box"]["h"] - orta) <= chidam * orta)
    return out


if __name__ == "__main__":
    path = sys.argv[1]
    img = np.array(Image.open(path).convert("RGB"))
    h, w = img.shape[:2]
    bs = burchaklar(img)
    print(f"{path}  {w}x{h}  burchak topildi: {len(bs)}")
    print(f"{'x':>5} {'y':>5} {'w':>4} {'h':>4} {'rang':>5} {'oqlik':>6}  zona")
    for t in bs:
        b = t["box"]
        yc = (b["y"] + b["h"] / 2) / h
        zona = "qo'l" if yc > 0.66 else ("stol" if yc > 0.25 else "yuqori")
        if b["x"] / w < 0.16 and 0.3 < yc < 0.6:
            zona = "kozir"
        print(f"{b['x']:5} {b['y']:5} {b['w']:4} {b['h']:4} {t['rang']:>5} {t['oqlik']:6.2f}  {zona}")


def kozir_topish(img, roi=(0.0, 0.33, 0.22, 0.26)):
    """Kozir kartasi chapda YONBOSHLAB yotadi - belgilari 90 gradus burilgan.

    Shuning uchun o'sha hududni burib, keyin odatdagi burchak qidiruvi
    ishlatiladi. Qaytaradi: (burchak, burilgan_rasm) yoki (None, None).
    """
    h, w = img.shape[:2]
    x0, y0 = int(roi[0] * w), int(roi[1] * h)
    x1, y1 = int((roi[0] + roi[2]) * w), int((roi[1] + roi[3]) * h)
    kesim = img[y0:y1, x0:x1]
    # Soat strelkasi bo'yicha burish: yonboshlagan karta tik holatga keladi.
    burilgan = np.rot90(kesim, k=1).copy()
    # Kozir kartasi kichik va atrofi fon - oqlik talabi pastroq.
    bs = burchaklar(burilgan, min_rank_h=25, min_oqlik=0.30)
    if not bs:
        return None, burilgan
    # Eng kattasi - kozir kartasining burchagi
    return max(bs, key=lambda t: t["box"]["h"]), burilgan
