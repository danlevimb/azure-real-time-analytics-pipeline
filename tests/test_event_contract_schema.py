import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from simulator.domain.drone import Drone
from simulator.domain.mission import Mission
from simulator.telemetry.event_factory import EventFactory


class TestEventContractSchemas(unittest.TestCase):

    @staticmethod
    def _schema(version: str) -> dict:

        root = Path(__file__).resolve().parents[1]
        path = (
            root
            / "contracts"
            / f"event_contract_v{version.replace('.', '_')}.schema.json"
        )

        return json.loads(
            path.read_text(encoding="utf-8")
        )

    @staticmethod
    def _drone() -> Drone:

        return Drone(
            drone_id="DRN-001",
            battalion_id="BTN-01",
            latitude=72.0,
            longitude=-40.0,
            altitude_m=120.0,
            ground_speed_mps=20.0,
            vertical_speed_mps=0.0,
            heading_deg=45.0,
            battery_pct=98.0,
            optic_fiber_remaining_m=8421.5,
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
    def _time():

        return datetime(
            2026,
            9,
            22,
            18,
            0,
            0,
            tzinfo=timezone.utc,
        )

    def test_v1_0_telemetry_validates(self):

        event = EventFactory.telemetry(
            drone=self._drone(),
            mission=self._mission(),
            event_time=self._time(),
            schema_version="1.0",
            simulator_run_id="RUN-001",
            scenario="baseline",
            seed=20260922,
        )

        Draft202012Validator(
            self._schema("1.0")
        ).validate(event)

    def test_v1_1_telemetry_validates(self):

        event = EventFactory.telemetry(
            drone=self._drone(),
            mission=self._mission(),
            event_time=self._time(),
            schema_version="1.1",
            simulator_run_id="RUN-001",
            scenario="baseline",
            seed=20260922,
        )

        Draft202012Validator(
            self._schema("1.1")
        ).validate(event)

    def test_v1_1_state_transition_validates(self):

        event = EventFactory.state_transition(
            drone=self._drone(),
            mission=self._mission(),
            event_time=self._time(),
            schema_version="1.1",
            simulator_run_id="RUN-001",
            scenario="operational_failure",
            seed=20260922,
            state_domain="connection_state",
            previous_state="CONNECTED",
            new_state="DISCONNECTED",
            reason_code="SIMULATED_LINK_LOSS",
        )

        Draft202012Validator(
            self._schema("1.1")
        ).validate(event)


if __name__ == "__main__":
    unittest.main()
