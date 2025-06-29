import math
import requests
from typing import List, Tuple, Dict
from django.conf import settings
from deliveries.models import DeliveryOrder, Route, RouteStop, Truck

class RouteOptimizationService:
    def __init__(self):
        self.factory_location = (52.5200, 13.4050)  # Berlin coordinates
        self.osrm_endpoint = "http://router.project-osrm.org/route/v1/driving/"
        self.distance_cache = {}
    
    def optimize_daily_routes(self, date, trucks: List[Truck], orders: List[DeliveryOrder], min_deliveries: int = 5) -> List[Route]:
        """Optimize routes for given date using Clarke-Wright algorithm"""
        if not orders:
            return []
        
        print(f"Optimizing routes for {len(orders)} orders with {len(trucks)} trucks")
        
        # Calculate savings matrix
        savings = self._calculate_savings_matrix(orders)
        
        # Create initial routes (one order per route)
        routes = [[order] for order in orders]
        
        # Merge routes based on savings
        optimized_routes = self._merge_routes(routes, savings, trucks, min_deliveries)
        
        # Create Route objects
        django_routes = []
        for i, (route_orders, truck) in enumerate(optimized_routes):
            if route_orders:
                django_route = Route.objects.create(
                    name=f"Route {i+1} - {date}",
                    truck=truck,
                    driver=truck.driver,
                    date=date,
                    is_optimized=True
                )
                
                # Create route stops
                for stop_num, order in enumerate(route_orders, 1):
                    RouteStop.objects.create(
                        route=django_route,
                        delivery_order=order,
                        stop_number=stop_num
                    )
                    
                    # Update order status
                    order.status = 'assigned'
                    order.save()
                
                # Calculate total distance
                django_route.total_distance_km = self._calculate_route_distance(route_orders)
                django_route.save()
                
                django_routes.append(django_route)
        
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
        for i in range(len(orders)):
            for j in range(i+1, len(orders)):
                order_i = orders[i]
                order_j = orders[j]
                
                # Get coordinates
                pickup_i = (float(order_i.pickup_latitude), float(order_i.pickup_longitude))
                delivery_i = (float(order_i.delivery_latitude), float(order_i.delivery_longitude))
                pickup_j = (float(order_j.pickup_latitude), float(order_j.pickup_longitude))
                delivery_j = (float(order_j.delivery_latitude), float(order_j.delivery_longitude))
                
                # Calculate distance between points
                dist_pickup_pickup = self._get_road_distance(pickup_i, pickup_j)
                dist_delivery_delivery = self._get_road_distance(delivery_i, delivery_j)
                dist_pickup_delivery = self._get_road_distance(pickup_i, delivery_j)
                dist_delivery_pickup = self._get_road_distance(delivery_i, pickup_j)
                
                # Calculate savings for different combinations
                savings[(order_i.id, order_j.id, 'pickup-pickup')] = (
                    factory_distances[order_i.id]['pickup'] + 
                    factory_distances[order_j.id]['pickup'] - 
                    dist_pickup_pickup
                )
                
                savings[(order_i.id, order_j.id, 'delivery-delivery')] = (
                    factory_distances[order_i.id]['delivery'] + 
                    factory_distances[order_j.id]['delivery'] - 
                    dist_delivery_delivery
                )
                
                savings[(order_i.id, order_j.id, 'pickup-delivery')] = (
                    factory_distances[order_i.id]['pickup'] + 
                    factory_distances[order_j.id]['delivery'] - 
                    dist_pickup_delivery
                )
                
                savings[(order_j.id, order_i.id, 'pickup-delivery')] = (
                    factory_distances[order_j.id]['pickup'] + 
                    factory_distances[order_i.id]['delivery'] - 
                    dist_delivery_pickup
                )
        
        # Sort savings in descending order
        sorted_savings = sorted(savings.items(), key=lambda x: x[1], reverse=True)
        return sorted_savings
    
    def _merge_routes(self, routes: List[List[DeliveryOrder]], savings: List, trucks: List[Truck], min_deliveries: int):
        """Merge routes based on savings while respecting truck capacities and minimum deliveries"""
        truck_capacity = 1500  # kg (default capacity)
        optimized_routes = []
        truck_index = 0
        
        # Sort routes by total weight (descending)
        routes.sort(key=lambda r: sum(o.weight_kg for o in r), reverse=True)
        
        for saving in savings:
            (order_i_id, order_j_id, merge_type), saving_value = saving
            
            if saving_value <= 0 or truck_index >= len(trucks):
                break
            
            # Find routes containing these orders
            route_i, route_j = None, None
            for route in routes:
                if any(o.id == order_i_id for o in route):
                    route_i = route
                if any(o.id == order_j_id for o in route):
                    route_j = route
            
            if not route_i or not route_j or route_i == route_j:
                continue
            
            # Check if merge is possible based on truck capacity
            combined_weight = sum(o.weight_kg for o in route_i) + sum(o.weight_kg for o in route_j)
            if combined_weight > truck_capacity:
                continue
            
            # Check if we've reached minimum deliveries for current truck
            current_truck_deliveries = sum(len(r) for r in optimized_routes if r[1] == trucks[truck_index])
            if current_truck_deliveries >= min_deliveries and len(route_i) + len(route_j) > min_deliveries:
                truck_index += 1
                if truck_index >= len(trucks):
                    break
            
            # Merge routes based on merge type
            if merge_type == 'pickup-pickup':
                # Reverse route_j and prepend to route_i
                merged_route = route_j[::-1] + route_i
            elif merge_type == 'delivery-delivery':
                # Append route_j to route_i
                merged_route = route_i + route_j
            elif merge_type == 'pickup-delivery':
                # Append route_j to route_i
                merged_route = route_i + route_j
            elif merge_type == 'delivery-pickup':
                # Prepend route_j to route_i
                merged_route = route_j + route_i
            else:
                continue
            
            # Remove old routes and add merged route
            routes.remove(route_i)
            if route_j in routes:
                routes.remove(route_j)
            routes.append(merged_route)
        
        # Assign routes to trucks
        for i, truck in enumerate(trucks):
            if i < len(routes):
                optimized_routes.append((routes[i], truck))
            else:
                optimized_routes.append(([], truck))
        
        return optimized_routes
    
    def _calculate_route_distance(self, orders: List[DeliveryOrder]) -> float:
        """Calculate total distance for a route including factory trips"""
        if not orders:
            return 0.0
        
        total_distance = 0.0
        current_location = self.factory_location
        
        for order in orders:
            pickup_coord = (float(order.pickup_latitude), float(order.pickup_longitude))
            delivery_coord = (float(order.delivery_latitude), float(order.delivery_longitude))
            
            # Distance from current location to pickup
            total_distance += self._get_road_distance(current_location, pickup_coord)
            # Distance from pickup to delivery
            total_distance += self._get_road_distance(pickup_coord, delivery_coord)
            
            current_location = delivery_coord
        
        # Return to factory
        total_distance += self._get_road_distance(current_location, self.factory_location)
        
        return total_distance
    
    def _get_road_distance(self, start: Tuple[float, float], end: Tuple[float, float]) -> float:
        """Get road distance between two points using OSRM or haversine"""
        cache_key = (start, end)
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key]
        
        try:
            # Try OSRM first
            url = f"{self.osrm_endpoint}{start[1]},{start[0]};{end[1]},{end[0]}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data['code'] == 'Ok':
                distance = data['routes'][0]['distance'] / 1000  # Convert to km
                self.distance_cache[cache_key] = distance
                return distance
        except:
            pass
        
        # Fallback to haversine
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
