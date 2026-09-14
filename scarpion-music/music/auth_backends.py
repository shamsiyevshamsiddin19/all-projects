"""
E-pochta bilan ham kirish imkonini beruvchi tekshiruvchi (backend).

Muammo:
    Django sukut bo'yicha FAQAT foydalanuvchi nomi (username) bilan
    kirishga ruxsat beradi. Bizning kirish sahifamizda esa "E-pochta"
    deb yozilgan — odam o'sha yerga pochtasini yozadi va kira olmaydi.

Yechim:
    Shu backend avval foydalanuvchi nomi, topilmasa e-pochta bo'yicha
    qidiradi. settings.py dagi AUTHENTICATION_BACKENDS ro'yxatida
    Django'ning o'zinikidan OLDIN turadi.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # iexact = katta-kichik harf farqi hisobga olinmaydi.
        # Bir nechta foydalanuvchi bir xil pochta bilan ro'yxatdan
        # o'tgan bo'lsa (Django buni taqiqlamaydi) — .first() bilan
        # birinchisini olamiz, MultipleObjectsReturned chiqmasin.
        foydalanuvchi = User.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=username)
        ).order_by('id').first()

        if foydalanuvchi is None:
            # Foydalanuvchi topilmasa ham parolni "tekshirgandek" qilamiz.
            # Busiz javob vaqti farq qilib, qaysi pochta ro'yxatda
            # borligini tashqaridan bilib olish mumkin bo'lardi.
            User().set_password(password)
            return None

        if foydalanuvchi.check_password(password) and self.user_can_authenticate(foydalanuvchi):
            return foydalanuvchi

        return None
