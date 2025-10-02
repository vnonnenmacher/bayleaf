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
    """
    Create a MedicationItem for the logged-in patient, not linked to a prescription.
    """
    permission_classes = [IsPatient | IsBayleafAPIToken]

    def post(self, request):
        serializer = MedicationItemCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            item = serializer.save()
            return Response(MedicationItemSerializer(item).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# NEW: Retrieve + Update + Delete in one patient-scoped detail view
class MyMedicationItemDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET: retrieve a single item
    PATCH/PUT: update item fields (medication, dosage_amount, dosage_unit, frequency_hours, total_unit_amount, instructions)
    DELETE: delete the item
    All operations are scoped to the caller's own items via patient__user_ptr_id.
    """
    permission_classes = [IsPatient | IsBayleafAPIToken]
    lookup_url_kwarg = "id"

    def get_queryset(self):
        # Scope to the current patient's items (works for OBO and patient JWT)
        return (
            MedicationItem.objects
            .filter(patient__user_ptr_id=self.request.user.id)
            .select_related("medication", "dosage_unit")
        )

    def get_serializer_class(self):
        # Use read serializer for GET; write serializer for PUT/PATCH
        if self.request.method in ("PUT", "PATCH"):
            return MedicationItemUpdateSerializer
        return MedicationItemSerializer

    def update(self, request, *args, **kwargs):
        # Use write serializer to validate & save, then respond with read serializer
        instance = self.get_object()
        partial = request.method == "PATCH"
        write_serializer = MedicationItemUpdateSerializer(instance, data=request.data, partial=partial, context={"request": request})
        write_serializer.is_valid(raise_exception=True)
        item = write_serializer.save()
        read_data = MedicationItemSerializer(item).data
        return Response(read_data, status=status.HTTP_200_OK)
