from django.db import models

# Create your models here.
amals = [
    ('+', "qo'shish+"),
    ('-', "ayirish-"),
    ('*', "ko'paytirish"),
    ('/', "bo'lish"),
    ('^', "daraja"),
    ('sin', "sinus"),
    ('cos', "kosinus"),
    ('tan', "tangens"),
    ('sqr', "kvadrat"),
    ('sqrt', "ildiz"),
    ('fact', "faktorial"),
]


class Calculyator(models.Model):
    birinchi_son = models.FloatField()
    amal = models.CharField(max_length=10, choices=amals)
    ikkinchi_son = models.FloatField(default=0)
    natija = models.FloatField()

    def __str__(self):
        return f"{self.birinchi_son} {self.amal} {self.ikkinchi_son} = {self.natija}"
