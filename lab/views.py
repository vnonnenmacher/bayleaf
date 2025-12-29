import uuid

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from lab.models import (
    AllowedStateTransition,
    Analyte,
    AnalyteCode,
    AnalyteResult,
    Exam,
    ExamField,
    ExamFieldResult,
    ExamRequest,
    ExamVersion,
    Equipment,
    EquipmentGroup,
    MeasurementUnit,
    Sample,
    SampleState,
    SampleStateTransition,
    SampleType,
    Tag,
)
from lab.exam_processing.injector import AnalyteResultInjector
from lab.helpers.exam_request_helper import ExamRequestHelper
from lab.serializers import (
    AnalyteCodeSerializer,
    AnalyteResultSerializer,
    AnalyteSerializer,
    ExamFieldResultSerializer,
    ExamFieldSerializer,
    ExamRequestCancelSerializer,
    ExamRequestSerializer,
    ExamSerializer,
    ExamVersionSerializer,
    EquipmentGroupSerializer,
    EquipmentSerializer,
    MeasurementUnitSerializer,
    SampleSerializer,
    SampleStateSerializer,
    SampleTypeSerializer,
    TagSerializer,
)
from professionals.models import Professional
from professionals.permissions import IsProfessional


class SampleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def request_sample(self, request):
        serializer = SampleSerializer(data=request.data)
        if serializer.is_valid():
            sample = serializer.save()
            requested_state = SampleState.objects.get(is_initial_state=True)
            transition = SampleStateTransition.objects.create(
                sample=sample,
                previous_state=None,
                new_state=requested_state,
                changed_by=request.user
            )
            transition.transaction_hash = uuid.uuid4().hex  # Simulate blockchain hash
            transition.blockchain_timestamp = transition.created_at
            transition.is_verified = True
            transition.save()
            return Response(
                {
                    "message": "Sample requested successfully",
                    "sample_id": sample.id,
                    "transaction_hash": transition.transaction_hash,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def update_sample_state(self, request, pk=None):
        sample = self.get_object()
        new_state_id = request.data.get("new_state_id")

        if not new_state_id:
            return Response({"error": "new_state_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_state = SampleState.objects.get(id=new_state_id)
        except SampleState.DoesNotExist:
            return Response({"error": "New state does not exist."}, status=status.HTTP_404_NOT_FOUND)

        # Get the current state of the sample (latest transition)
        latest_transition = sample.state_transitions.order_by("-created_at").first()
        if not latest_transition:
            return Response({"error": "Sample has no state history."}, status=status.HTTP_400_BAD_REQUEST)

        current_state = latest_transition.new_state

        # Check if the transition is allowed
        is_allowed = AllowedStateTransition.objects.filter(
            from_state=current_state,
            to_state=new_state
        ).exists()

        if not is_allowed:
            return Response({
                "error": f"Transition from '{current_state.name}' to '{new_state.name}' is not allowed."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create the new transition
        new_transition = SampleStateTransition.objects.create(
            sample=sample,
            previous_state=current_state,
            new_state=new_state,
            changed_by=request.user,
            transaction_hash=uuid.uuid4().hex,
            blockchain_timestamp=None,  # Simulate blockchain timestamp
            is_verified=True
        )

        return Response({
            "message": "Sample state updated successfully.",
            "sample_id": sample.id,
            "new_state": new_state.name,
            "transaction_hash": new_transition.transaction_hash
        }, status=status.HTTP_200_OK)


class SampleTypeViewSet(viewsets.ModelViewSet):
    queryset = SampleType.objects.all()
    serializer_class = SampleTypeSerializer
    permission_classes = [IsAuthenticated]


class SampleStateViewSet(viewsets.ModelViewSet):
    queryset = SampleState.objects.all()
    serializer_class = SampleStateSerializer
    permission_classes = [IsAuthenticated]


class MeasurementUnitViewSet(viewsets.ModelViewSet):
    queryset = MeasurementUnit.objects.all()
    serializer_class = MeasurementUnitSerializer
    permission_classes = [IsProfessional]


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsProfessional]


class ExamVersionViewSet(viewsets.ModelViewSet):
    queryset = ExamVersion.objects.all()
    serializer_class = ExamVersionSerializer
    permission_classes = [IsProfessional]


class ExamFieldViewSet(viewsets.ModelViewSet):
    queryset = ExamField.objects.all()
    serializer_class = ExamFieldSerializer
    permission_classes = [IsProfessional]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProfessional]


class ExamRequestViewSet(viewsets.ModelViewSet):
    queryset = ExamRequest.objects.select_related("patient", "requested_by").all()
    serializer_class = ExamRequestSerializer
    permission_classes = [IsProfessional]
    http_method_names = ["get", "post", "patch", "put", "head", "options"]

    @action(detail=True, methods=["post"], permission_classes=[IsProfessional])
    def cancel(self, request, pk=None):
        exam_request = self.get_object()
        serializer = ExamRequestCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        professional = Professional.objects.get(id=request.user.id)
        helper = ExamRequestHelper()
        try:
            helper.cancel_exam_request(
                exam_request=exam_request,
                canceled_by=professional,
                reason=serializer.validated_data.get("cancel_reason"),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ExamRequestSerializer(exam_request).data, status=status.HTTP_200_OK)


class ExamFieldResultViewSet(viewsets.ModelViewSet):
    queryset = ExamFieldResult.objects.all()
    serializer_class = ExamFieldResultSerializer
    permission_classes = [IsProfessional]


class EquipmentGroupViewSet(viewsets.ModelViewSet):
    queryset = EquipmentGroup.objects.all()
    serializer_class = EquipmentGroupSerializer
    permission_classes = [IsProfessional]


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsProfessional]


class AnalyteViewSet(viewsets.ModelViewSet):
    queryset = Analyte.objects.all()
    serializer_class = AnalyteSerializer
    permission_classes = [IsProfessional]


class AnalyteCodeViewSet(viewsets.ModelViewSet):
    queryset = AnalyteCode.objects.all()
    serializer_class = AnalyteCodeSerializer
    permission_classes = [IsProfessional]


class AnalyteResultViewSet(viewsets.ModelViewSet):
    queryset = AnalyteResult.objects.all()
    serializer_class = AnalyteResultSerializer
    permission_classes = [IsProfessional]

    @action(detail=False, methods=["post"], permission_classes=[IsProfessional])
    def inject(self, request):
        equipment_code = request.data.get("equipment_code")
        analyte_code = request.data.get("analyte_code")
        raw_result = request.data.get("raw_result")
        sample_id = request.data.get("sample_id")
        numeric_value = request.data.get("numeric_value")
        units_code = request.data.get("units_code")
        metadata = request.data.get("metadata")

        injector = AnalyteResultInjector()
        try:
            analyte_result = injector.inject(
                equipment_code=equipment_code,
                analyte_code=analyte_code,
                raw_result=raw_result,
                sample_id=sample_id,
                numeric_value=numeric_value,
                units_code=units_code,
                metadata=metadata,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AnalyteResultSerializer(analyte_result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
