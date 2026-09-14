from math import (
    asin,
    atan2,
    cos,
    degrees,
    pi,
    radians,
    sin,
    sqrt,
)


EARTH_RADIUS_M = 6_371_008.8


def destination_point(
    latitude_deg: float,
    longitude_deg: float,
    bearing_deg: float,
    distance_m: float,
) -> tuple[float, float]:

    lat1 = radians(latitude_deg)
    lon1 = radians(longitude_deg)
    bearing = radians(bearing_deg)

    angular_distance = distance_m / EARTH_RADIUS_M

    lat2 = asin(
        sin(lat1) * cos(angular_distance)
        + cos(lat1)
        * sin(angular_distance)
        * cos(bearing)
    )

    lon2 = lon1 + atan2(
        sin(bearing)
        * sin(angular_distance)
        * cos(lat1),
        cos(angular_distance)
        - sin(lat1) * sin(lat2),
    )

    # Normalize longitude to [-180, 180)
    lon2 = (lon2 + pi) % (2 * pi) - pi

    return degrees(lat2), degrees(lon2)


def haversine_distance_m(
    lat1_deg: float,
    lon1_deg: float,
    lat2_deg: float,
    lon2_deg: float,
) -> float:

    lat1 = radians(lat1_deg)
    lat2 = radians(lat2_deg)

    delta_lat = radians(lat2_deg - lat1_deg)
    delta_lon = radians(lon2_deg - lon1_deg)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    return 2 * EARTH_RADIUS_M * asin(sqrt(a))

def initial_bearing_deg(
    lat1_deg: float,
    lon1_deg: float,
    lat2_deg: float,
    lon2_deg: float,
) -> float:

    lat1 = radians(lat1_deg)
    lat2 = radians(lat2_deg)

    delta_lon = radians(
        lon2_deg - lon1_deg
    )

    x = (
        sin(delta_lon)
        * cos(lat2)
    )

    y = (
        cos(lat1) * sin(lat2)
        - sin(lat1)
        * cos(lat2)
        * cos(delta_lon)
    )

    bearing = degrees(
        atan2(x, y)
    )

    return (bearing + 360.0) % 360.0