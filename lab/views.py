import uuid

from rest_framework import viewsets, status

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from lab.serializers import SampleSerializer, SampleTypeSerializer
from rest_framework.response import Response
from lab.models import Sample, SampleState, SampleStateTransition, SampleType


# Views
class SampleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def request_sample(self, request):
        serializer = SampleSerializer(data=request.data)
        if serializer.is_valid():
            sample = serializer.save()
            requested_state, _ = SampleState.objects.get_or_create(name="Requested")
            transition = SampleStateTransition.objects.create(
                sample=sample,
                previous_state=None,
                new_state=requested_state,
                changed_by=request.user
            )
            # Simulate blockchain transaction
            transition.transaction_hash = uuid.uuid4().hex  # Placeholder for blockchain hash
            transition.blockchain_timestamp = transition.created_at
            transition.is_verified = True
            transition.save()
            return Response({"message": "Sample requested successfully", "sample_id": sample.id, "transaction_hash": transition.transaction_hash},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SampleTypeViewSet(viewsets.ModelViewSet):
    queryset = SampleType.objects.all()
    serializer_class = SampleTypeSerializer
    permission_classes = [IsAuthenticated]
