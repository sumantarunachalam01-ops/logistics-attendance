import math

# Earth radius in meters
EARTH_RADIUS_METERS = 6371000

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth
    using the Haversine formula. Returns distance in meters.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')

    # Convert decimal degrees to radians
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))

    # Haversine formula
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = EARTH_RADIUS_METERS * c
    return round(distance, 1)

def is_within_geofence(user_lat: float, user_lon: float,
                       hub_lat: float, hub_lon: float,
                       allowed_radius_meters: int) -> tuple[bool, float]:
    """
    Check if user coordinates fall inside allowed radius of hub coordinates.
    Returns (is_inside, distance_meters).
    """
    distance = calculate_haversine_distance(user_lat, user_lon, hub_lat, hub_lon)
    is_inside = distance <= allowed_radius_meters
    return is_inside, distance
