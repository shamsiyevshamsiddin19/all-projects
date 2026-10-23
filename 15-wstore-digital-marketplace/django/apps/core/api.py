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

from django.core.exceptions import RequestDataTooBig, ValidationError
from django.core.validators import URLValidator
from django.db import transaction
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
        data = json.loads(body or b"{}", parse_float=Decimal,
                          parse_constant=_reject_json_constant)
    except RequestDataTooBig:
        return None, _err("So'rov tanasi juda katta", 413)
    except (ValueError, RecursionError, InvalidOperation):
        return None, _err("JSON noto'g'ri")
    if not isinstance(data, dict):
        return None, _err("JSON obyekt bo'lishi kerak")
    return data, None


def _reject_json_constant(value):
    raise ValueError("JSON soni chekli bo'lishi kerak")


def _product_data(data, *, creating=False):
    """POST/PATCH uchun bir xil tur, uzunlik va qiymat chegaralari."""
    cleaned = {}
    text_fields = {
        "title": "title", "description": "description",
        "subcategory": "subcategory", "cover_url": "cover_image_url",
        "demo_url": "demo_url", "category": "category", "status": "status",
    }
    for name, field_name in text_fields.items():
        if name not in data:
            continue
        value = data[name]
        field = Product._meta.get_field(field_name)
        if value is None and field.null:
            value = ""
        if not isinstance(value, str):
            raise ValidationError(f"«{name}» matn bo'lishi kerak")
        value = value.strip()
        max_length = (Category._meta.get_field("slug").max_length
                      if name == "category" else field.max_length)
        if max_length and len(value) > max_length:
            raise ValidationError(f"«{name}» ko'pi bilan {max_length} belgi bo'lishi kerak")
        if name == "title" and not value:
            raise ValidationError("«title» majburiy")
        if name in ("cover_url", "demo_url") and value:
            URLValidator(schemes=["http", "https"])(value)
        if name == "category":
            value = Category.objects.filter(slug=value).first()
            if value is None:
                raise ValidationError("«category» topilmadi")
        elif name == "status":
            value = value.upper()
        elif not value and field.null:
            value = None
        cleaned[field_name] = value

    if "price" in data:
        value = data["price"]
        if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
            raise ValidationError("«price» musbat son bo'lishi kerak")
        try:
            price = Decimal(value)
        except (InvalidOperation, ValueError):
            raise ValidationError("«price» musbat son bo'lishi kerak")
        if not price.is_finite() or price <= 0:
            raise ValidationError("«price» musbat va chekli son bo'lishi kerak")
        # DecimalField bazaga sig'maydigan yoki ortiqcha kasrli narxni rad etadi.
        cleaned["price"] = Product._meta.get_field("price").clean(price, None)

    for name in ("tech_stack", "features"):
        if name in data:
            value = data[name]
            if not isinstance(value, list) or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                raise ValidationError(f"«{name}» bo'sh bo'lmagan matnlar ro'yxati bo'lishi kerak")
            cleaned[name] = [item.strip() for item in value]

    if creating:
        for name in ("title", "price", "category"):
            if name not in cleaned:
                raise ValidationError(f"«{name}» majburiy")
    return cleaned


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
        qs = Product.objects.filter(seller=user, is_deleted=False).select_related("category").order_by("-created_at")
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

    try:
        values = _product_data(data, creating=True)
    except ValidationError as exc:
        return _err("; ".join(exc.messages))
    values.pop("status", None)

    product = Product(
        **values,
        telegram_username=user.telegram_username,
        seller=user,
        # Yangi mahsulot har doim DRAFT: e'lon to'lovi va moderatsiya
        # saytdagi oqim orqali o'tadi — API buni chetlab o'tolmaydi.
        status=Product.Status.DRAFT,
    )
    # Uzun sarlavhalar takrorlansa ham slug ustuni chegarasidan chiqmasin.
    base_slug = slugify(product.title) or "product"
    product.slug = base_slug
    suffix = 1
    while Product.objects.filter(slug=product.slug).exists():
        tail = f"-{suffix}"
        product.slug = base_slug[:255 - len(tail)] + tail
        suffix += 1
    product.save()
    return JsonResponse({"ok": True, "product": _product_json(product, request)}, status=201)


@api_token_required
@transaction.atomic
def product_detail_view(request, product_id):
    """
    GET    /api/v1/products/<id>
    PATCH  /api/v1/products/<id>
    DELETE /api/v1/products/<id>
    """
    product = Product.objects.select_for_update().filter(
        id=product_id, seller=request.api_user, is_deleted=False
    ).first()
    if not product:
        return _err("Mahsulot topilmadi", 404)

    if request.method == "GET":
        return JsonResponse({"ok": True, "product": _product_json(product, request)})

    if request.method == "DELETE":
        if product.sales_count or product.orders.filter(status=Order.PayStatus.PAID).exists():
            return _err("Sotilgan mahsulotni o'chirib bo'lmaydi — uni to'xtatib qo'ying", 409)
        product.is_deleted = True
        product.status = Product.Status.PAUSED
        product.save(update_fields=["is_deleted", "status", "updated_at"])
        return JsonResponse({"ok": True, "deleted": True})

    if request.method != "PATCH":
        return _err("Faqat GET, PATCH yoki DELETE", 405)

    data, err = _json_body(request)
    if err:
        return err

    try:
        values = _product_data(data)
    except ValidationError as exc:
        return _err("; ".join(exc.messages))

    # Holatni API orqali faqat ACTIVE <-> PAUSED oralig'ida o'zgartirish mumkin.
    # DRAFT/PENDING/REJECTED — moderatsiya hal qiladigan holatlar, ularga
    # sotuvchi o'zi o'tolmaydi (aks holda e'lon to'lovi chetlab o'tilardi).
    if "status" in data:
        wanted = values["status"]
        allowed = {Product.Status.ACTIVE, Product.Status.PAUSED}
        if wanted not in allowed:
            return _err("«status» faqat ACTIVE yoki PAUSED bo'lishi mumkin")
        if product.status not in allowed:
            return _err("Bu mahsulot hali moderatsiyadan o'tmagan", 409)

    if not values:
        return _err("O'zgartirish uchun maydon berilmadi")

    for field, value in values.items():
        setattr(product, field, value)
    changed = list(values)
    product.save()
    return JsonResponse({"ok": True, "updated": changed, "product": _product_json(product, request)})


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
