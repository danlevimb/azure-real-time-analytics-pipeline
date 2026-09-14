import unittest
from datetime import (
    datetime,
    timezone,
)

from simulator.domain.drone import Drone
from simulator.domain.mission import Mission
from simulator.telemetry.event_factory import (
    EventFactory,
)


class TestEventFactory(unittest.TestCase):

    @staticmethod
    def _build_drone() -> Drone:

        return Drone(
            drone_id="DRN-001",
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

    def test_state_transition_event_contract(self):

        drone = self._build_drone()
        mission = self._build_mission()

        event = EventFactory.state_transition(
            drone=drone,
            mission=mission,
            event_time=datetime(
                2026,
                8,
                19,
                18,
                0,
                4,
                tzinfo=timezone.utc,
            ),
            schema_version="1.0",
            simulator_run_id="RUN-DRN001-001",
            scenario="baseline",
            seed=20260819,
            state_domain="mission_phase",
            previous_state="TAKEOFF",
            new_state="EN_ROUTE",
            reason_code="TARGET_ALTITUDE_REACHED",
        )

        self.assertEqual(
            event["event_type"],
            "state_transition",
        )

        self.assertEqual(
            event["payload"]["state_domain"],
            "mission_phase",
        )

        self.assertEqual(
            event["payload"]["previous_state"],
            "TAKEOFF",
        )

        self.assertEqual(
            event["payload"]["new_state"],
            "EN_ROUTE",
        )

        self.assertEqual(
            event["payload"]["reason_code"],
            "TARGET_ALTITUDE_REACHED",
        )

        self.assertEqual(
            event["source_sequence_number"],
            1,
        )

    def test_telemetry_event_contract(self):

        drone = self._build_drone()
        mission = self._build_mission()

        event = EventFactory.telemetry(
            drone=drone,
            mission=mission,
            event_time=datetime(
                2026,
                8,
                19,
                18,
                0,
                1,
                tzinfo=timezone.utc,
            ),
            schema_version="1.0",
            simulator_run_id=(
                "RUN-DRN001-001"
            ),
            scenario="baseline",
            seed=20260819,
        )

        self.assertEqual(
            event["event_type"],
            "telemetry",
        )

        self.assertEqual(
            event["drone_id"],
            "DRN-001",
        )

        self.assertEqual(
            event["source_sequence_number"],
            1,
        )

        self.assertEqual(
            event["payload"]["position"][
                "altitude_m"
            ],
            120.0,
        )

        self.assertEqual(
            event["event_time"],
            "2026-08-19T18:00:01Z",
        )

    def test_maintenance_event_contract(self):

        drone = self._build_drone()
        mission = self._build_mission()

        event = EventFactory.maintenance_event(
            drone=drone,
            mission=mission,
            event_time=datetime(
                2026,
                8,
                19,
                18,
                1,
                0,
                tzinfo=timezone.utc,
            ),
            schema_version="1.0",
            simulator_run_id=(
                "RUN-DRN001-001"
            ),
            scenario="maintenance_lifecycle",
            seed=20260819,
            maintenance_action=(
                "MAINTENANCE_REQUIRED"
            ),
            maintenance_category=(
                "PLATFORM_INSPECTION"
            ),
            reason_code=(
                "HEALTH_DEGRADATION"
            ),
            severity="MEDIUM",
        )

        self.assertEqual(
            event["event_type"],
            "maintenance_event",
        )

        self.assertEqual(
            event["payload"][
                "maintenance_action"
            ],
            "MAINTENANCE_REQUIRED",
        )

        self.assertEqual(
            event["payload"][
                "maintenance_category"
            ],
            "PLATFORM_INSPECTION",
        )

        self.assertEqual(
            event["payload"][
                "reason_code"
            ],
            "HEALTH_DEGRADATION",
        )

        self.assertEqual(
            event["payload"]["severity"],
            "MEDIUM",
        )

        self.assertEqual(
            event["source_sequence_number"],
            1,
        )

    def test_status_confirmation_event_contract(self):

        drone = self._build_drone()
        mission = self._build_mission()

        event = EventFactory.status_confirmation(
            drone=drone,
            mission=mission,
            event_time=datetime(
                2026,
                8,
                19,
                18,
                1,
                1,
                tzinfo=timezone.utc,
            ),
            schema_version="1.0",
            simulator_run_id=(
                "RUN-DRN001-001"
            ),
            scenario="maintenance_lifecycle",
            seed=20260819,
            state_domain="asset_state",
            confirmed_state="MAINTENANCE",
            confirmation_type=(
                "SYSTEM_CONFIRMATION"
            ),
            reason_code=(
                "MAINTENANCE_ENTRY_CONFIRMED"
            ),
        )

        self.assertEqual(
            event["event_type"],
            "status_confirmation",
        )

        self.assertEqual(
            event["payload"][
                "state_domain"
            ],
            "asset_state",
        )

        self.assertEqual(
            event["payload"][
                "confirmed_state"
            ],
            "MAINTENANCE",
        )

        self.assertEqual(
            event["payload"][
                "confirmation_type"
            ],
            "SYSTEM_CONFIRMATION",
        )

        self.assertEqual(
            event["payload"][
                "reason_code"
            ],
            "MAINTENANCE_ENTRY_CONFIRMED",
        )

        self.assertEqual(
            event["source_sequence_number"],
            1,
        )

    def test_sequence_is_shared_across_event_families(self):

        drone = self._build_drone()
        mission = self._build_mission()

        event_time = datetime(
            2026,
            8,
            19,
            18,
            1,
            0,
            tzinfo=timezone.utc,
        )

        telemetry = EventFactory.telemetry(
            drone=drone,
            mission=mission,
            event_time=event_time,
            schema_version="1.0",
            simulator_run_id="RUN-DRN001-001",
            scenario="maintenance_lifecycle",
            seed=20260819,
        )

        maintenance = (
            EventFactory.maintenance_event(
                drone=drone,
                mission=mission,
                event_time=event_time,
                schema_version="1.0",
                simulator_run_id=(
                    "RUN-DRN001-001"
                ),
                scenario=(
                    "maintenance_lifecycle"
                ),
                seed=20260819,
                maintenance_action=(
                    "MAINTENANCE_REQUIRED"
                ),
                maintenance_category=(
                    "PLATFORM_INSPECTION"
                ),
                reason_code=(
                    "HEALTH_DEGRADATION"
                ),
                severity="MEDIUM",
            )
        )

        confirmation = (
            EventFactory.status_confirmation(
                drone=drone,
                mission=mission,
                event_time=event_time,
                schema_version="1.0",
                simulator_run_id=(
                    "RUN-DRN001-001"
                ),
                scenario=(
                    "maintenance_lifecycle"
                ),
                seed=20260819,
                state_domain="asset_state",
                confirmed_state=(
                    "MAINTENANCE"
                ),
                confirmation_type=(
                    "SYSTEM_CONFIRMATION"
                ),
                reason_code=(
                    "MAINTENANCE_ENTRY_CONFIRMED"
                ),
            )
        )

        transition = (
            EventFactory.state_transition(
                drone=drone,
                mission=mission,
                event_time=event_time,
                schema_version="1.0",
                simulator_run_id=(
                    "RUN-DRN001-001"
                ),
                scenario=(
                    "maintenance_lifecycle"
                ),
                seed=20260819,
                state_domain="asset_state",
                previous_state="ACTIVE",
                new_state="MAINTENANCE",
                reason_code=(
                    "MAINTENANCE_STARTED"
                ),
            )
        )

        self.assertEqual(
            [
                telemetry[
                    "source_sequence_number"
                ],
                maintenance[
                    "source_sequence_number"
                ],
                confirmation[
                    "source_sequence_number"
                ],
                transition[
                    "source_sequence_number"
                ],
            ],
            [
                1,
                2,
                3,
                4,
            ],
        )

        self.assertEqual(
            [
                telemetry[
                    "event_type"
                ],
                maintenance[
                    "event_type"
                ],
                confirmation[
                    "event_type"
                ],
                transition[
                    "event_type"
                ],
            ],
            [
                "telemetry",
                "maintenance_event",
                "status_confirmation",
                "state_transition",
            ],
        )


if __name__ == "__main__":
    unittest.main()
