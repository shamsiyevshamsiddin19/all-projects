"""
Foydalanuvchi profili, «Sotuvchi bo'lish» anketasi va API kalitlari.

Sotuvchi paneli endi to'g'ridan-to'g'ri yuqori menyudan ochilmaydi: avval
profil orqali anketa to'ldiriladi (`seller_onboarding_view`), shundan keyingina
panel va API kalitlari ochiladi. Shu sabab bu yerdagi view'lar `is_seller`
emas, `seller_onboarded` ni tekshiradi.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from orders.models import Order
from store.models import Product, Wishlist

from .forms import ApiTokenForm, ProfileForm, SellerOnboardingForm
from .models import ApiToken


@login_required
def profile_view(request):
    """Profil: shaxsiy ma'lumotlar, statistika va sotuvchi bo'limiga kirish."""
    user = request.user

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profil yangilandi."))
            return redirect("core:profile")
    else:
        form = ProfileForm(instance=user)

    stats = {
        "orders": Order.objects.filter(buyer=user, status=Order.PayStatus.PAID).count(),
        "wishlist": Wishlist.objects.filter(user=user).count(),
        "referrals": user.referrals.count(),
    }

    seller_stats = None
    if user.seller_onboarded:
        agg = Product.objects.filter(seller=user).aggregate(
            total=Count("id"), sales=Sum("sales_count")
        )
        seller_stats = {
            "products": agg["total"] or 0,
            "sales": agg["sales"] or 0,
            "balance": user.balance,
            "active_tokens": user.api_tokens.filter(revoked_at__isnull=True).count(),
        }

    return render(request, "core/profile.html", {
        "form": form,
        "stats": stats,
        "seller_stats": seller_stats,
    })


@login_required
def seller_onboarding_view(request):
    """«Sotuvchi bo'lish» — anketa to'ldirilgach rol SELLER ga o'tadi."""
    user = request.user

    if user.seller_onboarded:
        return redirect("orders:seller_dashboard")

    if request.method == "POST":
        form = SellerOnboardingForm(request.POST, instance=user)
        if form.is_valid():
            seller = form.save(commit=False)
            seller.seller_since = timezone.now()
            # Admin rolini pasaytirib yubormaymiz — faqat xaridorni ko'taramiz.
            if seller.role == user.Role.BUYER:
                seller.role = user.Role.SELLER
            seller.save()
            messages.success(request, _("Tabriklaymiz! Endi siz sotuvchisiz — birinchi loyihangizni qo'shing."))
            return redirect("orders:seller_dashboard")
    else:
        form = SellerOnboardingForm(instance=user)

    return render(request, "core/seller_onboarding.html", {"form": form})


@login_required
def api_tokens_view(request):
    """
    API kalitlari ro'yxati va yangisini yaratish.

    Yangi kalitning to'liq qiymati FAQAT shu javobda bir marta ko'rsatiladi —
    bazada xeshi saqlanadi, shuning uchun keyin uni qayta ko'rsatib bo'lmaydi.
    Qiymat sessiyaga yozilib, redirect'dan keyin bir marta o'qiladi: shunda
    sahifa yangilansa token qaytib chiqmaydi va brauzer tarixida qolmaydi.
    """
    user = request.user

    if not user.seller_onboarded:
        messages.info(request, _("API kalitlari sotuvchilar uchun — avval sotuvchi bo'ling."))
        return redirect("core:seller_onboarding")

    if request.method == "POST":
        form = ApiTokenForm(request.POST)
        if form.is_valid():
            if user.api_tokens.filter(revoked_at__isnull=True).count() >= 10:
                messages.error(request, _("Faol kalitlar soni 10 tadan oshmasligi kerak."))
            else:
                _token, raw = ApiToken.generate(user, form.cleaned_data["name"])
                request.session["new_api_token"] = raw
                messages.success(request, _("Kalit yaratildi. Uni hozir nusxalab oling — boshqa ko'rsatilmaydi."))
            return redirect("core:api_tokens")
    else:
        form = ApiTokenForm()

    return render(request, "core/api_tokens.html", {
        "form": form,
        "tokens": user.api_tokens.all(),
        # pop — bir marta ko'rsatiladi, keyin sessiyadan o'chadi
        "new_token": request.session.pop("new_api_token", None),
        "api_base": request.build_absolute_uri("/api/v1/").rstrip("/"),
    })


@login_required
@require_POST
def api_token_revoke_view(request, token_id):
    """Kalitni bekor qilish. O'chirmaymiz — tarix va audit uchun qoladi."""
    token = request.user.api_tokens.filter(pk=token_id, revoked_at__isnull=True).first()
    if token:
        token.revoked_at = timezone.now()
        token.save(update_fields=["revoked_at"])
        messages.info(request, _("«%(name)s» kaliti bekor qilindi.") % {"name": token.name})
    return redirect("core:api_tokens")
