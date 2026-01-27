from rest_framework import serializers
from network.models import Contact, Product, NetworkNode


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class NetworkNodeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления звена сети."""
    contact = ContactSerializer()
    products = ProductSerializer(many=True, required=False)

    class Meta:
        model = NetworkNode
        fields = (
            "id",
            "name",
            "node_type",
            "contact",
            "products",
            "supplier",
            "supplier_debt",
            "created_at",
            "level",
        )

        read_only_fields = ["created_at", "level"]

    def create(self, validated_data):
        """Создание звена с вложенными контактами и продуктами."""
        contact_data = validated_data.pop("contact")
        products_data = validated_data.pop("products", [])

        contact = Contact.objects.create(**contact_data)
        node = NetworkNode.objects.create(contact=contact, **validated_data)

        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data["name"],
                model=product_data["model"],
                defaults=product_data
            )
            node.products.add(product)

        return node

    def update(self, instance, validated_data):
        """Обновление данных звена с запретом изменения долга перед поставщиком."""
        validated_data.pop("supplier_debt", None)
        contact_data = validated_data.pop("contact", None)
        if contact_data:
            contact_serializer = ContactSerializer(
                instance.contact,
                data=contact_data,
                partial=True
            )
            if contact_serializer.is_valid():
                contact_serializer.save()

        products_data = validated_data.pop("products", None)
        if products_data is not None:
            instance.products.clear()
            for product_data in products_data:
                product, created = Product.objects.get_or_create(
                    name=product_data["name"],
                    model=product_data["model"],
                    defaults=product_data
                )
                instance.products.add(product)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
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



