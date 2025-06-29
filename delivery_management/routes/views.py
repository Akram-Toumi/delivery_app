from django.shortcuts import render
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.contrib import messages
from deliveries.models import Truck
from .forms import ManualOptimizationForm
from .services import RouteOptimizationService
from .models import Route

class ManualOptimizationView(FormView):
    template_name = 'routes/manual_optimize.html'
    form_class = ManualOptimizationForm
    success_url = reverse_lazy('routes:list')

    def form_valid(self, form):
        date = form.cleaned_data['date']
        num_trucks = form.cleaned_data['num_trucks']
        orders = form.cleaned_data['orders']
        
        trucks = Truck.objects.filter(is_active=True)[:num_trucks]
        
        if not trucks.exists():
            messages.error(self.request, "No active trucks available")
            return self.form_invalid(form)
        
        optimizer = RouteOptimizationService(truck_capacity=1500)
        routes = optimizer.optimize_daily_routes(date, list(trucks), list(orders))
        
        messages.success(
            self.request,
            f"Created {len(routes)} optimized routes for {len(orders)} orders using {len(trucks)} trucks"
        )
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

import folium
from django.views.generic import DetailView
from django.conf import settings

class RouteDetailView(DetailView):
    model = Route
    template_name = 'routes/route_detail.html'
    context_object_name = 'route'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        route = self.get_object()
        
        # Create Folium map centered on factory
        m = folium.Map(
            location=[52.5200, 13.4050],  # Berlin coordinates
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Add factory marker
        folium.Marker(
            location=[52.5200, 13.4050],
            popup='Factory',
            icon=folium.Icon(color='red', icon='industry')
        ).add_to(m)
        
        # Prepare route coordinates
        route_coords = [(52.5200, 13.4050)]  # Start at factory
        
        for stop in route.stops.all().order_by('stop_number'):
            # Pickup location
            pickup_coord = (float(stop.delivery_order.pickup_latitude), 
                           float(stop.delivery_order.pickup_longitude))
            folium.Marker(
                location=pickup_coord,
                popup=f'Pickup: {stop.delivery_order.order_number}',
                icon=folium.Icon(color='blue', icon='arrow-up')
            ).add_to(m)
            route_coords.append(pickup_coord)
            
            # Delivery location
            delivery_coord = (float(stop.delivery_order.delivery_latitude), 
                             float(stop.delivery_order.delivery_longitude))
            folium.Marker(
                location=delivery_coord,
                popup=f'Delivery: {stop.delivery_order.order_number}',
                icon=folium.Icon(color='green', icon='arrow-down')
            ).add_to(m)
            route_coords.append(delivery_coord)
        
        # Return to factory
        route_coords.append((52.5200, 13.4050))
        
        # Draw the route
        folium.PolyLine(
            route_coords,
            color='red',
            weight=3,
            opacity=0.8
        ).add_to(m)
        
        # Fit map to bounds
        m.fit_bounds(route_coords)
        
        # Get HTML representation
        context['map_html'] = m._repr_html_()
        
        return context
