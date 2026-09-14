import unittest

from simulator.domain.drone import Drone
from simulator.domain.mission import (
    Mission,
    MissionPhase,
)
from simulator.domain.route import (
    RouteInstance,
    Waypoint,
)
from simulator.domain.states.mission_state_machine import (
    MissionStateMachine,
)
from simulator.simulation.mission_engine import (
    MissionEngine,
)


class TestMission(unittest.TestCase):

    def test_invalid_phase_transition(self):

        mission = Mission(
            mission_id="MSN-001",
            mission_type="training",
            assigned_drone_id="DRN-001",
            route_instance_id="ROUTE-TEST",
            target_altitude_m=120.0,
            climb_rate_mps=30.0,
            descent_rate_mps=30.0,
            cruise_speed_mps=20.0,
            orbit_radius_m=60.0,
            orbit_duration_seconds=20.0,
            orbit_direction="CLOCKWISE",
        )

        with self.assertRaises(ValueError):
            MissionStateMachine.transition(
                mission,
                MissionPhase.ON_MISSION,
            )

    def test_takeoff_reaches_target_altitude(self):

        drone = Drone(
            drone_id="DRN-001",
            battalion_id="BTN-01",
            latitude=72.0,
            longitude=-40.0,
            altitude_m=0.0,
            ground_speed_mps=20.0,
            heading_deg=0.0,
        )

        mission = Mission(
            mission_id="MSN-001",
            mission_type="training",
            assigned_drone_id="DRN-001",
            route_instance_id="ROUTE-TEST",
            target_altitude_m=120.0,
            climb_rate_mps=30.0,
            descent_rate_mps=30.0,
            cruise_speed_mps=20.0,
            orbit_radius_m=60.0,
            orbit_duration_seconds=20.0,
            orbit_direction="CLOCKWISE",
        )

        route = RouteInstance(
            route_instance_id="ROUTE-TEST",
            waypoints=[
                Waypoint(
                    waypoint_id="WP-01",
                    latitude=72.01,
                    longitude=-39.99,
                )
            ],
        )

        MissionEngine.start(
            mission,
            drone,
        )
        
        self.assertEqual(
            drone.ground_speed_mps,
            0.0,
        )

        self.assertEqual(
            drone.vertical_speed_mps,
            30.0,
        )

        for _ in range(16):
            MissionEngine.update(
                mission,
                drone,
                route,
                0.25,
            )
            
        self.assertEqual(
            drone.ground_speed_mps,
            20.0,
        )

        self.assertEqual(
            drone.vertical_speed_mps,
            0.0,
        )

        self.assertEqual(
            mission.phase,
            MissionPhase.EN_ROUTE,
        )

        self.assertAlmostEqual(
            drone.altitude_m,
            120.0,
            delta=0.01,
        )

        # It must not move horizontally
        # while taking off.
        self.assertAlmostEqual(
            drone.latitude,
            72.0,
            places=6,
        )

        self.assertAlmostEqual(
            drone.longitude,
            -40.0,
            places=6,
        )


if __name__ == "__main__":
    unittest.main()