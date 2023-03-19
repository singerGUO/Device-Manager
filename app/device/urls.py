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
router.register('tags', views.TagViewSet)
router.register('sensors', views.SensorViewSet)

app_name = 'device'

urlpatterns = [
    path('', include(router.urls)),
]
