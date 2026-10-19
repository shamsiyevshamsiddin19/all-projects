from django.conf import settings


def platform(request):
    return {"PLATFORM_DOMAIN": settings.PLATFORM_DOMAIN}
