import json
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, FileResponse, Http404, HttpResponseForbidden
from django.db import transaction
from django.db.models import F
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.logging_utils import log_error
from store.models import Product
from .models import Order, ClickTransaction, Withdrawal
from .forms import WithdrawalForm
from .utils import (
    build_click_payment_url,
    parse_click_transaction_id,
    check_bridge_secret,
    amounts_match,
    amount_after_commission,
    generate_secure_download_token,
    CLICK_PREFIX_PURCHASE,
    CLICK_PREFIX_LISTING,
)

User = get_user_model()


def _simulation_requested(request):
    """
    "Demo to'lov" faqat DEMO_MODE yoniq bo'lganda qabul qilinadi.
    Avval bu tekshiruv yo'q edi: istalgan odam checkout'ga `simulate=1`
    yuborib, mahsulotni to'lovsiz PAID holatiga o'tkazib, yuklab olish
    tokenini olishi mumkin edi.
    """
    if not getattr(settings, "DEMO_MODE", False):
        return False
    return request.POST.get("simulate") == "1" or request.GET.get("simulate") == "1"


@login_required
@require_POST
def checkout_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, status=Product.Status.ACTIVE)

    # O'z mahsulotini sotib olish balansni o'z-o'ziga to'ldirish halqasi
    # bo'lardi (pul sotuvchi balansiga qaytadi) — to'sib qo'yamiz.
    if product.seller_id == request.user.id:
        messages.error(request, _("O'z loyihangizni sotib ololmaysiz."))
        return redirect("store:product_detail", slug=product.slug)

    # Allaqachon to'langan buyurtma bor bo'lsa — takroriy xarid o'rniga
    # mavjud buyurtmaga yo'naltiramiz (ikki marta pul to'lanmasin).
    existing_paid = Order.objects.filter(
        buyer=request.user, product=product, status=Order.PayStatus.PAID
    ).first()
    if existing_paid:
        messages.info(request, _("«%(title)s» allaqachon xarid qilingan.") % {"title": product.title})
        return redirect("orders:order_status", order_id=existing_paid.id)

    # Calculate amount in UZS
    amount_som = product.price_som

    with transaction.atomic():
        # Create an Order
        order = Order.objects.create(
            buyer=request.user,
            product=product,
            amount=amount_som,
            status=Order.PayStatus.PENDING,
            provider="click",
        )

        # Create Click Transaction
        ct = ClickTransaction.objects.create(
            kind=ClickTransaction.ClickKind.PURCHASE,
            order=order,
            product=product,
            amount=amount_som,
            status=Order.PayStatus.PENDING,
        )
        ct.merchant_trans_id = f"{CLICK_PREFIX_PURCHASE}{ct.id}"
        ct.save(update_fields=["merchant_trans_id"])

    # If demo simulation requested
    if _simulation_requested(request):
        # Simulate payment directly for local convenience
        with transaction.atomic():
            ct.status = Order.PayStatus.PAID
            ct.paid_at = timezone.now()
            ct.click_trans_id = f"DEMO-{ct.id}"
            ct.save()

            order.status = Order.PayStatus.PAID
            order.download_token = generate_secure_download_token()
            order.save()

            product.sales_count += 1
            product.save(update_fields=["sales_count"])

            # Credit seller balance
            net_credit = amount_after_commission(ct.amount)
            # F() — bir vaqtda kelgan ikkita to'lov bir-birining
            # balans yangilanishini bosib ketmasligi uchun
            User.objects.filter(pk=product.seller_id).update(
                balance=F("balance") + net_credit
            )

            # Referral bonus
            buyer = request.user
            if buyer.referred_by and not buyer.referral_bonus_paid:
                buyer.referral_bonus_paid = True
                buyer.save(update_fields=["referral_bonus_paid"])
                User.objects.filter(pk=buyer.referred_by_id).update(
                    balance=F("balance") + getattr(settings, "REFERRAL_BONUS_SOM", 10000)
                )

        messages.success(request, _("«%(title)s» to'lovi muvaffaqiyatli amalga oshirildi (Demo to'lov)!") % {"title": product.title})
        return redirect("orders:order_status", order_id=order.id)

    # Return URL after Click payment
    return_url = f"{getattr(settings, 'APP_URL', 'http://localhost:8000')}/orders/{order.id}/"
    click_url = build_click_payment_url(ct.merchant_trans_id, amount_som, return_url)
    return redirect(click_url)


