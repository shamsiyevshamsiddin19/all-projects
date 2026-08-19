from django.db import models
from django.utils.text import slugify


class Hotel(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20)
    check_in_time = models.TimeField(default="14:00")
    check_out_time = models.TimeField(default="12:00")
    star_rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True
    )
    logo = models.ImageField(upload_to="hotel_logos/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mehmonxona"
        verbose_name_plural = "Mehmonxonalar"

    def __str__(self):
        return self.name


class Amenity(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Qulaylik"
        verbose_name_plural = "Qulayliklar"

    def __str__(self):
        return self.name


class RoomType(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="room_types")
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=140, blank=True)
    description = models.TextField(blank=True)
    capacity = models.PositiveSmallIntegerField()
    bed_count = models.PositiveSmallIntegerField(default=1)
    area_sqm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="UZS")
    amenities = models.ManyToManyField(Amenity, blank=True)
    main_image = models.ImageField(upload_to="room_images/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Xona turi"
        verbose_name_plural = "Xona turlari"

    def __str__(self):
        return f"{self.name} ({self.hotel.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.hotel_id}-{self.name}") or "room-type"
            slug = base_slug
            i = 1
            while RoomType.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def rooms_count(self):
        return self.rooms.filter(is_active=True).count()


class RoomImage(models.Model):
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="room_images/gallery/")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "Xona rasmi"
        verbose_name_plural = "Xona rasmlari"


class RoomStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Bo'sh"
    OCCUPIED = "OCCUPIED", "Band"
    MAINTENANCE = "MAINTENANCE", "Ta'mirlashda"
    CLEANING = "CLEANING", "Tozalanmoqda"


class Room(models.Model):
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=10)
    floor = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=RoomStatus.choices, default=RoomStatus.AVAILABLE)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Xona"
        verbose_name_plural = "Xonalar"
        constraints = [
            models.UniqueConstraint(fields=["room_type", "room_number"], name="unique_room_number_per_type"),
        ]

    def __str__(self):
        return f"{self.room_number} ({self.room_type.name})"

    def clean(self):
        from django.core.exceptions import ValidationError

        conflict = (
            Room.objects.filter(room_type__hotel_id=self.room_type.hotel_id, room_number=self.room_number)
            .exclude(pk=self.pk)
            .exists()
        )
        if conflict:
            raise ValidationError({"room_number": "Bu xona raqami shu mehmonxonada band."})
