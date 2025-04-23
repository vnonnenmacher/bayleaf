from rest_framework import generics, permissions
from .models import Medication
from .serializers import MedicationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class MedicationListView(generics.ListAPIView):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]


class MedicationSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        key = request.query_params.get("key", "").strip()
        if not key:
            return Response({"error": "Missing search key"}, status=status.HTTP_400_BAD_REQUEST)

        matches = Medication.objects.filter(name__icontains=key).order_by("name")[:20]
        serializer = MedicationSerializer(matches, many=True)
        return Response(serializer.data)