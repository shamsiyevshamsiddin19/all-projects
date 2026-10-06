from django import forms
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import Withdrawal

class WithdrawalForm(forms.ModelForm):
    class Meta:
        model = Withdrawal
        fields = ["amount", "card_number"]
        widgets = {
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "50 000",
                "step": "1000",
            }),
            "card_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "8600 0000 0000 0000",
                "maxlength": "20",
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user_balance = kwargs.pop("user_balance", 0)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        min_allowed = getattr(settings, "MIN_WITHDRAWAL_SOM", 50000)
        if amount < min_allowed:
            raise forms.ValidationError(f"Minimal yechib olish summasi: {min_allowed:,} so'm.".replace(",", " "))
        if amount > self.user_balance:
            raise forms.ValidationError("Balansingizda yetarli mablag' mavjud emas.")
        return amount

    def clean_card_number(self):
        card = self.cleaned_data.get("card_number", "").replace(" ", "").replace("-", "")
        if len(card) != 16 or not card.isdigit():
            raise forms.ValidationError("Karta raqami 16 ta raqamdan iborat bo'lishi kerak (Uzcard / Humo).")
        return card
