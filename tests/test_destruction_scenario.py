import unittest
from datetime import (datetime, timezone,)
from simulator.domain.drone import Drone
from simulator.domain.mission import (Mission, MissionStatus,)
from simulator.scenarios.destruction import (DestructionScenario,)


class TestDestructionScenario(unittest.TestCase):

    @staticmethod
    def _drone():

        return Drone(
            drone_id = "DRN-003",
            battalion_id = "BTN-01",
            latitude = 72.0,
            longitude = -40.0,
            altitude_m = 120.0,
            ground_speed_mps = 20.0,
            heading_deg = 45.0,
        )

    @staticmethod
    def _mission():

        mission = Mission(
            mission_id = "MSN-003",
            mission_type = "training",
            assigned_drone_id = "DRN-003",
            route_instance_id = "ROUTE-TEST",
            target_altitude_m = 120.0,
            climb_rate_mps = 30.0,
            descent_rate_mps = 30.0,
            cruise_speed_mps = 20.0,
            orbit_radius_m = 60.0,
            orbit_duration_seconds = 20.0,
            orbit_direction = "CLOCKWISE",
        )

        mission.status = MissionStatus.ACTIVE

        return mission

    @staticmethod
    def _update(*, destruction, drone, mission, seconds,):

        return destruction.update(
            drone=drone,
            mission=mission,
            current_seconds=seconds,
            event_time=datetime(
                2026,
                9,
                28,
                18,
                0,
                tzinfo=timezone.utc,
            ),
            schema_version = "1.2",
            simulator_run_id = "RUN-DESTRUCTION-TEST",
            scenario = "drone_destruction",
            seed = 20260928,
        )

    def test_destruction_sets_terminal_states(self,):

        destruction = (
            DestructionScenario(target_drone_id = "DRN-003", destroy_at_seconds=30.0,))

        drone = self._drone()
        mission = self._mission()

        events = self._update(
            destruction=destruction,
            drone=drone,
            mission=mission,
            seconds=30.0,
        )

        self.assertEqual(drone.asset_state, "DESTROYED",)
        self.assertEqual(mission.status, MissionStatus.ABORTED,)
        self.assertEqual(drone.connection_state, "DISCONNECTED",)
        self.assertEqual(drone.ground_speed_mps, 0.0,)
        self.assertEqual(drone.vertical_speed_mps, 0.0, )
        self.assertEqual(len(events), 3, )

    def test_destruction_emits_once(self,):

        destruction = (
            DestructionScenario(
                target_drone_id=(
                    "DRN-003"
                ),
                destroy_at_seconds=30.0,
            )
        )

        drone = self._drone()
        mission = self._mission()

        first = self._update(
            destruction=destruction,
            drone=drone,
            mission=mission,
            seconds=30.0,
        )

        repeated = self._update(
            destruction=destruction,
            drone=drone,
            mission=mission,
            seconds=31.0,
        )

        self.assertEqual(len(first), 3,)
        self.assertEqual(repeated, [],)
        
    def test_destruction_does_not_affect_other_drone(self, ):

        destruction = (DestructionScenario(target_drone_id = "DRN-003", destroy_at_seconds = 30.0,))

        drone = self._drone()
        drone.drone_id = "DRN-004"
        mission = self._mission()

        events = self._update(
            destruction=destruction,
            drone=drone,
            mission=mission,
            seconds=30.0,
        )

        self.assertEqual(events,[],)
        self.assertNotEqual(drone.asset_state, "DESTROYED",)

if __name__ == "__main__":
    unittest.main()