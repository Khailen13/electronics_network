import pytest
from rest_framework.test import APIRequestFactory
from network.permissions import IsActiveEmployee


@pytest.mark.django_db
def test_is_active_employee_permission_active_user(active_user):
    """Проверяет разрешение доступа у активного пользователя."""
    permission = IsActiveEmployee()
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = active_user

    assert permission.has_permission(request, None) is True


@pytest.mark.django_db
def test_is_active_employee_permission_inactive_user(inactive_user):
    """Проверяет разрешение доступа у неактивного пользователя."""
    permission = IsActiveEmployee()
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = inactive_user

    assert permission.has_permission(request, None) is False


@pytest.mark.django_db
def test_is_active_employee_permission_inactive_user():
    """Проверяет разрешение доступа у анонимного пользователя."""
    permission = IsActiveEmployee()
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = None

    assert permission.has_permission(request, None) is False
