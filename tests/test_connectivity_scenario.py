import unittest
from datetime import datetime, timezone
from simulator.domain.drone import Drone
from simulator.domain.mission import Mission
from simulator.scenarios.connectivity import (ConnectivityScenario,)

class TestConnectivityScenario(unittest.TestCase):

    @staticmethod
    def _drone(communication_mode="RF",) -> Drone:

        return Drone(
            drone_id="DRN-001",
            battalion_id="BTN-01",
            latitude=72.0,
            longitude=-40.0,
            altitude_m=120.0,
            ground_speed_mps=20.0,
            heading_deg=45.0,
            communication_mode=communication_mode,
        )

    @staticmethod
    def _mission() -> Mission:

        return Mission(
            mission_id="MSN-001",
            mission_type="training",
            assigned_drone_id="DRN-001",
            route_instance_id="ROUTE-001",
            target_altitude_m=120.0,
            climb_rate_mps=30.0,
            descent_rate_mps=30.0,
            cruise_speed_mps=20.0,
            orbit_radius_m=60.0,
            orbit_duration_seconds=20.0,
        )

    @staticmethod
    def _event_time():

        return datetime(
            2026,
            9,
            22,
            18,
            0,
            0,
            tzinfo=timezone.utc,
        )

    @staticmethod
    def _scenario(
        reconnect_at_seconds=None,
    ) -> ConnectivityScenario:

        return ConnectivityScenario(
            target_drone_id="DRN-001",
            disconnect_at_seconds=60.0,
            reconnect_at_seconds=(
                reconnect_at_seconds
            ),
            reason_code=(
                "SIMULATED_LINK_LOSS"
            ),
        )

    def _update(self, *, scenario, drone, mission, seconds,):

        return scenario.update(
            drone=drone,
            mission=mission,
            current_seconds=seconds,
            event_time=self._event_time(),
            schema_version="1.1",
            simulator_run_id="RUN-001",
            scenario="operational_failure",
            seed=20260922,
        )

    def test_disconnect_emits_once_and_mutates_state(self):

        scenario = self._scenario()
        drone = self._drone()
        mission = self._mission()

        before = self._update(
            scenario=scenario,
            drone=drone,
            mission=mission,
            seconds=59.75,
        )

        at_disconnect = self._update(
            scenario=scenario,
            drone=drone,
            mission=mission,
            seconds=60.0,
        )

        after = self._update(
            scenario=scenario,
            drone=drone,
            mission=mission,
            seconds=61.0,
        )

        self.assertEqual(before, [])
        self.assertEqual(len(at_disconnect), 1)
        self.assertEqual(after, [])
        self.assertEqual(
            drone.connection_state,
            "DISCONNECTED",
        )

        payload = at_disconnect[0][
            "payload"
        ]

        self.assertEqual(
            payload["state_domain"],
            "connection_state",
        )
        self.assertEqual(
            payload["previous_state"],
            "CONNECTED",
        )
        self.assertEqual(
            payload["new_state"],
            "DISCONNECTED",
        )

    def test_reconnect_emits_once_when_configured(self):

        scenario = self._scenario(
            reconnect_at_seconds=80.0,
        )
        drone = self._drone()
        mission = self._mission()

        self._update(
            scenario=scenario,
            drone=drone,
            mission=mission,
            seconds=60.0,
        )

        reconnect = self._update(
            scenario=scenario,
            drone=drone,
            mission=mission,
            seconds=80.0,
        )

        repeated = self._update(
            scenario=scenario,
            drone=drone,
            mission=mission,
            seconds=81.0,
        )

        self.assertEqual(len(reconnect), 1)
        self.assertEqual(repeated, [])
        self.assertEqual(
            drone.connection_state,
            "CONNECTED",
        )
        self.assertEqual(
            reconnect[0]["payload"][
                "new_state"
            ],
            "CONNECTED",
        )

    def test_rf_jamming_disconnect_reason(self):

        scenario = ConnectivityScenario(
            target_drone_id="DRN-001",
            disconnect_at_seconds=60.0,
            reconnect_at_seconds=None,
            fault_type="RF_JAMMING",
        )

        drone = self._drone("RF")
        mission = self._mission()

        events = self._update(
            scenario=scenario,
            drone=drone,
            mission=mission,
            seconds=60.0,
        )

        self.assertEqual(
            events[0]["payload"][
                "reason_code"
            ],
            "RF_JAMMING",
        )

    def test_fiber_cut_requires_fiber_drone(self):

        scenario = ConnectivityScenario(
            target_drone_id="DRN-001",
            disconnect_at_seconds=60.0,
            reconnect_at_seconds=None,
            fault_type="FIBER_CUT",
        )

        drone = self._drone("RF")
        mission = self._mission()

        with self.assertRaises(
            ValueError
        ):
            self._update(
                scenario=scenario,
                drone=drone,
                mission=mission,
                seconds=60.0,
            )

    def test_fiber_cut_reconnect_emits_repaired_reason(self,):

        scenario = ConnectivityScenario(
            target_drone_id="DRN-001",
            disconnect_at_seconds=60.0,
            reconnect_at_seconds=80.0,
            fault_type="FIBER_CUT",
        )

        drone = self._drone("FIBER")
        mission = self._mission()

        self._update(
            scenario=scenario,
            drone=drone,
            mission=mission,
            seconds=60.0,
        )

        reconnect = self._update(
            scenario=scenario,
            drone=drone,
            mission=mission,
            seconds=80.0,
        )

        self.assertEqual(
            reconnect[0]["payload"][
                "reason_code"
            ],
            "FIBER_REPAIRED",
        )

if __name__ == "__main__":
    unittest.main()
