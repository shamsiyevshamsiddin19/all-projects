from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.http import Http404
from django.shortcuts import redirect, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

User = get_user_model()


def _safe_redirect_target(request, raw, fallback="store:catalog"):
    """
    `?next=` qiymatini tekshiradi. Tekshiruvsiz uni to'g'ridan-to'g'ri
    redirect'ga berish ochiq redirect (open redirect) bo'ladi.
    """
    if raw and url_has_allowed_host_and_scheme(
        url=raw,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return raw
    return resolve_url(fallback)


def login_view(request):
    """Kirish faqat Google OAuth oqimiga yo'naltiriladi."""
    if request.user.is_authenticated:
        return redirect("store:catalog")
    # Eski /login manzillari va bookmarklar ishlashda davom etadi, ammo
    # email/parol endpointi autentifikatsiya yo'li bo'lib qolmaydi.
    next_url = request.GET.get("next") or request.POST.get("next")
    google_url = resolve_url("core:google_login")
    if next_url:
        google_url = f"{google_url}?{urlencode({'next': next_url})}"
    return redirect(google_url)


def register_view(request):
    """Alohida ro'yxatdan o'tish ham Google OAuth orqali bajariladi."""
    return login_view(request)


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, _("Tizimdan muvaffaqiyatli chiqdingiz."))
    return redirect("store:catalog")


def demo_login_view(request):
    """
    Portfolio ko'rsatish uchun tezkor demo kirish: Xaridor yoki Sotuvchi.

    ADMIN ROLI ATAYLAB OLIB TASHLANDI. Ilgari `?role=admin` istalgan odamni
    superuser hisobiga kiritardi — sayt ommaviy domenda turgani uchun bu
    to'liq autentifikatsiyani chetlab o'tish demak edi. Admin panelga endi
    faqat /admin/ orqali, haqiqiy parol bilan kiriladi.

    Demo hisoblarga parol ham o'rnatilmaydi (`set_unusable_password`):
    ular faqat shu tugma orqali ishlaydi, /admin/ dan emas.
    """
    if not getattr(settings, "DEMO_MODE", False):
        raise Http404("Demo kirish o'chirilgan.")

    role = request.GET.get("role", "buyer").lower()
    if role not in ("buyer", "seller"):
        raise Http404("Bunday demo rol yo'q.")

    if role == "seller":
        defaults = {
            "email": "seller@wstore.uz",
            "first_name": "Sotuvchi Demo",
            "role": User.Role.SELLER,
            "balance": 150000,
        }
        username = "seller"
    else:
        defaults = {
            "email": "buyer@wstore.uz",
            "first_name": "Xaridor Demo",
            "role": User.Role.BUYER,
            "balance": 50000,
        }
        username = "buyer"

    user = User.objects.filter(username=username).first()
    if not user:
        user = User(username=username, **defaults)
        user.set_unusable_password()
        user.save()

    # Demo hisob hech qachon admin bo'lmasligi kerak — bazada allaqachon
    # huquq berilgan bo'lsa ham qaytarib olamiz.
    if user.is_staff or user.is_superuser:
        user.is_staff = False
        user.is_superuser = False
        user.save(update_fields=["is_staff", "is_superuser"])

    login(request, user)
    messages.success(
        request,
        _("%(role)s sifatida tezkor kirdingiz: %(name)s")
        % {"role": user.get_role_display(), "name": user.display_name},
    )
    return redirect("store:catalog")
