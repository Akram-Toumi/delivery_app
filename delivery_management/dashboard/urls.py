from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('admin-dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('manager-dashboard/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('driver-dashboard/', views.DriverDashboardView.as_view(), name='driver_dashboard'),
    path('customer-dashboard/', views.CustomerDashboardView.as_view(), name='customer_dashboard'),
]