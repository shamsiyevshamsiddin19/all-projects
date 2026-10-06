#!/usr/bin/env python3
"""Kadrlar ketma-ketligidan o'yin oqimini tiklaydi.

Bitta kadr faqat "hozir nima ko'rinyapti" ni aytadi. O'yin uchun esa
tarix kerak: qaysi kartalar bitoga ketdi (ular ekranda ko'rinmaydi),
raqiblarda nechta karta qoldi, hozir kim hujum qilyapti.

Shuning uchun ilova o'yinni BOSHIDAN kuzatishi kerak. O'rtadan ulansa,
bitoga ketganlar noma'lum qoladi va maslahat zaiflashadi.
"""
import os, sys, collections

sys.path.insert(0, os.path.dirname(__file__))

TAXLAM = 36


def stol_juftlari(stol_kartalari):
    """Stoldagi kartalarni (hujum, qoplagan) juftlariga ajratadi.

    Qoplagan karta hujum kartasining ustiga o'ngga-pastga siljib tushadi -
    bu siljish barqaror, shuning uchun juftlikni joylashuvdan aniqlash mumkin.
    """
    ks = sorted(stol_kartalari, key=lambda k: k["box"]["x"])
    band = set()
    juftlar = []
    for i, a in enumerate(ks):
        if i in band:
            continue
        qoplagan = None
        for j in range(i + 1, len(ks)):
            if j in band:
                continue
            b = ks[j]
            h = (a["box"]["h"] + b["box"]["h"]) / 2
            dx = (b["box"]["x"] - a["box"]["x"]) / h
            dy = (b["box"]["y"] - a["box"]["y"]) / h
            if 0.25 < dx < 0.75 and 0.02 < dy < 0.45:
                qoplagan = b
                band.add(j)
                break
        band.add(i)
        juftlar.append((a["karta"], qoplagan["karta"] if qoplagan else None))
    return juftlar


