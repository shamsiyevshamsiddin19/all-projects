"""
Google OAuth 2.0 — "Google bilan kirish".

Nega django-allauth emas: loyihada o'z `User` modeli (majburiy, unikal
`username` + unikal `email`), o'z kirish/ro'yxat sahifalari va o'z dizayni
bor. allauth o'zining shablonlari, `sites` ilovasi, qo'shimcha
migratsiyalari va "signup" oqimini olib keladi — ularning hammasini
mavjud oqimga moslash, shu yerdagi ~150 qatordan ko'proq ish bo'lardi.

Bu yerda standart "authorization code" oqimi ishlatiladi: kod serverdan
serverga (client_secret bilan, TLS ustida) tokenga almashtiriladi, shuning
uchun ID token imzosini alohida tekshirish shart emas — javob to'g'ridan-
to'g'ri Google'dan keladi. CSRF esa `state` parametri bilan to'siladi.
"""
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model, login
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, resolve_url
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.text import slugify

from .logging_utils import log_error
from .views import _safe_redirect_target

User = get_user_model()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

SESSION_STATE_KEY = "google_oauth_state"
SESSION_NEXT_KEY = "google_oauth_next"

HTTP_TIMEOUT = 10


def _redirect_uri(request):
    """
    Google konsolidagi "Authorized redirect URI" bilan BIR XIL bo'lishi shart —
    bitta belgi farq qilsa ham `redirect_uri_mismatch` xatosi chiqadi.
    """
    configured = getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", "")
    if configured:
        return configured
    return request.build_absolute_uri(reverse("core:google_callback"))


def _unique_username(base):
    """
    Google emailidan foydalanuvchi nomi yasaydi. `username` unikal va
    majburiy, Google esa uni bermaydi.
    """
    candidate = slugify(base).replace("-", "_")[:24] or "user"
    if not User.objects.filter(username__iexact=candidate).exists():
        return candidate
    # Ketma-ket raqam emas, tasodifiy qo'shimcha: ketma-ketlik boshqa
    # foydalanuvchilar nomini taxmin qilishga imkon berardi.
    for _ in range(10):
        suffix = secrets.token_hex(2)
        attempt = f"{candidate[:24]}_{suffix}"
        if not User.objects.filter(username__iexact=attempt).exists():
            return attempt
    return f"user_{secrets.token_hex(6)}"


def google_login_view(request):
    """Foydalanuvchini Google'ning ruxsat so'rash sahifasiga yo'naltiradi."""
    if not getattr(settings, "GOOGLE_AUTH_ENABLED", False):
        messages.error(request, _("Google orqali kirish hozircha sozlanmagan."))
        return redirect("core:login")

    if request.user.is_authenticated:
        return redirect("store:catalog")

    # Referal kodini saqlab qolamiz — Google'dan qaytgach yangi hisob
    # yaratilsa, taklif qilgan foydalanuvchi bog'lanishi kerak.
    ref = request.GET.get("ref")
    if ref:
        request.session["referral_code"] = ref

    state = secrets.token_urlsafe(32)
    request.session[SESSION_STATE_KEY] = state
    request.session[SESSION_NEXT_KEY] = _safe_redirect_target(
        request, request.GET.get("next")
    )

    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": _redirect_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        # Foydalanuvchida bir nechta Google hisobi bo'lsa, qaysi biri bilan
        # kirishni tanlash imkonini beradi.
        "prompt": "select_account",
    }
    return redirect(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


def google_callback_view(request):
    """Google qaytargan kodni tokenga almashtiradi va foydalanuvchini kiritadi."""
    if not getattr(settings, "GOOGLE_AUTH_ENABLED", False):
        messages.error(request, _("Google orqali kirish hozircha sozlanmagan."))
        return redirect("core:login")

    next_url = request.session.pop(SESSION_NEXT_KEY, None) or resolve_url("store:catalog")
    expected_state = request.session.pop(SESSION_STATE_KEY, None)

    if request.GET.get("error"):
        # Foydalanuvchi "Bekor qilish" bosgan holat ham shu yerga tushadi.
        messages.info(request, _("Google orqali kirish bekor qilindi."))
        return redirect("core:login")

    state = request.GET.get("state", "")
    if not expected_state or not constant_time_compare(expected_state, state):
        # CSRF yoki eskirgan havola: boshqa saytdan yuborilgan callback
        # bo'lishi mumkin, shuning uchun hech qanday hisobga kirmaymiz.
        messages.error(request, _("Kirish so'rovi eskirgan. Qaytadan urinib ko'ring."))
        return redirect("core:login")

    code = request.GET.get("code")
    if not code:
        messages.error(request, _("Google'dan kod qaytmadi. Qaytadan urinib ko'ring."))
        return redirect("core:login")

    try:
        token_resp = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "redirect_uri": _redirect_uri(request),
                "grant_type": "authorization_code",
            },
            timeout=HTTP_TIMEOUT,
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise ValueError("Google access_token qaytarmadi")

        info_resp = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=HTTP_TIMEOUT,
        )
        info_resp.raise_for_status()
        info = info_resp.json()
    except Exception as exc:
        log_error(exc, context="google_callback")
        messages.error(request, _("Google bilan bog'lanishda xatolik yuz berdi."))
        return redirect("core:login")

    google_id = info.get("sub")
    email = (info.get("email") or "").strip().lower()

    if not google_id or not email:
        messages.error(request, _("Google hisobidan email olinmadi."))
        return redirect("core:login")

    # Tasdiqlanmagan email bilan bog'lash xavfli: begona odam o'sha emailga
    # hisob ochib, shu yerdagi mavjud hisobni egallab olishi mumkin edi.
    if not info.get("email_verified"):
        messages.error(request, _("Google hisobingizdagi email tasdiqlanmagan."))
        return redirect("core:login")

    try:
        user, created = _get_or_create_user(request, info, google_id, email)
    except IntegrityError as exc:
        log_error(exc, context="google_callback:create_user")
        messages.error(request, _("Hisob yaratishda xatolik yuz berdi."))
        return redirect("core:login")

    login(request, user)
    if created:
        messages.success(request, _("Xush kelibsiz, %(name)s! Hisobingiz Google orqali yaratildi.") % {"name": user.display_name})
    else:
        messages.success(request, _("Xush kelibsiz, %(name)s!") % {"name": user.display_name})
    return redirect(next_url)


