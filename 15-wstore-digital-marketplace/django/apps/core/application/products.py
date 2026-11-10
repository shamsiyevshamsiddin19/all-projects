"""Sotuvchi mahsulot API'sining validatsiya va use-case qatlami."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.utils.text import slugify

from store.models import Category, Product

from ..models import User


class ProductApplicationError(Exception):
    """Application qoidasi buzilganda HTTP qatlamiga uzatiladigan xato."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class ProductListResult:
    """Mahsulotlar ro'yxati va filtrdan oldingi emas, haqiqiy jami soni."""

    total: int
    items: list[Product]


@dataclass(frozen=True)
class ProductUpdateResult:
    """Yangilangan mahsulot va API javobida qaytariladigan maydonlar."""

    product: Product
    changed_fields: tuple[str, ...]


class ProductPayloadValidator:
    """POST va PATCH payloadlarini Product model chegaralariga moslaydi."""

    _TEXT_FIELDS = {
        "title": "title",
        "description": "description",
        "subcategory": "subcategory",
        "cover_url": "cover_image_url",
        "demo_url": "demo_url",
        "category": "category",
        "status": "status",
    }
    _LIST_FIELDS = ("tech_stack", "features")
    # Eski mijozlar yuborishi mumkin bo'lgan, ammo faqat server boshqaradigan
    # maydonlar. Ularni sukutda chetlab o'tamiz; boshqa noma'lum maydon esa
    # shartnoma xatosi sifatida qaytariladi.
    _SERVER_MANAGED_FIELDS = {"seller", "sales_count", "is_deleted", "slug"}
    _HTTP_URL_VALIDATOR = URLValidator(schemes=["http", "https"])

    def validate(
        self,
        data: dict[str, Any],
        *,
        creating: bool = False,
    ) -> dict[str, Any]:
        """Payloadni tozalaydi; noma'lum maydonlarni yozishga ruxsat bermaydi."""
        allowed_fields = (
            set(self._TEXT_FIELDS)
            | set(self._LIST_FIELDS)
            | {"price"}
            | self._SERVER_MANAGED_FIELDS
        )
        unknown_fields = set(data) - allowed_fields
        if unknown_fields:
            names = ", ".join(sorted(unknown_fields))
            raise ValidationError(f"Ruxsat berilmagan maydonlar: {names}")

        cleaned: dict[str, Any] = {}
        self._clean_text_fields(data, cleaned)
        self._clean_price(data, cleaned)
        self._clean_list_fields(data, cleaned)

        if creating:
            for name in ("title", "price", "category"):
                if name not in cleaned:
                    raise ValidationError(f"«{name}» majburiy")

        return cleaned

    def _clean_text_fields(
        self,
        data: dict[str, Any],
        cleaned: dict[str, Any],
    ) -> None:
        for api_name, model_name in self._TEXT_FIELDS.items():
            if api_name not in data:
                continue

            value = data[api_name]
            field = Product._meta.get_field(model_name)
            if value is None and field.null:
                value = ""
            if not isinstance(value, str):
                raise ValidationError(f"«{api_name}» matn bo'lishi kerak")

            value = value.strip()
            max_length = self._max_length(api_name, field)
            if max_length and len(value) > max_length:
                raise ValidationError(
                    f"«{api_name}» ko'pi bilan {max_length} belgi bo'lishi kerak"
                )
            if api_name == "title" and not value:
                raise ValidationError("«title» majburiy")
            if api_name in {"cover_url", "demo_url"} and value:
                self._HTTP_URL_VALIDATOR(value)

            cleaned[model_name] = self._convert_text_value(
                api_name,
                value,
                field.null,
            )

    @staticmethod
    def _max_length(api_name: str, field: Any) -> int | None:
        if api_name == "category":
            return Category._meta.get_field("slug").max_length
        return field.max_length

    @staticmethod
    def _convert_text_value(
        api_name: str,
        value: str,
        nullable: bool,
    ) -> Any:
        if api_name == "category":
            category = Category.objects.filter(slug=value).first()
            if category is None:
                raise ValidationError("«category» topilmadi")
            return category
        if api_name == "status":
            return value.upper()
        if not value and nullable:
            return None
        return value

    @staticmethod
    def _clean_price(data: dict[str, Any], cleaned: dict[str, Any]) -> None:
        if "price" not in data:
            return

        value = data["price"]
        if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
            raise ValidationError("«price» musbat son bo'lishi kerak")
        try:
            price = Decimal(value)
        except (InvalidOperation, ValueError):
            raise ValidationError("«price» musbat son bo'lishi kerak") from None
        if not price.is_finite() or price <= 0:
            raise ValidationError("«price» musbat va chekli son bo'lishi kerak")

        price_field = Product._meta.get_field("price")
        cleaned["price"] = price_field.clean(price, None)

    def _clean_list_fields(
        self,
        data: dict[str, Any],
        cleaned: dict[str, Any],
    ) -> None:
        for name in self._LIST_FIELDS:
            if name not in data:
                continue
            value = data[name]
            if not isinstance(value, list) or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                raise ValidationError(
                    f"«{name}» bo'sh bo'lmagan matnlar ro'yxati bo'lishi kerak"
                )
            cleaned[name] = [item.strip() for item in value]


