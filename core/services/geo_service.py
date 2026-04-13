"""
Geo-Service: Haversine + OSRM Public API
Zero-cost distance calculation for charity matching.
"""
import math
import requests
import logging

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on Earth using the Haversine formula.
    Returns distance in kilometers.
    """
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def osrm_road_distance(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Query OSRM Public API for exact road distance.
    Returns (distance_km, duration_minutes) or (None, None) on failure.
    
    API: http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}
    Note: OSRM uses lon,lat order (not lat,lon).
    """
    try:
        url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
            f"?overview=false"
        )
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('code') == 'Ok' and data.get('routes'):
            route = data['routes'][0]
            distance_km = route['distance'] / 1000.0  # meters → km
            duration_min = route['duration'] / 60.0    # seconds → minutes
            return round(distance_km, 2), round(duration_min, 1)

        logger.warning(f"OSRM returned non-Ok: {data.get('code')}")
        return None, None

    except Exception as e:
        logger.error(f"OSRM API error: {e}")
        return None, None


def filter_charities_by_radius(donor_lat, donor_lon, charities, max_radius_km=25):
    """
    Quick spatial filter using Haversine.
    charities: queryset/list of User objects with profile.latitude/longitude
    Returns list of (user, haversine_distance_km) sorted by distance.
    """
    results = []
    for charity in charities:
        profile = charity.profile
        dist = haversine_distance(donor_lat, donor_lon, profile.latitude, profile.longitude)
        if dist <= max_radius_km:
            results.append((charity, round(dist, 2)))

    results.sort(key=lambda x: x[1])
    return results


def get_route_details(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Get complete route info: both haversine and road distance.
    Returns dict with all distance data.
    """
    h_dist = haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
    road_dist, duration = osrm_road_distance(origin_lat, origin_lon, dest_lat, dest_lon)

    return {
        'haversine_km': round(h_dist, 2),
        'road_km': road_dist or round(h_dist * 1.3, 2),  # Fallback: haversine × 1.3
        'duration_min': duration or round(h_dist * 2.5, 1),  # Fallback estimate
        'osrm_available': road_dist is not None,
    }
