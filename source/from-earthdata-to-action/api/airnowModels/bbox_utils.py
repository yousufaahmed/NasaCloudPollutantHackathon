import math


def miles_to_degree_lat(miles: float) -> float:
    """Convert miles to degrees latitude. Roughly 69 miles per degree."""
    return miles / 69.0


def miles_to_degree_lon(miles: float, latitude_deg: float) -> float:
    """Convert miles to degrees longitude at a given latitude."""
    miles_per_degree = 69.172 * math.cos(math.radians(latitude_deg))
    if miles_per_degree == 0:
        # Near the poles, fall back to a very small delta to avoid division by zero
        return 0.0
    return miles / miles_per_degree


def bbox_from_center_miles(latitude_deg: float, longitude_deg: float, miles_to_edge: float = 10.0):
    """
    Return a bounding box (lon_min, lat_min, lon_max, lat_max) measured in degrees
    such that the distance from the center to any edge is `miles_to_edge` miles.

    The box is axis-aligned in WGS84 (EPSG:4326).
    """
    dlat = miles_to_degree_lat(miles_to_edge)
    dlon = miles_to_degree_lon(miles_to_edge, latitude_deg)

    lat_min = latitude_deg - dlat
    lat_max = latitude_deg + dlat
    lon_min = longitude_deg - dlon
    lon_max = longitude_deg + dlon

    return lon_min, lat_min, lon_max, lat_max


def bbox_to_string(bbox: tuple) -> str:
    """Format (lon_min, lat_min, lon_max, lat_max) as AirNow BBOX string."""
    lon_min, lat_min, lon_max, lat_max = bbox
    return f"{lon_min:.6f},{lat_min:.6f},{lon_max:.6f},{lat_max:.6f}"


