"""Copy name/avatar from the OAuth provider onto our own user record."""
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_updated
from django.dispatch import receiver


def _apply_profile(user, sociallogin):
    if sociallogin is None:
        return
    data = sociallogin.account.extra_data or {}
    name = data.get("name") or data.get("login") or ""
    picture = data.get("picture") or data.get("avatar_url") or ""
    changed = []
    if name and not user.full_name:
        user.full_name = name[:150]
        changed.append("full_name")
    if picture and not user.avatar_url:
        user.avatar_url = picture
        changed.append("avatar_url")
    if changed:
        user.save(update_fields=changed)


@receiver(user_signed_up)
def on_signed_up(request, user, sociallogin=None, **kwargs):
    _apply_profile(user, sociallogin)


@receiver(social_account_updated)
def on_social_updated(request, sociallogin, **kwargs):
    _apply_profile(sociallogin.user, sociallogin)
