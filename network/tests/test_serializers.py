from datetime import date, timedelta, datetime
from django.utils import timezone

import pytest
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoCoreValidationError

from network.models import NetworkNode, Contact
from network.serializers import (
    NetworkNodeWriteSerializer,
    ContactSerializer,
    ProductSerializer,
    NetworkNodeReadSerializer,
)


@pytest.mark.django_db
def test_contact_serializer_output_representation(contact_objects):
    """Проверяет преобразование ContactSerializer в словарь."""
    contact_obj = contact_objects[0]
    serializer = ContactSerializer(contact_obj)
    serializer_data = serializer.data

    assert "id" in serializer_data
    assert "email" in serializer_data
    assert "country" in serializer_data
    assert "city" in serializer_data
    assert "street" in serializer_data
    assert "building_number" in serializer_data
    assert "network_node" in serializer_data

    assert serializer_data["id"] == contact_obj.id
    assert serializer_data["email"] == contact_obj.email
    assert serializer_data["country"] == contact_obj.country
    assert serializer_data["city"] == contact_obj.city
    assert serializer_data["street"] == contact_obj.street
    assert serializer_data["building_number"] == contact_obj.building_number
    assert serializer_data["network_node"] == contact_obj.network_node


@pytest.mark.django_db
def test_contact_serializer_invalid_email(contact_data_in_dict):
    """Проверяет поведение ContactSerializer при передаче некорректного email."""
    contact_data = contact_data_in_dict
    contact_data["email"] = "1invalid_email"
    serializer = ContactSerializer(data=contact_data)
    assert not serializer.is_valid()
    assert "email" in serializer.errors


@pytest.mark.django_db
def test_product_serializer_output_representation(product_objects):
    """Проверяет преобразование ProductSerializer в словарь."""
    product_obj = product_objects[0]
    serializer = ProductSerializer(product_obj)
    serializer_data = serializer.data

    assert "id" in serializer_data
    assert "name" in serializer_data
    assert "model" in serializer_data
    assert "release_date" in serializer_data

    assert serializer_data["id"] == product_obj.id
    assert serializer_data["name"] == product_obj.name
    assert serializer_data["model"] == product_obj.model
    assert (
        date.fromisoformat(serializer_data["release_date"]) == product_obj.release_date
    )


@pytest.mark.django_db
def test_product_release_date_validation(product_data_in_dict):
    """Проверяет поведение сериализатора при прошлой, сегодняшней и будущей дате выпуска."""
    today = timezone.now().date()

    past_date = today + timedelta(days=-1)
    product_data = product_data_in_dict
    product_data["release_date"] = str(past_date)
    serializer = ProductSerializer(data=product_data)
    assert serializer.is_valid()
    assert serializer.data["release_date"] == str(past_date)

    product_data = product_data_in_dict
    product_data["release_date"] = str(today)
    serializer = ProductSerializer(data=product_data)
    assert serializer.is_valid()
    assert serializer.data["release_date"] == str(today)

    future_date = today + timedelta(days=1)
    product_data = product_data_in_dict
    product_data["release_date"] = str(future_date)
    serializer = ProductSerializer(data=product_data)
    assert not serializer.is_valid()
    assert "release_date" in serializer.errors


@pytest.mark.django_db
def test_network_node_write_serializer_on_create_object(
    network_node_data_in_dict, contact_data_in_dict, product_data_in_dict
):
    """
    Проверяет создание сериализатором NetworkNodeWriteSerializer объекта модели NetworkNode,
    а также объектов связанных моделей Contact и Product.
    """
    node_data = network_node_data_in_dict
    node_data["contact"] = contact_data_in_dict
    node_data["products"] = [
        product_data_in_dict,
    ]
    serializer = NetworkNodeWriteSerializer(data=node_data)
    assert serializer.is_valid()
    node_obj = serializer.save()
    assert isinstance(node_obj, NetworkNode)
    assert node_obj.name == node_data["name"]
    assert isinstance(node_obj.contact, Contact)
    assert node_obj.contact.email == contact_data_in_dict["email"]
    assert node_obj.contact.country == contact_data_in_dict["country"]
    assert node_obj.contact.city == contact_data_in_dict["city"]
    assert node_obj.contact.street == contact_data_in_dict["street"]
    assert node_obj.contact.building_number == contact_data_in_dict["building_number"]
    assert node_obj.products.all().count() == 1
    assert node_obj.products.all()[0].name == product_data_in_dict["name"]
    assert node_obj.products.all()[0].model == product_data_in_dict["model"]
    assert node_obj.products.all()[0].release_date == date.fromisoformat(
        product_data_in_dict["release_date"]
    )
    assert not node_obj.supplier
    assert node_obj.supplier_debt == 0
    assert node_obj.created_at is not None
    assert node_obj.node_type == network_node_data_in_dict["node_type"]


@pytest.mark.django_db
def test_network_node_write_serializer_on_update_object_without_contact_and_products(
    network_nodes,
):
    """Проверяет обновление сериализатором NetworkNodeWriteSerializer данных объекта модели NetworkNode."""
    original_node = network_nodes[0]
    new_data = {"name": "Новый завод"}
    serializer = NetworkNodeWriteSerializer(original_node, data=new_data, partial=True)
    assert serializer.is_valid()
    updated_node = serializer.save()
    assert updated_node.id == original_node.id
    assert updated_node.name == original_node.name
    assert updated_node.created_at == original_node.created_at


