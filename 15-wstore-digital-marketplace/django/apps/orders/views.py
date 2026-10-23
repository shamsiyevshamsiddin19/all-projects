import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, FileResponse, Http404, HttpResponseForbidden
from django.db import transaction
from django.db.models import F, Sum
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.decorators import seller_required
from core.logging_utils import log_error
from store.models import Product
from .models import Order, ClickTransaction, Withdrawal
from .forms import WithdrawalForm
from core.telegram import send_telegram_notification
from .utils import (
    payments_configured,
    build_click_payment_url,
    parse_click_transaction_id,
    check_click_auth,
    extract_click_payload,
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
    product = get_object_or_404(Product, id=product_id, status=Product.Status.ACTIVE, is_deleted=False)

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

    if not _simulation_requested(request) and (not product.archive_available or not payments_configured()):
        messages.error(request, _("Onlayn xarid hozircha mavjud emas. Sotuvchi bilan bog'laning."))
        return redirect("store:product_detail", slug=product.slug)

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


@seller_required
@require_POST
def listing_pay_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user, is_deleted=False)
    if product.status != Product.Status.DRAFT:
        return redirect("orders:seller_dashboard")
    if not _simulation_requested(request) and not payments_configured():
        messages.error(request, _("Onlayn to'lov vaqtincha mavjud emas."))
        return redirect("orders:seller_dashboard")
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

    click_url = None
    if (order.status == Order.PayStatus.PENDING and order.product
            and not order.product.is_deleted and order.product.status == Product.Status.ACTIVE
            and order.product.archive_available and payments_configured()):
        ct = order.click_transactions.filter(status=Order.PayStatus.PENDING).order_by("-id").first()
        if not ct and order.product:
            ct = ClickTransaction.objects.create(
                kind=ClickTransaction.ClickKind.PURCHASE,
                order=order,
                product=order.product,
                amount=order.amount,
                status=Order.PayStatus.PENDING,
            )
            ct.merchant_trans_id = f"{CLICK_PREFIX_PURCHASE}{ct.id}"
            ct.save(update_fields=["merchant_trans_id"])

        if ct:
            return_url = f"{getattr(settings, 'APP_URL', 'http://localhost:8000')}/orders/{order.id}/"
            click_url = build_click_payment_url(ct.merchant_trans_id, ct.amount, return_url)

    return render(request, "orders/order_status.html", {
        "order": order,
        "click_url": click_url,
    })