@transaction.atomic
def _get_or_create_user(request, info, google_id, email):
    """
    Uch holat: (1) shu Google hisobi bilan kirgan, (2) shu email bilan
    parolli hisob bor — bog'laymiz, (3) umuman yangi foydalanuvchi.
    """
    first_name = (info.get("given_name") or "").strip()
    last_name = (info.get("family_name") or "").strip()
    picture = (info.get("picture") or "").strip()

    user = User.objects.filter(google_id=google_id).first()
    if user:
        _fill_from_google(user, first_name, last_name, picture, email)
        _sync_admin(user)
        return user, False

    user = User.objects.filter(email__iexact=email).first()
    if user:
        # Mavjud hisobni Google bilan bog'laymiz — email Google tomonidan
        # tasdiqlangani yuqorida tekshirildi.
        user.google_id = google_id
        _fill_from_google(user, first_name, last_name, picture, email, extra=["google_id"])
        _sync_admin(user)
        return user, False

    is_owner = _is_admin_email(email)
    user = User(
        username=_unique_username(email.split("@")[0]),
        email=email,
        first_name=first_name or email.split("@")[0],
        last_name=last_name,
        avatar=picture or None,
        google_id=google_id,
        role=User.Role.ADMIN if is_owner else User.Role.BUYER,
        is_staff=is_owner,
        is_superuser=is_owner,
    )
    # Google orqali kirgan hisobda parol yo'q: `set_unusable_password()`
    # bo'sh parol bilan kirishga yo'l qo'ymaydi.
    user.set_unusable_password()

    ref_code = request.session.get("referral_code")
    if ref_code:
        referrer = User.objects.filter(referral_code=ref_code).first()
        if referrer:
            user.referred_by = referrer

    user.save()
    request.session.pop("referral_code", None)
    return user, True


def _is_admin_email(email):
    """Email `.env` dagi ADMIN_EMAILS ro'yxatidami."""
    return email.lower() in getattr(settings, "ADMIN_EMAILS", [])


def _sync_admin(user):
    """
    ADMIN_EMAILS ro'yxatidagi hisobga admin huquqini beradi.

    Faqat BERADI, hech qachon OLMAYDI: Django admin panelidan qo'lda
    tayinlangan moderatorlar keyingi kirishda huquqidan ayrilib
    qolmasligi kerak.
    """
    if not _is_admin_email(user.email):
        return
    changed = []
    if not user.is_staff:
        user.is_staff = True
        changed.append("is_staff")
    if not user.is_superuser:
        user.is_superuser = True
        changed.append("is_superuser")
    if user.role != User.Role.ADMIN:
        user.role = User.Role.ADMIN
        changed.append("role")
    if changed:
        user.save(update_fields=changed + ["updated_at"])


def _fill_from_google(user, first_name, last_name, picture, email, extra=None):
    """
    Google'dagi ma'lumotni faqat bo'sh maydonlarga yozadi — foydalanuvchi
    saytda o'zgartirgan ismni har kirishda qaytarib tashlamaslik uchun.
    Avatar bundan mustasno: Google havolasi muddati bilan yangilanadi.

    Hech narsa o'zgarmasa `save()` umuman chaqirilmaydi — aks holda har bir
    kirishda keraksiz UPDATE bajarilardi.
    """
    changed = list(extra or [])
    if first_name and not user.first_name:
        user.first_name = first_name
        changed.append("first_name")
    if last_name and not user.last_name:
        user.last_name = last_name
        changed.append("last_name")
    if picture and user.avatar != picture:
        user.avatar = picture
        changed.append("avatar")
    if email and user.email.lower() != email:
        user.email = email
        changed.append("email")
    if changed:
        user.save(update_fields=list(dict.fromkeys(changed)) + ["updated_at"])
