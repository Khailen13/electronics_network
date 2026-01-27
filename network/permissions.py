from rest_framework import permissions


class IsActiveEmployee(permissions.BasePermission):
    """Разрешение прав доступа только активным пользователям."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_active
        )
