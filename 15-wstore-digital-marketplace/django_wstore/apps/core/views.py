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
    1-click fast demo authentication (useful for testing buyer/seller/admin roles).

    FAQAT DEMO_MODE yoniq bo'lganda ishlaydi. Bunsiz bu endpoint har kimga
    `?role=admin` orqali superuser hisobiga kirish imkonini berardi — ya'ni
    to'liq autentifikatsiya chetlab o'tilardi.
    """
    if not getattr(settings, "DEMO_MODE", False):
        raise Http404("Demo kirish o'chirilgan.")

    role = request.GET.get("role", "buyer").lower()

    if role == "seller":
        user = User.objects.filter(role=User.Role.SELLER).first() or User.objects.filter(username="seller").first() or User.objects.filter(email="seller@wstore.uz").first()
        if not user:
            user = User.objects.create(
                username="seller",
                email="seller@wstore.uz",
                first_name="Sotuvchi Demo",
                role=User.Role.SELLER,
                balance=150000,
            )
            user.set_password("seller123")
            user.save()
    elif role == "admin":
        user = User.objects.filter(is_superuser=True).first() or User.objects.filter(username="admin").first() or User.objects.filter(email="admin@wstore.uz").first()
        if not user:
            user = User.objects.create(
                username="admin",
                email="admin@wstore.uz",
                first_name="Admin Demo",
                role=User.Role.ADMIN,
                is_staff=True,
                is_superuser=True,
            )
            user.set_password("admin123")
            user.save()
    else:
        user = User.objects.filter(role=User.Role.BUYER).first() or User.objects.filter(username="buyer").first() or User.objects.filter(email="buyer@wstore.uz").first()
        if not user:
            user = User.objects.create(
                username="buyer",
                email="buyer@wstore.uz",
                first_name="Xaridor Demo",
                role=User.Role.BUYER,
                balance=50000,
            )
            user.set_password("buyer123")
            user.save()

    login(request, user)
    messages.success(request, _("%(role)s sifatida tezkor kirdingiz: %(name)s") % {
        "role": user.get_role_display(), "name": user.display_name})
    return redirect("store:catalog")
