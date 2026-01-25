from django.contrib import admin

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
        "id",
        "name",
        "contact",
        "supplier",
        "supplier_debt",
        "created_at",
    ]
