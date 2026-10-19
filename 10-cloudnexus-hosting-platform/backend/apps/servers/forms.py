import re

from django import forms

from .models import Server
from .validators import validate_slug


def suggest_slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    base = re.sub(r"-{2,}", "-", base)
    return base[:63].rstrip("-")


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = ("name", "slug")
        labels = {"name": "Server nomi", "slug": "Subdomen"}
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Mening AI saytim",
                "autofocus": "autofocus",
                "autocomplete": "off",
            }),
            "slug": forms.TextInput(attrs={
                "placeholder": "aisayt",
                "autocapitalize": "none",
                "autocomplete": "off",
                "spellcheck": "false",
            }),
        }

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip().lower()
        validate_slug(slug)
        if Server.objects.filter(slug=slug).exists():
            raise forms.ValidationError("Bu subdomen allaqachon band.")
        return slug

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if len(name) < 2:
            raise forms.ValidationError("Nom kamida 2 ta belgidan iborat bo'lsin.")
        return name
