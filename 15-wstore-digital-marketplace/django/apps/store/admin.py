from django.contrib import admin
from .models import Category, Product, Review, Wishlist, Report

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "products_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = "Mahsulotlar soni"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price_display", "status", "sales_count", "rating", "seller", "created_at")
    list_filter = ("status", "category", "subcategory", "created_at")
    search_fields = ("title", "description", "slug", "seller__username", "seller__email")
    prepopulated_fields = {"slug": ("title",)}
    actions = ["make_active", "make_rejected", "make_paused"]

    def price_display(self, obj):
        return f"${obj.price} ({obj.price_som:,} so'm)".replace(",", " ")
    price_display.short_description = "Narx"

    @admin.action(description="Tanlangan mahsulotlarni tasdiqlash (ACTIVE)")
    def make_active(self, request, queryset):
        count = queryset.update(status=Product.Status.ACTIVE)
        self.message_user(request, f"{count} ta mahsulot muvaffaqiyatli faollashtirildi (ACTIVE).")

    @admin.action(description="Tanlangan mahsulotlarni rad etish (REJECTED)")
    def make_rejected(self, request, queryset):
        count = queryset.update(status=Product.Status.REJECTED)
        self.message_user(request, f"{count} ta mahsulot rad etildi (REJECTED).")

    @admin.action(description="Tanlangan mahsulotlarni to'xtatish (PAUSED)")
    def make_paused(self, request, queryset):
        count = queryset.update(status=Product.Status.PAUSED)
        self.message_user(request, f"{count} ta mahsulot to'xtatildi (PAUSED).")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at", "comment_short")
    list_filter = ("rating", "created_at")
    search_fields = ("product__title", "user__username", "comment")

    def comment_short(self, obj):
        return obj.comment[:60]
    comment_short.short_description = "Sharh"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    search_fields = ("user__username", "product__title")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("product", "reporter", "reason", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("product__title", "reporter__username", "reason", "comment")
    actions = ["mark_resolved"]

    @admin.action(description="Tanlangan shikoyatlarni hal qilingan deb belgilash")
    def mark_resolved(self, request, queryset):
        count = queryset.update(status=Report.ReportStatus.RESOLVED)
        self.message_user(request, f"{count} ta shikoyat hal qilindi deb belgilandi.")
