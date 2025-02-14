from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PatientCreateSerializer


class PatientCreateView(APIView):
    permission_classes = []  # No authentication required

    def post(self, request):
        serializer = PatientCreateSerializer(data=request.data)
        if serializer.is_valid():
            patient = serializer.save()
            return Response(
                {"message": "Patient created successfully", "pid": patient.pid},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)