import unittest
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from simulator.domain.drone import Drone
from simulator.domain.mission import (
    Mission,
    MissionPhase,
)
from simulator.scenarios.maintenance_lifecycle import (
    MaintenanceLifecycleScenario,
)


class TestMaintenanceLifecycleScenario(
    unittest.TestCase
):

    @staticmethod
    def _build_drone() -> Drone:

        return Drone(
            drone_id="DRN-004",
            battalion_id="BTN-01",
            latitude=72.0,
            longitude=-40.0,
            altitude_m=120.0,
            ground_speed_mps=20.0,
            vertical_speed_mps=0.0,
            heading_deg=45.0,
        )

    @staticmethod
    def _build_mission() -> Mission:

        return Mission(
            mission_id="MSN-004",
            mission_type="training",
            assigned_drone_id="DRN-004",
            route_instance_id="ROUTE-004",
            target_altitude_m=120.0,
            climb_rate_mps=30.0,
            descent_rate_mps=30.0,
            cruise_speed_mps=20.0,
            orbit_radius_m=60.0,
            orbit_duration_seconds=20.0,
        )

    @staticmethod
    def _event_time(
        second: int,
    ) -> datetime:

        base_time = datetime(
            2026,
            8,
            25,
            18,
            0,
            0,
            tzinfo=timezone.utc,
        )

        return (
            base_time
            + timedelta(
                seconds=second
            )
        )

    @staticmethod
    def _build_scenario():
        return MaintenanceLifecycleScenario(
            target_drone_id="DRN-004",
            degrade_at_seconds=55.0,
            maintenance_duration_seconds=8.0,
            return_to_service_hold_seconds=2.0,
        )

    def _update(
        self,
        scenario,
        drone,
        mission,
        second,
    ):

        return scenario.update(
            drone=drone,
            mission=mission,
            current_seconds=float(
                second
            ),
            event_time=(
                self._event_time(
                    second
                )
            ),
            schema_version="1.0",
            simulator_run_id=(
                "RUN-FLEET005-MNT-001"
            ),
            scenario=(
                "maintenance_lifecycle"
            ),
            seed=20260825,
        )

    def test_health_degradation_creates_required_events(
        self,
    ):

        drone = self._build_drone()
        mission = self._build_mission()
        scenario = self._build_scenario()

        events = self._update(
            scenario,
            drone,
            mission,
            55,
        )

        self.assertEqual(
            drone.platform_health,
            "DEGRADED",
        )

        self.assertEqual(
            [
                event["event_type"]
                for event
                in events
            ],
            [
                "state_transition",
                "maintenance_event",
            ],
        )

        self.assertEqual(
            events[
                1
            ][
                "payload"
            ][
                "maintenance_action"
            ],
            "MAINTENANCE_REQUIRED",
        )

    def test_maintenance_starts_only_after_landing(
        self,
    ):

        drone = self._build_drone()
        mission = self._build_mission()
        scenario = self._build_scenario()

        self._update(
            scenario,
            drone,
            mission,
            55,
        )

        before_landing = self._update(
            scenario,
            drone,
            mission,
            80,
        )

        self.assertEqual(
            before_landing,
            [],
        )

        mission.phase = (
            MissionPhase.LANDED
        )

        drone.asset_state = (
            "AVAILABLE"
        )

        after_landing = self._update(
            scenario,
            drone,
            mission,
            82,
        )

        self.assertEqual(
            drone.asset_state,
            "MAINTENANCE",
        )

        self.assertEqual(
            [
                event["event_type"]
                for event
                in after_landing
            ],
            [
                "maintenance_event",
                "state_transition",
                "status_confirmation",
            ],
        )

    def test_maintenance_completion_restores_health_and_service(
        self,
    ):

        drone = self._build_drone()
        mission = self._build_mission()
        scenario = self._build_scenario()

        self._update(
            scenario,
            drone,
            mission,
            55,
        )

        mission.phase = (
            MissionPhase.LANDED
        )

        drone.asset_state = (
            "AVAILABLE"
        )

        self._update(
            scenario,
            drone,
            mission,
            82,
        )

        completion_events = (
            self._update(
                scenario,
                drone,
                mission,
                90,
            )
        )

        self.assertEqual(
            drone.platform_health,
            "NORMAL",
        )

        self.assertEqual(
            drone.asset_state,
            "RETURNED_TO_SERVICE",
        )

        self.assertEqual(
            [
                event["event_type"]
                for event
                in completion_events
            ],
            [
                "maintenance_event",
                "state_transition",
                "state_transition",
                "status_confirmation",
            ],
        )

        release_events = (
            self._update(
                scenario,
                drone,
                mission,
                92,
            )
        )

        self.assertEqual(
            drone.asset_state,
            "AVAILABLE",
        )

        self.assertTrue(
            scenario.lifecycle_completed
        )

        self.assertEqual(
            [
                event["event_type"]
                for event
                in release_events
            ],
            [
                "maintenance_event",
                "state_transition",
                "status_confirmation",
            ],
        )

    def test_scenario_events_share_one_drone_sequence(
        self,
    ):

        drone = self._build_drone()
        mission = self._build_mission()
        scenario = self._build_scenario()

        all_events = []

        all_events.extend(
            self._update(
                scenario,
                drone,
                mission,
                55,
            )
        )

        mission.phase = (
            MissionPhase.LANDED
        )

        drone.asset_state = (
            "AVAILABLE"
        )

        all_events.extend(
            self._update(
                scenario,
                drone,
                mission,
                82,
            )
        )

        all_events.extend(
            self._update(
                scenario,
                drone,
                mission,
                90,
            )
        )

        all_events.extend(
            self._update(
                scenario,
                drone,
                mission,
                92,
            )
        )

        self.assertEqual(
            [
                event[
                    "source_sequence_number"
                ]
                for event
                in all_events
            ],
            list(
                range(
                    1,
                    len(
                        all_events
                    )
                    + 1,
                )
            ),
        )


if __name__ == "__main__":
    unittest.main()
