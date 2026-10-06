import factory

from apps.accounts.models import TelegramUser
from apps.hotels.models import Hotel, Room, RoomType


class TelegramUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TelegramUser

    telegram_id = factory.Sequence(lambda n: 1000 + n)
    first_name = "Test"
    last_name = "User"


class HotelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Hotel

    name = "Test Hotel"
    address = "Test address"
    city = "Tashkent"
    phone_number = "+998900000000"


class RoomTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RoomType

    hotel = factory.SubFactory(HotelFactory)
    name = factory.Sequence(lambda n: f"Standard {n}")
    capacity = 2
    base_price = 500000


class RoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Room

    room_type = factory.SubFactory(RoomTypeFactory)
    room_number = factory.Sequence(lambda n: str(100 + n))
