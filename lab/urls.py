from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnalyteCodeViewSet,
    AnalyteResultViewSet,
    AnalyteViewSet,
    ExamFieldResultViewSet,
    ExamFieldViewSet,
    ExamRequestViewSet,
    ExamVersionViewSet,
    ExamViewSet,
    EquipmentGroupViewSet,
    EquipmentViewSet,
    MeasurementUnitViewSet,
    SampleStateViewSet,
    SampleTypeViewSet,
    SampleViewSet,
    TagViewSet,
)

# Create a router and register the SampleViewSet
router = DefaultRouter()
router.register(r'samples', SampleViewSet, basename='sample')
router.register(r'sample-types', SampleTypeViewSet, basename='sampletype')
router.register(r'sample-states', SampleStateViewSet, basename='samplestate')
router.register(r'measurement-units', MeasurementUnitViewSet, basename='measurementunit')
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'exam-versions', ExamVersionViewSet, basename='examversion')
router.register(r'exam-fields', ExamFieldViewSet, basename='examfield')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'exam-requests', ExamRequestViewSet, basename='examrequest')
router.register(r'exam-field-results', ExamFieldResultViewSet, basename='examfieldresult')
router.register(r'equipment-groups', EquipmentGroupViewSet, basename='equipmentgroup')
router.register(r'equipments', EquipmentViewSet, basename='equipment')
router.register(r'analytes', AnalyteViewSet, basename='analyte')
router.register(r'analyte-codes', AnalyteCodeViewSet, basename='analytecode')
router.register(r'analyte-results', AnalyteResultViewSet, basename='analyteresult')

urlpatterns = [
    path('', include(router.urls)),
]
