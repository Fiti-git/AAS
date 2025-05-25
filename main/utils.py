from math import radians, cos, sin, asin, sqrt
from .models import Outlet

def haversine(lat1, lon1, lat2, lon2):
    # Earth radius in meters
    R = 6371000  
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def verify_location(employee, lat, lon):
    try:
        for outlet_id in employee.outlet:
            outlet = Outlet.objects.get(id=outlet_id)
            
            # Calculate the distance using the haversine formula
            distance = haversine(lat, lon, outlet.latitude, outlet.longitude)
            
            # If within the radius of any outlet, location is verified
            if distance <= outlet.radius_meters:
                return True
        
        # If no outlet is within range, return False
        return False

    except (Outlet.DoesNotExist, TypeError, AttributeError) as e:
        print(f"Location verification error: {e}")
        return False