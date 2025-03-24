from rest_framework import serializers
from lab.models import AllowedStateTransition, Sample, SampleState, SampleType
from patients.models import Patient
from patients.serializers import ReducedPatientSerializer


# Serializers
class SampleSerializer(serializers.ModelSerializer):
    patient_uuid = serializers.UUIDField(write_only=True)
    current_state = serializers.SerializerMethodField(read_only=True)
    patient = ReducedPatientSerializer(read_only=True)

    class Meta:
        model = Sample
        fields = ['id', 'patient_uuid', 'sample_type', 'current_state', 'patient']

    def validate_patient_uuid(self, value):
        if not Patient.objects.filter(pid=value).exists():
            raise serializers.ValidationError("Patient not found.")
        return value

    def create(self, validated_data):
        patient = Patient.objects.get(pid=validated_data.pop('patient_uuid'))
        sample = Sample.objects.create(patient=patient, **validated_data)
        return sample

    def get_current_state(self, obj):
        state = obj.get_current_state()
        if state:
            return {
                "id": state.id,
                "name": state.name
            }
        return None


class SampleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SampleType
        fields = ['id', 'name', 'description', 'created_at']


class SampleStateSerializer(serializers.ModelSerializer):
    # 🔸 Accept list of state IDs on write
    allowed_transitions = serializers.PrimaryKeyRelatedField(
        queryset=SampleState.objects.all(),
        many=True,
        required=False,
        write_only=True
    )
    incoming_transitions = serializers.PrimaryKeyRelatedField(
        queryset=SampleState.objects.all(),
        many=True,
        required=False,
        write_only=True
    )

    # 🔸 Return full state objects (id + name) on read
    allowed_transitions_detail = serializers.SerializerMethodField()
    incoming_transitions_detail = serializers.SerializerMethodField()

    class Meta:
        model = SampleState
        fields = [
            "id",
            "name",
            "description",
            "created_at",
            "is_initial_state",
            "is_final_state",
            "allowed_transitions",
            "incoming_transitions",
            "allowed_transitions_detail",
            "incoming_transitions_detail",
        ]
        read_only_fields = ("created_at",)

    # 🔸 GET method: output full objects for allowed transitions
    def get_allowed_transitions_detail(self, obj):
        return [
            {"id": t.to_state.id, "name": t.to_state.name}
            for t in obj.allowed_transitions.select_related("to_state").all()
        ]

    # 🔸 GET method: output full objects for incoming transitions
    def get_incoming_transitions_detail(self, obj):
        return [
            {"id": t.from_state.id, "name": t.from_state.name}
            for t in obj.incoming_transitions.select_related("from_state").all()
        ]

    def create(self, validated_data):
        allowed_transitions = validated_data.pop("allowed_transitions", [])
        incoming_transitions = validated_data.pop("incoming_transitions", [])

        sample_state = SampleState.objects.create(**validated_data)

        for to_state in allowed_transitions:
            AllowedStateTransition.objects.create(from_state=sample_state, to_state=to_state)

        for from_state in incoming_transitions:
            AllowedStateTransition.objects.create(from_state=from_state, to_state=sample_state)

        return sample_state

    def update(self, instance, validated_data):
        allowed_transitions = validated_data.pop("allowed_transitions", [])
        incoming_transitions = validated_data.pop("incoming_transitions", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if allowed_transitions:
            AllowedStateTransition.objects.filter(from_state=instance).delete()
            for to_state in allowed_transitions:
                AllowedStateTransition.objects.create(from_state=instance, to_state=to_state)

        if incoming_transitions:
            AllowedStateTransition.objects.filter(to_state=instance).delete()
            for from_state in incoming_transitions:
                AllowedStateTransition.objects.create(from_state=from_state, to_state=instance)

        return instance
