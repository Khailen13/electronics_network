from django.db import models


class Contact(models.Model):
    email = models.EmailField(verbose_name="Адрес электронной почты")
    country = models.CharField(max_length=200, verbose_name="Страна")
    city = models.CharField(max_length=255, verbose_name="Город")
    street = models.CharField(max_length=255, verbose_name="Улица")
    building_number = models.CharField(max_length=20, verbose_name="Номер дома")

    class Meta:
        verbose_name = "Контакты"
        verbose_name_plural = "Контакты"

    def __str__(self):
        return self.email
