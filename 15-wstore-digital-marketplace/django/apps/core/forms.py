from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()

# Django'ning o'z parol validatorlari faqat ingliz/rus matniga ega — "uz"
# uchun tarjimasi yo'q. Kod bo'yicha o'zimizning (uchala tilga tarjima
# qilingan) xabarimizga almashtiramiz.
PASSWORD_ERROR_MESSAGES = {
    "password_too_short": _("Parol kamida 8 ta belgidan iborat bo'lishi kerak."),
    "password_too_common": _("Bu parol juda ko'p ishlatiladi — kamroq tarqalgan parol tanlang."),
    "password_entirely_numeric": _("Parol faqat raqamlardan iborat bo'lmasligi kerak."),
    "password_too_similar": _("Parol foydalanuvchi nomi yoki emailga juda o'xshab ketyapti."),
}


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
            "placeholder": _("Kamida 8 ta belgi"),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # "Admin" ro'yxatdan o'tish formasida TANLOV sifatida ko'rinmasin —
        # bu yerda faqat "maqsad" (xaridor/sotuvchi) so'raladi. Admin huquqi
        # (is_staff/is_superuser) faqat ADMIN_EMAILS orqali yoki Django
        # admin panelidan qo'lda beriladi, hech qachon o'z-o'zidan emas.
        self.fields["role"].choices = [
            c for c in self.fields["role"].choices if c[0] != User.Role.ADMIN
        ]

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

        if p1:
            # settings.AUTH_PASSWORD_VALIDATORS sozlangan edi (4 ta qoida —
            # minimal uzunlik, umumiy parollar, faqat raqam, username/email
            # bilan o'xshashlik), lekin hech qachon chaqirilmagan edi: shu
            # sabab "123456" kabi parol ham qabul qilinardi. Tekshirish uchun
            # hali saqlanmagan User instansi beriladi — shunda
            # UserAttributeSimilarityValidator username/email bilan
            # solishtira oladi.
            dummy_user = User(
                username=cleaned_data.get("username", ""),
                email=cleaned_data.get("email", ""),
            )
            try:
                validate_password(p1, user=dummy_user)
            except DjangoValidationError as exc:
                # Django'ning o'z xato matnlari faqat ingliz/rus tiliga
                # tarjima qilingan — "uz" uchun yo'q, shuning uchun o'zbek
                # rejimida ham inglizcha chiqib qolardi. Kod bo'yicha
                # o'zimizning (uch tilga tarjima qilingan) xabarimizni
                # ko'rsatamiz.
                for err in getattr(exc, "error_list", [exc]):
                    self.add_error("password", PASSWORD_ERROR_MESSAGES.get(
                        getattr(err, "code", None), err
                    ))

        return cleaned_data


class ProfileForm(forms.ModelForm):
    """Har qanday foydalanuvchi tahrirlay oladigan asosiy ma'lumotlar."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "telegram_username", "bio", "website"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Ismingiz")}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Familiyangiz")}),
            "telegram_username": forms.TextInput(attrs={"class": "form-control", "placeholder": "username"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3,
                                         "placeholder": _("O'zingiz va ishlaringiz haqida qisqacha")}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
        }

    def clean_telegram_username(self):
        # Foydalanuvchilar odatda «@» bilan yozadi — uni tashlab yuboramiz,
        # aks holda havola t.me/@nom bo'lib ochilmaydi.
        v = (self.cleaned_data.get("telegram_username") or "").strip().lstrip("@")
        return v or None


class SellerOnboardingForm(forms.ModelForm):
    """
    «Sotuvchi bo'lish» anketasi.

    Telegram va karta majburiy: biri xaridor bilan bog'lanish uchun,
    ikkinchisi sotuvdan tushgan pulni yechib olish uchun kerak.
    """

    agree = forms.BooleanField(
        required=True,
        label=_("Sotuvchi shartlariga roziman"),
        error_messages={"required": _("Davom etish uchun shartlarga rozilik bildiring.")},
    )

    class Meta:
        model = User
        fields = ["telegram_username", "card_number", "bio", "website"]
        widgets = {
            "telegram_username": forms.TextInput(attrs={"class": "form-control", "placeholder": "username"}),
            "card_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "8600 0000 0000 0000",
                                                  "maxlength": "25"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3,
                                         "placeholder": _("Qanday loyihalar yaratasiz?")}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://github.com/..."}),
        }

    def clean_telegram_username(self):
        v = (self.cleaned_data.get("telegram_username") or "").strip().lstrip("@")
        if not v:
            raise forms.ValidationError(_("Telegram username majburiy — xaridorlar siz bilan shu orqali bog'lanadi."))
        return v

    def clean_card_number(self):
        raw = (self.cleaned_data.get("card_number") or "")
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) != 16:
            raise forms.ValidationError(_("Karta raqami 16 ta raqamdan iborat bo'lishi kerak (Uzcard / Humo)."))
        return digits


class ApiTokenForm(forms.Form):
    """Yangi API kalit yaratish — faqat nomi so'raladi."""

    name = forms.CharField(
        max_length=80,
        label=_("Kalit nomi"),
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("Masalan: AI yuklovchi"),
        }),
    )
