from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Medication
from .serializers import MedicationSerializer


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