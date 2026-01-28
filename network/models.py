from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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
        return (
            f"{self.country}, {self.city}, ул. {self.street}, д. {self.building_number}"
        )


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    model = models.CharField(max_length=100, verbose_name="Модель")
    release_date = models.DateField(verbose_name="Дата выхода продукта на рынок")

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

    def __str__(self):
        return f"{self.name} - {self.model} ({self.release_date})"

    def clean(self):
        """Валидация даты выпуска продукта."""
        if self.release_date > timezone.now().date():
            raise ValidationError("Продаваемая продукция уже должна быть выпущена.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


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
        on_delete=models.PROTECT,
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

        if self.supplier is None:
            self.level = 0
        else:
            self.level = self.supplier.level + 1

        if self.node_type == "factory" and self.supplier:
            raise ValidationError("У завода не может быть поставщика")

        if self.node_type != "factory" and not self.supplier:
            raise ValidationError("Укажите поставщика")

        if self.level > 2:
            raise ValidationError(
                f"Торговая сеть с поставщиком {self.supplier} уже имеет 3 уровня. Выберите другого поставщика"
            )

        if self.pk and self.supplier and self.supplier.id == self.id:
            raise ValidationError("Нельзя указывать себя в качестве поставщика")

    def clean_products(self):
        """Проверяет наличие продуктов у поставщика."""
        if not self.supplier:
            return

        current_products = set(self.products.all())
        supplier_products = set(self.supplier.products.all())

        invalid_products = current_products - supplier_products

        if invalid_products:
            product_names = ", ".join(str(p) for p in invalid_products)
            supplier_name = self.supplier.name

            raise ValidationError(f"Следующие продукты отсутствуют у поставщика '{supplier_name}': {product_names}.")

    def save(self, *args, **kwargs):
        """Сохраняет после валидации."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_node_type_display()}: {self.name}"
