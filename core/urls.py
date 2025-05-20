from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, healthcheck

router = DefaultRouter()
router.register("services", ServiceViewSet, basename="services")

urlpatterns = [
    path("", include(router.urls)),
    path("healthcheck/", healthcheck),
]
