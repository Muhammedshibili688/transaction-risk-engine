import math
from typing import Tuple

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Stateless helper to calculate distance between two coordinates in km.
    """
    if None in (lat1, lon1, lat2, lon2):
        return 0.0
    
    R = 6371.0 # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_time_delta_hours(time_str1: str, time_str2: str) -> float:
    """Calculates hours between two ISO timestamps."""
    from datetime import datetime
    t1 = datetime.fromisoformat(time_str1)
    t2 = datetime.fromisoformat(time_str2)
    delta = abs((t2 - t1).total_seconds())
    return max(delta / 3600, 0.0001) # Avoid division by zero (min 0.36 seconds)