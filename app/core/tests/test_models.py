"""
Tests for models.
"""
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email='user@example.com', password='testpass123'):
    """Create a return a new user."""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        '''Test that creating a user without an email raises value error'''
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_device(self):
        '''Test creating a device is sucessful'''
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )
        device = models.Device.objects.create(
            user=user,
            title='Sample device name',
            time_minutes=5,
            value=Decimal('5.50'),
            description='Sample device description.',
        )

        self.assertEqual(str(device), device.title)

    def test_create_tag(self):
        """Test creating a tag is successful."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)

    def test_create_sensor(self):
        """Test creating an sensor is successful."""
        user = create_user()
        sensor = models.Sensor.objects.create(
            user=user,
            name='Sensor1'
        )

        self.assertEqual(str(sensor), sensor.name)

    @patch('core.models.uuid.uuid4')
    def test_device_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.device_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/device/{uuid}.jpg')
