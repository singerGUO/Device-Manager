"""
Views for the device APIs
"""
from rest_framework import (
    viewsets,
    mixins,
    status,
)
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import (
    Device,
    Tag,
    Sensor,
)
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
        elif self.action == 'upload_image':
            return serializers.DeviceImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new device."""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to device."""
        device = self.get_object()
        serializer = self.get_serializer(device, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseDeviceAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base viewset for sensor attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagViewSet(BaseDeviceAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class SensorViewSet(BaseDeviceAttrViewSet):
    """Manage sensors in the database."""
    serializer_class = serializers.SensorSerializer
    queryset = Sensor.objects.all()
