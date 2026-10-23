from django import forms
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _
from .models import Product, Review, Report, Category

TECH_CHOICES = [
    "React", "Next.js", "TypeScript", "Node.js", "PHP", "Python",
    "TailwindCSS", "Telegram", "Vue", "Flutter", "Laravel", "Django",
    "PostgreSQL", "MongoDB", "Docker", "Firebase", "React Native",
    "FastAPI", "AI / OpenAI", "GraphQL", "Redis", "NestJS", "Supabase",
    "Nuxt", "Svelte", "Angular", "Kotlin", "Swift", "Go", "Rust"
]

SUBCAT_CHOICES = [
    ("", _("-- Barchasi / Tanlanmagan --")),
    ("portfolio", _("Portfolio saytlar")),
    ("teacher", _("O'qituvchilar / Kurslar")),
    ("edu", _("Ta'lim / Maktab / Universitet")),
    ("pharmacy", _("Dorixona / Meditsina")),
    ("restaurant", _("Restoran / Kafe")),
    ("other", _("Boshqa")),
]


def _validate_upload_size(upload, limit):
    # Saqlangan faylni tahrirlash paytida qayta ochmaymiz; yangi yuklamani tekshiramiz.
    if isinstance(upload, UploadedFile) and upload.size > limit:
        raise forms.ValidationError(
            _("Fayl hajmi %(limit)s baytdan oshmasligi kerak."),
            params={"limit": limit},
        )
    return upload


class ProductForm(forms.ModelForm):
    tech_stack_selection = forms.MultipleChoiceField(
        choices=[(t, t) for t in TECH_CHOICES],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "tech-checkbox"}),
        label=_("Ishlatilgan texnologiyalar")
    )
    features_raw = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Har bir xususiyatni yangi qatordan yozing:\n- Oson o'rnatish\n- To'liq manba kodi\n- 24/7 qo'llab-quvvatlash"
        }),
        required=False,
        label=_("Asosiy xususiyatlar (har qatorda bittadan)")
    )
    screenshots_raw = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": "Skrinshot rasmlari havolalarini (URL) har qatordan bittadan yozing"
        }),
        required=False,
        label=_("Skrinshotlar (URL havolalar)")
    )

    class Meta:
        model = Product
        fields = [
            "title", "category", "subcategory", "price", "description",
            "cover_image_file", "cover_image_url", "file_archive",
            "demo_url", "telegram_username"
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Masalan: Telegram Do'kon Boti (Aiogram 3)",
            }),
            "category": forms.Select(attrs={
                "class": "form-control",
            }),
            "subcategory": forms.Select(choices=SUBCAT_CHOICES, attrs={
                "class": "form-control",
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "29.00",
                "step": "0.01",
                "min": "0.01",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Loyiha haqida batafsil ma'lumot, o'rnatish yo'riqnomasi va talablar...",
            }),
            "cover_image_file": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
            "cover_image_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://images.unsplash.com/...",
            }),
            "file_archive": forms.FileInput(attrs={
                "class": "form-control",
                "accept": ".zip,.tar.gz,.rar",
            }),
            "demo_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://demo.example.com",
            }),
            "telegram_username": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "developer_ali (belgisiz)",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ModelChoiceField standart holatda Category.__str__() (ya'ni
        # bazadagi o'zbekcha `name`) ni ko'rsatadi. EN/RU rejimida ham
        # "Botlar", "Saytlar" kabi tarjimasiz nom chiqib qolardi — katalog
        # sahifasida buning oldi `category.display_name` bilan olingan edi,
        # lekin mahsulot qo'shish formasi bu yerdan chetda qolgan ekan.
        self.fields["category"].label_from_instance = lambda c: c.display_name
        for name in ("cover_image_url", "demo_url"):
            self.fields[name].validators.append(URLValidator(schemes=["http", "https"]))
        if self.instance and self.instance.pk:
            self.fields["tech_stack_selection"].initial = self.instance.tech_stack or []
            if self.instance.features:
                self.fields["features_raw"].initial = "\n".join(self.instance.features)
            if self.instance.screenshots:
                self.fields["screenshots_raw"].initial = "\n".join(self.instance.screenshots)

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError(_("Narx musbat son bo'lishi kerak."))
        return price

    def clean_screenshots_raw(self):
        value = self.cleaned_data.get("screenshots_raw", "")
        validate_url = URLValidator(schemes=["http", "https"])
        for line in value.splitlines():
            if line.strip():
                validate_url(line.strip())
        return value

    def clean_file_archive(self):
        upload = self.cleaned_data.get("file_archive")
        if isinstance(upload, UploadedFile):
            if not upload.name.lower().endswith((".zip", ".tar.gz", ".rar")):
                raise forms.ValidationError(_("Faqat ZIP, TAR.GZ yoki RAR arxivini yuklang."))
            _validate_upload_size(
                upload, getattr(settings, "PRODUCT_ARCHIVE_MAX_SIZE", 40 * 1024 * 1024)
            )
        return upload

    def clean_cover_image_file(self):
        return _validate_upload_size(
            self.cleaned_data.get("cover_image_file"),
            getattr(settings, "PRODUCT_IMAGE_MAX_SIZE", 10 * 1024 * 1024),
        )

    def save(self, commit=True):
        product = super().save(commit=False)
        product.tech_stack = self.cleaned_data.get("tech_stack_selection", [])
        
        feats = self.cleaned_data.get("features_raw", "").strip()
        product.features = [f.strip() for f in feats.splitlines() if f.strip()]
        
        screens = self.cleaned_data.get("screenshots_raw", "").strip()
        product.screenshots = [s.strip() for s in screens.splitlines() if s.strip()]

        if commit:
            product.save()
        return product


class ReviewForm(forms.ModelForm):
    def clean_rating(self):
        rating = self.cleaned_data["rating"]
        if not 1 <= rating <= 5:
            raise forms.ValidationError(_("Baho 1 dan 5 gacha bo'lishi kerak."))
        return rating

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(
                choices=[(5, "⭐⭐⭐⭐⭐ (5 - A'lo)"), (4, "⭐⭐⭐⭐ (4 - Yaxshi)"), (3, "⭐⭐⭐ (3 - Qoniqarli)"), (2, "⭐⭐ (2 - Past)"), (1, "⭐ (1 - Yomon)")],
                attrs={"class": "form-control"}
            ),
            "comment": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Mahsulot haqida fikringiz...",
                "required": True,
            }),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "comment"]
        widgets = {
            "reason": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Sabab (masalan: ishlamayapti, plagiat, zararli kod)",
                "required": True,
            }),
            "comment": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Batafsil izoh...",
            }),
        }
