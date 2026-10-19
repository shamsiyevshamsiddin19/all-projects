"""Umumiy ruxsat dekoratorlari."""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _


def seller_required(view):
    """
    Sotuvchi anketasidan o'tganlarni kiritadi.

    Ilgari sotuvchi paneliga shunchaki `@login_required` bilan — ya'ni
    istalgan ro'yxatdan o'tgan foydalanuvchi manzilni yozib kira olardi.
    Endi avval «Sotuvchi bo'lish» anketasi to'ldiriladi: faqat shunda
    xaridor bilan bog'lanish (Telegram) va to'lov (karta) ma'lumoti bo'ladi.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/auth/login/?next={request.path}")
        if not request.user.seller_onboarded:
            messages.info(request, _("Bu bo'lim sotuvchilar uchun — avval sotuvchi bo'ling."))
            return redirect("core:seller_onboarding")
        return view(request, *args, **kwargs)

    return wrapper
