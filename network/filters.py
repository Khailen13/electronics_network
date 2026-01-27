import django_filters
from network.models import NetworkNode

class NetworkNodeFilter(django_filters.FilterSet):
    country = django_filters.CharFilter(
        field_name="contact__country",
        lookup_expr="icontains"
    )

    class Meta:
        model = NetworkNode
        fields = []

