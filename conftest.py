import pytest
from django.contrib.auth.models import User
from django.test import Client

from network.models import Contact, NetworkNode, Product


@pytest.fixture
def contact_data_in_dict():
    """Данные контакта в виде словаря."""

    contact_data = {
        "email": "example@mail.com",
        "country": "Россия",
        "city": "Москва",
        "street": "Строителей",
        "building_number": "3",
    }

    return contact_data


@pytest.fixture
def contact_objects():
    """Возвращает три объекта Contact."""

    contacts_same_data = {
        "country": "Россия",
        "city": "Москва",
        "street": "Тестовая",
        "building_number": "1",
        "network_node": None,
    }
    contact_objects = []
    for number in range(1, 4):
        contact_objects.append(
            Contact.objects.create(
                email=f"contact_{number}@mail.com", **contacts_same_data
            )
        )

    return contact_objects


@pytest.fixture
def product_data_in_dict():
    """Данные продукта в виде словаря."""

    product_data = {
        "name": "Смартфон",
        "model": "Samsung",
        "release_date": "2025-12-01",
    }

    return product_data


@pytest.fixture
def product_objects():
    """Возвращает три объекта Product."""

    products_same_data = {"model": "X", "release_date": "2020-02-20"}
    product_objects = []
    for number in range(1, 4):
        product_objects.append(
            Product.objects.create(name=f"Продукт_{number}", **products_same_data)
        )

    return product_objects


@pytest.fixture
def network_node_data_in_dict():
    """Данные звена торговой сети в виде словаря."""

    node_data = {"name": "Завод", "supplier_debt": 0, "node_type": "factory"}

    return node_data


@pytest.fixture
def network_nodes(contact_objects, product_objects):
    """Возвращает объекты торговой сети, составляющие цепь 'Завод - Розничная сеть - ИП'."""

    contact_1, contact_2, contact_3 = contact_objects
    product_1, product_2, product_3 = product_objects

    factory = NetworkNode.objects.create(
        node_type="factory", name="Завод 1", supplier=None, supplier_debt=0
    )

    retail = NetworkNode.objects.create(
        node_type="retail",
        name="Розничная сеть 1",
        supplier=factory,
        supplier_debt=100_000,
    )

    entrepreneur = NetworkNode.objects.create(
        node_type="entrepreneur",
        name="ИП Иванов",
        supplier=retail,
        supplier_debt=10_000,
    )

    contact_1.network_node = factory
    contact_2.network_node = retail
    contact_3.network_node = entrepreneur
    Contact.objects.bulk_update([contact_1, contact_2, contact_3], ["network_node"])

    factory.products.set([product_1, product_2, product_3])
    retail.products.set([product_1, product_2])
    entrepreneur.products.set([product_1])

    return factory, retail, entrepreneur


@pytest.fixture
def active_user():
    """Активный пользователь"""
    return User.objects.create_user(
        username="active_user", password="123qwerty", is_active=True
    )


@pytest.fixture
def inactive_user():
    """Неактивный пользователь"""
    return User.objects.create_user(
        username="inactive_user", password="123qwerty", is_active=False
    )


@pytest.fixture
def admin_user():
    """Создает администратора."""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="123qwerty"
    )


@pytest.fixture
def admin_client(admin_user):
    """Клиент с правами администратора."""
    client = Client()
    client.force_login(admin_user)
    return client
