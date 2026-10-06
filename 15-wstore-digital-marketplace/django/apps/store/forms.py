from django import forms
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
                "step": "1",
                "min": "1",
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
        if self.instance and self.instance.pk:
            self.fields["tech_stack_selection"].initial = self.instance.tech_stack or []
            if self.instance.features:
                self.fields["features_raw"].initial = "\n".join(self.instance.features)
            if self.instance.screenshots:
                self.fields["screenshots_raw"].initial = "\n".join(self.instance.screenshots)

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
