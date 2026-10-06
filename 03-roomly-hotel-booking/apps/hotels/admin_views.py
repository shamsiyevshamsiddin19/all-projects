import calendar
from datetime import date, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from apps.bookings.models import Booking, BookingStatus
from apps.payments.models import PaymentState, PaymentStatus

from .models import Room, RoomType


@staff_member_required
def dashboard_view(request):
    today = timezone.localdate()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    stats = {
        "today_bookings": Booking.objects.filter(created_at__date=today).count(),
        "pending_bookings": Booking.objects.filter(status=BookingStatus.PENDING).count(),
        "week_bookings": Booking.objects.filter(created_at__date__gte=week_ago).count(),
        "month_bookings": Booking.objects.filter(created_at__date__gte=month_ago).count(),
        "total_paid": PaymentStatus.objects.filter(status=PaymentState.PAID).aggregate(total=Sum("amount"))["total"]
        or 0,
        "pending_payments": PaymentStatus.objects.filter(status=PaymentState.PENDING).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0,
        "new_users_week": Booking.objects.filter(created_at__date__gte=week_ago).values("user").distinct().count(),
    }

    total_rooms = Room.objects.filter(is_active=True).count()
    occupied = Booking.objects.filter(
        status__in=[BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN],
        check_in_date__lte=today,
        check_out_date__gt=today,
    ).count()
    stats["occupancy_percent"] = round((occupied / total_rooms) * 100, 1) if total_rooms else 0

    top_room_types = (
        Booking.objects.values("room_type__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    return render(
        request,
        "admin/dashboard.html",
        {"stats": stats, "top_room_types": top_room_types, **admin_context(request)},
    )


@staff_member_required
def booking_calendar_view(request):
    today = timezone.localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    days_in_month = calendar.monthrange(year, month)[1]
    days = [date(year, month, d) for d in range(1, days_in_month + 1)]

    rooms = Room.objects.select_related("room_type").filter(is_active=True).order_by("room_type__name", "room_number")
    bookings = Booking.objects.filter(
        status__in=[BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN],
        check_in_date__lte=days[-1],
        check_out_date__gte=days[0],
    ).select_related("room")

    booked_cells = set()
    for booking in bookings:
        if booking.room_id is None:
            continue
        d = max(booking.check_in_date, days[0])
        last = min(booking.check_out_date - timedelta(days=1), days[-1])
        while d <= last:
            booked_cells.add((booking.room_id, d))
            d += timedelta(days=1)

    matrix = []
    for room in rooms:
        row = {"room": room, "cells": [(day, (room.id, day) in booked_cells) for day in days]}
        matrix.append(row)

    return render(
        request,
        "admin/booking_calendar.html",
        {"days": days, "matrix": matrix, "year": year, "month": month, **admin_context(request)},
    )


def admin_context(request):
    from django.contrib import admin

    return admin.site.each_context(request)
