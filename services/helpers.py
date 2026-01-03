import math
from models.helpers.coordinate import Coordinate

def clamp_positive(x: float, min_value: float) -> float:
    """Ensures x is at least min_val (prevents log10(0)) and negative values"""
    return x if x >= min_value else min_value

def haversine_km(c1: Coordinate, c2: Coordinate) -> float:
    """Distance between 2 lat/lon points in KM"""
    R = 6371.0 # Earth radius in km
    
    lat1 = math.radians(c1.latitude)
    lon1 = math.radians(c1.longitude)
    lat2 = math.radians(c2.latitude)
    lon2 = math.radians(c2.longitude)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)

    return 2 * R * math.asin(math.sqrt(a))
    