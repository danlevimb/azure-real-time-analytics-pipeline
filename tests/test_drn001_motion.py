import unittest

from simulator.domain.drone import Drone
from simulator.domain.route import (
    RouteInstance,
    Waypoint,
)
from simulator.simulation.geodesy import (
    haversine_distance_m,
)
from simulator.simulation.movement_engine import (
    MovementEngine,
)


class TestDRN001Motion(unittest.TestCase):

    def test_ten_seconds_at_twenty_mps(self):

        start_lat = 72.0
        start_lon = -40.0

        drone = Drone(
            drone_id="DRN-001",
            battalion_id="BTN-01",
            latitude=start_lat,
            longitude=start_lon,
            altitude_m=120.0,
            ground_speed_mps=20.0,
            heading_deg=45.0,
        )

        route = RouteInstance(
            route_instance_id="TEST-ROUTE",
            waypoints=[
                Waypoint(
                    waypoint_id="WP-FAR",
                    latitude=72.1,
                    longitude=-39.7,
                )
            ],
        )

        for _ in range(40):
            MovementEngine.update_route(
                drone,
                route,
                0.25,
            )

        distance = haversine_distance_m(
            start_lat,
            start_lon,
            drone.latitude,
            drone.longitude,
        )

        self.assertAlmostEqual(
            distance,
            200.0,
            delta=0.5,
        )

    def test_route_reaches_all_waypoints(self):

        final_lat = 71.998982503
        final_lon = -39.993744597

        drone = Drone(
            drone_id="DRN-001",
            battalion_id="BTN-01",
            latitude=72.0,
            longitude=-40.0,
            altitude_m=120.0,
            ground_speed_mps=20.0,
            heading_deg=0.0,
        )

        route = RouteInstance(
            route_instance_id="TEST-WAYPOINTS",
            waypoints=[
                Waypoint(
                    "WP-01",
                    72.000953849,
                    -39.996913043,
                ),
                Waypoint(
                    "WP-02",
                    72.000672683,
                    -39.991753969,
                ),
                Waypoint(
                    "WP-03",
                    final_lat,
                    final_lon,
                ),
            ],
        )

        # 35 simulated seconds maximum.
        for _ in range(140):

            result = MovementEngine.update_route(
                drone,
                route,
                0.25,
            )

            if result.route_completed:
                break

        self.assertTrue(route.is_complete)

        remaining = haversine_distance_m(
            drone.latitude,
            drone.longitude,
            final_lat,
            final_lon,
        )

        self.assertAlmostEqual(
            remaining,
            0.0,
            delta=0.1,
        )


if __name__ == "__main__":
    unittest.main()