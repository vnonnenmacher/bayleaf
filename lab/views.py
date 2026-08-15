import uuid

from django.db.models import Prefetch
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
    RequestedExam,
    Sample,
    Sector,
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
    SectorSerializer,
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

    @staticmethod
    def _parse_bool(value):
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "y"}:
            return True
        if normalized in {"0", "false", "no", "n"}:
            return False
        return None

    @staticmethod
    def _parse_list_param(params, key):
        raw_values = params.getlist(key)
        values = []
        for raw in raw_values:
            values.extend(item.strip() for item in raw.split(",") if item.strip())
        return values

    @staticmethod
    def _build_exam_payload(requested_exam):
        exam = requested_exam.exam_version.exam
        return {
            "requested_exam_id": requested_exam.id,
            "is_completed": requested_exam.is_completed,
            "exam_version_id": requested_exam.exam_version.id,
            "exam": {
                "id": exam.id,
                "code": exam.code,
                "name": exam.name,
                "sector": None,
            },
        }

    @staticmethod
    def _build_request_payload(exam_request):
        validated_by = exam_request.validated_by
        requested_by = exam_request.requested_by
        birth_date = exam_request.patient.birth_date
        return {
            "id": exam_request.id,
            "code": exam_request.code,
            "notes": exam_request.notes,
            "created_at": exam_request.created_at.isoformat() if exam_request.created_at else None,
            "updated_at": exam_request.updated_at.isoformat() if exam_request.updated_at else None,
            "is_validated": exam_request.is_validated,
            "validated_by": None if validated_by is None else {
                "id": validated_by.pk,
                "full_name": validated_by.full_name,
            },
            "requested_by": {
                "id": requested_by.pk,
                "full_name": requested_by.full_name,
            },
            "patient": {
                "pid": exam_request.patient.pid,
                "first_name": exam_request.patient.first_name,
                "last_name": exam_request.patient.last_name,
                "birth_date": birth_date.isoformat() if birth_date else None,
            },
        }

    @action(detail=False, methods=["get"], url_path="search-exam-requests", permission_classes=[IsProfessional])
    def search_exam_requests(self, request):
        code = (request.query_params.get("code") or "").strip()
        is_validated = self._parse_bool(request.query_params.get("is_validated"))
        is_completed = self._parse_bool(request.query_params.get("is_completed"))

        sample_state_ids_raw = self._parse_list_param(request.query_params, "sample_status")
        sample_state_names = {name.lower() for name in self._parse_list_param(request.query_params, "sample_status_name")}
        sample_state_ids = set()
        for value in sample_state_ids_raw:
            try:
                sample_state_ids.add(int(value))
            except ValueError:
                continue

        queryset = self.get_queryset().select_related(
            "patient",
            "requested_by",
            "validated_by",
        )

        if code:
            queryset = queryset.filter(code__icontains=code)
        if is_validated is not None:
            queryset = queryset.filter(is_validated=is_validated)
        if is_completed is not None:
            queryset = queryset.filter(requested_exams__is_completed=is_completed).distinct()

        sample_queryset = Sample.objects.select_related("sample_type").prefetch_related(
            Prefetch(
                "state_transitions",
                queryset=SampleStateTransition.objects.select_related("new_state").order_by("-created_at"),
            ),
            Prefetch(
                "requested_exams",
                queryset=RequestedExam.objects.select_related("exam_version__exam").order_by("id"),
            ),
        )

        queryset = queryset.prefetch_related(Prefetch("samples", queryset=sample_queryset)).order_by("-created_at")

        payload = []
        for exam_request in queryset:
            samples_payload = []

            for sample in exam_request.samples.all():
                current_state = None
                for transition in sample.state_transitions.all():
                    if transition.is_verified:
                        current_state = transition.new_state
                        break

                if sample_state_ids and (current_state is None or current_state.id not in sample_state_ids):
                    continue

                if sample_state_names:
                    if current_state is None or current_state.name.lower() not in sample_state_names:
                        continue

                requested_exams = list(sample.requested_exams.all())
                if is_completed is not None:
                    requested_exams = [exam for exam in requested_exams if exam.is_completed == is_completed]

                if is_completed is not None and not requested_exams:
                    continue

                samples_payload.append(
                    {
                        "id": sample.id,
                        "sample_type": {
                            "id": sample.sample_type.id,
                            "name": sample.sample_type.name,
                        },
                        "current_state": None if current_state is None else {
                            "id": current_state.id,
                            "name": current_state.name,
                        },
                        "exams": [self._build_exam_payload(exam) for exam in requested_exams],
                    }
                )

            if (sample_state_ids or sample_state_names or is_completed is not None) and not samples_payload:
                continue

            payload.append(
                {
                    "request": self._build_request_payload(exam_request),
                    "samples": samples_payload,
                }
            )

        page = self.paginate_queryset(payload)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(payload, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="fetch-results", permission_classes=[IsProfessional])
    def fetch_results(self, request):
        sample_ids = self._parse_list_param(request.query_params, "sample_ids")
        request_ids_raw = self._parse_list_param(request.query_params, "request_ids")
        requested_exam_ids_raw = self._parse_list_param(request.query_params, "requested_exam_ids")

        if not sample_ids and not request_ids_raw and not requested_exam_ids_raw:
            return Response(
                {"error": "Provide at least one of: sample_ids, request_ids, requested_exam_ids."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            request_ids = [int(v) for v in request_ids_raw]
            requested_exam_ids = [int(v) for v in requested_exam_ids_raw]
        except ValueError:
            return Response({"error": "IDs must be integers."}, status=status.HTTP_400_BAD_REQUEST)

        field_result_qs = ExamFieldResult.objects.select_related(
            "exam_field__measurement_unit",
        ).order_by("exam_field__priority", "exam_field__id")

        requested_exam_qs = RequestedExam.objects.select_related(
            "exam_version__exam",
        ).prefetch_related(
            Prefetch("field_results", queryset=field_result_qs),
        ).order_by("id")

        if requested_exam_ids:
            requested_exam_qs = requested_exam_qs.filter(id__in=requested_exam_ids)

        sample_qs = Sample.objects.select_related("sample_type").prefetch_related(
            Prefetch("requested_exams", queryset=requested_exam_qs),
        ).order_by("id")

        if sample_ids:
            sample_qs = sample_qs.filter(id__in=sample_ids)

        exam_request_qs = ExamRequest.objects.only("id", "code").prefetch_related(
            Prefetch("samples", queryset=sample_qs),
        )

        if request_ids:
            exam_request_qs = exam_request_qs.filter(id__in=request_ids)
        elif sample_ids:
            exam_request_qs = exam_request_qs.filter(samples__id__in=sample_ids).distinct()
        elif requested_exam_ids:
            exam_request_qs = exam_request_qs.filter(
                requested_exams__id__in=requested_exam_ids
            ).distinct()

        payload = []
        for exam_request in exam_request_qs:
            samples_payload = []
            for sample in exam_request.samples.all():
                exams_payload = []
                for req_exam in sample.requested_exams.all():
                    exam = req_exam.exam_version.exam
                    field_results_payload = [
                        {
                            "id": fr.id,
                            "field_name": fr.exam_field.name,
                            "field_code": fr.exam_field.code,
                            "raw_value": fr.raw_value,
                            "computed_value": fr.computed_value,
                            "classification": fr.classification,
                            "measurement_unit": None if fr.exam_field.measurement_unit is None else {
                                "name": fr.exam_field.measurement_unit.name,
                                "code": fr.exam_field.measurement_unit.code,
                            },
                        }
                        for fr in req_exam.field_results.all()
                    ]
                    exams_payload.append(
                        {
                            "requested_exam_id": req_exam.id,
                            "is_completed": req_exam.is_completed,
                            "exam": {"id": exam.id, "code": exam.code, "name": exam.name},
                            "field_results": field_results_payload,
                        }
                    )
                samples_payload.append(
                    {
                        "id": sample.id,
                        "sample_type": {"id": sample.sample_type.id, "name": sample.sample_type.name},
                        "exams": exams_payload,
                    }
                )
            payload.append({"request": {"id": exam_request.id, "code": exam_request.code}, "samples": samples_payload})

        return Response(payload, status=status.HTTP_200_OK)

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


class SectorViewSet(viewsets.ModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [IsProfessional]

    @action(detail=False, methods=["get"], url_path="term-search", permission_classes=[IsProfessional])
    def term_search(self, request):
        term = (request.query_params.get("term") or "").strip()
        if not term:
            return Response({"error": "Missing search term"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(name__icontains=term).order_by("name")
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsProfessional]

    @action(detail=False, methods=["get"], url_path="term-search", permission_classes=[IsProfessional])
    def term_search(self, request):
        term = (request.query_params.get("term") or "").strip()
        if not term:
            return Response({"error": "Missing search term"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(name__icontains=term).order_by("name")
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


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