class Kuzatuv:
    def __init__(self, raqiblar=2, tinchlik=2):
        self.raqiblar = raqiblar
        self.tinchlik = tinchlik      # holat necha kadr turgandan keyin ishonamiz
        self.tarix = collections.deque(maxlen=3)
        self.yangi_oyin()
        self.jurnal = []
        self.ziddiyat = 0      # mantiqqa zid holatlar (o'yinlar bo'ylab jami)

    def yangi_oyin(self):
        self.kozir = None
        self.bitoga = set()
        self.qol = set()
        self.stol = set()          # silliqlangan (bir necha kadr turgan) stol
        self.juftlar = []
        self.zaxira = None
        self.raqib = [6] * self.raqiblar
        self.tur_hodisalari = []     # shu tur ichida ko'rilgan hodisalar
        self.ekrandagi = set()       # hozir ekranda turgan pufakchalar
        self.himoyachi = None        # yashil halqa kimda

    # --- yordamchilar -------------------------------------------------
    def _barqaror(self, kalit):
        """Oxirgi kadrlarda kamida `tinchlik` marta ko'ringan kartalar."""
        if len(self.tarix) < self.tinchlik:
            return set(self.tarix[-1][kalit]) if self.tarix else set()
        son = collections.Counter()
        for h in self.tarix:
            son.update(set(h[kalit]))
        return {k for k, v in son.items() if v >= self.tinchlik}

    def _jurnal(self, vaqt, matn):
        self.jurnal.append((vaqt, matn))

    # --- asosiy qadam -------------------------------------------------
    def qadam(self, h, vaqt=0.0):
        oldingi_stol = set(self.stol)
        self.tarix.append(h)

        # Kozir o'yin davomida o'zgarmaydi - bir marta o'qilsa yetadi.
        if h["kozir"] and not self.kozir:
            self.kozir = h["kozir"]
            self._jurnal(vaqt, f"kozir {self.kozir}")

        # Zaxira soni faqat kamayadi; ko'tarilsa - yangi o'yin boshlangan.
        if h["zaxira"] is not None:
            if self.zaxira is not None and h["zaxira"] > self.zaxira + 1:
                self._jurnal(vaqt, f"YANGI O'YIN (zaxira {self.zaxira} -> {h['zaxira']})")
                self.yangi_oyin()
            self.zaxira = h["zaxira"]

        self.qol = self._barqaror("qol")
        yangi_stol = self._barqaror("stol")

        # Stol bo'shadi - tur tugadi. Kartalar qayerga ketdi?
        if oldingi_stol and not yangi_stol:
            # Tur ichida kimdir "oldim" degan bo'lsa - kartalar o'shanga ketadi.
            # "pas" va "bito" esa turning bito bilan yopilganini bildiradi.
            olgan = next((e for e in self.tur_hodisalari if e[1] == "oldim"), None)
            if olgan:
                egasi = olgan[0]
                if egasi == "men":
                    self._jurnal(vaqt, f"men oldim: {len(oldingi_stol)} karta")
                else:
                    i = 0 if egasi == "chap" else 1
                    self.raqib[i] += len(oldingi_stol)
                    self._jurnal(vaqt, f"{egasi} oldi: {len(oldingi_stol)} karta")
            else:
                self.bitoga |= oldingi_stol
                self._jurnal(vaqt, f"bito: {' '.join(sorted(oldingi_stol))} "
                                   f"(jami {len(self.bitoga)})")
            self.tur_hodisalari = []

        if h.get("himoyachi"):
            self.himoyachi = h["himoyachi"]
        self.stol = yangi_stol
        # Juftlik joriy kadrdagi joylashuvdan aniqlanadi; silliqlangan to'plamda
        # bor-u, shu kadrda ko'rinmagan karta "qoplanmagan" deb qo'shiladi.
        korinayotgan = [k for k in h["_kartalar"]
                        if k["zona"] == "stol" and k["karta"] in yangi_stol]
        self.juftlar = stol_juftlari(korinayotgan)
        topilgan = {c for j in self.juftlar for c in j if c}
        for yoq in sorted(yangi_stol - topilgan):
            self.juftlar.append((yoq, None))

        # Pufakcha ekranda bir necha soniya turadi. Shuning uchun hodisa faqat
        # PAYDO BO'LGAN payti qayd qilinadi - aks holda u keyingi turga ham o'tib ketadi.
        hozir = {(e["kim"], e["hodisa"]) for e in h["hodisalar"]}
        for juft in hozir - self.ekrandagi:
            self.tur_hodisalari.append(juft)
        self.ekrandagi = hozir

        # Bitoga ketgan karta qaytib kelmaydi. Kelsa - biror joyda xato o'qilgan.
        # Bunda ko'z bilan ko'rinayotganiga ishonamiz: u to'g'ridan-to'g'ri kuzatuv,
        # bitoga ketganlar esa xulosa.
        qaytganlar = self.stol & self.bitoga
        if qaytganlar:
            self.ziddiyat += len(qaytganlar)
            self.bitoga -= qaytganlar
            self._jurnal(vaqt, f"ZIDDIYAT: {' '.join(sorted(qaytganlar))} bitodan qaytdi "
                               f"- xato o'qilgan, bitodan chiqarildi")

        return self.holat()

    def raqiblardagi_jami(self):
        """Saqlanish qonuni: 36 ta kartadan ko'ringanlarini ayirsak, qolgani raqiblarda."""
        stolda = len(self.stol)
        korigan = len(self.qol) + stolda + len(self.bitoga) + (self.zaxira or 0)
        return max(0, TAXLAM - korigan)

    def holat(self):
        return dict(kozir=self.kozir, qol=sorted(self.qol), juftlar=self.juftlar,
                    bitoga=len(self.bitoga), zaxira=self.zaxira,
                    raqiblarda=self.raqiblardagi_jami(), raqib=list(self.raqib))

    def dvigatel_uchun(self):
        """Kotlin dvigateli tushunadigan ko'rinish."""
        jami = self.raqiblardagi_jami()
        # Alohida sonlar aniq emas - saqlanish qonuni bilan moslanadi.
        taqsim = list(self.raqib)
        if sum(taqsim) > 0:
            k = jami / sum(taqsim)
            taqsim = [max(0, round(x * k)) for x in taqsim]
        farq = jami - sum(taqsim)
        if taqsim:
            taqsim[0] += farq
        return dict(
            rol="himoya" if self.himoyachi == "men" else "hujum",
            himoyachi=self.himoyachi,
            kozir=self.kozir,
            qol=sorted(self.qol),
            hujumlar=[a for a, _ in self.juftlar],
            qoplaganlar=[d for _, d in self.juftlar],
            zaxira=self.zaxira or 0,
            bitoga=sorted(self.bitoga),
            raqiblar=[max(0, x) for x in taqsim],
        )