@login_required
@require_POST
def listing_pay_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    fee = getattr(settings, "LISTING_FEE_SOM", 5000)

    with transaction.atomic():
        ct = ClickTransaction.objects.create(
            kind=ClickTransaction.ClickKind.LISTING,
            product=product,
            amount=fee,
            status=Order.PayStatus.PENDING,
        )
        ct.merchant_trans_id = f"{CLICK_PREFIX_LISTING}{ct.id}"
        ct.save(update_fields=["merchant_trans_id"])

    # If demo simulation requested
    if _simulation_requested(request):
        with transaction.atomic():
            ct.status = Order.PayStatus.PAID
            ct.paid_at = timezone.now()
            ct.save()

            if product.status == Product.Status.DRAFT:
                product.status = Product.Status.PENDING
                product.save(update_fields=["status"])

        messages.success(request, _("«%(title)s» e'lon to'lovi qabul qilindi va moderatsiyaga yuborildi!") % {"title": product.title})
        return redirect("orders:seller_dashboard")

    return_url = f"{getattr(settings, 'APP_URL', 'http://localhost:8000')}/orders/seller/"
    click_url = build_click_payment_url(ct.merchant_trans_id, fee, return_url)
    return redirect(click_url)


@login_required
def order_status_view(request, order_id):
    order = get_object_or_404(Order.objects.select_related("product", "buyer"), id=order_id)
    if order.buyer != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Ruxsat berilmagan.")

    return render(request, "orders/order_status.html", {
        "order": order,
    })


@login_required
@require_POST
def order_simulate_pay_view(request, order_id):
    """
    Kutilayotgan buyurtmani demo rejimida to'langan deb belgilaydi.

    Ilgari «To'lovni simulyatsiya qilish» tugmasi checkout_view'ga yuborardi,
    u esa HAR SAFAR YANGI buyurtma yaratardi — natijada joriy buyurtma abadiy
    PENDING holatda qolar, sahifadagi avtomatik tekshiruv hech qachon
    yangilanmas, bazada esa keraksiz buyurtmalar to'planib borardi.
    """
    order = get_object_or_404(Order.objects.select_related("product"), id=order_id, buyer=request.user)

    if not _simulation_requested(request):
        raise Http404("Demo to'lov o'chirilgan.")

    if order.status == Order.PayStatus.PAID:
        return redirect("orders:order_status", order_id=order.id)

    with transaction.atomic():
        ct = order.click_transactions.filter(status=Order.PayStatus.PENDING).first()
        if ct:
            ct.status = Order.PayStatus.PAID
            ct.paid_at = timezone.now()
            ct.click_trans_id = f"DEMO-{ct.id}"
            ct.save(update_fields=["status", "paid_at", "click_trans_id"])

        order.status = Order.PayStatus.PAID
        order.download_token = generate_secure_download_token()
        order.save(update_fields=["status", "download_token"])

        product = order.product
        product.sales_count += 1
        product.save(update_fields=["sales_count"])

        User.objects.filter(pk=product.seller_id).update(
            balance=F("balance") + amount_after_commission(order.amount)
        )

        buyer = order.buyer
        if buyer.referred_by and not buyer.referral_bonus_paid:
            buyer.referral_bonus_paid = True
            buyer.save(update_fields=["referral_bonus_paid"])
            User.objects.filter(pk=buyer.referred_by_id).update(
                balance=F("balance") + getattr(settings, "REFERRAL_BONUS_SOM", 10000)
            )

    messages.success(request, _("«%(title)s» to'lovi qabul qilindi (Demo to'lov)!") % {"title": order.product.title})
    return redirect("orders:order_status", order_id=order.id)


