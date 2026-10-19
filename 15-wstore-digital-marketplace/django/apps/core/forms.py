from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class LoginForm(forms.Form):
    login = forms.CharField(
        label=_("Login yoki Email"),
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("Username yoki emailingiz"),
            "autocomplete": "username",
            "required": True,
        })
    )
    password = forms.CharField(
        label=_("Parol"),
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "••••••••",
            "autocomplete": "current-password",
            "required": True,
        })
    )


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label=_("Parol"),
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": _("Kamida 6 ta belgi"),
            "autocomplete": "new-password",
            "required": True,
        })
    )
    password_confirm = forms.CharField(
        label=_("Parolni tasdiqlang"),
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "••••••••",
            "autocomplete": "new-password",
            "required": True,
        })
    )

    class Meta:
        model = User
        fields = ["username", "email", "role"]
        widgets = {
            "username": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "devbek",
                "required": True,
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "misol@gmail.com",
                "required": True,
            }),
            "role": forms.Select(attrs={
                "class": "form-control",
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(_("Bu foydalanuvchi nomi band."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("Bu email manzil bilan allaqachon ro'yxatdan o'tilgan."))
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password_confirm")
        if p1 and p2 and p1 != p2:
            self.add_error("password_confirm", _("Kiritilgan parollar bir xil emas."))
        if p1 and len(p1) < 6:
            self.add_error("password", _("Parol kamida 6 ta belgidan iborat bo'lishi kerak."))
        return cleaned_data
