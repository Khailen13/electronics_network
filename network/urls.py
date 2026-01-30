from rest_framework.routers import DefaultRouter

from network.views import NetworkNodeViewSet

app_name = "network"

router = DefaultRouter()
router.register(r"network-nodes", NetworkNodeViewSet, basename="network-node")

urlpatterns = router.urls
