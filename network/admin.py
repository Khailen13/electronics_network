from django.contrib import admin
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
        "contact",
        "supplier_link",
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

    def supplier_link(self, obj):
        if obj.supplier:
            supplier = obj.supplier
            url = f"/admin/network/networknode/{supplier.id}/change/"
            return format_html('<a href="{}">{}</a>', url, supplier.name)
        return "-"

    supplier_link.short_description = "Поставщик"

    def supplier_link_detailed(self, obj):
        return self.supplier_link(obj)

    supplier_link_detailed.short_description = "Ссылка на поставщика"
