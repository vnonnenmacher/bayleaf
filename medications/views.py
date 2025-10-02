from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView

from users.permissions import IsBayleafAPIToken
from patients.permissions import IsPatient

from .models import Medication, MedicationItem
from .serializers import (
    MedicationItemSerializer,
    MedicationItemCreateSerializer,
    MedicationItemUpdateSerializer,
    MedicationPrescribeSerializer,
    MedicationSerializer,
)

from medications.helpers.add_medication_helper import AddMedicationHelper


class MedicationViewSet(viewsets.ModelViewSet):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="drug-search")
    def drug_search(self, request):
        key = request.query_params.get("key", "").strip()
        if not key:
            return Response({"error": "Missing search key"}, status=status.HTTP_400_BAD_REQUEST)

        results = Medication.objects.filter(name__icontains=key).order_by("name")[:20]
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)


class MedicationPrescribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MedicationPrescribeSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            prescription = serializer.save()
            return Response(
                {"message": "Medication prescribed successfully", "prescription_id": str(prescription.id)},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyMedicationsView(ListAPIView):
    """
    Returns MedicationItems for the logged-in patient.
    Works with OBO because request.user is the patient user.
    """
    serializer_class = MedicationItemSerializer
    permission_classes = [IsPatient | IsBayleafAPIToken]

    def get_queryset(self):
        return (
            MedicationItem.objects
            .filter(patient__user_ptr_id=self.request.user.id)
            .select_related("medication", "dosage_unit")
            .order_by("-id")
        )


class MyMedicationItemCreateView(APIView):
    permission_classes = [IsPatient | IsBayleafAPIToken]

    def post(self, request):
        serializer = MedicationItemCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            item = serializer.save()  # item.patient is set via serializer create
            # optional scheduling inputs from client:
            first_dose_at = request.data.get("first_dose_at")  # ISO8601 or omitted
            window_minutes = int(request.data.get("window_minutes", 90))

            helper = AddMedicationHelper(created_by_user=request.user)
            helper.create_item_with_events(
                item=item,
                first_dose_at=first_dose_at,
                window_minutes=window_minutes,
            )
            return Response(MedicationItemSerializer(item).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyMedicationItemDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsPatient | IsBayleafAPIToken]
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return (
            MedicationItem.objects
            .filter(patient__user_ptr_id=self.request.user.id)
            .select_related("medication", "dosage_unit")
        )

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return MedicationItemUpdateSerializer
        return MedicationItemSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = request.method == "PATCH"

        # capture pre-change schedule fields
        old_freq = instance.frequency_hours
        old_total = instance.total_unit_amount

        write_serializer = MedicationItemUpdateSerializer(
            instance, data=request.data, partial=partial, context={"request": request}
        )
        write_serializer.is_valid(raise_exception=True)
        item = write_serializer.save()

        # figure out if schedule changed
        schedule_changed = (
            (old_freq != item.frequency_hours) or
            (old_total != item.total_unit_amount)
        )

        first_dose_at = request.data.get("first_dose_at")  # optional new anchor
        window_minutes = int(request.data.get("window_minutes", 90))

        helper = AddMedicationHelper(created_by_user=request.user)
        helper.update_item_and_events(
            item=item,
            schedule_changed=schedule_changed or (first_dose_at is not None),
            first_dose_at=first_dose_at,
            window_minutes=window_minutes,
        )

        read_data = MedicationItemSerializer(item).data
        return Response(read_data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        delete_completed = bool(request.query_params.get("delete_completed", False))
        helper = AddMedicationHelper(created_by_user=request.user)
        helper.remove_item_and_events(item=item, delete_completed=delete_completed)
        return Response(status=status.HTTP_204_NO_CONTENT)
