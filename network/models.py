from django.core.exceptions import ValidationError
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


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    model = models.CharField(max_length=100, verbose_name="Модель")
    release_date = models.DateField(verbose_name="Дата выхода продукта на рынок")

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

    def __str__(self):
        return f"Название: {self.name}, модель: {self.model}"


class NetworkNode(models.Model):
    NODE_TYPES = [
        ("factory", "Завод"),
        ("retail", "Розничная сеть"),
        ("entrepreneur", "Индивидуальный предприниматель"),
    ]

    name = models.CharField(max_length=200, verbose_name="Название")
    contact = models.ForeignKey(
        to=Contact, on_delete=models.CASCADE, verbose_name="Контакты"
    )
    products = models.ManyToManyField(
        to=Product, verbose_name="Продукты", related_name="network_nodes"
    )
    supplier = models.ForeignKey(
        to="self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Поставщик",
    )
    supplier_debt = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Задолженность перед поставщиком",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    node_type = models.CharField(
        max_length=12, choices=NODE_TYPES, verbose_name="Тип звена"
    )
    level = models.PositiveIntegerField(
        default=0, editable=False, verbose_name="Уровень иерархии"
    )

    class Meta:
        verbose_name = "Звено сети"
        verbose_name_plural = "Звенья сети"

    def clean(self):
        """Валидация уровней иерархии."""

        super().clean()

        if self.supplier is None:
            self.level = 0
        else:
            self.level = self.supplier.level + 1

        if self.node_type == "factory" and self.supplier:
            raise ValidationError("У завода не может быть поставщика")

        if self.level > 2:
            raise ValidationError(
                f"Торговая сеть с поставщиком {self.supplier} уже имеет 3 уровня. Выберите другого поставщика"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_node_type_display()}: {self.name}"
