"""wstore uchun shablon filtrlari."""
from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter(name="som")
def som(value):
    """
    Summani o'zbekcha ko'rinishda formatlaydi: 1082000 -> "1 082 000".

    Ilgari shablonlarda `{{ balance|floatformat:0 }}` ishlatilardi va
    "1082000" kabi o'qib bo'lmaydigan raqam chiqardi. admin.py da esa
    allaqachon `f"{int(x):,}".replace(",", " ")` naqshi ishlatilgan —
    shu qoida endi butun sayt bo'ylab bir xil.
    """
    if value in (None, ""):
        return "0"
    try:
        amount = Decimal(str(value).replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        return value
    return f"{int(amount):,}".replace(",", " ")


@register.filter(name="plain")
def plain(value):
    """
    Raqamni lokalizatsiyasiz, nuqtali ko'rinishda qaytaradi.

    `data-usd` atributi uchun zarur: LANGUAGE_CODE="uz" bo'lgani uchun
    Django narxni "29,50" deb chiqarardi, JS'dagi parseFloat esa vergulda
    to'xtab 29 ni olardi — ya'ni tanga qismi jimgina yo'qolardi.
    """
    if value in (None, ""):
        return ""
    try:
        return f"{Decimal(str(value).replace(',', '.')):f}"
    except (InvalidOperation, ValueError):
        return value
