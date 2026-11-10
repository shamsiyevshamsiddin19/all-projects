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
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.core.exceptions import RequestDataTooBig
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from store.models import Category, Product

from .application import ProductApplicationError, ProductApplicationService
from .models import ApiToken
from .presentation import product_to_dict

MAX_BODY = 256 * 1024  # 256 KB — JSON tanasi uchun yetarli
product_service = ProductApplicationService()


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
        if not token.user.is_seller:
            return _err("API faqat sotuvchilar uchun", 403)

        request.api_token = token
        request.api_user = token.user
        token.touch()
        return view(request, *args, **kwargs)

    return wrapper


def _json_body(request):
    """So'rov tanasini JSON sifatida o'qiydi. (ma'lumot, xato) qaytaradi."""
    try:
        body = request.body
        if len(body) > MAX_BODY:
            return None, _err("So'rov tanasi juda katta", 413)
        data = json.loads(
            body or b"{}", parse_float=Decimal, parse_constant=_reject_json_constant
        )
    except RequestDataTooBig:
        return None, _err("So'rov tanasi juda katta", 413)
    except (ValueError, RecursionError, InvalidOperation):
        return None, _err("JSON noto'g'ri")
    if not isinstance(data, dict):
        return None, _err("JSON obyekt bo'lishi kerak")
    return data, None


def _reject_json_constant(value):
    raise ValueError("JSON soni chekli bo'lishi kerak")


# --------------------------------------------------------------------------
# Endpointlar
# --------------------------------------------------------------------------


@api_token_required
def me_view(request):
    """GET /api/v1/me — kalit kimga tegishli."""
    u = request.api_user
    return JsonResponse(
        {
            "ok": True,
            "user": {
                "username": u.username,
                "email": u.email,
                "display_name": u.display_name,
                "role": u.role,
                "balance": float(u.balance),
                "seller_since": u.seller_since.isoformat() if u.seller_since else None,
            },
            "token": {
                "name": request.api_token.name,
                "prefix": request.api_token.token_prefix,
            },
        }
    )


@api_token_required
def products_view(request):
    """
    GET  /api/v1/products — o'z mahsulotlari ro'yxati
    POST /api/v1/products — yangi mahsulot (DRAFT holatida)
    """
    user = request.api_user

    if request.method == "GET":
        result = product_service.list_products(
            seller=user,
            status=request.GET.get("status"),
        )
        return JsonResponse(
            {
                "ok": True,
                "count": result.total,
                "products": [product_to_dict(item, request) for item in result.items],
            }
        )

    if request.method != "POST":
        return _err("Faqat GET yoki POST", 405)

    data, err = _json_body(request)
    if err:
        return err

    try:
        product = product_service.create_product(seller=user, data=data)
    except ProductApplicationError as exc:
        return _err(exc.message, exc.status_code)
    return JsonResponse(
        {"ok": True, "product": product_to_dict(product, request)},
        status=201,
    )


@api_token_required
def product_detail_view(request, product_id):
    """
    GET    /api/v1/products/<id>
    PATCH  /api/v1/products/<id>
    DELETE /api/v1/products/<id>
    """
    try:
        product = product_service.retrieve_product(
            seller=request.api_user,
            product_id=product_id,
        )
    except ProductApplicationError as exc:
        return _err(exc.message, exc.status_code)

    if request.method == "GET":
        return JsonResponse({"ok": True, "product": product_to_dict(product, request)})

    if request.method == "DELETE":
        try:
            product_service.archive_product(
                seller=request.api_user,
                product_id=product_id,
            )
        except ProductApplicationError as exc:
            return _err(exc.message, exc.status_code)
        return JsonResponse({"ok": True, "deleted": True})

    if request.method != "PATCH":
        return _err("Faqat GET, PATCH yoki DELETE", 405)

    data, err = _json_body(request)
    if err:
        return err

    try:
        result = product_service.update_product(
            seller=request.api_user,
            product_id=product_id,
            data=data,
        )
    except ProductApplicationError as exc:
        return _err(exc.message, exc.status_code)
    return JsonResponse(
        {
            "ok": True,
            "updated": list(result.changed_fields),
            "product": product_to_dict(result.product, request),
        }
    )


@api_token_required
def stats_view(request):
    """GET /api/v1/stats — sotuv tahlili."""
    user = request.api_user

    products = Product.objects.filter(seller=user, is_deleted=False)
    agg = products.aggregate(total=Count("id"), sales=Sum("sales_count"))

    paid = Order.objects.filter(
        product__seller=user, status=Order.PayStatus.PAID
    ).select_related("product")

    revenue = paid.aggregate(total=Sum("amount"))["total"] or 0

    by_product = list(
        products.values(
            "id", "title", "slug", "status", "sales_count", "rating"
        ).order_by("-sales_count")[:50]
    )
    for row in by_product:
        row["id"] = str(row["id"])

    return JsonResponse(
        {
            "ok": True,
            "summary": {
                "products": agg["total"] or 0,
                "total_sales": agg["sales"] or 0,
                "paid_orders": paid.count(),
                "revenue_som": float(revenue),
                "balance_som": float(user.balance),
            },
            "by_product": by_product,
        }
    )


@api_token_required
def categories_view(request):
    """GET /api/v1/categories — mahsulot yaratishda kerak bo'ladigan ro'yxat."""
    return JsonResponse(
        {
            "ok": True,
            "categories": [
                {"slug": c.slug, "name": c.name}
                for c in Category.objects.all().order_by("name")
            ],
        }
    )
