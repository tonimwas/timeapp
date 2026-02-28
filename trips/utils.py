import math
import requests
from typing import Tuple

from django.conf import settings


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth using the Haversine formula.
    Returns distance in kilometers.
    """
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Earth's radius in km
    R = 6371.0
    return R * c


def calculate_transport(lat1: float, lng1: float, lat2: float, lng2: float) -> Tuple[str, int, int]:
    """
    Calculate transport details between two coordinates.
    Returns (mode, fare, minutes).
    """
    distance_km = haversine_distance(lat1, lng1, lat2, lng2)
    fare = int(distance_km * settings.TRANSPORT_FARE_RATE)  # Round to nearest int
    minutes = int(distance_km * settings.TRANSPORT_TIME_MULTIPLIER)
    mode = "Matatu"  # Default mode
    return mode, fare, minutes


def get_neighbourhood(lat: float, lng: float) -> str:
    """
    Reverse geocode lat/lng to determine neighbourhood using Nominatim.
    Returns the neighbourhood name or 'Unknown'.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}"
    response = requests.get(url, headers={'User-Agent': 'TimeApp'})
    if response.status_code == 200:
        data = response.json()
        display_name = data.get('display_name', '')
        parts = display_name.split(', ')
        neighbourhood = parts[0] if parts else 'Unknown'
        return neighbourhood
    return 'Unknown'
