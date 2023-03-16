"""
URL mappings for the device app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from device import views


router = DefaultRouter()
router.register('devices', views.DeviceViewSet)

app_name = 'device'

urlpatterns = [
    path('', include(router.urls)),
]
