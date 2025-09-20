from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from patients.models import Patient
from users.permissions import IsBayleafAPIToken
from patients.permissions import IsPatient

from .models import Medication, MedicationItem
from .serializers import MedicationItemSerializer, MedicationPrescribeSerializer, MedicationSerializer


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
            return Response({
                "message": "Medication prescribed successfully",
                "prescription_id": str(prescription.id)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyMedicationsView(ListAPIView):
    """
    Returns MedicationItems for the logged-in patient.
    Only accessible with Bayleaf API tokens and by users who are patients.
    """
    serializer_class = MedicationItemSerializer
    permission_classes = [IsPatient | IsBayleafAPIToken]

    def get_queryset(self):

        # MedicationItem inherits from AbstractPrescriptionItem, which includes `patient`.
        # Filter strictly by the authenticated user's id to avoid any leakage.
        return (
            MedicationItem.objects
            .filter(patient_id=Patient.objects.get(user_ptr_id=self.request.user.id))
            .select_related("medication", "dosage_unit")
            .order_by("-id")
        )
