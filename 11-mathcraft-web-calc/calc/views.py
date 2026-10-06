import math
from django.shortcuts import render
from django.http import HttpResponse
from .models import Calculyator


def format_number(val):
    """Sonni chiroyli formatda chiqarish (masalan 12.0 -> 12, 0.70710678 -> 0.7071)"""
    if isinstance(val, (int, float)):
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        return f"{val:.8f}".rstrip("0").rstrip(".")
    return str(val)


def hisobla(request):
    # Dastlabki holatlar
    ekran = "0"
    birinchi_son = ""
    amal = ""
    ifoda = ""
    rejim = "Scientific"
    burchak = "Deg"
    xotira = "0"
    tema = "dark"

    if request.method == "POST":
        tugma = request.POST.get("tugma", "")
        ekran = request.POST.get("ekran", "0")
        birinchi_son = request.POST.get("birinchi_son", "")
        amal = request.POST.get("amal", "")
        rejim = request.POST.get("rejim", "Scientific")
        burchak = request.POST.get("burchak", "Deg")
        xotira = request.POST.get("xotira", "0")
        tema = request.POST.get("tema", "dark")

        # 1. MAVZU (THEME) ALMASHTIRISH (🌙 / ☀️)
        if tugma == "toggle_theme":
            tema = "light" if tema == "dark" else "dark"

        # 2. REJIMLARNI O'ZGARTIRISH (Standard, Scientific, Programmer, Graph, Converter)
        elif tugma.startswith("rejim_"):
            rejim = tugma.replace("rejim_", "")

        # 3. BURCHAK BIRLIGINI O'ZGARTIRISH (Deg <-> Rad)
        elif tugma in ["Deg", "rad"]:
            burchak = "Rad" if burchak == "Deg" else "Deg"

        # 4. TARIXDAN NATIJANI TANLASH
        elif tugma.startswith("tarix_"):
            ekran = tugma.replace("tarix_", "")

        # 5. TARIXNI TOZALASH
        elif tugma == "clear_history":
            Calculyator.objects.all().delete()

        # 6. TARIXNI YUKLAB OLISH (SAVE / EXPORT HISTORY)
        elif tugma == "save_history":
            tarix_qatorlari = [
                f"{item.birinchi_son} {item.amal} {item.ikkinchi_son} = {item.natija}"
                for item in Calculyator.objects.all().order_by("id")
            ]
            fayl_matni = "\n".join(tarix_qatorlari) or "Hisob-kitoblar tarixi bo'sh."
            response = HttpResponse(fayl_matni, content_type="text/plain; charset=utf-8")
            response["Content-Disposition"] = 'attachment; filename="kalkulyator_tarix.txt"'
            return response

        # 7. XOTIRA AMALLARI (Memory: m+, mr, mc)
        elif tugma == "m+":
            try:
                xotira = str(float(xotira) + float(ekran))
            except ValueError:
                pass
        elif tugma == "mr":
            ekran = format_number(float(xotira))
        elif tugma == "mc":
            xotira = "0"

        # 8. TOZALASH AMALLARI (C, CE, Backspace)
        elif tugma == "C":
            ekran = "0"
            birinchi_son = ""
            amal = ""
            ifoda = ""
        elif tugma == "CE":
            ekran = "0"
        elif tugma == "Backspece":
            ekran = ekran[:-1]
            if not ekran or ekran == "-":
                ekran = "0"

        # 9. RAQAMLAR (0 - 9)
        elif tugma in "0123456789":
            if ekran == "0":
                ekran = tugma
            else:
                ekran += tugma

        # 10. NUQTA VA ISHORA (., ±)
        elif tugma == ".":
            if "." not in ekran:
                ekran += "."
        elif tugma == "±":
            if ekran != "0":
                ekran = ekran[1:] if ekran.startswith("-") else "-" + ekran

        # 11. MATEMATIK KONSTANTA: e
        elif tugma == "e":
            ekran = format_number(math.e)

        # 12. FOIZ (%): Ekranni 100 ga bo'lish
        elif tugma == "%":
            try:
                ekran = format_number(float(ekran) / 100)
            except ValueError:
                ekran = "Xato"

        # 13. ILMIY UNAR FUNKSIYALAR (sin, cos, tan, cot, sec, csc, ln, log, x!, x^2, e^x...)
        elif tugma in [
            "sin", "cos", "tan", "cot", "sec", "csc",
            "x^2", "x^3", "e^x", "10^x", "2^x", "|x|",
            "ln", "log_x", "x!"
        ]:
            try:
                son = float(ekran)
                natija = None
                amali_nomi = tugma

                # Trigonometriya (Burchak burchak_birligiga qarab hisoblanadi)
                rad = math.radians(son) if burchak == "Deg" else son

                if tugma == "sin":
                    natija = math.sin(rad)
                elif tugma == "cos":
                    natija = math.cos(rad)
                elif tugma == "tan":
                    natija = math.tan(rad)
                elif tugma == "cot":
                    natija = 1 / math.tan(rad) if math.tan(rad) != 0 else "Xato"
                elif tugma == "sec":
                    natija = 1 / math.cos(rad) if math.cos(rad) != 0 else "Xato"
                elif tugma == "csc":
                    natija = 1 / math.sin(rad) if math.sin(rad) != 0 else "Xato"

                # Darajalar va Eksponentalar
                elif tugma == "x^2":
                    natija = son ** 2
                elif tugma == "x^3":
                    natija = son ** 3
                elif tugma == "e^x":
                    natija = math.exp(son)
                elif tugma == "10^x":
                    natija = 10 ** son
                elif tugma == "2^x":
                    natija = 2 ** son
                elif tugma == "|x|":
                    natija = abs(son)

                # Logarifmlar va Faktorial
                elif tugma == "ln":
                    natija = math.log(son) if son > 0 else "Xato"
                elif tugma == "log_x":
                    natija = math.log10(son) if son > 0 else "Xato"
                elif tugma == "x!":
                    if 0 <= son <= 100 and son.is_integer():
                        natija = math.factorial(int(son))
                    else:
                        natija = "Xato"

                if isinstance(natija, (int, float)):
                    natija_str = format_number(natija)
                    ifoda = f"{tugma}({ekran}) ="
                    # Tarixga saqlash
                    Calculyator.objects.create(
                        birinchi_son=son,
                        amal=amali_nomi[:10],
                        ikkinchi_son=0,
                        natija=float(natija)
                    )
                    ekran = natija_str
                else:
                    ekran = str(natija)

            except (ValueError, OverflowError, ZeroDivisionError):
                ekran = "Xato"

        # 14. IKKI SONLI AMALLAR (+, -, ×, ÷, x^y)
        elif tugma in ["+", "-", "×", "÷", "x^y"]:
            birinchi_son = ekran
            amal = tugma
            ifoda = f"{birinchi_son} {amal}"
            ekran = "0"

        # 15. TENGLIK (=) BOSILGANDA
        elif tugma == "=" and birinchi_son and amal:
            try:
                son1 = float(birinchi_son)
                son2 = float(ekran)
                natija = None

                if amal == "+":
                    natija = son1 + son2
                elif amal == "-":
                    natija = son1 - son2
                elif amal == "×":
                    natija = son1 * son2
                elif amal == "÷":
                    if son2 != 0:
                        natija = son1 / son2
                    else:
                        natija = "0 ga bo'lib bo'lmaydi"
                elif amal == "x^y":
                    natija = son1 ** son2

                if isinstance(natija, (int, float)):
                    natija_str = format_number(natija)
                    ifoda = f"{birinchi_son} {amal} {ekran} ="

                    # Model amal belgisini tekislash
                    model_amal = amal
                    if amal == "×":
                        model_amal = "*"
                    elif amal == "÷":
                        model_amal = "/"
                    elif amal == "x^y":
                        model_amal = "^"

                    Calculyator.objects.create(
                        birinchi_son=son1,
                        amal=model_amal[:10],
                        ikkinchi_son=son2,
                        natija=float(natija)
                    )
                    ekran = natija_str
                    birinchi_son = ""
                    amal = ""
                else:
                    ekran = str(natija)
                    birinchi_son = ""
                    amal = ""

            except (ValueError, OverflowError):
                ekran = "Xato"
                birinchi_son = ""
                amal = ""

    # Dasturchi (Programmer) rejimi uchun konvertatsiya (BIN, OCT, HEX, DEC)
    programmer_data = {}
    try:
        butun_qiymat = int(float(ekran))
        programmer_data = {
            "hex": hex(butun_qiymat).upper().replace("0X", ""),
            "dec": str(butun_qiymat),
            "oct": oct(butun_qiymat).replace("0o", ""),
            "bin": bin(butun_qiymat).replace("0b", ""),
        }
    except (ValueError, OverflowError):
        programmer_data = {"hex": "0", "dec": "0", "oct": "0", "bin": "0"}

    # Tarix ro'yxati (oxirgi 20 ta)
    tarix = Calculyator.objects.all().order_by("-id")[:20]

    context = {
        "ekran": ekran,
        "natija": ekran,
        "birinchi_son": birinchi_son,
        "amal": amal,
        "ifoda": ifoda,
        "rejim": rejim,
        "burchak": burchak,
        "xotira": xotira,
        "tema": tema,
        "programmer": programmer_data,
        "tarix": tarix,
    }
    return render(request, "calc/hisobla.html", context)
