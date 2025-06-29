import math
import requests
from typing import List, Dict, Tuple
from django.conf import settings
from deliveries.models import DeliveryOrder, Route, RouteStop, Truck
from datetime import date

class RouteOptimizationService:
    def __init__(self, factory_location=(52.5200, 13.4050), truck_capacity=1500):
        self.factory_location = factory_location
        self.truck_capacity = truck_capacity
        self.osrm_endpoint = "http://router.project-osrm.org/route/v1/driving/"
        self.distance_cache = {}

    def optimize_daily_routes(self, date: date, trucks: List[Truck], orders: List[DeliveryOrder]) -> List[Route]:
        """Optimize routes with manual truck configuration"""
        if not orders:
            return []

        # Calculate savings matrix
        savings = self._calculate_savings_matrix(orders)
        
        # Create initial routes (one order per route)
        routes = [[order] for order in orders]
        
        # Merge routes based on savings
        optimized_routes = self._merge_routes(routes, savings, trucks)
        
        # Create Route objects
        django_routes = []
        for i, (route_orders, truck) in enumerate(optimized_routes):
            if route_orders and truck:
                route = self._create_route(
                    name=f"Optimized Route {i+1}",
                    date=date,
                    truck=truck,
                    orders=route_orders
                )
                django_routes.append(route)
        
        return django_routes

    def _calculate_savings_matrix(self, orders: List[DeliveryOrder]) -> Dict:
        """Calculate Clarke-Wright savings for all order pairs"""
        savings = {}
        
        # Pre-calculate distances from factory
        factory_distances = {}
        for order in orders:
            pickup_coord = (float(order.pickup_latitude), float(order.pickup_longitude))
            delivery_coord = (float(order.delivery_latitude), float(order.delivery_longitude))
            
            factory_distances[order.id] = {
                'pickup': self._get_road_distance(self.factory_location, pickup_coord),
                'delivery': self._get_road_distance(self.factory_location, delivery_coord)
            }

        # Calculate savings for all pairs
        for i, order1 in enumerate(orders):
            for j, order2 in enumerate(orders[i+1:], i+1):
                # Get coordinates
                pickup1 = (float(order1.pickup_latitude), float(order1.pickup_longitude))
                delivery1 = (float(order1.delivery_latitude), float(order1.delivery_longitude))
                pickup2 = (float(order2.pickup_latitude), float(order2.pickup_longitude))
                delivery2 = (float(order2.delivery_latitude), float(order2.delivery_longitude))

                # Calculate all possible savings combinations
                savings_combinations = [
                    # Pickup to pickup
                    (factory_distances[order1.id]['pickup'] + factory_distances[order2.id]['pickup'] - 
                     self._get_road_distance(pickup1, pickup2)),
                    
                    # Pickup to delivery
                    (factory_distances[order1.id]['pickup'] + factory_distances[order2.id]['delivery'] - 
                     self._get_road_distance(pickup1, delivery2)),
                    
                    # Delivery to pickup
                    (factory_distances[order1.id]['delivery'] + factory_distances[order2.id]['pickup'] - 
                     self._get_road_distance(delivery1, pickup2)),
                    
                    # Delivery to delivery
                    (factory_distances[order1.id]['delivery'] + factory_distances[order2.id]['delivery'] - 
                     self._get_road_distance(delivery1, delivery2)),
                ]

                max_saving = max(savings_combinations)
                if max_saving > 0:
                    savings[(order1.id, order2.id)] = max_saving

        return savings

    def _merge_routes(self, routes: List[List[DeliveryOrder]], savings: Dict, trucks: List[Truck]) -> List[Tuple[List[DeliveryOrder], Truck]]:
        """Merge routes based on savings while respecting truck capacities"""
        # Sort savings in descending order
        sorted_savings = sorted(savings.items(), key=lambda x: x[1], reverse=True)
        
        # Initialize truck assignments
        truck_assignments = []
        truck_capacities = {truck.id: self.truck_capacity for truck in trucks}
        truck_utilization = {truck.id: 0 for truck in trucks}
        
        # Assign routes to trucks
        for route in routes:
            route_weight = sum(order.weight_kg for order in route)
            
            # Find available truck with enough capacity
            assigned = False
            for truck in trucks:
                if truck_utilization[truck.id] + route_weight <= truck_capacities[truck.id]:
                    truck_assignments.append((route, truck))
                    truck_utilization[truck.id] += route_weight
                    assigned = True
                    break
            
            if not assigned:
                # No truck available, leave unassigned
                truck_assignments.append((route, None))
        
        # Apply savings merges
        for (order1_id, order2_id), saving in sorted_savings:
            # Find routes containing these orders
            route1_idx, route2_idx = None, None
            for i, (route, _) in enumerate(truck_assignments):
                if any(order.id == order1_id for order in route):
                    route1_idx = i
                if any(order.id == order2_id for order in route):
                    route2_idx = i
            
            # Skip if same route or not found
            if route1_idx == route2_idx or route1_idx is None or route2_idx is None:
                continue
            
            route1, truck1 = truck_assignments[route1_idx]
            route2, truck2 = truck_assignments[route2_idx]
            
            # Check if same truck and capacity allows merge
            if truck1 and truck2 and truck1.id == truck2.id:
                combined_weight = sum(order.weight_kg for order in route1) + sum(order.weight_kg for order in route2)
                if combined_weight <= truck1.capacity_kg:
                    # Merge routes
                    merged_route = route1 + route2
                    truck_assignments[route1_idx] = (merged_route, truck1)
                    truck_assignments.pop(route2_idx)
        
        return truck_assignments

    def _create_route(self, name: str, date: date, truck: Truck, orders: List[DeliveryOrder]) -> Route:
        """Create a Route model instance with stops"""
        route = Route.objects.create(
            name=name,
            truck=truck,
            driver=truck.driver,
            date=date,
            is_optimized=True
        )
        
        # Create stops and calculate distance
        total_distance = 0
        last_location = self.factory_location
        
        for stop_num, order in enumerate(orders, 1):
            # Create stop
            RouteStop.objects.create(
                route=route,
                delivery_order=order,
                stop_number=stop_num
            )
            
            # Update order status
            order.status = 'assigned'
            order.save()
            
            # Calculate distances
            pickup = (float(order.pickup_latitude), float(order.pickup_longitude))
            delivery = (float(order.delivery_latitude), float(order.delivery_longitude))
            
            total_distance += self._get_road_distance(last_location, pickup)
            total_distance += self._get_road_distance(pickup, delivery)
            last_location = delivery
        
        # Return to factory
        total_distance += self._get_road_distance(last_location, self.factory_location)
        
        route.total_distance_km = total_distance
        route.save()
        return route

    def _get_road_distance(self, start: Tuple[float, float], end: Tuple[float, float]) -> float:
        """Get road distance between two points using OSRM or haversine"""
        cache_key = (start, end)
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key]
        
        try:
            # OSRM API call
            url = f"{self.osrm_endpoint}{start[1]},{start[0]};{end[1]},{end[0]}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data['code'] == 'Ok':
                distance = data['routes'][0]['distance'] / 1000  # Convert to km
                self.distance_cache[cache_key] = distance
                return distance
        except:
            pass
        
        # Fallback to haversine distance
        distance = self._haversine_distance(start, end)
        self.distance_cache[cache_key] = distance
        return distance

    def _haversine_distance(self, start: Tuple[float, float], end: Tuple[float, float]) -> float:
        """Calculate great-circle distance between two points"""
        lat1, lon1 = math.radians(start[0]), math.radians(start[1])
        lat2, lon2 = math.radians(end[0]), math.radians(end[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return 6371 * c  # Earth radius in km