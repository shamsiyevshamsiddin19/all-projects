from django.conf import settings
from django.http import Http404
from django.shortcuts import render, redirect, resolve_url
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import LoginForm, RegisterForm

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
    """
    Kirish sahifasi — Google OAuth va Email/Parol orqali kirish.
    """
    if request.user.is_authenticated:
        return redirect("store:catalog")

    # Capture referral if present
    ref = request.GET.get("ref")
    if ref:
        request.session["referral_code"] = ref

    next_url = _safe_redirect_target(request, request.GET.get("next") or request.POST.get("next"))
    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            login_input = form.cleaned_data["login"].strip()
            password = form.cleaned_data["password"]

            user = None
            if "@" in login_input:
                user_obj = User.objects.filter(email__iexact=login_input).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            else:
                user = authenticate(request, username=login_input, password=password)

            if user:
                login(request, user)
                messages.success(request, _("Xush kelibsiz, %(name)s!") % {"name": user.display_name})
                return redirect(next_url)
            else:
                messages.error(request, _("Login yoki parol noto'g'ri kiritildi."))

    return render(request, "core/login.html", {
        "form": form,
        "next": next_url,
    })


def register_view(request):
    """
    Ro'yxatdan o'tish sahifasi — yangi foydalanuvchi yaratish yoki Google orqali kirish.
    """
    if request.user.is_authenticated:
        return redirect("store:catalog")

    ref = request.GET.get("ref")
    if ref:
        request.session["referral_code"] = ref

    next_url = _safe_redirect_target(request, request.GET.get("next") or request.POST.get("next"))
    form = RegisterForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])

            ref_code = request.session.get("referral_code")
            if ref_code:
                referrer = User.objects.filter(referral_code=ref_code).first()
                if referrer:
                    user.referred_by = referrer

            user.save()
            login(request, user)
            messages.success(request, _("Ro'yxatdan muvaffaqiyatli o'tdingiz! Xush kelibsiz!"))
            return redirect(next_url)

    return render(request, "core/register.html", {
        "form": form,
        "next": next_url,
    })


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
