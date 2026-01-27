from itertools import product

from django.contrib import admin, messages
from django.utils.html import format_html

from network.models import NetworkNode, Product, Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "country",
        "city",
        "street",
        "building_number",
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "model",
        "release_date",
    ]


@admin.register(NetworkNode)
class NetworkNodeAdmin(admin.ModelAdmin):
    list_display = [
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
        "contact",
        "products",
        "supplier",
        "supplier_link_detailed",
        "supplier_debt",
    ]

    actions = ["clear_debt"]

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
