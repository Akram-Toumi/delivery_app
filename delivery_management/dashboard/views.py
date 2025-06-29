from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from accounts.decorators import role_required, admin_required, manager_required, driver_required
from deliveries.models import DeliveryOrder, Route, Truck
from accounts.models import User

class DashboardView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # Redirect to role-specific dashboard
        role = request.user.role
        if role == 'admin':
            return redirect('dashboard:admin_dashboard')
        elif role == 'manager':
            return redirect('dashboard:manager_dashboard')
        elif role == 'driver':
            return redirect('dashboard:driver_dashboard')
        elif role == 'customer':
            return redirect('dashboard:customer_dashboard')
        else:
            return redirect('dashboard:customer_dashboard')

class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/admin_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Statistics
        context.update({
            'total_orders': DeliveryOrder.objects.count(),
            'pending_orders': DeliveryOrder.objects.filter(status='pending').count(),
            'active_routes': Route.objects.filter(status='active').count(),
            'total_drivers': User.objects.filter(role='driver').count(),
            'total_trucks': Truck.objects.filter(is_active=True).count(),
            
            # Recent orders
            'recent_orders': DeliveryOrder.objects.order_by('-created_at')[:10],
            
            # Today's routes
            'todays_routes': Route.objects.filter(date=today),
            
            # Performance metrics
            'delivery_success_rate': self.get_delivery_success_rate(),
            'avg_delivery_time': self.get_avg_delivery_time(),
        })
        return context
    
    def get_delivery_success_rate(self):
        total = DeliveryOrder.objects.count()
        delivered = DeliveryOrder.objects.filter(status='delivered').count()
        return round((delivered / total * 100) if total > 0 else 0, 1)
    
    def get_avg_delivery_time(self):
        # Calculate average delivery time logic here
        return "2.5 hours"  # Placeholder

class ManagerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/manager_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'manager']:
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        context.update({
            'pending_orders': DeliveryOrder.objects.filter(status='pending').count(),
            'todays_routes': Route.objects.filter(date=today),
            'available_trucks': Truck.objects.filter(is_active=True, route__isnull=True),
            'active_drivers': User.objects.filter(role='driver', is_active_driver=True),
        })
        return context

class DriverDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/driver_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['admin', 'manager', 'driver']:
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Get driver's routes
        my_routes = Route.objects.filter(
            driver=self.request.user,
            date=today
        )
        
        context.update({
            'my_routes': my_routes,
            'completed_deliveries': sum(route.stops.filter(is_completed=True).count() for route in my_routes),
            'pending_deliveries': sum(route.stops.filter(is_completed=False).count() for route in my_routes),
        })
        return context

class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/customer_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get customer's orders
        customer = getattr(self.request.user, 'customer', None)
        if customer:
            context.update({
                'my_orders': DeliveryOrder.objects.filter(customer=customer).order_by('-created_at'),
                'pending_orders': DeliveryOrder.objects.filter(customer=customer, status='pending').count(),
                'in_transit_orders': DeliveryOrder.objects.filter(customer=customer, status='in_transit').count(),
            })
        
        return context