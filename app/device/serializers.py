"""
Serializers for device APIs
"""
from rest_framework import serializers

from core.models import Device


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for devices."""

    class Meta:
        model = Device
        fields = ['id', 'title', 'time_minutes', 'value', 'link']
        read_only_fields = ['id']


class DeviceDetailSerializer(DeviceSerializer):
    """Serializer for device detail view."""

    class Meta(DeviceSerializer.Meta):
        fields = DeviceSerializer.Meta.fields + ['description']
