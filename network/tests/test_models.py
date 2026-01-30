from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.utils import timezone

import pytest

from network.models import Contact, Product, NetworkNode


@pytest.mark.django_db
class TestContact:
    """Проверка модели Contact."""

    @pytest.fixture(autouse=True)
    def setup(self, contact_data_in_dict):
        """Создание одного контакт-объекта для тестов, объединенных в класс."""
        self.contact_data = contact_data_in_dict
        self.contact_obj = Contact.objects.create(**contact_data_in_dict)
        self.contact_obj.refresh_from_db()
        yield

    def test_create(self):
        """Проверка данных созданного объекта."""
        assert Contact.objects.all().count() == 1
        assert self.contact_obj.email == self.contact_data["email"]
        assert self.contact_obj.country == self.contact_data["country"]
        assert self.contact_obj.city == self.contact_data["city"]
        assert self.contact_obj.street == self.contact_data["street"]
        assert self.contact_obj.building_number == self.contact_data["building_number"]

    def test_update(self):
        """Проверка изменения данных объекта."""
        new_data = {
            "email": "test@mail.com",
            "country": "test_country",
            "city": "test_city",
            "street": "test_street",
            "building_number": "test_building_number",
        }

        self.contact_obj.email = new_data["email"]
        self.contact_obj.country = new_data["country"]
        self.contact_obj.city = new_data["city"]
        self.contact_obj.street = new_data["street"]
        self.contact_obj.building_number = new_data["building_number"]

        self.contact_obj.save()
        self.contact_obj.refresh_from_db()

        assert self.contact_obj.email == new_data["email"]
        assert self.contact_obj.country == new_data["country"]
        assert self.contact_obj.city == new_data["city"]
        assert self.contact_obj.street == new_data["street"]
        assert self.contact_obj.building_number == new_data["building_number"]

    def test_delete(self):
        """Проверка удаления объекта."""
        assert Contact.objects.all().count() == 1
        self.contact_obj.delete()
        assert Contact.objects.all().count() == 0

    def test_string_representation(self):
        """Проверка строкового представления."""
        expected = f"{self.contact_obj.country}, {self.contact_obj.city}, ул. {self.contact_obj.street}, д. {self.contact_obj.building_number}"
        assert str(self.contact_obj) == expected

    def test_invalid_email(self):
        """Проверка назначения некорректного email."""
        self.contact_obj.email = "invalid-email"
        with pytest.raises(ValidationError):
            self.contact_obj.full_clean()


@pytest.mark.django_db
class TestProduct:
    """Проверка модели Product."""

    @pytest.fixture(autouse=True)
    def setup(self, product_data_in_dict):
        """Создание одного продукт-объекта для тестов, объединенных в класс."""
        self.product_data = product_data_in_dict
        self.product_obj = Product.objects.create(**product_data_in_dict)
        self.product_obj.refresh_from_db()
        yield

    def test_create(self):
        """Проверка данных созданного объекта."""
        release_date_date_obj = date.fromisoformat(self.product_data["release_date"])
        assert Product.objects.all().count() == 1
        assert self.product_obj.name == self.product_data["name"]
        assert self.product_obj.model == self.product_data["model"]
        assert self.product_obj.release_date == release_date_date_obj

    def test_update(self):
        """Проверка изменения данных объекта."""
        release_date_date_obj = date.fromisoformat(self.product_data["release_date"])
        new_release_date = release_date_date_obj + timedelta(days=-1)
        new_data = {
            "name": self.product_data["name"] + "_updated",
            "model": self.product_data["model"] + "_updated",
            "release_date": str(new_release_date),
        }

        self.product_obj.name = new_data["name"]
        self.product_obj.model = new_data["model"]
        self.product_obj.release_date = new_data["release_date"]

        self.product_obj.save()
        self.product_obj.refresh_from_db()

        assert self.product_obj.name == new_data["name"]
        assert self.product_obj.model == new_data["model"]
        assert self.product_obj.release_date == new_release_date

    def test_delete(self):
        """Проверка удаления объекта."""
        assert Product.objects.all().count() == 1
        self.product_obj.delete()
        assert Product.objects.all().count() == 0

    def test_string_representation(self):
        """Проверка строкового представления."""
        expected = f"{self.product_obj.name} - {self.product_obj.model} ({self.product_obj.release_date})"
        assert str(self.product_obj) == expected

    def test_release_date_future(self):
        """Проверка при попытке назначить будущую дату релиза."""
        future_date = timezone.now().date() + timedelta(days=1)
        with pytest.raises(
            ValidationError, match="Продаваемая продукция уже должна быть выпущена."
        ):
            Product.objects.create(
                name="Продукт", model="Модель", release_date=future_date
            )

    def test_release_date_today(self):
        """Проверка при попытке назначить сегодняшнюю дату релиза."""
        today = timezone.now().date()
        product = Product.objects.create(
            name="Продукт", model="Модель", release_date=today
        )
        assert product.release_date == today


