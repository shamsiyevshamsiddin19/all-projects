import urllib.parse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from .models import Category, Product, Review, Wishlist, Report
from .forms import ProductForm, ReviewForm, ReportForm, TECH_CHOICES, SUBCAT_CHOICES

PRICE_RANGES = [
    {"label": "$0 – $10", "min": 0, "max": 10},
    {"label": "$10 – $50", "min": 10, "max": 50},
    {"label": "$50 – $100", "min": 50, "max": 100},
    {"label": "$100 – $200", "min": 100, "max": 200},
    {"label": "$200 +", "min": 200, "max": 999999},
]

def catalog_view(request):
    # Capture referral if present in query params
    ref = request.GET.get("ref")
    if ref:
        request.session["referral_code"] = ref

    categories = Category.objects.all().order_by("name")
    products = Product.objects.filter(status=Product.Status.ACTIVE).select_related("category", "seller")

    # Search query
    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        )

    # Category filter
    category_slug = request.GET.get("category", "").strip()
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # Subcategory filter
    subcat = request.GET.get("subcat", "").strip()
    if subcat:
        products = products.filter(subcategory=subcat)

    # Tech stack filter
    #
    # Avval `tech_stack__contains=tech` ishlatilgan edi — ikki muammo bilan:
    #   1) JSONField'da `contains` SQLite/Oracle'da QO'LLAB-QUVVATLANMAYDI,
    #      ya'ni istalgan texnologiya tanlansa sayt 500 xato berardi;
    #   2) halqa ichidagi filter AND mantiqini berardi, izoh esa "any of"
    #      (OR) deb yozilgan — ikkitasini tanlasa hech narsa chiqmasdi.
    # icontains matn bo'yicha qidiradi va har ikkala bazada ishlaydi.
    selected_tech = request.GET.getlist("tech")
    if selected_tech:
        tech_q = Q()
        for tech in selected_tech:
            tech_q |= Q(tech_stack__icontains=f'"{tech}"')
        products = products.filter(tech_q)

    # Price range filter
    price_min = request.GET.get("min_price")
    price_max = request.GET.get("max_price")
    if price_min:
        try:
            products = products.filter(price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            products = products.filter(price__lte=float(price_max))
        except ValueError:
            pass

    # Sorting
    sort = request.GET.get("sort", "popular")
    if sort == "popular":
        products = products.order_by("-sales_count", "-rating", "-created_at")
    elif sort == "price_asc":
        products = products.order_by("price", "-created_at")
    elif sort == "price_desc":
        products = products.order_by("-price", "-created_at")
    elif sort == "rating":
        products = products.order_by("-rating", "-sales_count", "-created_at")
    else:  # newest
        products = products.order_by("-created_at")

    has_filters = bool(q or category_slug or subcat or selected_tech or price_min or price_max)

    # Highlights (shown when no filter is active, identical to Next.js)
    top_selling = Product.objects.filter(status=Product.Status.ACTIVE).select_related("category", "seller").order_by("-sales_count")[:10]
    new_arrivals = Product.objects.filter(status=Product.Status.ACTIVE).select_related("category", "seller").order_by("-created_at")[:10]

    # Minimal products list for real-time client-side search autocomplete
    all_active = Product.objects.filter(status=Product.Status.ACTIVE).select_related("category", "seller")
    search_index = [
        {
            "id": str(p.id),
            "title": p.title,
            "slug": p.slug,
            "price": float(p.price),
            "cover_url": p.cover_url,
            "category": p.category.name,
            "tech": p.tech_stack,
        }
        for p in all_active
    ]

    # Pagination: 30 products per page (matching Next.js PAGE_SIZE = 30)
    paginator = Paginator(products, 30)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Sahifalash havolalari uchun joriy filtrlarni saqlab qolamiz.
    # Ilgari shablon faqat q/category/subcat/sort ni qo'lda qo'shardi —
    # `tech` va narx oralig'i 2-sahifaga o'tganda yo'qolib ketardi.
    page_params = request.GET.copy()
    page_params.pop("page", None)
    pagination_qs = page_params.urlencode()

    # Wishlist IDs for authenticated user
    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = {str(pid) for pid in Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)}

    return render(request, "store/catalog.html", {
        "page_obj": page_obj,
        "categories": categories,
        "category_slug": category_slug,
        "subcat": subcat,
        "selected_tech": selected_tech,
        "tech_options": TECH_CHOICES,
        "subcat_options": SUBCAT_CHOICES[1:],  # exclude empty
        "price_ranges": PRICE_RANGES,
        "price_min": price_min,
        "price_max": price_max,
        "sort": sort,
        "q": q,
        "has_filters": has_filters,
        "top_selling": top_selling,
        "new_arrivals": new_arrivals,
        "search_index": search_index,
        # paginator allaqachon hisoblagan — alohida COUNT so'rovi shart emas
        "total_count": paginator.count,
        "pagination_qs": pagination_qs,
        "wishlist_ids": wishlist_ids,
    })


