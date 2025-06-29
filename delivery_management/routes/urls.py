from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
    path('', views.RouteListView.as_view(), name='list'),
    path('create/', views.RouteCreateView.as_view(), name='create'),
    path('<int:pk>/', views.RouteDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.RouteUpdateView.as_view(), name='edit'),
    path('<int:pk>/status/', views.update_route_status, name='update_status'),
    path('<int:route_id>/stops/add/', views.add_route_stop, name='add_stop'),
    path('optimize/', views.optimize_routes, name='optimize'),
]