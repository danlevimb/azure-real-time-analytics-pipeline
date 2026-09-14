from math import degrees
from dataclasses import dataclass

from simulator.domain.drone import Drone
from simulator.domain.route import RouteInstance
from simulator.simulation.geodesy import (
    destination_point,
    haversine_distance_m,
    initial_bearing_deg,
)


@dataclass
class MovementResult:
    reached_waypoints: list[str]
    route_completed: bool


class MovementEngine:

    @staticmethod        
    def update_orbit(
        drone: Drone,
        center_latitude: float,
        center_longitude: float,
        radius_m: float,
        current_angle_deg: float,
        dt_seconds: float,
        clockwise: bool = True,
    ) -> float:

        if radius_m <= 0:
            raise ValueError(
                "Orbit radius must be > 0"
            )

        arc_distance_m = (
            drone.ground_speed_mps
            * dt_seconds
        )

        angular_change_deg = degrees(
            arc_distance_m / radius_m
        )

        if clockwise:
            new_angle_deg = (
                current_angle_deg
                + angular_change_deg
            )
        else:
            new_angle_deg = (
                current_angle_deg
                - angular_change_deg
            )

        new_angle_deg %= 360.0

        (
            drone.latitude,
            drone.longitude,
        ) = destination_point(
            latitude_deg=center_latitude,
            longitude_deg=center_longitude,
            bearing_deg=new_angle_deg,
            distance_m=radius_m,
        )

        # Tangential heading.
        if clockwise:
            drone.heading_deg = (
                new_angle_deg + 90.0
            ) % 360.0
        else:
            drone.heading_deg = (
                new_angle_deg - 90.0
            ) % 360.0

        return new_angle_deg
    
    def update_route(
        drone: Drone,
        route: RouteInstance,
        dt_seconds: float,
    ) -> MovementResult:

        reached_waypoints: list[str] = []

        distance_budget_m = (
            drone.ground_speed_mps
            * dt_seconds
        )

        while (
            distance_budget_m > 0
            and not route.is_complete
        ):
            waypoint = route.current_waypoint

            if waypoint is None:
                break

            remaining_distance_m = (
                haversine_distance_m(
                    drone.latitude,
                    drone.longitude,
                    waypoint.latitude,
                    waypoint.longitude,
                )
            )

            bearing_deg = initial_bearing_deg(
                drone.latitude,
                drone.longitude,
                waypoint.latitude,
                waypoint.longitude,
            )

            drone.heading_deg = bearing_deg

            if (
                distance_budget_m
                >= remaining_distance_m
            ):
                # Snap exactly to waypoint.
                drone.latitude = waypoint.latitude
                drone.longitude = waypoint.longitude

                distance_budget_m -= (
                    remaining_distance_m
                )

                reached_waypoints.append(
                    waypoint.waypoint_id
                )

                route.advance()

            else:
                (
                    drone.latitude,
                    drone.longitude,
                ) = destination_point(
                    latitude_deg=drone.latitude,
                    longitude_deg=drone.longitude,
                    bearing_deg=bearing_deg,
                    distance_m=distance_budget_m,
                )

                distance_budget_m = 0

        return MovementResult(
            reached_waypoints=reached_waypoints,
            route_completed=route.is_complete,
        )