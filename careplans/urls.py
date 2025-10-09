# careplans/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CarePlanTemplateViewSet, GoalTemplateViewSet, ActionTemplateViewSet,
    CarePlanViewSet, CarePlanGoalViewSet, CarePlanActionViewSet,
    CarePlanReviewViewSet, CarePlanActivityEventViewSet,
    MyCarePlansView,
)

router = DefaultRouter()
router.register(r"templates/careplans", CarePlanTemplateViewSet, basename="careplan-template")
router.register(r"templates/goals", GoalTemplateViewSet, basename="goal-template")
router.register(r"templates/actions", ActionTemplateViewSet, basename="action-template")

router.register(r"careplans", CarePlanViewSet, basename="careplan")
router.register(r"goals", CarePlanGoalViewSet, basename="careplan-goal")
router.register(r"actions", CarePlanActionViewSet, basename="careplan-action")
router.register(r"reviews", CarePlanReviewViewSet, basename="careplan-review")
router.register(r"events", CarePlanActivityEventViewSet, basename="careplan-activity-event")

urlpatterns = [
    path("careplans/my/", MyCarePlansView.as_view(), name="my-careplans"),
    path("", include(router.urls))
]
