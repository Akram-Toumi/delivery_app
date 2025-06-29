from rest_framework import serializers
from deliveries.models import DeliveryOrder, Route, RouteStop
from accounts.models import User

class DeliveryOrderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = DeliveryOrder
        fields = [
            'id', 'order_number', 'customer', 'weight_kg', 'priority', 'priority_display',
            'status', 'status_display', 'pickup_address', 'delivery_address',
            'requested_delivery_date', 'estimated_delivery_time', 'special_instructions'
        ]

class RouteStopSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='delivery_order.order_number', read_only=True)
    delivery_address = serializers.CharField(source='delivery_order.delivery_address', read_only=True)
    weight_kg = serializers.IntegerField(source='delivery_order.weight_kg', read_only=True)
    status = serializers.CharField(source='delivery_order.status', read_only=True)
    
    class Meta:
        model = RouteStop
        fields = [
            'id', 'stop_number', 'order_number', 'delivery_address',
            'weight_kg', 'status', 'estimated_arrival_time',
            'actual_arrival_time', 'is_completed', 'notes'
        ]

class RouteSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    truck_plate = serializers.CharField(source='truck.license_plate', read_only=True)
    
    class Meta:
        model = Route
        fields = [
            'id', 'name', 'date', 'truck', 'truck_plate', 'driver', 'driver_name',
            'total_distance_km', 'estimated_duration_minutes', 'status', 'status_display'
        ]

class DriverLocationSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8)
    
    def validate_latitude(self, value):
        if not (-90 <= value <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value
    
    def validate_longitude(self, value):
        if not (-180 <= value <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value