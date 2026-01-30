import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from faker import Faker

from network.models import Contact, NetworkNode, Product


class Command(BaseCommand):
    help = "Создает демонстрационные данные для торговых сетей"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Общее количество создаваемых торговых сетей",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Очистить старые данные перед созданием",
        )

    def handle(self, *args, **options):
        fake = Faker("ru_RU")
        count = options["count"]
        clear = options["clear"]

        if clear:
            self.stdout.write("Очистка старых данных...")
            Contact.objects.all().delete()
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM network_networknode_products;")

            with connection.cursor() as cursor:
                cursor.execute("UPDATE network_networknode SET supplier_id = NULL;")

            NetworkNode.objects.all().delete()
            Product.objects.all().delete()

            self.stdout.write("Старые данные очищены.")

        self.stdout.write("Создание демонстрационных данных...")

        product_names = [
            "Смартфон",
            "Ноутбук",
            "Монитор",
            "Планшет",
            "Динамики",
            "Утюг",
            "Пылесос",
            "Микроволновая печь",
            "Тостер",
            "Кофемашина",
            "Стиральная машина",
            "Телевизор",
        ]

        for i in range(count):
            products = []
            for _ in range(random.randint(2, 4)):
                product = Product.objects.create(
                    name=random.choice(product_names),
                    model=f"MDL-{random.randint(1, 999)}",
                    release_date=fake.date_between(start_date="-3y", end_date="today"),
                )
                products.append(product)

            factory = self.create_node(fake, supplier=None, products=products)

            node_level1 = self.create_node(fake, supplier=factory, products=products)

            if node_level1:
                self.create_node(fake, supplier=node_level1, products=products)

            if (i + 1) % 5 == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Успешно созданы данные для {i + 1}/{count} сетей."
                    )
                )

        self.stdout.write(
            self.style.SUCCESS("Создание демонстрационных данных успешно завершено.")
        )

    def create_contact(self, fake, node):
        """Создает контакты для демонстрации."""

        contact = Contact.objects.create(
            email=fake.email(),
            country=random.choice(["Россия", "Беларусь", "Казахстан"]),
            city=fake.city(),
            street=fake.street_name(),
            building_number=fake.building_number(),
            network_node=node,
        )
        return contact

    def create_node(self, fake, supplier, products):
        """Создает звено демонстрационной торговой сети"""

        if supplier:
            node_type = random.choice(["retail", "entrepreneur", None])
        else:
            node_type = "factory"

        if node_type is None:
            return None

        if node_type == "factory":
            name = f"Завод {fake.company()}"
        elif node_type == "retail":
            name = f"Сеть {fake.company()}"
        else:
            name = f"ИП {fake.last_name()}"

        supplier_debt = Decimal("0.00")
        if node_type != "factory":
            supplier_debt = Decimal(str(round(random.uniform(10_000, 300_000), 2)))

        node = NetworkNode.objects.create(
            name=name,
            node_type=node_type,
            supplier=supplier,
            supplier_debt=supplier_debt,
        )
        node.products.set(products)
        self.create_contact(fake, node)

        return node
