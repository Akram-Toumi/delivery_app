from django.urls import path
from . import views

app_name = 'deliveries'

urlpatterns = [
    path('', views.DeliveryOrderListView.as_view(), name='list'),
    path('create/', views.DeliveryOrderCreateView.as_view(), name='create'),
    path('<int:pk>/', views.DeliveryOrderDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.DeliveryOrderUpdateView.as_view(), name='update'),
]