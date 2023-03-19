"""
Tests for the sensors API.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Sensor

from device.serializers import SensorSerializer


SENSORS_URL = reverse('device:sensor-list')


def detail_url(sensor_id):
    """Create and return an sensor detail URL."""
    return reverse('device:sensor-detail', args=[sensor_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicSensorsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving sensors."""
        res = self.client.get(SENSORS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatesSensorsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_sensors(self):
        """Test retrieving a list of sensors."""
        Sensor.objects.create(user=self.user, name='temp')
        Sensor.objects.create(user=self.user, name='humidity')

        res = self.client.get(SENSORS_URL)

        sensors = Sensor.objects.all().order_by('-name')
        serializer = SensorSerializer(sensors, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_sensors_limited_to_user(self):
        """Test list of sensors is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        Sensor.objects.create(user=user2, name='Salt')
        sensor = Sensor.objects.create(user=self.user, name='temp')

        res = self.client.get(SENSORS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], sensor.name)
        self.assertEqual(res.data[0]['id'], sensor.id)

    def test_update_sensor(self):
        """Test updating an sensor."""
        sensor = Sensor.objects.create(user=self.user, name='temp')

        payload = {'name': 'humidity'}
        url = detail_url(sensor.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sensor.refresh_from_db()
        self.assertEqual(sensor.name, payload['name'])

    def test_delete_sensor(self):
        """Test deleting an sensor."""
        sensor = Sensor.objects.create(user=self.user, name='humidity')

        url = detail_url(sensor.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        sensors = Sensor.objects.filter(user=self.user)
        self.assertFalse(sensors.exists())
