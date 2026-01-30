from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from network.models import Contact, NetworkNode, Product


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
                release_date=product_data["release_date"],
            )
            product_objects.append(product)

        node.products.set(product_objects)

        try:
            node.clean_products()
        except DjangoValidationError as e:
            raise serializers.ValidationError({"products": str(e)})

    def create(self, validated_data):
        """Создание звена с вложенными контактами и продуктами."""
        contact_data = validated_data.pop("contact")
        products_data = validated_data.pop("products", [])

        with transaction.atomic():
            node = NetworkNode(**validated_data)

            try:
                node.full_clean()
            except DjangoValidationError as e:
                raise serializers.ValidationError(e.message_dict)

            node.save()

            Contact.objects.create(network_node=node, **contact_data)
            self._handle_products(node, products_data)

        return node

    def update(self, instance, validated_data):
        """Обновление данных звена с запретом изменения долга перед поставщиком."""
        if "supplier_debt" in validated_data:
            raise serializers.ValidationError(
                {
                    "supplier_debt": "Изменение задолженности перед поставщиком через API запрещено."
                }
            )

        contact_data = validated_data.pop("contact", None)
        products_data = validated_data.pop("products", None)

        with transaction.atomic():
            old_products = set(instance.products.all())

            if products_data is not None:
                self._handle_products(instance, products_data)

            if contact_data:
                serializer = ContactSerializer(
                    instance.contact, data=contact_data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            try:
                if products_data is not None:
                    new_products = set(instance.products.all())
                    removed_products = old_products - new_products

                    if removed_products:
                        clients = instance.networknode_set.all()
                        for client in clients:
                            client_products = set(client.products.all())
                            problematic = client_products & removed_products
                            if problematic:
                                product_names = ", ".join(str(p) for p in problematic)
                                raise ValidationError(
                                    f"Нельзя удалить продукты: {product_names}."
                                    f"Они должны поставляться клиенту '{client.name}'."
                                )

                instance.full_clean()
                instance.save()
            except DjangoValidationError as e:
                if products_data is not None:
                    instance.products.set(old_products)
                raise serializers.ValidationError(e.message_dict)
            except ValidationError as e:
                if products_data is not None:
                    instance.products.set(old_products)
                raise e

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
