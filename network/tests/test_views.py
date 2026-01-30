import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_api_requires_auth():
    """Проверяет невозможность взаимодействия по API без аутентификации."""
    client = APIClient()
    response = client.get("/api/network-nodes/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_api_requires_active_user(active_user, inactive_user):
    """Проверяет невозможность взаимодействия по API у неактивных сотрудников."""
    client = APIClient()

    client.force_authenticate(user=inactive_user)
    response = client.get("/api/network-nodes/")
    assert response.status_code == 403

    client.force_authenticate(user=active_user)
    response = client.get("/api/network-nodes/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_api_filter_by_country(active_user, network_nodes):
    """Проверяет фильтрацию по стране."""
    node = network_nodes[0]
    node.contact.country = "Искомая"
    node.contact.save()

    client = APIClient()
    client.force_authenticate(user=active_user)

    response = client.get("/api/network-nodes/?country=Искомая")

    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.django_db
def test_api_detail_view(active_user, network_nodes):
    """Проверяет получение детальной информации."""
    node = network_nodes[0]

    client = APIClient()
    client.force_authenticate(user=active_user)

    response = client.get(f"/api/network-nodes/{node.id}/")

    assert response.status_code == 200
    assert response.data["name"] == node.name


@pytest.mark.django_db
def test_cannot_update_debt_through_api(active_user, network_nodes):
    """Проверяет невозможность обновления задолженности перед поставщиком по API."""
    node = network_nodes[1]

    client = APIClient()
    client.force_authenticate(user=active_user)

    response = client.patch(
        f"/api/network-nodes/{node.id}/", {"supplier_debt": 0}, format="json"
    )

    assert response.status_code == 400
    assert "supplier_debt" in response.data
