from django.contrib import admin
from django.utils.html import format_html

from .models import Amenity, Hotel, Room, RoomImage, RoomType


class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 0
    fields = ("name", "capacity", "base_price", "is_active")


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "star_rating", "is_active")
    list_filter = ("city", "is_active", "star_rating")
    search_fields = ("name", "city", "address")
    inlines = [RoomTypeInline]


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "icon")
    search_fields = ("name",)


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1
    fields = ("room_number", "floor", "status", "is_active")


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "hotel", "capacity", "base_price", "is_active", "rooms_count", "image_preview")
    list_filter = ("hotel", "is_active")
    search_fields = ("name", "hotel__name")
    filter_horizontal = ("amenities",)
    inlines = [RoomImageInline, RoomInline]
    prepopulated_fields = {}

    @admin.display(description="Rasm")
    def image_preview(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', obj.main_image.url)
        return "-"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_number", "room_type", "floor", "status", "is_active")
    list_filter = ("status", "room_type__hotel", "floor")
    list_editable = ("status",)
    search_fields = ("room_number",)
