from django.contrib import admin, messages
from django.db import transaction
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django import forms
from django.utils.html import format_html
from rest_framework.exceptions import ValidationError

from network.models import NetworkNode, Product, Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "email",
        "country",
        "city",
        "street",
        "building_number",
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "model",
        "release_date",
    ]


class NetworkNodeAdminForm(forms.ModelForm):
    class Meta:
        model = NetworkNode
        fields = "__all__"

    def clean(self):
        """Валидация формы."""
        cleaned_data = super().clean()

        if not self.errors and self.instance and self.instance.pk:
            products = cleaned_data.get("products")
            supplier = cleaned_data.get("supplier")

            if supplier and products:
                supplier_products = set(supplier.products.all())
                selected_products = set(products)

                invalid_products = selected_products - supplier_products
                if invalid_products:
                    product_names = ", ".join(str(p) for p in invalid_products)
                    raise forms.ValidationError(
                        f"Следующие продукты отсутствуют у поставщика '{supplier.name}': {product_names}"
                    )

                old_instance = NetworkNode.objects.get(pk=self.instance.pk)
                old_products = set(old_instance.products.all())
                removed_products = old_products - selected_products

                if removed_products:
                    for client in old_instance.networknode_set.all():
                        client_products = set(client.products.all())
                        problematic = client_products & removed_products
                        if problematic:
                            product_names = ", ".join(str(p) for p in problematic)
                            raise forms.ValidationError(
                                f"Нельзя удалить {product_names} - они нужны клиенту '{client.name}'."
                            )

        return cleaned_data


@admin.register(NetworkNode)
class NetworkNodeAdmin(admin.ModelAdmin):
    form = NetworkNodeAdminForm

    list_display = [
        "id",
        "name",
        "node_type",
        "level",
        "contact",
        "supplier_link",
        "display_products",
        "supplier_debt",
        "created_at",
    ]
    list_filter = [
        "contact__city",
    ]
    search_fields = [
        "name",
    ]
    readonly_fields = [
        "supplier_link_detailed",
    ]
    fields = [
        "name",
        "node_type",
        "products",
        "supplier",
        "supplier_link_detailed",
        "supplier_debt",
    ]

    actions = ["clear_debt"]

    class ContactInline(admin.StackedInline):
        model = Contact
        can_delete = False

    inlines = [ContactInline]

    def display_products(self, obj):
        """Отображает список продуктов в общем списке звеньев."""

        products = obj.products.all()

        if not products:
            return "-"

        displayed_products = list(products)[:2]
        display = ", ".join([str(p) for p in displayed_products])

        not_displayed_products_count = len(products) - 2
        if not_displayed_products_count > 0:
            display += f" и ещё {not_displayed_products_count}"

        return display

    display_products.short_description = "Продукты"

    def supplier_link(self, obj):
        """Создает HTML-ссылку на поставщика при отображении списка звеньев торговой сети."""

        if obj.supplier:
            supplier = obj.supplier
            url = f"/admin/network/networknode/{supplier.id}/change/"
            return format_html('<a href="{}">{}</a>', url, supplier.name)
        return "-"

    supplier_link.short_description = "Поставщик"

    def supplier_link_detailed(self, obj):
        """Создает HTML-ссылку на поставщика при детальном отображении звена торговой сети."""

        return self.supplier_link(obj)

    supplier_link_detailed.short_description = "Ссылка на поставщика"

    def clear_debt(self, request, queryset):
        """Admin action для очистки задолженности перед поставщиком."""

        updated = queryset.update(supplier_debt=0)
        self.message_user(
            request, f"Задолженность очищена для {updated} объектов.", messages.SUCCESS
        )

    clear_debt.short_description = "Очистить задолженность перед поставщиком"
