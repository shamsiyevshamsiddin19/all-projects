"""
Egasiz qolgan albom va ijrochilarni administratorga biriktiradi.

0004 migratsiyasi "owner" maydonini qo'shdi, lekin mavjud 65 ta albom
va 37 ta ijrochi egasiz qoldi. Egasiz yozuvni esa hech kim himoya
qilmaydi — istalgan odam o'chirib yuborishi mumkin edi.

Shuning uchun ularning hammasini eng birinchi administratorga beramiz.
"""

from django.db import migrations


def egani_biriktir(apps, schema_editor):
    """Egasiz yozuvlarga eng birinchi superuser ni ega qilib qo'yadi."""
    User = apps.get_model('auth', 'User')
    Album = apps.get_model('music', 'Album')
    Artist = apps.get_model('music', 'Artist')

    # Eng birinchi yaratilgan administrator — odatda loyiha egasi.
    admin = User.objects.filter(is_superuser=True).order_by('id').first()
    if admin is None:
        # Hech qanday admin bo'lmasa qiladigan ish yo'q. Yozuvlar
        # egasiz qolaveradi; keyin admin yaratilgach bu migratsiyani
        # qo'lda qayta ishlatish mumkin.
        return

    Album.objects.filter(owner__isnull=True).update(owner=admin)
    Artist.objects.filter(owner__isnull=True).update(owner=admin)


def orqaga(apps, schema_editor):
    """
    Orqaga qaytarish: egalikni olib tashlaymiz.

    DIQQAT: bu KIM nimani qo'shganini bilmaydi — hammasini egasiz
    qiladi. Shuning uchun faqat 0004 ni butunlay orqaga qaytarish
    uchun mo'ljallangan.
    """
    Album = apps.get_model('music', 'Album')
    Artist = apps.get_model('music', 'Artist')
    Album.objects.update(owner=None)
    Artist.objects.update(owner=None)


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0004_album_owner_artist_owner'),
    ]

    operations = [
        migrations.RunPython(egani_biriktir, orqaga),
    ]