@login_required
@require_POST
def order_simulate_pay_view(request, order_id):
    """
    Kutilayotgan buyurtmani demo rejimida to'langan deb belgilaydi.
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
        if product:
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

    title = order.product_title or (order.product.title if order.product else "")
    send_telegram_notification(
        f"🧪 <b>Demo xarid!</b>\n\n"
        f"📦 Mahsulot: {title}\n"
        f"💰 Summa: {order.amount:,.0f} so'm\n"
        f"👤 Xaridor: {order.buyer.username}"
    )

    messages.success(request, _("«%(title)s» to'lovi qabul qilindi (Demo to'lov)!") % {"title": title})
    return redirect("orders:order_status", order_id=order.id)


@login_required
def order_status_poll_api(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    return JsonResponse({
        "status": order.status,
        "is_paid": order.status == Order.PayStatus.PAID,
        "download_token": order.download_token,
    })


@login_required
def download_file_view(request, token):
    order = get_object_or_404(Order.objects.select_related("product"), download_token=token, status=Order.PayStatus.PAID)
    if order.buyer != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Faqat xarid qilgan foydalanuvchi yuklab olishi mumkin.")

    product = order.product
    if not product:
        raise Http404("Ushbu mahsulot arxivdan olib tashlangan.")

    # Check if a file_archive exists
    if not product.archive_available:
        raise Http404("Loyiha fayli hozircha mavjud emas. Sotuvchi bilan bog'laning.")
    try:
        archive = product.file_archive.open("rb")
    except OSError:
        raise Http404("Loyiha fayli hozircha mavjud emas.")
    Order.objects.filter(pk=order.pk).update(download_count=F("download_count") + 1)
    response = FileResponse(archive, as_attachment=True, filename=os.path.basename(product.file_archive.name))
    response["Cache-Control"] = "private, no-store"
    return response


def dashboard_view(request):
    """
    Buyer cabinet: purchased products, status, referral link card.
    """
    if not request.user.is_authenticated:
        return render(request, "orders/dashboard.html", {
            "orders": [],
            "referrals_count": 0,
            "bonus_earned": 0,
            "referral_link": "",
        })

    orders = Order.objects.filter(buyer=request.user).select_related("product").order_by("-created_at")
    referrals_count = request.user.referrals.count()
    paid_referrals_count = request.user.referrals.filter(referral_bonus_paid=True).count()
    bonus_earned = paid_referrals_count * getattr(settings, "REFERRAL_BONUS_SOM", 10000)

    # APP_URL .env da aniq berilgan bo'lsa o'shani ishlatamiz (prod domeni),
    # aks holda so'rov manzilidan yasaymiz.
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


@seller_required
def seller_dashboard_view(request):
    """
    Seller panel: products list, statistics, balance overview.
    """
    if not request.user.is_authenticated:
        return render(request, "orders/seller_dashboard.html", {
            "products": [],
            "total_sales": 0,
            "revenue": 0,
            "balance": 0,
        })

    products = Product.objects.filter(seller=request.user, is_deleted=False).order_by("-created_at")
    paid = Order.objects.filter(product__seller=request.user, status=Order.PayStatus.PAID)
    total_sales = paid.count()
    revenue = paid.aggregate(total=Sum("amount"))["total"] or 0

    return render(request, "orders/seller_dashboard.html", {
        "products": products,
        "total_sales": total_sales,
        "revenue": revenue,
        "balance": request.user.balance,
    })


@seller_required
def seller_balance_view(request):
    """
    Seller balance & withdrawal requests page.
    """
    if not request.user.is_authenticated:
        return render(request, "orders/seller_balance.html", {
            "form": None,
            "withdrawals": [],
            "balance": 0,
        })

    withdrawals = Withdrawal.objects.filter(seller=request.user).order_by("-created_at")

    if request.method == "POST":
        form = WithdrawalForm(request.POST, user_balance=request.user.balance)
        if form.is_valid():
            with transaction.atomic():
                withdrawal = form.save(commit=False)
                withdrawal.seller = request.user
                withdrawal.status = Withdrawal.WithdrawalStatus.PENDING
                deducted = User.objects.filter(pk=request.user.pk, balance__gte=withdrawal.amount).update(
                    balance=F("balance") - withdrawal.amount
                )
                if not deducted:
                    messages.error(request, _("Balansingizda yetarli mablag' mavjud emas."))
                    return redirect("orders:seller_balance")
                withdrawal.save()
                request.user.refresh_from_db(fields=["balance"])

            send_telegram_notification(
                f"💸 <b>Yangi pul yechish so'rovi!</b>\n\n"
                f"👤 Sotuvchi: {request.user.username} ({request.user.email})\n"
                f"💰 Summa: {withdrawal.amount:,.0f} so'm\n"
                f"💳 Karta: {withdrawal.masked_card}"
            )

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
    Direct Click Merchant API (action=0) and Bridge webhook endpoint.
    """
    if request.method != "POST":
        return JsonResponse({"error": -1, "prepare_id": 0, "error_note": "Faqat POST so'rov qabul qilinadi"})

    body = extract_click_payload(request)
    if not body:
        return JsonResponse({"error": -1, "prepare_id": 0, "error_note": "Bo'sh so'rov"})

    if not check_click_auth(body, action=0):
        return JsonResponse({"error": -1, "prepare_id": 0, "error_note": "Autentifikatsiya (imzo) xatosi"})

    merchant_trans_id = body.get("merchant_trans_id")
    tx_id = parse_click_transaction_id(merchant_trans_id)
    if not tx_id:
        return JsonResponse({"error": -5, "prepare_id": 0, "error_note": "Tranzaksiya topilmadi"})

    ct = ClickTransaction.objects.filter(id=tx_id).first()
    if not ct or ct.merchant_trans_id != merchant_trans_id:
        return JsonResponse({"error": -5, "prepare_id": 0, "error_note": "Tranzaksiya topilmadi"})

    if not amounts_match(body.get("amount"), ct.amount):
        return JsonResponse({"error": -2, "prepare_id": ct.id, "error_note": "Noto'g'ri summa"})

    if ct.status == Order.PayStatus.PAID:
        return JsonResponse({"error": -4, "prepare_id": ct.id, "error_note": "Allaqachon to'langan"})
    if ct.status in [Order.PayStatus.FAILED, Order.PayStatus.REFUNDED]:
        return JsonResponse({"error": -9, "prepare_id": ct.id, "error_note": "Tranzaksiya bekor qilingan"})

    return JsonResponse({
        "error": 0,
        "error_note": "Success",
        "click_trans_id": body.get("click_trans_id"),
        "merchant_trans_id": merchant_trans_id,
        "merchant_prepare_id": ct.id,
        "prepare_id": ct.id,
    })


