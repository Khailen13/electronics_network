import pytest

from network.filters import NetworkNodeFilter
from network.models import NetworkNode


@pytest.mark.django_db
def test_network_node_filter_by_country(network_nodes):
    """Проверяет фильтрацию по стране."""
    factory, retail, entrepreneur = network_nodes

    factory.contact.country = "Россия"
    retail.contact.country = "Беларусь"
    entrepreneur.contact.country = "Россия"

    factory.contact.save()
    retail.contact.save()
    entrepreneur.contact.save()

    filterset = NetworkNodeFilter(
        data={"country": "Россия"}, queryset=NetworkNode.objects.all()
    )

    result = filterset.qs
    assert factory in result
    assert entrepreneur in result
    assert retail not in result


@pytest.mark.django_db
def test_network_node_filter_insensitive(network_nodes):
    """Проверяет регистронезависимость фильтрацию."""
    factory, retail, entrepreneur = network_nodes

    factory = network_nodes[0]
    factory.contact.country = "Россия"
    factory.contact.save()

    filterset = NetworkNodeFilter(
        data={"country": "россия"}, queryset=NetworkNode.objects.all()
    )

    assert factory in filterset.qs
