import hashlib
import json
import tempfile
import unittest

from pathlib import Path

from simulator.observability.run_manifest import (
    write_run_manifest,
)


class TestRunManifest(
    unittest.TestCase
):

    @staticmethod
    def _config(
        run_id: str = "RUN-TEST-001",
    ) -> dict:

        return {
            "simulation": {
                "start_time_utc":
                    "2026-08-27T18:00:00Z",

                "duration_seconds":
                    100,

                "tick_ms":
                    250,

                "speed_multiplier":
                    1,

                "seed":
                    20260827,
            },

            "simulation_context": {
                "simulator_run_id":
                    run_id,

                "scenario":
                    "manifest_test",
            },

            "telemetry": {
                "schema_version":
                    "1.0",

                "interval_ms":
                    1000,
            },

            "transport": {
                "base_delay_ms":
                    750,

                "buffering": {
                    "enabled":
                        False,
                },

                "fault_injection": {},
            },

            "fleet": {
                "fleet_id":
                    "FLEET-TEST",

                "battalion_id":
                    "BTN-TEST",

                "members": [
                    {
                        "drone_id":
                            "DRN-001",

                        "mission_id":
                            "MSN-001",
                    },
                ],
            },

            "maintenance_scenario": {
                "enabled":
                    False,
            },
        }

    def test_manifest_and_snapshot_are_written(
        self,
    ):

        with tempfile.TemporaryDirectory() as temp_dir:

            root = Path(
                temp_dir
            )

            config_path = (
                root
                / "fleet.yaml"
            )

            config_bytes = (
                b"example: exact-bytes\n"
            )

            config_path.write_bytes(
                config_bytes
            )

            output_dir = (
                root
                / "output"
            )

            (
                manifest_path,
                snapshot_path,
            ) = write_run_manifest(
                config_path=config_path,
                config=self._config(),
                output_dir=output_dir,
            )

            self.assertTrue(
                manifest_path.exists()
            )

            self.assertTrue(
                snapshot_path.exists()
            )

            self.assertEqual(
                snapshot_path.read_bytes(),
                config_bytes,
            )

    def test_manifest_hash_matches_exact_config_bytes(
        self,
    ):

        with tempfile.TemporaryDirectory() as temp_dir:

            root = Path(
                temp_dir
            )

            config_path = (
                root
                / "fleet.yaml"
            )

            config_bytes = (
                b"alpha: 1\nbeta: 2\n"
            )

            config_path.write_bytes(
                config_bytes
            )

            output_dir = (
                root
                / "output"
            )

            (
                manifest_path,
                _,
            ) = write_run_manifest(
                config_path=config_path,
                config=self._config(),
                output_dir=output_dir,
            )

            manifest = json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )

            expected_hash = (
                hashlib.sha256(
                    config_bytes
                )
                .hexdigest()
            )

            self.assertEqual(
                manifest[
                    "config_sha256"
                ],
                expected_hash,
            )

            self.assertEqual(
                manifest[
                    "config_validation"
                ],
                "PASSED",
            )

            self.assertEqual(
                manifest[
                    "drone_count"
                ],
                1,
            )

    def test_same_run_id_with_different_config_is_rejected(
        self,
    ):

        with tempfile.TemporaryDirectory() as temp_dir:

            root = Path(
                temp_dir
            )

            output_dir = (
                root
                / "output"
            )

            first_config_path = (
                root
                / "first.yaml"
            )

            first_config_path.write_text(
                "version: one\n",
                encoding="utf-8",
            )

            write_run_manifest(
                config_path=(
                    first_config_path
                ),
                config=self._config(
                    "RUN-COLLISION-001"
                ),
                output_dir=output_dir,
            )

            second_config_path = (
                root
                / "second.yaml"
            )

            second_config_path.write_text(
                "version: two\n",
                encoding="utf-8",
            )

            with self.assertRaises(
                ValueError
            ):

                write_run_manifest(
                    config_path=(
                        second_config_path
                    ),
                    config=self._config(
                        "RUN-COLLISION-001"
                    ),
                    output_dir=output_dir,
                )


if __name__ == "__main__":
    unittest.main()