def product_detail_view(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category", "seller"),
        slug=slug
    )

    # Non-active products are only visible to the seller or staff
    if product.status != Product.Status.ACTIVE:
        if not request.user.is_authenticated or (request.user != product.seller and not request.user.is_staff):
            return HttpResponseForbidden("Ushbu mahsulot hozircha faol emas.")

    reviews = product.reviews.select_related("user").order_by("-created_at")
    # select_related — kartochkalar seller/category ga murojaat qiladi,
    # bunsiz har bir tavsiya uchun qo'shimcha so'rov ketardi
    recommended = Product.objects.filter(
        status=Product.Status.ACTIVE,
        category=product.category
    ).exclude(pk=product.pk).select_related("category", "seller")[:4]

    # Wishlist status
    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(user=request.user, product=product).exists()

    # User's existing review if any
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    review_form = ReviewForm(instance=user_review)
    report_form = ReportForm()

    # Build Telegram direct contact link
    telegram_link = None
    if product.telegram_username:
        clean_user = product.telegram_username.lstrip("@").strip()
        msg = f"Assalomu alaykum! wstore.uz dagi «{product.title}» loyihangiz bo'yicha yozmoqdaman."
        encoded = urllib.parse.quote(msg)
        telegram_link = f"https://t.me/{clean_user}?text={encoded}"

    return render(request, "store/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "recommended": recommended,
        "is_wishlisted": is_wishlisted,
        "review_form": review_form,
        "user_review": user_review,
        "report_form": report_form,
        "telegram_link": telegram_link,
    })


@login_required
def product_create_view(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            # Ensure user has seller role
            if request.user.role == request.user.Role.BUYER:
                request.user.role = request.user.Role.SELLER
                request.user.save(update_fields=["role"])

            # Status is DRAFT until listing fee is paid or approved
            product.status = Product.Status.DRAFT
            product.save()
            messages.success(request, _("«%(title)s» muvaffaqiyatli yaratildi! E'lon to'lovini amalga oshiring.") % {"title": product.title})
            return redirect("orders:seller_dashboard")
    else:
        form = ProductForm()

    return render(request, "store/product_create.html", {
        "form": form,
    })


@login_required
def product_edit_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if product.seller != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Siz faqat o'z mahsulotingizni tahrirlashingiz mumkin.")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, _("Mahsulot muvaffaqiyatli yangilandi."))
            return redirect("orders:seller_dashboard")
    else:
        form = ProductForm(instance=product)

    return render(request, "store/product_edit.html", {
        "form": form,
        "product": product,
    })


@login_required
@require_POST
def product_toggle_pause_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if product.seller != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Ruxsat berilmagan.")

    if product.status == Product.Status.ACTIVE:
        product.status = Product.Status.PAUSED
        messages.info(request, _("«%(title)s» vaqtincha to'xtatildi.") % {"title": product.title})
    elif product.status == Product.Status.PAUSED:
        product.status = Product.Status.ACTIVE
        messages.success(request, _("«%(title)s» qayta faollashtirildi.") % {"title": product.title})
    product.save(update_fields=["status"])
    return redirect("orders:seller_dashboard")


@login_required
@require_POST
def product_delete_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if product.seller != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Ruxsat berilmagan.")

    title = product.title
    product.delete()
    messages.warning(request, _("«%(title)s» o'chirildi.") % {"title": title})
    return redirect("orders:seller_dashboard")


@login_required
@require_POST
def wishlist_toggle_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    item = Wishlist.objects.filter(user=request.user, product=product).first()
    
    if item:
        item.delete()
        wishlisted = False
    else:
        Wishlist.objects.create(user=request.user, product=product)
        wishlisted = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("format") == "json":
        return JsonResponse({"wishlisted": wishlisted, "count": Wishlist.objects.filter(user=request.user).count()})

    messages.info(
        request,
        (_("«%(title)s» sevimlilarga qo'shildi") if wishlisted
         else _("«%(title)s» sevimlilardan olib tashlandi")) % {"title": product.title}
    )
    # Referer'ni tekshiruvsiz redirect'ga berish ochiq redirect bo'lardi —
    # faqat o'z domenimizdagi manzilga qaytamiz.
    referer = request.META.get("HTTP_REFERER")
    if referer and url_has_allowed_host_and_scheme(
        url=referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(referer)
    return redirect("store:catalog")


@login_required
def wishlist_list_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related("product", "product__category", "product__seller")
    products = [w.product for w in wishlist_items]
    wishlist_ids = {str(p.id) for p in products}
    return render(request, "store/wishlist.html", {
        "products": products,
        "wishlist_ids": wishlist_ids,
    })


@login_required
@require_POST
def add_review_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    form = ReviewForm(request.POST)
    if form.is_valid():
        Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                "rating": form.cleaned_data["rating"],
                "comment": form.cleaned_data["comment"],
            }
        )
        product.update_rating()
        messages.success(request, _("Sharhingiz qabul qilindi!"))
    return redirect("store:product_detail", slug=slug)


@login_required
@require_POST
def report_product_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    form = ReportForm(request.POST)
    if form.is_valid():
        report = form.save(commit=False)
        report.product = product
        report.reporter = request.user
        report.save()
        messages.warning(request, _("Shikoyatingiz qabul qilindi va moderatorlarga yuborildi."))
    return redirect("store:product_detail", slug=slug)
