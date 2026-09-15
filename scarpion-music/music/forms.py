from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator

from .models import Artist, Album, Song


# ModelForm = modelga asoslangan forma.
# Maydonlarni qo'lda yozmaymiz - Django ularni modeldan o'zi oladi
# va tekshiruvni (validatsiyani) ham o'zi qiladi.
class ArtistForm(forms.ModelForm):
    class Meta:
        model = Artist
        # Foydalanuvchi to'ldiradigan maydonlar.
        # slug bu yerda YO'Q - uni models.py dagi save() avtomatik yasaydi.
        # created_at ham yo'q - u auto_now_add bilan o'zi to'ladi.
        fields = ['name', 'bio', 'photo']
        # widgets = HTML elementining ko'rinishini o'zgartirish
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'name': 'Ijrochi nomi',
            'bio': 'Biografiya',
            'photo': 'Rasm',
        }


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['title', 'artist', 'release_date', 'cover', 'genres']
        widgets = {
            # type='date' -> brauzerning o'z kalendarchasi ochiladi
            'release_date': forms.DateInput(attrs={'type': 'date'}),
            # M2M uchun katakchalar ro'yxati (oddiy select'dan qulayroq)
            'genres': forms.CheckboxSelectMultiple(),
        }
        labels = {
            'title': 'Albom nomi',
            'artist': 'Ijrochi',
            'release_date': 'Chiqqan sanasi',
            'cover': 'Muqova',
            'genres': 'Janrlar',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Django sukut bo'yicha "---------" deb qo'yadi — o'zbekchaga almashtiramiz.
        self.fields['artist'].empty_label = 'Ijrochini tanlang'


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        # album bu yerda YO'Q - u URL manzilidan olinadi
        # (qaysi albom sahifasida turgan bo'lsak, o'shanga biriktiriladi).
        fields = ['track_number', 'title', 'duration_ms']
        labels = {
            'track_number': 'Trek raqami',
            'title': "Qo'shiq nomi",
            'duration_ms': 'Davomiyligi (millisekund)',
        }

    # __init__ = forma yaratilayotgan paytda ishlaydi.
    # View bizga albomni uzatadi, biz uni eslab qolamiz - pastdagi
    # clean_track_number() da kerak bo'ladi.
    def __init__(self, *args, album=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.album = album

    # clean_<maydon_nomi> = shu maydonni tekshiradigan metod.
    # Django uni forma yuborilganda avtomatik chaqiradi.
    def clean_track_number(self):
        number = self.cleaned_data['track_number']
        if self.album:
            qs = self.album.songs.filter(track_number=number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                # ValidationError ko'tarilsa, forma saqlanmaydi va
                # xato matni foydalanuvchiga ko'rsatiladi.
                raise forms.ValidationError(
                    f'Bu albomda {number}-trek allaqachon mavjud.'
                )
        return number


# ==========================================================
#  KIRISH VA RO'YXATDAN O'TISH
# ==========================================================
class KirishForm(AuthenticationForm):
    """
    Django'ning tayyor kirish formasi, faqat yozuvlari o'zbekcha
    va maydonlarga o'zimizning CSS klaslarimiz qo'yilgan.

    "username" maydoni e-pochtani ham qabul qiladi — buni
    auth_backends.py dagi EmailOrUsernameBackend hal qiladi.
    """

    username = forms.CharField(
        label='E-pochta yoki foydalanuvchi nomi',
        widget=forms.TextInput(attrs={
            'class': 'auth__input',
            'placeholder': 'pochtangiz@mail.com',
            'autofocus': True,
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        label='Parol',
        widget=forms.PasswordInput(attrs={
            'class': 'auth__input',
            'placeholder': 'Parolingizni kiriting',
            'autocomplete': 'current-password',
        }),
    )

    # Django'ning inglizcha xato matnlarini almashtiramiz
    error_messages = {
        'invalid_login': "E-pochta yoki parol noto'g'ri.",
        'inactive': 'Bu akkaunt faol emas.',
    }


class RoyxatForm(UserCreationForm):
    """
    Ro'yxatdan o'tish. UserCreationForm ustiga e-pochta maydoni
    qo'shilgan va uning takrorlanmasligi tekshiriladi.
    """

    email = forms.EmailField(
        label='E-pochta',
        widget=forms.EmailInput(attrs={
            'class': 'auth__input',
            'placeholder': 'pochtangiz@mail.com',
            'autocomplete': 'email',
        }),
    )

    class Meta:
        model = User
        fields = ('username', 'email')
        # Bu xabar model darajasida chiqadi (bazadagi unique cheklovi).
        # Django niki inglizcha: "A user with that username already exists."
        error_messages = {
            'username': {
                'unique': "Bu foydalanuvchi nomi band. Boshqasini tanlang.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Django ning UnicodeUsernameValidator i inglizcha xabar beradi va
        # uni error_messages orqali almashtirib bo'lmaydi — tekshiruvchi
        # o'z xabarini o'zi ko'taradi. Shuning uchun uni ro'yxatdan olib
        # tashlab, o'rniga bir xil qoidali o'zbekcha variantini qo'yamiz.
        maydon = self.fields['username']
        maydon.validators = [
            v for v in maydon.validators
            if not isinstance(v, UnicodeUsernameValidator)
        ] + [
            RegexValidator(
                r'^[\w.@+-]+\Z',
                "Faqat harf, raqam va @ . + - _ belgilari mumkin. "
                "Bo'sh joy ishlatmang.",
            )
        ]

        self.fields['username'].label = 'Foydalanuvchi nomi'
        self.fields['username'].widget.attrs.update({
            'class': 'auth__input',
            'placeholder': 'masalan: shamsiddin',
            'autofocus': True,
            'autocomplete': 'username',
        })
        self.fields['username'].help_text = "Harf, raqam va @ . + - _ belgilari."

        self.fields['password1'].label = 'Parol'
        self.fields['password1'].widget.attrs.update({
            'class': 'auth__input',
            'placeholder': 'Kamida 8 ta belgi',
            'autocomplete': 'new-password',
        })
        self.fields['password1'].help_text = "Kamida 8 ta belgi, faqat raqamdan iborat bo'lmasin."

        self.fields['password2'].label = 'Parolni takrorlang'
        self.fields['password2'].widget.attrs.update({
            'class': 'auth__input',
            'placeholder': 'Xuddi shu parol',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].help_text = ''

    def clean_email(self):
        """
        Bir pochta bilan ikki marta ro'yxatdan o'tishni to'xtatamiz.
        Django buni o'zi tekshirmaydi — email maydoni unique emas.
        """
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Bu e-pochta allaqachon ro\'yxatdan o\'tgan.')
        return email
