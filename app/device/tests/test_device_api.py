"""
Tests for device APIs
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Device,
    Tag,
)

from device.serializers import (
    DeviceSerializer,
    DeviceDetailSerializer,
)

DEVICES_URL = reverse('device:device-list')


def detail_url(device_id):
    """Create and return a device detail URL."""
    return reverse('device:device-detail', args=[device_id])


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


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


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
        self.user = create_user(email='user@example.com', password='test123')
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
        other_user = create_user(email='other@example.com', password='test123')
        create_device(user=other_user)
        create_device(user=self.user)

        res = self.client.get(DEVICES_URL)

        devices = Device.objects.filter(user=self.user)
        serializer = DeviceSerializer(devices, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_device_detail(self):
        """Test get device detail."""
        device = create_device(user=self.user)

        url = detail_url(device.id)
        res = self.client.get(url)

        serializer = DeviceDetailSerializer(device)
        self.assertEqual(res.data, serializer.data)

    def test_create_device(self):
        """Test creating a device."""
        payload = {
            'title': 'Sample device',
            'time_minutes': 30,
            'value': Decimal('5.99'),
        }
        res = self.client.post(DEVICES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        device = Device.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(device, k), v)
        self.assertEqual(device.user, self.user)

    def test_partial_update(self):
        """Test partial update of a deice."""
        original_link = 'https://example.com/device.pdf'
        device = create_device(
            user=self.user,
            title='Sample device title',
            link=original_link,
        )

        payload = {'title': 'New device title'}
        url = detail_url(device.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        device.refresh_from_db()
        self.assertEqual(device.title, payload['title'])
        self.assertEqual(device.link, original_link)
        self.assertEqual(device.user, self.user)

    def test_full_update(self):
        """Test full update of device."""
        device = create_device(
            user=self.user,
            title='Sample device title',
            link='https://exmaple.com/device.pdf',
            description='Sample device description.',
        )

        payload = {
            'title': 'New device title',
            'link': 'https://example.com/new-device.pdf',
            'description': 'New device description',
            'time_minutes': 10,
            'value': Decimal('2.50'),
        }
        url = detail_url(device.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        device.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(device, k), v)
        self.assertEqual(device.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the device user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        device = create_device(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(device.id)
        self.client.patch(url, payload)

        device.refresh_from_db()
        self.assertEqual(device.user, self.user)

    def test_delete_device(self):
        """Test deleting a device successful."""
        device = create_device(user=self.user)

        url = detail_url(device.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Device.objects.filter(id=device.id).exists())

    def test_device_other_users_device_error(self):
        """Test trying to delete another users device gives error."""
        new_user = create_user(email='user2@example.com', password='test123')
        device = create_device(user=new_user)

        url = detail_url(device.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Device.objects.filter(id=device.id).exists())

    def test_create_device_with_new_tags(self):
        """Test creating a device with new tags."""
        payload = {
            'title': 'DX',
            'time_minutes': 30,
            'value': Decimal('2.50'),
            'tags': [{'name': 'Cooling device'}, {'name': 'small_unit'}],
        }
        res = self.client.post(DEVICES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        devices = Device.objects.filter(user=self.user)
        self.assertEqual(devices.count(), 1)
        device = devices[0]
        self.assertEqual(device.tags.count(), 2)
        for tag in payload['tags']:
            exists = device.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_device_with_existing_tags(self):
        """Test creating a device with existing tag."""
        tag_meter = Tag.objects.create(user=self.user, name='meter')
        payload = {
            'title': 'unknown device',
            'time_minutes': 60,
            'value': Decimal('4.50'),
            'tags': [{'name': 'meter'}, {'name': 'small_unit'}],
        }
        res = self.client.post(DEVICES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        devices = Device.objects.filter(user=self.user)
        self.assertEqual(devices.count(), 1)
        device = devices[0]
        self.assertEqual(device.tags.count(), 2)
        self.assertIn(tag_meter, device.tags.all())
        for tag in payload['tags']:
            exists = device.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_update_device_assign_tag(self):
        """Test assigning an existing tag when updating a device."""
        tag_small_unit = Tag.objects.create(user=self.user, name='small_unit')
        device = create_device(user=self.user)
        device.tags.add(tag_small_unit)

        tag_large_unit = Tag.objects.create(user=self.user, name='large_unit')
        payload = {'tags': [{'name': 'large_unit'}]}
        url = detail_url(device.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_large_unit, device.tags.all())
        self.assertNotIn(tag_small_unit, device.tags.all())

    def test_clear_device_tags(self):
        """Test clearing a devices tags."""
        tag = Tag.objects.create(user=self.user, name='small_unit')
        device = create_device(user=self.user)
        device.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(device.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(device.tags.count(), 0)
