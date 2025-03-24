import uuid

from rest_framework import viewsets, status

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from lab.serializers import SampleSerializer, SampleStateSerializer, SampleTypeSerializer
from rest_framework.response import Response
from lab.models import Sample, SampleState, SampleStateTransition, SampleType, AllowedStateTransition


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
