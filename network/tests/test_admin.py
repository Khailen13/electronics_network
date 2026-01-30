import pytest


@pytest.mark.django_db
class TestAdminPanel:
    """Базовые тесты админ-панели."""

    def test_admin_panel_accessible(self, admin_client):
        """Проверяет доступность админ-панели."""
        response = admin_client.get("/admin/")
        assert response.status_code == 200

    def test_network_node_admin_list(self, admin_client, network_nodes):
        """Проверяет отображение списка звеньев в админ-панели."""
        node_name = network_nodes[0].name
        response = admin_client.get("/admin/network/networknode/")
        assert response.status_code == 200
        assert node_name in response.content.decode("utf-8")

    def test_contact_admin_list(self, admin_client, contact_objects):
        """Проверяет отображение списка контактов в админ-панели."""
        contact_email = contact_objects[0].email
        response = admin_client.get("/admin/network/contact/")
        assert response.status_code == 200
        assert contact_email in response.content.decode("utf-8")

    def test_product_admin_list(self, admin_client, product_objects):
        """Проверяет отображение списка продуктов в админ-панели."""
        product_name = product_objects[0].name
        response = admin_client.get("/admin/network/product/")
        assert response.status_code == 200
        assert product_name in response.content.decode("utf-8")


@pytest.mark.django_db
def test_clear_debt_action(admin_client, network_nodes):
    """Проверяет очистку задолженности перед поставщиком."""
    retail = network_nodes[1]

    assert retail.supplier_debt > 0

    response = admin_client.post(
        "/admin/network/networknode/",
        {"action": "clear_debt", "_selected_action": [retail.id]},
        follow=True,
    )
    assert response.status_code == 200

    retail.refresh_from_db()
    assert retail.supplier_debt == 0
