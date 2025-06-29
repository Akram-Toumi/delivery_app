from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import DeliveryOrder, Customer
from .forms import DeliveryOrderForm

class DeliveryOrderListView(LoginRequiredMixin, ListView):
    model = DeliveryOrder
    template_name = 'deliveries/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Search by order number or customer
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(customer__company_name__icontains=search)
            )
        
        # For customers, only show their orders
        if self.request.user.role == 'customer':
            customer = getattr(self.request.user, 'customer', None)
            if customer:
                queryset = queryset.filter(customer=customer)
        
        return queryset.order_by('-created_at')

class DeliveryOrderCreateView(LoginRequiredMixin, CreateView):
    model = DeliveryOrder
    form_class = DeliveryOrderForm
    template_name = 'deliveries/order_create.html'
    success_url = reverse_lazy('deliveries:list')

    def form_valid(self, form):
        # Generate order number
        form.instance.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{DeliveryOrder.objects.count() + 1}"
        
        # Set status based on user role
        if self.request.user.role == 'customer':
            form.instance.status = 'pending'
        
        messages.success(self.request, 'Delivery order created successfully!')
        return super().form_valid(form)

class DeliveryOrderDetailView(LoginRequiredMixin, DetailView):
    model = DeliveryOrder
    template_name = 'deliveries/order_detail.html'
    context_object_name = 'order'

class DeliveryOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = DeliveryOrder
    form_class = DeliveryOrderForm
    template_name = 'deliveries/order_update.html'
    
    def get_success_url(self):
        return reverse_lazy('deliveries:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Delivery order updated successfully!')
        return super().form_valid(form)