@csrf_exempt
def click_complete_webhook(request):
    """
    Direct Click Merchant API (action=1) and Bridge webhook endpoint.
    """
    if request.method != "POST":
        return JsonResponse({"error": -1, "prepare_id": 0, "error_note": "Faqat POST so'rov qabul qilinadi"})

    body = extract_click_payload(request)
    if not body:
        return JsonResponse({"error": -1, "prepare_id": 0, "error_note": "Bo'sh so'rov"})

    if not check_click_auth(body, action=1):
        return JsonResponse({"error": -1, "prepare_id": 0, "error_note": "Autentifikatsiya (imzo) xatosi"})

    merchant_trans_id = body.get("merchant_trans_id")
    tx_id = parse_click_transaction_id(merchant_trans_id)
    if not tx_id:
        return JsonResponse({"error": -5, "prepare_id": 0, "error_note": "Tranzaksiya topilmadi"})

    ct = ClickTransaction.objects.filter(id=tx_id).first()
    if not ct or ct.merchant_trans_id != merchant_trans_id:
        return JsonResponse({"error": -5, "prepare_id": 0, "error_note": "Tranzaksiya topilmadi"})

    if not amounts_match(body.get("amount"), ct.amount):
        return JsonResponse({"error": -2, "prepare_id": ct.id, "error_note": "Noto'g'ri summa"})

    # Idempotent response for repeat calls
    if ct.status == Order.PayStatus.PAID:
        return JsonResponse({
            "error": 0,
            "error_note": "Success",
            "click_trans_id": body.get("click_trans_id"),
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": ct.id,
            "prepare_id": ct.id,
        })

    if ct.status in [Order.PayStatus.FAILED, Order.PayStatus.REFUNDED]:
        return JsonResponse({"error": -9, "prepare_id": ct.id, "error_note": "Tranzaksiya bekor qilingan"})

    if body.get("sign_string") and str(body.get("merchant_prepare_id")) != str(ct.pk):
        return JsonResponse({"error": -6, "prepare_id": ct.id, "error_note": "Prepare ID noto'g'ri"})
    try:
        click_error = int(body.get("click_error") or body.get("error") or 0)
    except (TypeError, ValueError):
        return JsonResponse({"error": -8, "prepare_id": ct.id, "error_note": "So'rov noto'g'ri"})
    if click_error != 0:
        ClickTransaction.objects.filter(pk=ct.pk, status=Order.PayStatus.PENDING).update(
            status=Order.PayStatus.FAILED, click_trans_id=str(body.get("click_trans_id") or "")
        )
        return JsonResponse({"error": -9, "prepare_id": ct.id, "error_note": "Click to'lov xatosi"})

    try:
        with transaction.atomic():
            # Shartli UPDATE SQLite va PostgreSQL'da takror kreditni to'sadi.
            claimed = ClickTransaction.objects.filter(pk=ct.pk, status=Order.PayStatus.PENDING).update(
                status=Order.PayStatus.PAID,
                click_trans_id=str(body.get("click_trans_id") or ""), paid_at=timezone.now()
            )
            if not claimed:
                ct.refresh_from_db()
                return JsonResponse({
                    "error": 0 if ct.status == Order.PayStatus.PAID else -9,
                    "click_trans_id": body.get("click_trans_id"),
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_confirm_id": ct.pk, "prepare_id": ct.pk,
                })

            if ct.kind == ClickTransaction.ClickKind.PURCHASE and ct.order:
                order = ct.order
                paid = Order.objects.filter(pk=order.pk, status=Order.PayStatus.PENDING).update(
                    status=Order.PayStatus.PAID, provider="click",
                    download_token=generate_secure_download_token()
                )
                if not paid:
                    if order.status != Order.PayStatus.PAID:
                        raise ValueError("Buyurtma to'lovni qabul qiladigan holatda emas")
                    return JsonResponse({
                        "error": 0, "click_trans_id": body.get("click_trans_id"),
                        "merchant_trans_id": merchant_trans_id,
                        "merchant_confirm_id": ct.pk, "prepare_id": ct.pk,
                    })

                product = order.product
                if product:
                    Product.objects.filter(pk=product.pk).update(sales_count=F("sales_count") + 1)

                    # Credit seller balance
                    credit = amount_after_commission(ct.amount)
                    User.objects.filter(pk=product.seller_id).update(
                        balance=F("balance") + credit
                    )

                # Check referral bonus
                buyer = order.buyer
                if buyer.referred_by_id and User.objects.filter(
                    pk=buyer.pk, referral_bonus_paid=False
                ).update(referral_bonus_paid=True):
                    User.objects.filter(pk=buyer.referred_by_id).update(
                        balance=F("balance") + getattr(settings, "REFERRAL_BONUS_SOM", 10000)
                    )

                title = order.product_title or (product.title if product else "")
                seller_name = product.seller.username if product else "Nomalum"
                notification = (
                    f"🎉 <b>Yangi xarid (Click)!</b>\n\n"
                    f"📦 Mahsulot: {title}\n"
                    f"💰 Summa: {ct.amount:,.0f} so'm\n"
                    f"👤 Xaridor: {buyer.username} ({buyer.email})\n"
                    f"🏪 Sotuvchi: {seller_name}"
                )
                transaction.on_commit(lambda: send_telegram_notification(notification))

            elif ct.kind == ClickTransaction.ClickKind.LISTING and ct.product:
                product = ct.product
                if product.status == Product.Status.DRAFT:
                    product.status = Product.Status.PENDING
                    product.save(update_fields=["status"])

                notification = (
                    f"📦 <b>E'lon to'lovi qabul qilindi (Click)!</b>\n\n"
                    f"🏷 Mahsulot: {product.title}\n"
                    f"💰 Summa: {ct.amount:,.0f} so'm\n"
                    f"👤 Sotuvchi: {product.seller.username}"
                )
                transaction.on_commit(lambda: send_telegram_notification(notification))

    except Exception as exc:
        log_error(exc, context=f"click_complete merchant_trans_id={merchant_trans_id}")
        return JsonResponse({"error": -1, "prepare_id": 0, "error_note": "Ichki xatolik yuz berdi"})

    return JsonResponse({
        "error": 0,
        "error_note": "Success",
        "click_trans_id": body.get("click_trans_id"),
        "merchant_trans_id": merchant_trans_id,
        "merchant_confirm_id": ct.id,
        "prepare_id": ct.id,
    })
