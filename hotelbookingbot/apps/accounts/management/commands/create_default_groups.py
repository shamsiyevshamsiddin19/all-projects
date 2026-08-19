from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db.models import Q

GROUP_PERMISSIONS = {
    "Operatorlar": [
        ("bookings", "booking", ["view_booking", "change_booking"]),
        ("bookings", "guest", ["view_guest"]),
    ],
    "Menejerlar": [
        ("bookings", "booking", ["view_booking", "change_booking"]),
        ("bookings", "guest", ["view_guest"]),
        ("hotels", "roomtype", ["add_roomtype", "change_roomtype", "view_roomtype"]),
        ("hotels", "room", ["add_room", "change_room", "view_room"]),
        ("payments", "paymentstatus", ["view_paymentstatus", "change_paymentstatus"]),
    ],
    "Administratorlar": [
        ("bookings", "booking", ["view_booking", "change_booking", "add_booking", "delete_booking"]),
        ("bookings", "guest", ["view_guest", "change_guest"]),
        ("hotels", "roomtype", ["add_roomtype", "change_roomtype", "view_roomtype", "delete_roomtype"]),
        ("hotels", "room", ["add_room", "change_room", "view_room", "delete_room"]),
        ("payments", "paymentstatus", ["view_paymentstatus", "change_paymentstatus"]),
        ("accounts", "telegramuser", ["view_telegramuser", "change_telegramuser"]),
    ],
}


class Command(BaseCommand):
    help = "Standart Django admin guruhlarini (Operatorlar, Menejerlar, Administratorlar, Superadmin) yaratadi"

    def handle(self, *args, **options):
        for group_name, perms in GROUP_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            permissions = Permission.objects.none()
            for app_label, model, codenames in perms:
                permissions |= Permission.objects.filter(
                    Q(content_type__app_label=app_label, content_type__model=model, codename__in=codenames)
                )
            group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(f"Guruh tayyor: {group_name} ({permissions.count()} ruxsat)"))

        Group.objects.get_or_create(name="Superadmin")
        self.stdout.write(self.style.SUCCESS("Superadmin guruhi mavjud (is_superuser=True foydalanuvchilar uchun)."))
