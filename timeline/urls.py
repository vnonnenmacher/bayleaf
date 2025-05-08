from django.urls import path
from .views import PatientTimelineView

urlpatterns = [
    path('timeline/', PatientTimelineView.as_view(), name='patient-timeline'),
]
