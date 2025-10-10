from __future__ import annotations

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema

from professionals.models import Professional
from .models import (
    CarePlanTemplate, GoalTemplate, ActionTemplate,
    CarePlan, CarePlanGoal, CarePlanAction, CarePlanReview, CarePlanActivityEvent,
)
from .serializers import (
    CarePlanTemplateSerializer, GoalTemplateSerializer, ActionTemplateSerializer,
    CarePlanSerializer, CarePlanDetailSerializer, CarePlanUpsertSerializer,
    CarePlanGoalSerializer, CarePlanActionSerializer, CarePlanActionReadSerializer,
    CarePlanReviewSerializer, CarePlanActivityEventSerializer,
)

from users.permissions import IsBayleafAPIToken
from professionals.permissions import IsProfessional
from patients.permissions import IsPatient


# ============================================================
# Care Plan Templates (Professionals & Agents: full CRUD)
# ============================================================
class CarePlanTemplateViewSet(viewsets.ModelViewSet):
    queryset = CarePlanTemplate.objects.all().select_related("created_by")
    serializer_class = CarePlanTemplateSerializer
    permission_classes = [IsProfessional | IsBayleafAPIToken]

    def perform_create(self, serializer):
        pro = Professional.objects.filter(user_ptr_id=self.request.user.id).first()
        serializer.save(created_by=pro)


class GoalTemplateViewSet(viewsets.ModelViewSet):
    queryset = GoalTemplate.objects.select_related("template")
    serializer_class = GoalTemplateSerializer
    permission_classes = [IsProfessional | IsBayleafAPIToken]


class ActionTemplateViewSet(viewsets.ModelViewSet):
    queryset = ActionTemplate.objects.select_related("template")
    serializer_class = ActionTemplateSerializer
    permission_classes = [IsProfessional | IsBayleafAPIToken]


# ============================================================
# Care Plans (Patients R/O; Professionals & Agents RW)
# ============================================================
class CarePlanViewSet(viewsets.ModelViewSet):
    """
    Patients: read-only, scoped to their own plans.
    Professionals & Agents: full CRUD.
    """
    permission_classes = [IsProfessional | IsPatient | IsBayleafAPIToken]

    def get_queryset(self):
        qs = CarePlan.objects.select_related("patient", "template", "owner").prefetch_related(
            "goals", "actions", "reviews"
        )
        user = self.request.user
        if IsProfessional().has_permission(self.request, self):
            return qs
        if IsPatient().has_permission(self.request, self):
            return qs.filter(patient__user_ptr_id=user.id)
        return qs.none()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CarePlanDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return CarePlanUpsertSerializer
        return CarePlanSerializer

    def _deny_patient_modification(self):
        return Response({"detail": "Patients cannot modify care plans."}, status=status.HTTP_403_FORBIDDEN)

    def create(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().destroy(request, *args, **kwargs)


# ============================================================
# Goals (Patients R/O; Professionals & Agents RW)
# ============================================================
class CarePlanGoalViewSet(viewsets.ModelViewSet):
    queryset = CarePlanGoal.objects.select_related("careplan", "template")
    serializer_class = CarePlanGoalSerializer
    permission_classes = [IsProfessional | IsPatient | IsBayleafAPIToken]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if IsProfessional().has_permission(self.request, self):
            return qs
        if IsPatient().has_permission(self.request, self):
            return qs.filter(careplan__patient__user_ptr_id=user.id)
        return qs.none()

    def _deny_patient_modification(self):
        return Response({"detail": "Patients cannot modify goals."}, status=status.HTTP_403_FORBIDDEN)

    def create(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().destroy(request, *args, **kwargs)


# ============================================================
# Actions (Patients R/O; Professionals & Agents RW)
# ============================================================
class CarePlanActionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsProfessional | IsPatient | IsBayleafAPIToken]

    def get_queryset(self):
        qs = CarePlanAction.objects.select_related(
            "careplan", "template", "assigned_to"
        ).prefetch_related("scheduled_events")
        user = self.request.user
        if IsProfessional().has_permission(self.request, self):
            return qs
        if IsPatient().has_permission(self.request, self):
            return qs.filter(careplan__patient__user_ptr_id=user.id)
        return qs.none()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return CarePlanActionReadSerializer
        return CarePlanActionSerializer

    def _deny_patient_modification(self):
        return Response({"detail": "Patients cannot modify actions."}, status=status.HTTP_403_FORBIDDEN)

    def create(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().destroy(request, *args, **kwargs)


# ============================================================
# Reviews (Professionals RW; Patients R/O)
# ============================================================
class CarePlanReviewViewSet(viewsets.ModelViewSet):
    queryset = CarePlanReview.objects.select_related("careplan", "reviewed_by")
    serializer_class = CarePlanReviewSerializer
    permission_classes = [IsProfessional | IsPatient | IsBayleafAPIToken]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if IsProfessional().has_permission(self.request, self):
            return qs
        if IsPatient().has_permission(self.request, self):
            return qs.filter(careplan__patient__user_ptr_id=user.id)
        return qs.none()

    def _deny_patient_modification(self):
        return Response({"detail": "Patients cannot modify reviews."}, status=status.HTTP_403_FORBIDDEN)

    def create(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self):
            return self._deny_patient_modification()
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        pro = Professional.objects.filter(user_ptr_id=self.request.user.id).first()
        serializer.save(reviewed_by=pro)

    def perform_update(self, serializer):
        pro = Professional.objects.filter(user_ptr_id=self.request.user.id).first()
        serializer.save(reviewed_by=pro)


# ============================================================
# Scheduled Events (Patients RW; Professionals & Agents RW)
# ============================================================
class CarePlanActivityEventViewSet(viewsets.ModelViewSet):
    """
    Patients can list & update their scheduled events (timed).
    Status transitions are validated by BaseEvent.update_status inside the serializer.
    """
    serializer_class = CarePlanActivityEventSerializer
    permission_classes = [IsProfessional | IsPatient | IsBayleafAPIToken]

    def get_queryset(self):
        qs = CarePlanActivityEvent.objects.select_related(
            "action", "action__careplan", "action__careplan__patient"
        )
        user = self.request.user
        if IsProfessional().has_permission(self.request, self):
            return qs
        if IsPatient().has_permission(self.request, self):
            return qs.filter(action__careplan__patient__user_ptr_id=user.id)
        return qs.none()


# ============================================================
# "My Plans" (expanded) for Patients; OBO handled automatically
# ============================================================
class MyCarePlansView(APIView):
    permission_classes = [IsPatient | IsBayleafAPIToken]

    @swagger_auto_schema(
        operation_description="Return the authenticated patient's care plans with goals, actions, and reviews.",
        responses={200: CarePlanDetailSerializer(many=True)}
    )
    def get(self, request):
        qs = CarePlan.objects.filter(patient__user_ptr_id=request.user.id).select_related(
            "patient", "template", "owner"
        ).prefetch_related(
            "goals",
            "actions__medication_detail",
            "actions__appointment_detail",
            "reviews",
        )
        data = CarePlanDetailSerializer(qs, many=True).data
        return Response(data)
