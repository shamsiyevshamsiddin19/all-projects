"""
Kirish talabi — manzilni iflos qilmagan holda.

MUAMMO:
    Django ning tayyor LoginRequiredMiddleware i kirmagan odamni
    kirish sahifasiga yuborayotganda manzilga qo'shimcha yozadi:

        /kirish/?next=/ijrochi/

    U "?next=" qismi orqali qayerga bormoqchi bo'lganini eslab qoladi.
    Foydali, lekin manzil chiroyli ko'rinmaydi.

YECHIM:
    Xuddi shu ma'lumotni manzilga emas, SESSIYAGA yozamiz. Sessiya —
    server tomonda saqlanadigan xotira, brauzerda faqat uning raqami
    (cookie) turadi. Natijada:

        manzil:  /kirish/          <- toza
        xatti-harakat: o'zgarmadi  <- baribir o'sha sahifaga qaytaradi

    Sessiya kirmagan odam uchun ham ishlaydi — Django uni avtomatik
    yaratadi.
"""

from django.contrib.auth.middleware import LoginRequiredMiddleware
from django.shortcuts import redirect

# Sessiyadagi kalit nomi. views.py dagi KirishView shuni o'qiydi.
KEYINGI_MANZIL = 'kirishdan_keyingi_manzil'


class KirishTalabMiddleware(LoginRequiredMiddleware):
    """LoginRequiredMiddleware, faqat ?next= o'rniga sessiya bilan."""

    def handle_no_permission(self, request, view_func):
        # DIQQAT: faqat GET so'rovni eslab qolamiz.
        #
        # POST ni eslab qolishning ma'nosi yo'q: kirgandan keyin uni
        # qayta yuborib bo'lmaydi (yuborilgan ma'lumot yo'qolgan).
        # Bunday holda odam oddiy bosh sahifaga tushadi.
        if request.method == 'GET':
            request.session[KEYINGI_MANZIL] = request.get_full_path()

        return redirect('music:login')
