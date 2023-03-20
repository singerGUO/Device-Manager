"""
Tests for the tags API.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Tag,
    Device,
)

from device.serializers import TagSerializer


TAGS_URL = reverse('device:tag-list')


def detail_url(tag_id):
    """Create and return a tag detail url."""
    return reverse('device:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        Tag.objects.create(user=user2, name='Fruity')
        tag = Tag.objects.create(user=self.user, name='Comfort Food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test updating a tag."""
        tag = Tag.objects.create(user=self.user, name='After Dinner')

        payload = {'name': 'Dessert'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting a tag."""
        tag = Tag.objects.create(user=self.user, name='Breakfast')

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_devices(self):
        """Test listing tags to those assigned to devices."""
        tag1 = Tag.objects.create(user=self.user, name='small_unit')
        tag2 = Tag.objects.create(user=self.user, name='large_unit')
        device = Device.objects.create(
            title='AHU',
            time_minutes=10,
            value=Decimal('2.50'),
            user=self.user,
        )
        device.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered tags returns a unique list."""
        tag = Tag.objects.create(user=self.user, name='small_unit')
        Tag.objects.create(user=self.user, name='large_unit')
        device1 = Device.objects.create(
            title='AHU',
            time_minutes=5,
            value=Decimal('5.00'),
            user=self.user,
        )
        device2 = Device.objects.create(
            title='Fan',
            time_minutes=3,
            value=Decimal('2.00'),
            user=self.user,
        )
        device1.tags.add(tag)
        device2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
