import tempfile
import unittest

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path

from simulator.domain.drone import Drone
from simulator.domain.mission import Mission
from simulator.observability.ground_truth_logger import (
    GroundTruthLogger,
)


class TestGroundTruthLogger(unittest.TestCase):

    def test_ground_truth_snapshot_contract(
        self,
    ):

        drone = Drone(
            drone_id="DRN-001",
            battalion_id="BTN-01",
            latitude=72.0,
            longitude=-40.0,
            altitude_m=120.0,
            ground_speed_mps=20.0,
            vertical_speed_mps=0.0,
            heading_deg=45.0,
            communication_mode="FIBER",
            optic_fiber_remaining_m=10000.0,
        )

        mission = Mission(
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

        with tempfile.TemporaryDirectory() as temp_dir:

            path = (
                Path(temp_dir)
                / "ground_truth.jsonl"
            )

            logger = GroundTruthLogger(
                output_path=path,
                simulator_run_id=(
                    "RUN-DRN001-001"
                ),
            )

            snapshot = logger.log_snapshot(
                drone=drone,
                mission=mission,
                simulation_time=datetime(
                    2026,
                    8,
                    19,
                    18,
                    0,
                    1,
                    tzinfo=timezone.utc,
                ),
                elapsed_seconds=1.0,
            )

            logger.close()

            self.assertEqual(
                snapshot["record_type"],
                "ground_truth_snapshot",
            )

            self.assertEqual(
                snapshot["drone_id"],
                "DRN-001",
            )

            self.assertEqual(
                snapshot["position"][
                    "altitude_m"
                ],
                120.0,
            )

            self.assertEqual(
                snapshot["power"][
                    "battery_pct"
                ],
                100.0,
            )

            self.assertEqual(
                snapshot["consumables"][
                    "optic_fiber_remaining_m"
                ],
                10000.0,
            )

            self.assertEqual(
                snapshot["states"][
                    "mission_phase"
                ],
                "READY",
            )

            self.assertTrue(
                path.exists()
            )

            lines = path.read_text(
                encoding="utf-8"
            ).splitlines()

            self.assertEqual(
                len(lines),
                1,
            )


if __name__ == "__main__":
    unittest.main()