class ProductApplicationService:
    """Mahsulot API use-case'larini egalik va moderatsiya qoidalari bilan bajaradi."""

    _MUTABLE_STATUSES = {Product.Status.ACTIVE, Product.Status.PAUSED}

    def __init__(self, validator: ProductPayloadValidator | None = None) -> None:
        self._validator = validator or ProductPayloadValidator()

    def list_products(
        self,
        *,
        seller: User,
        status: str | None,
    ) -> ProductListResult:
        products = (
            Product.objects.filter(seller=seller, is_deleted=False)
            .select_related("category")
            .order_by("-created_at")
        )
        if status:
            products = products.filter(status=status.upper())
        return ProductListResult(total=products.count(), items=list(products[:200]))

    def retrieve_product(self, *, seller: User, product_id: UUID) -> Product:
        product = self._owned_product(seller=seller, product_id=product_id)
        if product is None:
            raise ProductApplicationError("Mahsulot topilmadi", 404)
        return product

    def create_product(self, *, seller: User, data: dict[str, Any]) -> Product:
        values = self._validated_values(data, creating=True)
        values.pop("status", None)
        product = Product(
            **values,
            telegram_username=seller.telegram_username,
            seller=seller,
            status=Product.Status.DRAFT,
        )
        product.slug = self._next_slug(product.title)
        product.save()
        return product

    @transaction.atomic
    def update_product(
        self,
        *,
        seller: User,
        product_id: UUID,
        data: dict[str, Any],
    ) -> ProductUpdateResult:
        product = self._locked_owned_product(seller=seller, product_id=product_id)
        values = self._validated_values(data)
        self._validate_status_transition(product=product, data=data, values=values)
        if not values:
            raise ProductApplicationError("O'zgartirish uchun maydon berilmadi")

        for field, value in values.items():
            setattr(product, field, value)
        changed_fields = tuple(values)
        product.save()
        return ProductUpdateResult(product, changed_fields)

    @transaction.atomic
    def archive_product(self, *, seller: User, product_id: UUID) -> None:
        product = self._locked_owned_product(seller=seller, product_id=product_id)
        # Arxivlash hech qachon tarixiy buyurtma yoki kechikib keladigan
        # to'lov callbackini yetim qoldirmaydi. Mahsulot faqat vitrinadan
        # olinadi; uning qatori va xaridor huquqlari saqlanadi.
        product.is_deleted = True
        product.status = Product.Status.PAUSED
        product.save(update_fields=["is_deleted", "status", "updated_at"])

    def _validated_values(
        self,
        data: dict[str, Any],
        *,
        creating: bool = False,
    ) -> dict[str, Any]:
        try:
            return self._validator.validate(data, creating=creating)
        except ValidationError as exc:
            raise ProductApplicationError("; ".join(exc.messages)) from exc

    def _validate_status_transition(
        self,
        *,
        product: Product,
        data: dict[str, Any],
        values: dict[str, Any],
    ) -> None:
        if "status" not in data:
            return
        wanted = values["status"]
        if wanted not in self._MUTABLE_STATUSES:
            raise ProductApplicationError(
                "«status» faqat ACTIVE yoki PAUSED bo'lishi mumkin"
            )
        if product.status not in self._MUTABLE_STATUSES:
            raise ProductApplicationError(
                "Bu mahsulot hali moderatsiyadan o'tmagan",
                409,
            )

    @staticmethod
    def _owned_product(*, seller: User, product_id: UUID) -> Product | None:
        return (
            Product.objects.filter(
                id=product_id,
                seller=seller,
                is_deleted=False,
            )
            .select_related("category")
            .first()
        )

    @staticmethod
    def _locked_owned_product(*, seller: User, product_id: UUID) -> Product:
        product = (
            Product.objects.select_for_update()
            .filter(id=product_id, seller=seller, is_deleted=False)
            .first()
        )
        if product is None:
            raise ProductApplicationError("Mahsulot topilmadi", 404)
        return product

    @staticmethod
    def _next_slug(title: str) -> str:
        base_slug = slugify(title) or "product"
        candidate = base_slug
        suffix = 1
        while Product.objects.filter(slug=candidate).exists():
            tail = f"-{suffix}"
            candidate = f"{base_slug[: 255 - len(tail)]}{tail}"
            suffix += 1
        return candidate
