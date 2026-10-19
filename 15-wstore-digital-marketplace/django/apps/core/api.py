"""
wstore REST API v1 — sotuvchining tashqi skripti yoki AI agenti uchun.

Autentifikatsiya: `Authorization: Bearer wst_...` sarlavhasi.

Nega DRF emas: API yuzasi kichik (6 ta endpoint) va server xotirasi tor
(945 MB). DRF qo'shimcha bog'liqlik va xotira talab qiladi, bu yerda esa
oddiy JSON view'lar yetarli.

XAVFSIZLIK QOIDASI: har bir so'rov `request.api_user` bo'yicha filtrlanadi.
Hech bir endpoint boshqa sotuvchining ma'lumotini qaytarmasligi yoki
o'zgartirmasligi kerak — shuning uchun hamma joyda `seller=request.api_user`
sharti bor va u hech qachon so'rov parametridan olinmaydi.
"""
import json
from functools import wraps

from django.db.models import Count, Sum
from django.http import JsonResponse
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from store.models import Category, Product

from .models import ApiToken

MAX_BODY = 256 * 1024  # 256 KB — JSON tanasi uchun yetarli


def _err(message, status=400, **extra):
    return JsonResponse({"ok": False, "error": message, **extra}, status=status)


def api_token_required(view):
    """
    Bearer tokenni tekshiradi va `request.api_user` ni o'rnatadi.

    CSRF o'chiriladi: bu brauzer sessiyasi emas, token bilan ishlaydigan
    mashina-mashina API. Token sarlavhada keladi, cookie'da emas — shuning
    uchun CSRF hujumi bu yerga tegishli emas.
    """

    @csrf_exempt
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return _err("Authorization: Bearer <token> sarlavhasi kerak", 401)

        token = ApiToken.authenticate(header[7:].strip())
        if token is None:
            return _err("Token yaroqsiz yoki bekor qilingan", 401)
        if not token.user.is_active:
            return _err("Hisob faol emas", 403)

        request.api_token = token
        request.api_user = token.user
        token.touch()
        return view(request, *args, **kwargs)

    return wrapper


def _json_body(request):
    """So'rov tanasini JSON sifatida o'qiydi. (ma'lumot, xato) qaytaradi."""
    if len(request.body) > MAX_BODY:
        return None, _err("So'rov tanasi juda katta", 413)
    try:
        data = json.loads(request.body or b"{}")
    except ValueError:
        return None, _err("JSON noto'g'ri")
    if not isinstance(data, dict):
        return None, _err("JSON obyekt bo'lishi kerak")
    return data, None


def _product_json(p, request=None):
    url = p.cover_url
    if request and url.startswith("/"):
        url = request.build_absolute_uri(url)
    return {
        "id": str(p.id),
        "title": p.title,
        "slug": p.slug,
        "description": p.description,
        "price": float(p.price),
        "category": p.category.slug if p.category_id else None,
        "subcategory": p.subcategory,
        "tech_stack": p.tech_stack or [],
        "features": p.features or [],
        "cover_url": url,
        "demo_url": p.demo_url,
        "status": p.status,
        "rating": p.rating,
        "sales_count": p.sales_count,
        "created_at": p.created_at.isoformat(),
    }


# --------------------------------------------------------------------------
# Endpointlar
# --------------------------------------------------------------------------

@api_token_required
def me_view(request):
    """GET /api/v1/me — kalit kimga tegishli."""
    u = request.api_user
    return JsonResponse({
        "ok": True,
        "user": {
            "username": u.username,
            "email": u.email,
            "display_name": u.display_name,
            "role": u.role,
            "balance": float(u.balance),
            "seller_since": u.seller_since.isoformat() if u.seller_since else None,
        },
        "token": {"name": request.api_token.name, "prefix": request.api_token.token_prefix},
    })


@api_token_required
def products_view(request):
    """
    GET  /api/v1/products — o'z mahsulotlari ro'yxati
    POST /api/v1/products — yangi mahsulot (DRAFT holatida)
    """
    user = request.api_user

    if request.method == "GET":
        qs = Product.objects.filter(seller=user).select_related("category").order_by("-created_at")
        status = request.GET.get("status")
        if status:
            qs = qs.filter(status=status.upper())
        return JsonResponse({
            "ok": True,
            "count": qs.count(),
            "products": [_product_json(p, request) for p in qs[:200]],
        })

    if request.method != "POST":
        return _err("Faqat GET yoki POST", 405)

    data, err = _json_body(request)
    if err:
        return err

    title = (data.get("title") or "").strip()
    if not title:
        return _err("«title» majburiy")

    try:
        price = float(data.get("price"))
        if price <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return _err("«price» musbat son bo'lishi kerak")

    category = Category.objects.filter(slug=(data.get("category") or "").strip()).first()
    if not category:
        return _err(
            "«category» topilmadi",
            categories=list(Category.objects.values_list("slug", flat=True)),
        )

    product = Product(
        title=title[:255],
        description=(data.get("description") or "").strip(),
        price=price,
        category=category,
        subcategory=(data.get("subcategory") or "").strip() or None,
        tech_stack=data.get("tech_stack") or [],
        features=data.get("features") or [],
        cover_image_url=(data.get("cover_url") or "").strip() or None,
        demo_url=(data.get("demo_url") or "").strip() or None,
        telegram_username=user.telegram_username,
        seller=user,
        # Yangi mahsulot har doim DRAFT: e'lon to'lovi va moderatsiya
        # saytdagi oqim orqali o'tadi — API buni chetlab o'tolmaydi.
        status=Product.Status.DRAFT,
    )
    product.save()
    return JsonResponse({"ok": True, "product": _product_json(product, request)}, status=201)


