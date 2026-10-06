from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Booking

_STATUS_CACHE_ATTR = "_previous_status"


@receiver(pre_save, sender=Booking)
def cache_previous_status(sender, instance: Booking, **kwargs):
    if instance.pk:
        previous = Booking.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
        setattr(instance, _STATUS_CACHE_ATTR, previous)
    else:
        setattr(instance, _STATUS_CACHE_ATTR, None)


@receiver(post_save, sender=Booking)
def notify_on_booking_change(sender, instance: Booking, created, **kwargs):
    from apps.notifications.tasks import notify_booking_status_change, notify_new_booking_to_staff

    if created:
        notify_new_booking_to_staff.delay(instance.id)
        return

    previous_status = getattr(instance, _STATUS_CACHE_ATTR, None)
    if previous_status is not None and previous_status != instance.status:
        notify_booking_status_change.delay(instance.id)
