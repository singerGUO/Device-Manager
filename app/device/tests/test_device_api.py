"""
Tests for device APIs
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Device

from device.serializers import DeviceSerializer


DEVICES_URL = reverse('device:device-list')


def create_device(user, **params):
    """Create and return a sample device."""
    defaults = {
        'title': 'Sample device title',
        'time_minutes': 20,
        'value': Decimal('5.25'),
        'description': 'celcius',
        'link': 'http://example.com/device.pdf',
    }
    defaults.update(params)

    device = Device.objects.create(user=user, **defaults)
    return device


class PublicDeviceAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(DEVICES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateDeviceApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_devices(self):
        """Test retrieving a list of devices."""
        create_device(user=self.user)
        create_device(user=self.user)

        res = self.client.get(DEVICES_URL)

        devices = Device.objects.all().order_by('-id')
        serializer = DeviceSerializer(devices, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_device_list_limited_to_user(self):
        """Test list of devices is limited to authenticated user."""
        other_user = get_user_model().objects.create_user(
            'other@example.com',
            'password123',
        )
        create_device(user=other_user)
        create_device(user=self.user)

        res = self.client.get(DEVICES_URL)

        devices = Device.objects.filter(user=self.user)
        serializer = DeviceSerializer(devices, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
