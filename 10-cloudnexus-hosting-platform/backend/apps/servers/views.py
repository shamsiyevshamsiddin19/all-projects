from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ServerForm, suggest_slug
from .models import Server, SshKey
from .services import generate_keypair
from .validators import validate_slug

# Private keys live in the session only, keyed by server slug, until the
# user downloads them or the session ends. They never reach the database.
SESSION_KEY = "pending_private_keys"


def _stash_private_key(request, slug: str, private_key: str) -> None:
    pending = request.session.get(SESSION_KEY, {})
    pending[slug] = private_key
    request.session[SESSION_KEY] = pending
    request.session.modified = True


def _pop_private_key(request, slug: str):
    pending = request.session.get(SESSION_KEY, {})
    key = pending.pop(slug, None)
    request.session[SESSION_KEY] = pending
    request.session.modified = True
    return key


def _peek_private_key(request, slug: str):
    return request.session.get(SESSION_KEY, {}).get(slug)


def landing(request):
    if request.user.is_authenticated:
        return redirect("servers:dashboard")
    return render(request, "landing.html")


@login_required
def dashboard(request):
    servers = Server.objects.alive().filter(owner=request.user)
    return render(request, "servers/dashboard.html", {
        "servers": servers,
        "can_create": request.user.can_create_server(),
        "used": servers.count(),
        "limit": request.user.server_limit,
    })


@login_required
def create(request):
    if not request.user.can_create_server():
        messages.error(
            request,
            f"Tarifingizda {request.user.server_limit} ta serverga ruxsat berilgan.",
        )
        return redirect("servers:dashboard")

    if request.method == "POST":
        form = ServerForm(request.POST)
        if form.is_valid():
            server = form.save(commit=False)
            server.owner = request.user
            server.status = Server.Status.READY
            server.save()

            generated = generate_keypair(comment=f"{request.user.email} ({server.domain})")
            SshKey.objects.create(
                server=server,
                public_key=generated.public_key,
                fingerprint=generated.fingerprint,
            )
            _stash_private_key(request, server.slug, generated.private_key)
            return redirect("servers:key_ready", slug=server.slug)
    else:
        form = ServerForm()

    return render(request, "servers/create.html", {"form": form})


@login_required
def key_ready(request, slug):
    """Shown once after a key is generated — the only chance to save it."""
    server = get_object_or_404(Server.objects.alive(), slug=slug, owner=request.user)
    private_key = _peek_private_key(request, slug)
    if not private_key:
        messages.warning(
            request,
            "Maxfiy kalit allaqachon yuklab olingan yoki sessiya tugagan. "
            "Kerak bo'lsa yangi kalit yarating.",
        )
        return redirect(server.get_absolute_url())
    return render(request, "servers/key_ready.html", {
        "server": server,
        "private_key": private_key,
        "key": server.active_key,
    })


@login_required
def key_download(request, slug):
    server = get_object_or_404(Server.objects.alive(), slug=slug, owner=request.user)
    private_key = _pop_private_key(request, slug)
    if not private_key:
        messages.error(request, "Maxfiy kalit endi mavjud emas — yangisini yarating.")
        return redirect(server.get_absolute_url())

    key = server.active_key
    if key and not key.downloaded_at:
        key.downloaded_at = timezone.now()
        key.save(update_fields=["downloaded_at"])

    response = HttpResponse(private_key, content_type="application/x-pem-file")
    response["Content-Disposition"] = f'attachment; filename="{server.slug}_ed25519"'
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
def detail(request, slug):
    server = get_object_or_404(Server.objects.alive(), slug=slug, owner=request.user)
    return render(request, "servers/detail.html", {
        "server": server,
        "key": server.active_key,
        "has_pending_key": bool(_peek_private_key(request, slug)),
    })


@login_required
@require_POST
def regenerate_key(request, slug):
    server = get_object_or_404(Server.objects.alive(), slug=slug, owner=request.user)
    server.ssh_keys.filter(is_revoked=False).update(is_revoked=True)

    generated = generate_keypair(comment=f"{request.user.email} ({server.domain})")
    SshKey.objects.create(
        server=server,
        public_key=generated.public_key,
        fingerprint=generated.fingerprint,
    )
    _stash_private_key(request, server.slug, generated.private_key)
    messages.success(request, "Yangi kalit yaratildi. Eski kalit bekor qilindi.")
    return redirect("servers:key_ready", slug=server.slug)


@login_required
@require_POST
def delete(request, slug):
    server = get_object_or_404(Server.objects.alive(), slug=slug, owner=request.user)
    if request.POST.get("confirm") != server.slug:
        messages.error(request, "Tasdiqlash uchun subdomen nomini to'g'ri kiriting.")
        return redirect(server.get_absolute_url())
    server.is_deleted = True
    server.save(update_fields=["is_deleted"])
    server.ssh_keys.update(is_revoked=True)
    _pop_private_key(request, slug)
    messages.success(request, f"«{server.name}» o'chirildi.")
    return redirect("servers:dashboard")


@login_required
def check_slug(request):
    """Live availability check for the create form (HTMX/fetch)."""
    raw = (request.GET.get("slug") or "").strip().lower()
    if not raw and request.GET.get("name"):
        raw = suggest_slug(request.GET["name"])

    if not raw:
        return JsonResponse({"ok": False, "slug": "", "message": ""})

    try:
        validate_slug(raw)
    except ValidationError as exc:
        return JsonResponse({"ok": False, "slug": raw, "message": exc.messages[0]})

    if Server.objects.filter(slug=raw).exists():
        return JsonResponse({"ok": False, "slug": raw, "message": "Bu subdomen band."})

    return JsonResponse({
        "ok": True,
        "slug": raw,
        "domain": f"{raw}.{settings.PLATFORM_DOMAIN}",
        "message": "Bo'sh — olish mumkin",
    })
