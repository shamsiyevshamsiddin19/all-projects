from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.hotels.models import Amenity, Hotel, Room, RoomType
from apps.notifications.models import PromoCode

AMENITIES = [
    ("Wi-Fi", "📶"),
    ("Konditsioner", "❄️"),
    ("Minibar", "🥤"),
    ("TV", "📺"),
    ("Seyf", "🔒"),
    ("Fen", "💨"),
    ("Dush kabinasi", "🚿"),
    ("Balkon", "🏞"),
    ("Ish stoli", "🖥"),
    ("Bepul nonushta", "🍳"),
]

ROOM_TYPES = [
    {
        "name": "Standard",
        "description": "Qulay va ixcham xona — qisqa muddatli safarlar uchun ideal.",
        "capacity": 2,
        "bed_count": 1,
        "area_sqm": "18.00",
        "base_price": "350000",
        "amenities": ["Wi-Fi", "Konditsioner", "TV", "Dush kabinasi"],
        "rooms_count": 10,
    },
    {
        "name": "Comfort",
        "description": "Standartdan kengroq, qo'shimcha qulayliklar bilan jihozlangan xona.",
        "capacity": 2,
        "bed_count": 1,
        "area_sqm": "22.00",
        "base_price": "480000",
        "amenities": ["Wi-Fi", "Konditsioner", "TV", "Minibar", "Dush kabinasi", "Fen"],
        "rooms_count": 8,
    },
    {
        "name": "Deluxe",
        "description": "Katta, yorug' xona — biznes safarlar va oilaviy dam olish uchun mos.",
        "capacity": 3,
        "bed_count": 2,
        "area_sqm": "28.00",
        "base_price": "650000",
        "amenities": ["Wi-Fi", "Konditsioner", "TV", "Minibar", "Seyf", "Ish stoli", "Dush kabinasi", "Fen"],
        "rooms_count": 6,
    },
    {
        "name": "Lyuks (Suite)",
        "description": "Alohida yotoq va mehmon xonasidan iborat premium apartament.",
        "capacity": 4,
        "bed_count": 2,
        "area_sqm": "40.00",
        "base_price": "950000",
        "amenities": [
            "Wi-Fi",
            "Konditsioner",
            "TV",
            "Minibar",
            "Seyf",
            "Ish stoli",
            "Balkon",
            "Dush kabinasi",
            "Fen",
            "Bepul nonushta",
        ],
        "rooms_count": 4,
    },
    {
        "name": "Family",
        "description": "Oilalar uchun keng xona, bolalar bilan qulay yashash imkoniyati.",
        "capacity": 5,
        "bed_count": 3,
        "area_sqm": "45.00",
        "base_price": "1100000",
        "amenities": ["Wi-Fi", "Konditsioner", "TV", "Minibar", "Balkon", "Dush kabinasi", "Bepul nonushta"],
        "rooms_count": 2,
    },
]


class Command(BaseCommand):
    help = "Mehmonxona uchun soxta (demo) ma'lumotlar bilan to'ldiradi: 30 xona, bir nechta tarif, qulayliklar, promo kod"

    def handle(self, *args, **options):
        hotel, created = Hotel.objects.get_or_create(
            name="Grand Tashkent Hotel",
            defaults=dict(
                address="Amir Temur ko'chasi 45, Toshkent",
                city="Toshkent",
                description=(
                    "Toshkent markazida joylashgan zamonaviy mehmonxona. "
                    "Biznes safarlar va oilaviy dam olish uchun qulay xonalar, "
                    "24/7 xizmat ko'rsatish va bepul Wi-Fi."
                ),
                phone_number="+998712001122",
                check_in_time=time(14, 0),
                check_out_time=time(12, 0),
                star_rating=4,
                is_active=True,
            ),
        )
        self.stdout.write(self.style.SUCCESS(f"Hotel: {hotel.name} ({'yaratildi' if created else 'mavjud edi'})"))

        amenity_objs = {}
        for name, icon in AMENITIES:
            amenity, _ = Amenity.objects.get_or_create(name=name, defaults={"icon": icon})
            amenity_objs[name] = amenity
        self.stdout.write(self.style.SUCCESS(f"Qulayliklar: {len(amenity_objs)} ta tayyor"))

        total_rooms = 0
        floor = 1
        room_seq_on_floor = 1

        for rt_data in ROOM_TYPES:
            room_type, rt_created = RoomType.objects.get_or_create(
                hotel=hotel,
                name=rt_data["name"],
                defaults=dict(
                    description=rt_data["description"],
                    capacity=rt_data["capacity"],
                    bed_count=rt_data["bed_count"],
                    area_sqm=rt_data["area_sqm"],
                    base_price=rt_data["base_price"],
                    currency="UZS",
                    is_active=True,
                ),
            )
            room_type.amenities.set([amenity_objs[a] for a in rt_data["amenities"]])
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Tarif: {room_type.name} — {room_type.base_price} UZS/kecha "
                    f"({'yaratildi' if rt_created else 'yangilandi'})"
                )
            )

            for _ in range(rt_data["rooms_count"]):
                if room_seq_on_floor > 20:
                    floor += 1
                    room_seq_on_floor = 1
                room_number = f"{floor}{room_seq_on_floor:02d}"
                Room.objects.get_or_create(
                    room_type=room_type,
                    room_number=room_number,
                    defaults={"floor": floor, "status": "AVAILABLE", "is_active": True},
                )
                room_seq_on_floor += 1
                total_rooms += 1

        self.stdout.write(self.style.SUCCESS(f"Jami xonalar: {total_rooms} ta ({len(ROOM_TYPES)} ta tarifda)"))

        now = timezone.now()
        promo, promo_created = PromoCode.objects.get_or_create(
            code="WELCOME10",
            defaults=dict(
                discount_percent=10,
                valid_from=now,
                valid_to=now + timedelta(days=90),
                max_uses=100,
                is_active=True,
            ),
        )
        self.stdout.write(
            self.style.SUCCESS(f"Promo kod: {promo.code} (-{promo.discount_percent}%) — {'yaratildi' if promo_created else 'mavjud edi'}")
        )

        self.stdout.write(self.style.SUCCESS("Demo ma'lumotlar muvaffaqiyatli to'ldirildi."))