@login_required
def order_status_poll_api(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    return JsonResponse({
        "status": order.status,
        "is_paid": order.status == Order.PayStatus.PAID,
        "download_token": order.download_token,
    })


def download_file_view(request, token):
    order = get_object_or_404(Order.objects.select_related("product"), download_token=token, status=Order.PayStatus.PAID)
    product = order.product

    # Check if a file_archive exists
    if product.file_archive and os.path.exists(product.file_archive.path):
        return FileResponse(
            open(product.file_archive.path, "rb"),
            as_attachment=True,
            filename=f"{product.slug}.zip"
        )

    # Fallback placeholder demo archive response
    import io
    import zipfile
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.md", f"# {product.title}\n\nwstore.uz dan xarid qilingan manba kodi.\nMuallif: {product.seller.username}\n")
        zf.writestr("index.html", f"<!DOCTYPE html><html><head><title>{product.title}</title></head><body><h1>{product.title}</h1><p>wstore.uz loyihasi</p></body></html>")
    mem_zip.seek(0)
    return FileResponse(mem_zip, as_attachment=True, filename=f"{product.slug}.zip")


@login_required
def dashboard_view(request):
    """
    Buyer cabinet: purchased products, status, referral link card.
    """
    orders = Order.objects.filter(buyer=request.user).select_related("product").order_by("-created_at")
    referrals_count = request.user.referrals.count()
    paid_referrals_count = request.user.referrals.filter(referral_bonus_paid=True).count()
    bonus_earned = paid_referrals_count * getattr(settings, "REFERRAL_BONUS_SOM", 10000)

    # APP_URL .env da aniq berilgan bo'lsa o'shani ishlatamiz (prod domeni),
    # aks holda so'rov manzilidan yasaymiz. Ilgari standart qiymat doim
    # "http://localhost:8000" edi va boshqa portda ishlaganda havola noto'g'ri
    # chiqardi — foydalanuvchi uni nusxalab tarqatsa, ochilmasdi.
    app_url = (getattr(settings, "APP_URL", "") or "").rstrip("/")
    if not app_url or "localhost:8000" in app_url:
        app_url = request.build_absolute_uri("/").rstrip("/")
    referral_link = f"{app_url}/?ref={request.user.referral_code}"

    return render(request, "orders/dashboard.html", {
        "orders": orders,
        "referrals_count": referrals_count,
        "bonus_earned": bonus_earned,
        "referral_link": referral_link,
    })


@login_required
def seller_dashboard_view(request):
    """
    Seller panel: products list, statistics, balance overview.
    """
    products = Product.objects.filter(seller=request.user).order_by("-created_at")
    total_sales = sum(p.sales_count for p in products)
    revenue = sum(float(p.price) * p.sales_count for p in products)

    return render(request, "orders/seller_dashboard.html", {
        "products": products,
        "total_sales": total_sales,
        "revenue": revenue,
        "balance": request.user.balance,
    })


@login_required
def seller_balance_view(request):
    """
    Seller balance & withdrawal requests page.
    """
    withdrawals = Withdrawal.objects.filter(seller=request.user).order_by("-created_at")

    if request.method == "POST":
        form = WithdrawalForm(request.POST, user_balance=request.user.balance)
        if form.is_valid():
            with transaction.atomic():
                withdrawal = form.save(commit=False)
                withdrawal.seller = request.user
                withdrawal.status = Withdrawal.WithdrawalStatus.PENDING
                withdrawal.save()

                # Deduct from user balance (F() — atomik ayirish)
                User.objects.filter(pk=request.user.pk).update(
                    balance=F("balance") - withdrawal.amount
                )
                request.user.refresh_from_db(fields=["balance"])

            messages.success(request, _("%(amount)s so'm yechib olish uchun so'rov qabul qilindi. Tez orada ko'rib chiqiladi.") % {
                "amount": f"{withdrawal.amount:,.0f}".replace(",", " ")})
            return redirect("orders:seller_balance")
    else:
        form = WithdrawalForm(user_balance=request.user.balance)

    return render(request, "orders/seller_balance.html", {
        "form": form,
        "withdrawals": withdrawals,
        "balance": request.user.balance,
    })


# ---------------- CLICK WEBHOOK BRIDGE ENDPOINTS ----------------

@csrf_exempt
def click_prepare_webhook(request):
    """
    Exact implementation of handleClickPrepare matching Next.js bridge.
    """
    if request.method != "POST":
        return JsonResponse({"error": -1, "prepare_id": 0})

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": -1, "prepare_id": 0})

    if not check_bridge_secret(body.get("secret")):
        return JsonResponse({"error": -1, "prepare_id": 0})

    merchant_trans_id = body.get("merchant_trans_id")
    tx_id = parse_click_transaction_id(merchant_trans_id)
    if not tx_id:
        return JsonResponse({"error": -5, "prepare_id": 0})

    ct = ClickTransaction.objects.filter(id=tx_id).first()
    if not ct or ct.merchant_trans_id != merchant_trans_id:
        return JsonResponse({"error": -5, "prepare_id": 0})

    if not amounts_match(body.get("amount"), ct.amount):
        return JsonResponse({"error": -2, "prepare_id": ct.id})

    if ct.status == Order.PayStatus.PAID:
        return JsonResponse({"error": -4, "prepare_id": ct.id})
    if ct.status in [Order.PayStatus.FAILED, Order.PayStatus.REFUNDED]:
        return JsonResponse({"error": -9, "prepare_id": ct.id})

    return JsonResponse({"error": 0, "prepare_id": ct.id})


@csrf_exempt
def click_complete_webhook(request):
    """
    Exact implementation of handleClickComplete matching Next.js bridge.
    """
    if request.method != "POST":
        return JsonResponse({"error": -1, "prepare_id": 0})

    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": -1, "prepare_id": 0})

    if not check_bridge_secret(body.get("secret")):
        return JsonResponse({"error": -1, "prepare_id": 0})

    merchant_trans_id = body.get("merchant_trans_id")
    tx_id = parse_click_transaction_id(merchant_trans_id)
    if not tx_id:
        return JsonResponse({"error": -5, "prepare_id": 0})

    ct = ClickTransaction.objects.filter(id=tx_id).first()
    if not ct or ct.merchant_trans_id != merchant_trans_id:
        return JsonResponse({"error": -5, "prepare_id": 0})

    if not amounts_match(body.get("amount"), ct.amount):
        return JsonResponse({"error": -2, "prepare_id": ct.id})

    # Idempotent response for repeat calls
    if ct.status == Order.PayStatus.PAID:
        return JsonResponse({"error": 0, "prepare_id": ct.id})
    if ct.status in [Order.PayStatus.FAILED, Order.PayStatus.REFUNDED]:
        return JsonResponse({"error": -9, "prepare_id": ct.id})

    click_error = int(body.get("click_error") or 0)
    if click_error != 0:
        ct.status = Order.PayStatus.FAILED
        ct.click_trans_id = str(body.get("click_trans_id") or "")
        ct.save(update_fields=["status", "click_trans_id"])
        return JsonResponse({"error": -9, "prepare_id": ct.id})

    try:
        with transaction.atomic():
            ct.status = Order.PayStatus.PAID
            ct.click_trans_id = str(body.get("click_trans_id") or "")
            ct.paid_at = timezone.now()
            ct.save()

            if ct.kind == ClickTransaction.ClickKind.PURCHASE and ct.order:
                order = ct.order
                order.status = Order.PayStatus.PAID
                order.provider = "click"
                order.download_token = generate_secure_download_token()
                order.save()

                product = order.product
                product.sales_count += 1
                product.save(update_fields=["sales_count"])

                # Credit seller balance
                credit = amount_after_commission(ct.amount)
                User.objects.filter(pk=product.seller_id).update(
                    balance=F("balance") + credit
                )

                # Check referral bonus
                buyer = order.buyer
                if buyer.referred_by and not buyer.referral_bonus_paid:
                    buyer.referral_bonus_paid = True
                    buyer.save(update_fields=["referral_bonus_paid"])
                    
                    User.objects.filter(pk=buyer.referred_by_id).update(
                        balance=F("balance") + getattr(settings, "REFERRAL_BONUS_SOM", 10000)
                    )

            elif ct.kind == ClickTransaction.ClickKind.LISTING and ct.product:
                product = ct.product
                if product.status == Product.Status.DRAFT:
                    product.status = Product.Status.PENDING
                    product.save(update_fields=["status"])

    except Exception as exc:
        # Ilgari xatolik jimgina yutilardi (`e` hatto ishlatilmasdi ham) —
        # Click "error -1" olardi, lekin sababi hech qayerda qolmasdi.
        log_error(exc, context=f"click_complete merchant_trans_id={merchant_trans_id}")
        return JsonResponse({"error": -1, "prepare_id": 0})

    return JsonResponse({"error": 0, "prepare_id": ct.id})
