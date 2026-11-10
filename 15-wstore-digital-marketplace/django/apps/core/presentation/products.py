"""Mahsulot modelini API v1 JSON ko'rinishiga serializatsiya qilish."""

from typing import Any

from django.http import HttpRequest

from store.models import Product


def product_to_dict(
    product: Product,
    request: HttpRequest | None = None,
) -> dict[str, Any]:
    """Mavjud API v1 contractini o'zgartirmasdan mahsulotni lug'atga aylantiradi."""
    cover_url = product.cover_url
    if request is not None and cover_url.startswith("/"):
        cover_url = request.build_absolute_uri(cover_url)
    return {
        "id": str(product.id),
        "title": product.title,
        "slug": product.slug,
        "description": product.description,
        "price": float(product.price),
        "category": product.category.slug if product.category_id else None,
        "subcategory": product.subcategory,
        "tech_stack": product.tech_stack or [],
        "features": product.features or [],
        "cover_url": cover_url,
        "demo_url": product.demo_url,
        "status": product.status,
        "rating": product.rating,
        "sales_count": product.sales_count,
        "created_at": product.created_at.isoformat(),
    }
