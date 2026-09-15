"""
Parol tekshiruvchilari — o'zbekcha xabarlar bilan.

NEGA KERAK?
    Django ning o'z tekshiruvchilari to'g'ri ishlaydi, lekin
    xabarlari inglizcha:

        "This password is too short. It must contain at least 8 characters."

    settings.py da LANGUAGE_CODE = 'uz' turgan bo'lsa ham o'zgarmaydi,
    chunki Django ning o'zbekcha tarjima to'plamida aynan shu qatorlar
    yo'q (boshqa ba'zi qatorlar tarjima qilingan).

YECHIM:
    Django tekshiruvchilaridan meros olamiz va faqat XABARNI
    almashtiramiz. Tekshirish mantig'i o'zgarmaydi — u sinovdan
    o'tgan va ishonchli.
"""

from django.contrib.auth import password_validation as tekshir
from django.core.exceptions import ValidationError


class UzunlikTekshiruvchi(tekshir.MinimumLengthValidator):
    """Parol juda qisqa emasligini tekshiradi."""

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                f"Parol juda qisqa — kamida {self.min_length} ta belgi bo'lishi kerak.",
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return f"Kamida {self.min_length} ta belgi."


class OddiyParolTekshiruvchi(tekshir.CommonPasswordValidator):
    """
    Parol keng tarqalgan parollar ro'yxatida yo'qligini tekshiradi
    (Django ichida 20 000 ga yaqin parol ro'yxati bor: "password",
    "12345678", "qwerty" va hokazo).
    """

    def validate(self, password, user=None):
        if password.lower().strip() in self.passwords:
            raise ValidationError(
                "Bu parol juda ko'p ishlatiladi — uni topish oson. "
                "Boshqasini o'ylab toping.",
                code='password_too_common',
            )

    def get_help_text(self):
        return "Keng tarqalgan parol bo'lmasin."


class RaqamliParolTekshiruvchi(tekshir.NumericPasswordValidator):
    """Parol faqat raqamlardan iborat emasligini tekshiradi."""

    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(
                "Parol faqat raqamlardan iborat bo'lmasin — "
                "kamida bitta harf qo'shing.",
                code='password_entirely_numeric',
            )

    def get_help_text(self):
        return "Faqat raqamdan iborat bo'lmasin."


class OxshashlikTekshiruvchi(tekshir.UserAttributeSimilarityValidator):
    """
    Parol foydalanuvchi nomi yoki e-pochtasiga o'xshamasligini
    tekshiradi. "shamsiddin" nomli odam "shamsiddin" parolini
    qo'yishi xavfli.
    """

    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            # Django ning xabari inglizcha — o'zimiznikiga almashtiramiz
            raise ValidationError(
                "Parol ism yoki e-pochtangizga juda o'xshash. "
                "Boshqacharoq parol tanlang.",
                code='password_too_similar',
            )

    def get_help_text(self):
        return "Ism yoki e-pochtangizga o'xshamasin."
