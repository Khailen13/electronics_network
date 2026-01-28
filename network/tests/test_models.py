from datetime import date, timedelta

from django.core.exceptions import ValidationError
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
        with pytest.raises(ValidationError, match="Продаваемая продукция уже должна быть выпущена."):
            Product.objects.create(
                name="Продукт",
                model="Модель",
                release_date=future_date
            )

    def test_release_date_today(self):
        """Проверка при попытке назначить сегодняшнюю дату релиза."""
        today = timezone.now().date()
        product = Product.objects.create(
            name="Продукт",
            model="Модель",
            release_date=today
        )
        assert product.release_date == today

