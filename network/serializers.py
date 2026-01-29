from logging import raiseExceptions

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from network.models import Contact, Product, NetworkNode


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    def validate_release_date(self, value):
        """Валидация даты релиза для API."""
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "Продаваемая продукция уже должна быть выпущена."
            )
        return value

    class Meta:
        model = Product
        fields = "__all__"


class NetworkNodeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления звена сети."""
    contact = ContactSerializer()
    products = ProductSerializer(many=True, required=False)

    class Meta:
        model = NetworkNode
        fields = "__all__"

        read_only_fields = ["created_at", "level"]

    def _handle_products(self, node, products_data):
        """Обрабатывает продукты для узла сети."""
        if products_data is None:
            return

        product_objects = []
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data["name"],
                model=product_data["model"],
                release_date=product_data["release_date"]
            )
            product_objects.append(product)

        node.products.set(product_objects)

        try:
            node.clean_products()
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                "products": str(e)
            })

    def create(self, validated_data):
        """Создание звена с вложенными контактами и продуктами."""
        contact_data = validated_data.pop("contact")
        products_data = validated_data.pop("products", [])

        with transaction.atomic():
            node = NetworkNode.objects.create(**validated_data)
            Contact.objects.create(network_node=node, **contact_data)
            self._handle_products(node, products_data)

        return node

    def update(self, instance, validated_data):
        """Обновление данных звена с запретом изменения долга перед поставщиком."""
        if "supplier_debt" in validated_data:
            raise serializers.ValidationError({
                "supplier_debt": "Изменение задолженности перед поставщиком через API запрещено."
            })

        contact_data = validated_data.pop("contact", None)
        products_data = validated_data.pop("products", None)

        with transaction.atomic():
            if contact_data:
                serializer = ContactSerializer(
                    instance.contact,
                    data=contact_data,
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            self._handle_products(instance, products_data)

            return instance


class NetworkNodeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения звеньев сети с вложенными данными."""
    contact = ContactSerializer(read_only=True)
    products = ProductSerializer(many=True, read_only=True)
    supplier = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = NetworkNode
        fields = "__all__"
        read_only_fields = ["created_at", "level", "supplier_debt"]