@pytest.mark.django_db
class TestNetworkNode:
    """Проверка модели NetworkNode."""

    @pytest.fixture(autouse=True)
    def setup(self, network_nodes):
        """Создание торговой сети для тестов, объединенных в класс."""
        self.factory_net1_lv0, self.retail_net1_lv1, self.entrepreneur_net1_lv2 = (
            network_nodes
        )
        yield

    def test_create(
        self, contact_data_in_dict, product_data_in_dict, network_node_data_in_dict
    ):
        """Проверка данных созданного объекта."""
        nodes_count_before_create = NetworkNode.objects.all().count()
        product = Product.objects.create(**product_data_in_dict)
        node = NetworkNode.objects.create(**network_node_data_in_dict)
        contact = Contact.objects.create(**contact_data_in_dict, network_node=node)
        node.products.set(
            [
                product,
            ]
        )
        nodes_count_after_create = NetworkNode.objects.all().count()
        assert nodes_count_after_create - nodes_count_before_create == 1
        assert node.name == network_node_data_in_dict["name"]
        assert node.contact == contact
        assert node.products.count() == 1
        assert product in node.products.all()
        assert node.supplier == None
        assert node.supplier_debt == network_node_data_in_dict["supplier_debt"]
        assert node.node_type == network_node_data_in_dict["node_type"]
        assert node.level == 0
        assert node.created_at is not None

    def test_update(
        self, contact_data_in_dict, product_data_in_dict, network_node_data_in_dict
    ):
        """Проверка изменения данных объекта."""
        product1 = Product.objects.create(**product_data_in_dict)
        node = NetworkNode.objects.create(**network_node_data_in_dict)
        contact = Contact.objects.create(**contact_data_in_dict, network_node=node)

        node.products.set(
            [
                product1,
            ]
        )

        node_new_name = "Новый завод"
        contact_new_email = "new@mail.com"
        product2 = Product.objects.create(**product_data_in_dict)
        product2.name = "product2"
        product2.save()

        node.name = node_new_name
        node.products.set(
            [
                product2,
            ]
        )
        node.contact.email = contact_new_email

        node.save()
        contact.save()
        node.refresh_from_db()

        assert node.name == node_new_name
        assert node.contact.email == contact_new_email
        assert node.products.count() == 1
        assert product2 in node.products.all()

    def test_delete_object(self, contact_data_in_dict, network_node_data_in_dict):
        """Проверка удаления объекта с каскадным удалением контакта."""
        node = NetworkNode.objects.create(**network_node_data_in_dict)
        contact = Contact.objects.create(**contact_data_in_dict, network_node=node)
        node_id = node.id
        contact_id = contact.id
        node.delete()
        assert not NetworkNode.objects.filter(id=node_id).exists()
        assert not Contact.objects.filter(id=contact_id).exists()

    def test_string_representation(self):
        """Проверка строкового представления."""
        node = self.factory_net1_lv0
        expected = f"{node.get_node_type_display()}: {node.name}"
        assert str(node) == expected

    def test_factory_cannot_have_supplier_on_create(self):
        """Проверяет невозможность создания завода с поставщиком."""
        with pytest.raises(ValidationError, match="У завода не может быть поставщика"):
            NetworkNode.objects.create(
                name="Завод",
                node_type="factory",
                supplier=self.entrepreneur_net1_lv2,
            )

    def test_factory_cannot_get_supplier_on_update(self):
        """Проверяет невозможность назначения поставщика при обновлении данных существующего завода."""
        factory = NetworkNode.objects.create(name="Завод", node_type="factory")
        factory.supplier = self.retail_net1_lv1
        with pytest.raises(ValidationError, match="У завода не может быть поставщика"):
            factory.full_clean()

    def test_retail_and_entrepreneur_must_have_supplier_on_create(self):
        """Проверяет необходимость наличия поставщика при создании розничной сети и ИП."""
        with pytest.raises(ValidationError, match="Укажите поставщика"):
            NetworkNode.objects.create(name="Розничная сеть", node_type="retail")

        with pytest.raises(ValidationError, match="Укажите поставщика"):
            NetworkNode.objects.create(name="ИП Иванов", node_type="entrepreneur")

    def test_retail_and_entrepreneur_must_have_supplier_on_update(self, network_nodes):
        """Проверяет необходимость наличия поставщика при обновлении розничной сети и ИП."""
        retail = network_nodes[1]
        entrepreneur = network_nodes[2]

        retail.supplier = None
        entrepreneur.supplier = None

        with pytest.raises(ValidationError, match="Укажите поставщика"):
            retail.full_clean()

        with pytest.raises(ValidationError, match="Укажите поставщика"):
            entrepreneur.full_clean()

    def test_node_cannot_be_supplier_for_itself_on_update(self):
        """Проверяет невозможность ссылки на самого себя в поле поставщика при обновлении."""
        self.retail_net1_lv1.supplier = self.retail_net1_lv1
        with pytest.raises(
            ValidationError, match="Нельзя указывать себя в качестве поставщика"
        ):
            self.retail_net1_lv1.full_clean()

    def test_impossibility_delete_node_with_clients(self):
        """Проверяет невозможность удаления узла сети при наличии клиента."""
        factory_with_reseller = self.factory_net1_lv0
        with pytest.raises(ProtectedError):
            factory_with_reseller.delete()

    def test_supplier_cannot_be_level_2(self, contact_objects):
        """Проверяет невозможность выбора поставщика уровня иерархии 2."""
        node_on_level_2 = self.entrepreneur_net1_lv2
        with pytest.raises(ValidationError):
            NetworkNode.objects.create(
                name="Розничная сеть",
                node_type="retail",
                supplier=node_on_level_2,
            )

    def test_can_change_supplier_with_zero_debt(self):
        """Проверяет возможность изменения поставщика при нулевой задолженности."""
        factory = self.factory_net1_lv0
        entrepreneur = self.entrepreneur_net1_lv2

        entrepreneur.supplier_debt = 0
        entrepreneur.save()

        entrepreneur.supplier = factory
        entrepreneur.save()

        assert entrepreneur.supplier == factory
        assert entrepreneur.level == 1

    def test_cannot_change_supplier_with_debt(self):
        """Проверяет невозможность изменения поставщика при ненулевой задолженности."""
        factory = self.factory_net1_lv0
        entrepreneur = self.entrepreneur_net1_lv2

        entrepreneur.supplier = factory
        with pytest.raises(
            ValidationError,
            match="Нельзя изменить поставщика при наличии задолженности",
        ):
            entrepreneur.full_clean()

    def test_cannot_change_supplier_if_exceeds_max_level(self):
        """Проверяет невозможность изменения поставщика при превышении максимальной глубины иерархии."""
        retail_on_level_1 = self.retail_net1_lv1
        new_retail = NetworkNode.objects.create(
            name="Розничная сеть",
            node_type="retail",
            supplier=self.factory_net1_lv0,
        )
        NetworkNode.objects.create(
            name="ИП Иванов",
            node_type="entrepreneur",
            supplier=new_retail,
        )

        new_retail.supplier = retail_on_level_1

        with pytest.raises(
            ValidationError,
            match="это приводит к превышению глубины 3-х уровневой иерархии",
        ):
            new_retail.full_clean()

    def test_cannot_change_supplier_without_required_products(self, contact_objects):
        """Проверяет невозможность изменения поставщика, если у него нет продуктов, требуемых перепродавцам."""
        factory_without_products = NetworkNode.objects.create(
            name="Новый завод", node_type="factory"
        )
        retail_with_client = self.retail_net1_lv1
        retail_with_client.supplier_debt = 0
        retail_with_client.save()
        retail_with_client.supplier = factory_without_products
        with pytest.raises(ValidationError, match="нет необходимых продуктов"):
            retail_with_client.full_clean()
