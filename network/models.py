from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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
        """Проверка уровней иерархии и изменения поставщика."""

        if self.supplier is None:
            self.level = 0
        else:
            self.level = self.supplier.level + 1

        if self.node_type == "factory" and self.supplier:
            raise ValidationError("У завода не может быть поставщика.")

        if self.node_type != "factory" and not self.supplier:
            raise ValidationError("Укажите поставщика.")

        if self.level > 2:
            raise ValidationError(
                f"Торговая сеть с поставщиком {self.supplier} уже имеет 3 уровня. Выберите другого поставщика."
            )

        if self.pk and self.supplier and self.supplier.id == self.id:
            raise ValidationError("Нельзя указывать себя в качестве поставщика")

        if self.pk and self.supplier_id:
            old = NetworkNode.objects.get(pk=self.pk)
            if old.supplier_id != self.supplier_id:
                self._validate_supplier_change(old)

        if self.pk:
            old = NetworkNode.objects.get(pk=self.pk)
            if old.node_type in ["retail", "entrepreneur"] and self.node_type == "factory" and old.supplier_debt > 0:
                raise ValidationError("Нельзя изменить тип звена на 'завод' при наличии задолженности перед поставщиком.")

        if self.pk:
            self._validate_product_removal_for_clients()
            self.clean_products()

    def _validate_supplier_change(self, old_instance):
        """Валидация изменения поставщика."""

        if old_instance.supplier_debt > 0:
            raise ValidationError(
                "Нельзя изменить поставщика при наличии задолженности."
            )

        if self._would_exceed_max_depth():
            raise ValidationError(
                "Выбрать указанного поставщика невозможно - это приводит к превышению глубины 3-х уровневой иерархии."
            )

        if not self._new_supplier_has_all_products():
            raise ValidationError(
                "У нового поставщика нет необходимых продуктов."
            )

    def _would_exceed_max_depth(self):
        """Проверяет непревышение максимальной глубины иерархии."""
        new_self_level = self.supplier.level + 1
        max_descendant_depth = self._get_max_descendant_depth()
        total_depth = new_self_level + max_descendant_depth
        return total_depth > 2

    def _get_max_descendant_depth(self):
        """Ищет максимальный уровень иерархии покупателей-перепродавцов."""
        max_depth = 0
        for reseller in self.networknode_set.all():
            if max_depth >= 2:
                break

            reseller_depth = reseller._get_max_descendant_depth()
            max_depth = max(max_depth, reseller_depth + 1)

        return max_depth

    def _new_supplier_has_all_products(self):
        """Проверяет наличие всех продуктов покупателей-перепродавцов у нового поставщика."""

        required_products = set()
        for reseller in self.networknode_set.all():
            required_products.update(reseller.products.all())

        supplier_products = set(self.supplier.products.all())

        return required_products.issubset(supplier_products)

    def _validate_product_removal_for_clients(self):
        """Проверяет, что удаление продуктов не нарушает цепочку поставок."""
        old = NetworkNode.objects.get(pk=self.pk)
        old_products = set(old.products.all())
        new_products = set(self.products.all())
        removed_products = old_products - new_products

        if not removed_products:
            return

        for client in self.networknode_set.all():
            client_products = set(client.products.all())
            problematic = client_products & removed_products
            if problematic:
                product_names = ", ". join(str(p) for p in problematic)
                raise ValidationError(
                    f"Нельзя удалить {product_names} - они должны поставляться клиенту '{client.name}'."
                )


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


class Contact(models.Model):
    email = models.EmailField(verbose_name="Адрес электронной почты")
    country = models.CharField(max_length=200, verbose_name="Страна")
    city = models.CharField(max_length=255, verbose_name="Город")
    street = models.CharField(max_length=255, verbose_name="Улица")
    building_number = models.CharField(max_length=20, verbose_name="Номер дома")

    network_node = models.OneToOneField(
        NetworkNode,
        on_delete=models.CASCADE,
        related_name="contact",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Контакты"
        verbose_name_plural = "Контакты"

    def __str__(self):
        return (
            f"{self.country}, {self.city}, ул. {self.street}, д. {self.building_number}"
        )
