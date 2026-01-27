from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet

from network.filters import NetworkNodeFilter
from network.models import NetworkNode
from network.serializers import NetworkNodeWriteSerializer, NetworkNodeReadSerializer


class NetworkNodeViewSet(ModelViewSet):
    queryset = NetworkNode.objects.all()
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_class = NetworkNodeFilter

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return NetworkNodeWriteSerializer
        return NetworkNodeReadSerializer
