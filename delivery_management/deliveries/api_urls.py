from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    DeliveryOrderViewSet,
    RouteViewSet,
    DriverLocationViewSet
)

router = DefaultRouter()
router.register(r'orders', DeliveryOrderViewSet, basename='order')
router.register(r'routes', RouteViewSet, basename='route')

urlpatterns = [
    path('', include(router.urls)),
    path('driver/location/', DriverLocationViewSet.as_view({'post': 'update'}), name='driver-location'),
]