# careplans/views.py
from __future__ import annotations

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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


from professionals.permissions import IsProfessional, IsAgentOrProfessional

from patients.permissions import IsPatient


# ============================================================
# Care Plan Templates (Professionals & Agents: full CRUD)
# ============================================================
class CarePlanTemplateViewSet(viewsets.ModelViewSet):
    queryset = CarePlanTemplate.objects.all().select_related("created_by")
    serializer_class = CarePlanTemplateSerializer
    permission_classes = [IsAgentOrProfessional]

    @swagger_auto_schema(
        operation_description="List care plan templates.",
        responses={200: CarePlanTemplateSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new care plan template.",
        request_body=CarePlanTemplateSerializer,
        responses={201: CarePlanTemplateSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a care plan template.",
        responses={200: CarePlanTemplateSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a care plan template.",
        request_body=CarePlanTemplateSerializer,
        responses={200: CarePlanTemplateSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a care plan template.",
        request_body=CarePlanTemplateSerializer,
        responses={200: CarePlanTemplateSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a care plan template.",
        responses={204: "Deleted"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        pro = Professional.objects.filter(user_ptr_id=self.request.user.id).first()
        serializer.save(created_by=pro)


class GoalTemplateViewSet(viewsets.ModelViewSet):
    queryset = GoalTemplate.objects.select_related("template")
    serializer_class = GoalTemplateSerializer
    permission_classes = [IsAgentOrProfessional]

    @swagger_auto_schema(operation_description="List goal templates.",
                         responses={200: GoalTemplateSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Create a goal template.",
                         request_body=GoalTemplateSerializer,
                         responses={201: GoalTemplateSerializer})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a goal template.",
                         responses={200: GoalTemplateSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update a goal template.",
                         request_body=GoalTemplateSerializer,
                         responses={200: GoalTemplateSerializer})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Partially update a goal template.",
                         request_body=GoalTemplateSerializer,
                         responses={200: GoalTemplateSerializer})
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete a goal template.", responses={204: "Deleted"})
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ActionTemplateViewSet(viewsets.ModelViewSet):
    queryset = ActionTemplate.objects.select_related("template")
    serializer_class = ActionTemplateSerializer
    permission_classes = [IsAgentOrProfessional]

    @swagger_auto_schema(operation_description="List action templates.",
                         responses={200: ActionTemplateSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Create an action template.",
                         request_body=ActionTemplateSerializer,
                         responses={201: ActionTemplateSerializer})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve an action template.",
                         responses={200: ActionTemplateSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update an action template.",
                         request_body=ActionTemplateSerializer,
                         responses={200: ActionTemplateSerializer})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Partially update an action template.",
                         request_body=ActionTemplateSerializer,
                         responses={200: ActionTemplateSerializer})
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete an action template.", responses={204: "Deleted"})
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ============================================================
# Care Plans (Patients R/O; Professionals & Agents RW)
# ============================================================
class CarePlanViewSet(viewsets.ModelViewSet):
    """
    Patients: read-only, scoped to their own plans.
    Professionals & Agents: full CRUD.
    """
    permission_classes = [IsAgentOrProfessional | IsPatient]

    def get_queryset(self):
        qs = CarePlan.objects.all()\
            .select_related("patient", "template", "owner")\
            .prefetch_related("goals", "actions", "reviews")
        user = self.request.user
        if IsBayleafAPIToken().has_permission(self.request, self):
            return qs
        if IsProfessional().has_permission(self.request, self):
            return qs
        if IsPatient().has_permission(self.request, self):
            return qs.filter(patient__user_ptr_id=user.id)
        return qs.none()

    def get_serializer_class(self):
        if self.action in ("retrieve",):
            return CarePlanDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return CarePlanUpsertSerializer
        return CarePlanSerializer

    # ---- Swagger for actions ----
    @swagger_auto_schema(operation_description="List care plans.",
                         responses={200: CarePlanSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Create a care plan (Pro/Agent).",
                         request_body=CarePlanUpsertSerializer,
                         responses={201: CarePlanSerializer})
    def create(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot create care plans."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a care plan (expanded).",
                         responses={200: CarePlanDetailSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update a care plan (Pro/Agent).",
                         request_body=CarePlanUpsertSerializer,
                         responses={200: CarePlanSerializer})
    def update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot update care plans."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Partially update a care plan (Pro/Agent).",
                         request_body=CarePlanUpsertSerializer,
                         responses={200: CarePlanSerializer})
    def partial_update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot update care plans."}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete a care plan (Pro/Agent).",
                         responses={204: "Deleted"})
    def destroy(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot delete care plans."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


# ============================================================
# Goals (Patients R/O; Professionals & Agents RW)
# ============================================================
class CarePlanGoalViewSet(viewsets.ModelViewSet):
    queryset = CarePlanGoal.objects.select_related("careplan", "template")
    serializer_class = CarePlanGoalSerializer
    permission_classes = [IsAgentOrProfessional | IsPatient]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if IsBayleafAPIToken().has_permission(self.request, self) or IsProfessional().has_permission(self.request, self):
            return qs
        if IsPatient().has_permission(self.request, self):
            return qs.filter(careplan__patient__user_ptr_id=user.id)
        return qs.none()

    @swagger_auto_schema(operation_description="List goals.",
                         responses={200: CarePlanGoalSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Create a goal (Pro/Agent).",
                         request_body=CarePlanGoalSerializer,
                         responses={201: CarePlanGoalSerializer})
    def create(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot create goals."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a goal.",
                         responses={200: CarePlanGoalSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update a goal (Pro/Agent).",
                         request_body=CarePlanGoalSerializer,
                         responses={200: CarePlanGoalSerializer})
    def update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot update goals."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Partially update a goal (Pro/Agent).",
                         request_body=CarePlanGoalSerializer,
                         responses={200: CarePlanGoalSerializer})
    def partial_update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot update goals."}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete a goal (Pro/Agent).",
                         responses={204: "Deleted"})
    def destroy(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot delete goals."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


# ============================================================
# Actions (Patients R/O; Professionals & Agents RW)
# ============================================================
class CarePlanActionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAgentOrProfessional | IsPatient]

    def get_queryset(self):
        qs = CarePlanAction.objects.select_related(
            "careplan", "template", "assigned_to"
        ).prefetch_related(
            "scheduled_events"
        )
        user = self.request.user
        if IsBayleafAPIToken().has_permission(self.request, self) or IsProfessional().has_permission(self.request, self):
            return qs
        if IsPatient().has_permission(self.request, self):
            return qs.filter(careplan__patient__user_ptr_id=user.id)
        return qs.none()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return CarePlanActionReadSerializer
        return CarePlanActionSerializer

    @swagger_auto_schema(operation_description="List actions.",
                         responses={200: CarePlanActionReadSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Create an action (Pro/Agent).",
                         request_body=CarePlanActionSerializer,
                         responses={201: CarePlanActionReadSerializer})
    def create(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot create actions."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve an action (expanded details).",
                         responses={200: CarePlanActionReadSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update an action (Pro/Agent).",
                         request_body=CarePlanActionSerializer,
                         responses={200: CarePlanActionReadSerializer})
    def update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot update actions."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Partially update an action (Pro/Agent).",
                         request_body=CarePlanActionSerializer,
                         responses={200: CarePlanActionReadSerializer})
    def partial_update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot update actions."}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete an action (Pro/Agent).",
                         responses={204: "Deleted"})
    def destroy(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot delete actions."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


# ============================================================
# Reviews (Patients R/O; Professionals & Agents RW)
# ============================================================
class CarePlanReviewViewSet(viewsets.ModelViewSet):
    queryset = CarePlanReview.objects.select_related("careplan", "reviewed_by")
    serializer_class = CarePlanReviewSerializer
    # Reviews are professional-only
    permission_classes = [IsProfessional]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if IsBayleafAPIToken().has_permission(self.request, self) or IsProfessional().has_permission(self.request, self):
            return qs
        if IsPatient().has_permission(self.request, self):
            return qs.filter(careplan__patient__user_ptr_id=user.id)
        return qs.none()

    @swagger_auto_schema(operation_description="List reviews.",
                         responses={200: CarePlanReviewSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Create a review (Pro/Agent).",
                         request_body=CarePlanReviewSerializer,
                         responses={201: CarePlanReviewSerializer})
    def create(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot create reviews."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a review.",
                         responses={200: CarePlanReviewSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update a review (Pro/Agent).",
                         request_body=CarePlanReviewSerializer,
                         responses={200: CarePlanReviewSerializer})
    def update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot update reviews."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Partially update a review (Pro/Agent).",
                         request_body=CarePlanReviewSerializer,
                         responses={200: CarePlanReviewSerializer})
    def partial_update(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot update reviews."}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete a review (Pro/Agent).",
                         responses={204: "Deleted"})
    def destroy(self, request, *args, **kwargs):
        if IsPatient().has_permission(request, self) and not IsProfessional().has_permission(request, self) \
           and not IsBayleafAPIToken().has_permission(request, self):
            return Response({"detail": "Patients cannot delete reviews."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        # reviewer = the Professional making the call
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
    permission_classes = [IsAgentOrProfessional | IsPatient]

    def get_queryset(self):
        qs = CarePlanActivityEvent.objects.select_related(
            "action", "action__careplan", "action__careplan__patient"
        )
        user = self.request.user
        if IsBayleafAPIToken().has_permission(self.request, self) or IsProfessional().has_permission(self.request, self):
            return qs
        if IsPatient().has_permission(self.request, self):
            return qs.filter(action__careplan__patient__user_ptr_id=user.id)
        return qs.none()

    @swagger_auto_schema(operation_description="List scheduled events.",
                         responses={200: CarePlanActivityEventSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Create a scheduled event.",
                         request_body=CarePlanActivityEventSerializer,
                         responses={201: CarePlanActivityEventSerializer})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a scheduled event.",
                         responses={200: CarePlanActivityEventSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update a scheduled event (status transitions allowed).",
                         request_body=CarePlanActivityEventSerializer,
                         responses={200: CarePlanActivityEventSerializer})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Partially update a scheduled event (status transitions allowed).",
                         request_body=CarePlanActivityEventSerializer,
                         responses={200: CarePlanActivityEventSerializer})
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete a scheduled event.",
                         responses={204: "Deleted"})
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ============================================================
# "My Plans" (expanded) for Patients; Agents can pass patient_id
# ============================================================
class MyCarePlansView(APIView):
    permission_classes = [IsBayleafAPIToken | IsPatient]

    @swagger_auto_schema(
        operation_description=(
            "Return the authenticated patient's care plans with goals, actions, and reviews. "
            "Agents can fetch for a specific patient via `?patient_id=<uuid>`."
        ),
        manual_parameters=[
            openapi.Parameter(
                name="patient_id",
                in_=openapi.IN_QUERY,
                description="Patient UUID (agents only). If omitted, patient gets their own plans.",
                required=False,
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
            ),
        ],
        responses={200: CarePlanDetailSerializer(many=True)}
    )
    def get(self, request):
        qs = CarePlan.objects.filter(patient__user_ptr_id=request.user.id)

        qs = qs.select_related("patient", "template", "owner").prefetch_related(
            "goals",
            "actions__medication_detail",
            "actions__appointment_detail",
            "reviews",
        )
        data = CarePlanDetailSerializer(qs, many=True).data
        return Response(data)