@api_token_required
def product_detail_view(request, product_id):
    """
    GET    /api/v1/products/<id>
    PATCH  /api/v1/products/<id>
    DELETE /api/v1/products/<id>
    """
    product = Product.objects.filter(id=product_id, seller=request.api_user).first()
    if not product:
        return _err("Mahsulot topilmadi", 404)

    if request.method == "GET":
        return JsonResponse({"ok": True, "product": _product_json(product, request)})

    if request.method == "DELETE":
        if product.sales_count:
            return _err("Sotilgan mahsulotni o'chirib bo'lmaydi — uni to'xtatib qo'ying", 409)
        product.delete()
        return JsonResponse({"ok": True, "deleted": True})

    if request.method != "PATCH":
        return _err("Faqat GET, PATCH yoki DELETE", 405)

    data, err = _json_body(request)
    if err:
        return err

    changed = []
    for field in ("title", "description", "subcategory", "demo_url"):
        if field in data:
            setattr(product, field, (data[field] or "").strip() or None)
            changed.append(field)

    if "price" in data:
        try:
            price = float(data["price"])
            if price <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return _err("«price» musbat son bo'lishi kerak")
        product.price = price
        changed.append("price")

    for field in ("tech_stack", "features"):
        if field in data:
            if not isinstance(data[field], list):
                return _err(f"«{field}» ro'yxat bo'lishi kerak")
            setattr(product, field, data[field])
            changed.append(field)

    if "cover_url" in data:
        product.cover_image_url = (data["cover_url"] or "").strip() or None
        changed.append("cover_image_url")

    if "category" in data:
        category = Category.objects.filter(slug=(data["category"] or "").strip()).first()
        if not category:
            return _err("«category» topilmadi")
        product.category = category
        changed.append("category")

    # Holatni API orqali faqat ACTIVE <-> PAUSED oralig'ida o'zgartirish mumkin.
    # DRAFT/PENDING/REJECTED — moderatsiya hal qiladigan holatlar, ularga
    # sotuvchi o'zi o'tolmaydi (aks holda e'lon to'lovi chetlab o'tilardi).
    if "status" in data:
        wanted = (data["status"] or "").upper()
        allowed = {Product.Status.ACTIVE, Product.Status.PAUSED}
        if wanted not in allowed:
            return _err("«status» faqat ACTIVE yoki PAUSED bo'lishi mumkin")
        if product.status not in allowed:
            return _err("Bu mahsulot hali moderatsiyadan o'tmagan", 409)
        product.status = wanted
        changed.append("status")

    if not changed:
        return _err("O'zgartirish uchun maydon berilmadi")

    product.save()
    return JsonResponse({"ok": True, "updated": changed, "product": _product_json(product, request)})


@api_token_required
def stats_view(request):
    """GET /api/v1/stats — sotuv tahlili."""
    user = request.api_user

    products = Product.objects.filter(seller=user)
    agg = products.aggregate(total=Count("id"), sales=Sum("sales_count"))

    paid = Order.objects.filter(
        product__seller=user, status=Order.PayStatus.PAID
    ).select_related("product")

    revenue = paid.aggregate(total=Sum("amount"))["total"] or 0

    by_product = list(
        products.values("id", "title", "slug", "status", "sales_count", "rating")
        .order_by("-sales_count")[:50]
    )
    for row in by_product:
        row["id"] = str(row["id"])

    return JsonResponse({
        "ok": True,
        "summary": {
            "products": agg["total"] or 0,
            "total_sales": agg["sales"] or 0,
            "paid_orders": paid.count(),
            "revenue_som": float(revenue),
            "balance_som": float(user.balance),
        },
        "by_product": by_product,
    })


@api_token_required
def categories_view(request):
    """GET /api/v1/categories — mahsulot yaratishda kerak bo'ladigan ro'yxat."""
    return JsonResponse({
        "ok": True,
        "categories": [
            {"slug": c.slug, "name": c.name}
            for c in Category.objects.all().order_by("name")
        ],
    })
