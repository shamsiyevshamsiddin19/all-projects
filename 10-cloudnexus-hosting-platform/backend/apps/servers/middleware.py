from django.conf import settings
from django.shortcuts import render

from .models import Server


class SubdomainPlaceholderMiddleware:
    """<slug>.PLATFORM_DOMAIN has no deploy pipeline yet, so every
    subdomain request lands here instead of a 404 or connection error."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        domain = settings.PLATFORM_DOMAIN
        host = request.get_host().split(":")[0]
        if host != domain and host != f"www.{domain}" and host.endswith(f".{domain}"):
            slug = host[: -(len(domain) + 1)]
            server = Server.objects.alive().filter(slug=slug).first()
            status = 200 if server else 404
            return render(
                request,
                "servers/subdomain_placeholder.html",
                {"slug": slug, "server": server},
                status=status,
            )
        return self.get_response(request)
