from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from network.filters import NetworkNodeFilter
from network.models import NetworkNode
from network.permissions import IsActiveEmployee
from network.serializers import NetworkNodeWriteSerializer, NetworkNodeReadSerializer
from django.db.models import ProtectedError


class NetworkNodeViewSet(ModelViewSet):
    queryset = NetworkNode.objects.all()
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_class = NetworkNodeFilter
    permission_classes = [IsAuthenticated, IsActiveEmployee]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return NetworkNodeWriteSerializer
        return NetworkNodeReadSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "Нельзя удалить узел, который является поставщиком для других узлов"},
                status=status.HTTP_400_BAD_REQUEST
            )
