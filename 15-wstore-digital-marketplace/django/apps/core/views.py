from django.conf import settings
from django.http import Http404
from django.shortcuts import render, redirect, resolve_url
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET

User = get_user_model()


def _safe_redirect_target(request, raw, fallback="store:catalog"):
    """
    `?next=` qiymatini tekshiradi. Tekshiruvsiz uni to'g'ridan-to'g'ri
    redirect'ga berish ochiq redirect (open redirect) bo'ladi: hujumchi
    `?next=https://soxta-sayt.uz` yuborib, foydalanuvchini kirishdan keyin
    o'z saytiga olib ketishi mumkin edi.
    """
    if raw and url_has_allowed_host_and_scheme(
        url=raw,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return raw
    return resolve_url(fallback)

@require_GET
def login_view(request):
    """
    Kirish sahifasi — faqat "Google bilan kirish" tugmasi.

    Parol bilan kirish butunlay olib tashlandi. Shakllarni shablondan
    olib tashlashning o'zi yetarli emas edi: bu view POST qabul qilishda
    davom etsa, kimdir to'g'ridan-to'g'ri so'rov yuborib baribir parol
    bilan kira olardi. Shuning uchun view GET bilan cheklandi.

    Superuser'lar Django admin paneliga (/admin/) o'z parollari bilan
    alohida kirishadi — bu oqim o'zgarmadi.
    """
    if request.user.is_authenticated:
        return redirect("store:catalog")

    # Capture referral if present
    ref = request.GET.get("ref")
    if ref:
        request.session["referral_code"] = ref

    return render(request, "core/login.html", {
        "next": _safe_redirect_target(request, request.GET.get("next")),
    })


@require_GET
def register_view(request):
    """
    Alohida ro'yxatdan o'tish sahifasi endi yo'q: hisob Google orqali
    birinchi kirishda avtomatik yaratiladi (`oauth._get_or_create_user`).

    Manzilning o'zi saqlab qolindi — eski havolalar va xatcho'plar 404
    bermasligi uchun; ular kirish sahifasiga yo'naltiriladi.
    """
    if request.user.is_authenticated:
        return redirect("store:catalog")

    ref = request.GET.get("ref")
    if ref:
        request.session["referral_code"] = ref

    return redirect("core:login")


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
    messages.success(request, _("%(role)s sifatida tezkor kirdingiz: %(name)s") % {
        "role": user.get_role_display(), "name": user.display_name})
    return redirect("store:catalog")
