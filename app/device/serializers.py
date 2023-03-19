"""
Serializers for device APIs
"""
from rest_framework import serializers

from core.models import (
    Device,
    Tag,
)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for devices."""

    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Device
        fields = ['id', 'title', 'time_minutes', 'value', 'link', 'tags']
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, device):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            device.tags.add(tag_obj)

    def create(self, validated_data):
        """Create a device."""
        tags = validated_data.pop('tags', [])
        device = Device.objects.create(**validated_data)
        self._get_or_create_tags(tags, device)

        return device

    def update(self, instance, validated_data):
        """Update device."""
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class DeviceDetailSerializer(DeviceSerializer):
    """Serializer for device detail view."""

    class Meta(DeviceSerializer.Meta):
        fields = DeviceSerializer.Meta.fields + ['description']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']