@pytest.mark.django_db
def test_network_node_write_serializer_on_update_modify_contact(
    network_nodes, contact_data_in_dict
):
    """Проверяет изменение данных контактов при обновлении объекта модели NetworkNode."""
    original_node = network_nodes[0]
    new_contact_data = contact_data_in_dict
    new_data = {"name": "Новый завод", "contact": new_contact_data}
    serializer = NetworkNodeWriteSerializer(original_node, data=new_data, partial=True)
    assert serializer.is_valid()
    updated_node = serializer.save()
    assert updated_node.contact.id == original_node.contact.id
    assert updated_node.contact.email == new_contact_data["email"]
    assert updated_node.contact.country == new_contact_data["country"]
    assert updated_node.contact.city == new_contact_data["city"]
    assert updated_node.contact.street == new_contact_data["street"]
    assert updated_node.contact.building_number == new_contact_data["building_number"]


@pytest.mark.django_db
def test_network_node_write_serializer_create_new_product(contact_data_in_dict):
    """
    Проверяет добавление продуктов при обновлении,
    только если данные переданных продуктов отсутствуют в исходном списке продуктов.
    """
    product_1_data = {
        "name": "product_1",
        "model": "model_1",
        "release_date": "2001-01-01",
    }

    product_2_data = {
        "name": "product_2",
        "model": "model_2",
        "release_date": "2002-02-02",
    }

    node_original_data = {
        "name": "Новый завод",
        "node_type": "factory",
        "contact": contact_data_in_dict,
        "products": [product_1_data],
    }
    serializer = NetworkNodeWriteSerializer(data=node_original_data)
    assert serializer.is_valid()

    node = serializer.save()
    assert node.products.all().count() == 1
    product_1_obj = node.products.all()[0]
    assert product_1_obj.name == product_1_data["name"]
    assert product_1_obj.model == product_1_data["model"]
    assert product_1_obj.release_date == date.fromisoformat(
        product_1_data["release_date"]
    )

    node_modified_data = {"products": [product_1_data, product_2_data]}
    serializer = NetworkNodeWriteSerializer(node, data=node_modified_data, partial=True)
    serializer.is_valid()
    serializer.save()
    assert node.products.all().count() == 2
    assert product_1_obj in node.products.all()
    product_2_obj = node.products.get(name=product_2_data["name"])
    assert product_2_obj.model == product_2_data["model"]
    assert product_2_obj.release_date == date.fromisoformat(
        product_2_data["release_date"]
    )


@pytest.mark.django_db
def test_network_node_write_serializer_invalid_node_type(contact_data_in_dict):
    """Проверяет невозможность назначения некорректного типа звена."""

    node_data = {
        "name": "Завод",
        "node_type": "invalid_type",
        "contact": contact_data_in_dict,
    }
    serializer = NetworkNodeWriteSerializer(data=node_data)
    assert not serializer.is_valid()
    assert "node_type" in serializer.errors


@pytest.mark.django_db
def test_supplier_debt_read_only_in_update(network_nodes):
    """Проверяет невозможность изменения задолженности перед поставщиком при обновлении по API."""
    node = network_nodes[1]

    serializer = NetworkNodeWriteSerializer(
        node, data={"supplier_debt": 0}, partial=True
    )
    assert serializer.is_valid()
    with pytest.raises(
        ValidationError,
        match="Изменение задолженности перед поставщиком через API запрещено",
    ):
        serializer.save()


@pytest.mark.django_db
def test_node_products_must_be_subset_of_supplier_products(network_nodes):
    """Проверяет невозможность добавления продуктов, которых нет у поставщика."""
    node_on_level_1 = network_nodes[1]
    new_product = {
        "name": "new_product",
        "model": "new_model",
        "release_date": "2026-01-25",
    }
    serializer = NetworkNodeWriteSerializer(
        node_on_level_1,
        data={
            "products": [
                new_product,
            ]
        },
        partial=True,
    )

    with pytest.raises(ValidationError, match="продукты отсутствуют у поставщика"):
        serializer.is_valid()
        serializer.save()


@pytest.mark.django_db
def test_create_with_nonexistent_supplier(contact_data_in_dict):
    """Проверяет невозможность создания объекта NetworkNode c несуществующим id поставщика."""
    node_data = {
        "name": "Розничная сеть",
        "node_type": "retail",
        "contact": contact_data_in_dict,
        "supplier": 99999,
    }
    serializer = NetworkNodeWriteSerializer(data=node_data)
    assert not serializer.is_valid()
    assert "supplier" in serializer.errors


@pytest.mark.django_db
def test_network_node_read_serializer_output_representation(network_nodes):
    """Проверяет NetworkNodeReadSerializer на корректное представление данных."""
    node_obj = network_nodes[0]
    serializer = NetworkNodeReadSerializer(node_obj)
    serializer_data = serializer.data

    assert "id" in serializer_data
    assert "name" in serializer_data
    assert "products" in serializer_data
    assert "supplier" in serializer_data
    assert "supplier_debt" in serializer_data
    assert "created_at" in serializer_data
    assert "node_type" in serializer_data
    assert "level" in serializer_data

    assert serializer_data["id"] == node_obj.id
    assert serializer_data["name"] == node_obj.name
    assert serializer_data["contact"]["id"] == node_obj.contact.id
    assert len(serializer_data["products"]) == node_obj.products.all().count()
    assert set(item["id"] for item in serializer_data["products"]) == set(
        product.id for product in node_obj.products.all()
    )
    assert serializer_data["supplier"] == node_obj.supplier
    assert float(serializer_data["supplier_debt"]) == node_obj.supplier_debt
    assert datetime.fromisoformat(serializer_data["created_at"]) == node_obj.created_at
    assert serializer_data["node_type"] == node_obj.node_type
    assert serializer_data["level"] == node_obj.level
