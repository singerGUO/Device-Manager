"""
Views for the device APIs
"""
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Device
from device import serializers


class DeviceViewSet(viewsets.ModelViewSet):
    """View for manage device APIs."""
    serializer_class = serializers.DeviceDetailSerializer
    queryset = Device.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve devices for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.DeviceSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new device."""
        serializer.save(user=self.request.user)
