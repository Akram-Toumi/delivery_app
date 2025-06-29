from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from accounts.models import User
from deliveries.models import DeliveryOrder, Route, RouteStop
from .serializers import (
    DeliveryOrderSerializer, 
    RouteSerializer,
    RouteStopSerializer,
    DriverLocationSerializer
)

class DeliveryOrderViewSet(viewsets.ModelViewSet):
    queryset = DeliveryOrder.objects.all()
    serializer_class = DeliveryOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'customer':
            return self.queryset.filter(customer__user=user)
        elif user.role == 'driver':
            return self.queryset.filter(
                id__in=RouteStop.objects.filter(
                    route__driver=user
                ).values_list('delivery_order_id', flat=True)
            )
        return self.queryset

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'driver':
            return self.queryset.filter(driver=user)
        return self.queryset
    
    @action(detail=True, methods=['get'])
    def stops(self, request, pk=None):
        route = self.get_object()
        stops = route.stops.all().order_by('stop_number')
        serializer = RouteStopSerializer(stops, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start_route(self, request, pk=None):
        route = self.get_object()
        if route.status != 'planned':
            return Response(
                {'error': 'Route is not in planned status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        route.status = 'active'
        route.save()
        return Response({'status': 'Route started'})
    
    @action(detail=True, methods=['post'])
    def complete_route(self, request, pk=None):
        route = self.get_object()
        if route.status != 'active':
            return Response(
                {'error': 'Route is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        route.status = 'completed'
        route.save()
        return Response({'status': 'Route completed'})

class DriverLocationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request):
        user = request.user
        if user.role != 'driver':
            return Response(
                {'error': 'Only drivers can update location'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DriverLocationSerializer(data=request.data)
        if serializer.is_valid():
            user.current_location_lat = serializer.validated_data['latitude']
            user.current_location_lon = serializer.validated_data['longitude']
            user.save()
            
            # Update truck location if assigned
            if hasattr(user, 'truck'):
                user.truck.current_location_lat = serializer.validated_data['latitude']
                user.truck.current_location_lon = serializer.validated_data['longitude']
                user.truck.save()
            
            return Response({'status': 'Location updated'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)