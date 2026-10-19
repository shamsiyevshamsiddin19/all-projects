from django.contrib import admin

from .models import Server, SshKey


class SshKeyInline(admin.TabularInline):
    model = SshKey
    extra = 0
    readonly_fields = ("fingerprint", "public_key", "downloaded_at", "created_at")
    can_delete = False


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "owner", "status", "is_deleted", "created_at")
    list_filter = ("status", "is_deleted", "created_at")
    search_fields = ("name", "slug", "owner__email")
    readonly_fields = ("created_at", "updated_at")
    inlines = [SshKeyInline]


@admin.register(SshKey)
class SshKeyAdmin(admin.ModelAdmin):
    list_display = ("server", "fingerprint", "is_revoked", "downloaded_at", "created_at")
    list_filter = ("is_revoked",)
    search_fields = ("fingerprint", "server__slug")
    readonly_fields = ("public_key", "fingerprint", "created_at", "downloaded_at")
