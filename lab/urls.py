from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SampleStateViewSet, SampleTypeViewSet, SampleViewSet

# Create a router and register the SampleViewSet
router = DefaultRouter()
router.register(r'samples', SampleViewSet, basename='sample')
router.register(r'sample-types', SampleTypeViewSet, basename='sampletype')
router.register(r'sample-states', SampleStateViewSet, basename='samplestate')

urlpatterns = [
    path('', include(router.urls)),
]
