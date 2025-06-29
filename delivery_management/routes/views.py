from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from accounts.decorators import manager_required
from deliveries.models import DeliveryOrder, Truck
from .forms import RouteForm, RouteOptimizationForm, RouteStopForm, RouteStatusUpdateForm
from .services import RouteOptimizationService

class RouteListView(LoginRequiredMixin, ListView):
    model = Route
    template_name = 'routes/route_list.html'
    context_object_name = 'routes'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.request.user.role == 'driver':
            return queryset.filter(driver=self.request.user)
        elif self.request.user.role == 'manager':
            return queryset.filter(Q(driver__isnull=False) | Q(is_optimized=True))
        
        return queryset

class RouteDetailView(LoginRequiredMixin, DetailView):
    model = Route
    template_name = 'routes/route_detail.html'
    context_object_name = 'route'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_form'] = RouteStatusUpdateForm(instance=self.object)
        context['stop_form'] = RouteStopForm(route_id=self.object.id)
        context['map_center'] = {
            'lat': 52.5200,
            'lng': 13.4050
        }
        return context

class RouteCreateView(LoginRequiredMixin, CreateView):
    model = Route
    form_class = RouteForm
    template_name = 'routes/route_form.html'
    success_url = reverse_lazy('routes:list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Route created successfully")
        return response

class RouteUpdateView(LoginRequiredMixin, UpdateView):
    model = Route
    form_class = RouteForm
    template_name = 'routes/route_form.html'
    success_url = reverse_lazy('routes:list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Route updated successfully")
        return response

@manager_required
def optimize_routes(request):
    if request.method == 'POST':
        form = RouteOptimizationForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            trucks = form.cleaned_data['trucks']
            include_pending = form.cleaned_data['include_pending_orders']
            min_deliveries = form.cleaned_data['min_deliveries_per_truck']
            
            # Get orders to optimize
            orders = DeliveryOrder.objects.filter(
                Q(status='pending') | Q(status='assigned'),
                requested_delivery_date=date
            ) if include_pending else DeliveryOrder.objects.filter(
                status='assigned',
                requested_delivery_date=date
            )
            
            if not orders:
                messages.warning(request, "No orders found for optimization")
                return redirect('routes:optimize')
            
            # Optimize routes
            optimizer = RouteOptimizationService()
            optimized_routes = optimizer.optimize_daily_routes(date, trucks, orders, min_deliveries)
            
            messages.success(request, f"Successfully optimized {len(optimized_routes)} routes")
            return redirect('routes:list')
    else:
        form = RouteOptimizationForm()
    
    return render(request, 'routes/optimize_routes.html', {'form': form})

@manager_required
def add_route_stop(request, route_id):
    route = get_object_or_404(Route, pk=route_id)
    
    if request.method == 'POST':
        form = RouteStopForm(request.POST, route_id=route_id)
        if form.is_valid():
            stop = form.save(commit=False)
            stop.route = route
            stop.save()
            
            # Update order status
            stop.delivery_order.status = 'assigned'
            stop.delivery_order.save()
            
            messages.success(request, "Stop added to route successfully")
            return redirect('routes:detail', pk=route_id)
    else:
        form = RouteStopForm(route_id=route_id)
    
    return render(request, 'routes/add_stop.html', {'form': form, 'route': route})

@manager_required
def update_route_status(request, pk):
    route = get_object_or_404(Route, pk=pk)
    
    if request.method == 'POST':
        form = RouteStatusUpdateForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, "Route status updated successfully")
            return redirect('routes:detail', pk=pk)
    else:
        form = RouteStatusUpdateForm(instance=route)
    
    return render(request, 'routes/update_status.html', {'form': form, 'route': route})