from rest_framework import serializers


class TimelineItemSerializer(serializers.Serializer):
    type = serializers.CharField()
    title = serializers.CharField()
    when = serializers.DateTimeField()
    is_future = serializers.BooleanField()
    reference_id = serializers.CharField()
