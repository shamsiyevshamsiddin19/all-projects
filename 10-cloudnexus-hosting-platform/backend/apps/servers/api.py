"""REST API — this is what the future CLI and MCP server talk to."""
from django.conf import settings
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Server, SshKey
from .services import generate_keypair
from .validators import validate_slug


class SshKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = SshKey
        fields = ("fingerprint", "public_key", "is_revoked", "created_at")
        read_only_fields = fields


class ServerSerializer(serializers.ModelSerializer):
    domain = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True)
    ssh_remote = serializers.CharField(read_only=True)
    key = SshKeySerializer(source="active_key", read_only=True)

    class Meta:
        model = Server
        fields = (
            "name", "slug", "status", "domain", "url", "ssh_remote",
            "key", "created_at",
        )
        read_only_fields = ("status", "created_at")

    def validate_slug(self, value):
        value = (value or "").strip().lower()
        validate_slug(value)
        if Server.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Bu subdomen band.")
        return value


class ServerViewSet(viewsets.ModelViewSet):
    serializer_class = ServerSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        return Server.objects.alive().filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        if not request.user.can_create_server():
            return Response(
                {"detail": f"Tarif chegarasi: {request.user.server_limit} ta server."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        server = serializer.save(owner=request.user, status=Server.Status.READY)

        generated = generate_keypair(comment=f"{request.user.email} ({server.domain})")
        SshKey.objects.create(
            server=server,
            public_key=generated.public_key,
            fingerprint=generated.fingerprint,
        )
        data = self.get_serializer(server).data
        # Returned exactly once — never retrievable again.
        data["private_key"] = generated.private_key
        data["private_key_notice"] = (
            "Bu maxfiy kalit faqat shu javobda beriladi va saqlanmaydi. "
            "Yo'qotsangiz yangi kalit yarating."
        )
        return Response(data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        instance.ssh_keys.update(is_revoked=True)

    @action(detail=True, methods=["post"], url_path="keys/regenerate")
    def regenerate_key(self, request, slug=None):
        server = self.get_object()
        server.ssh_keys.filter(is_revoked=False).update(is_revoked=True)
        generated = generate_keypair(comment=f"{request.user.email} ({server.domain})")
        SshKey.objects.create(
            server=server,
            public_key=generated.public_key,
            fingerprint=generated.fingerprint,
        )
        return Response({
            "fingerprint": generated.fingerprint,
            "public_key": generated.public_key,
            "private_key": generated.private_key,
            "private_key_notice": "Faqat shu javobda beriladi, saqlanmaydi.",
        }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        "email": user.email,
        "name": user.display_name,
        "avatar_url": user.avatar_url,
        "plan": user.plan,
        "servers_used": user.servers.filter(is_deleted=False).count(),
        "server_limit": user.server_limit,
        "platform_domain": settings.PLATFORM_DOMAIN,
    })


@api_view(["GET"])
@permission_classes([])
def health(request):
    return Response({"status": "ok"})
