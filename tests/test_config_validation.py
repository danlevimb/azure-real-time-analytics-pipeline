import copy
import tempfile
import unittest

from pathlib import Path

import yaml

from simulator.config_loader import (
    load_config,
)


class TestFleetConfigValidation(
    unittest.TestCase
):

    def setUp(
        self,
    ):

        project_root = (
            Path(__file__)
            .resolve()
            .parents[1]
        )

        config_path = (
            project_root
            / "simulator"
            / "configs"
            / "fleet005_variability.yaml"
        )

        with config_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            self.base_config = (
                yaml.safe_load(
                    file
                )
            )

    def _load_mutated(
        self,
        config: dict,
    ):

        with tempfile.TemporaryDirectory() as temp_dir:

            path = (
                Path(temp_dir)
                / "config.yaml"
            )

            path.write_text(
                yaml.safe_dump(
                    config,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            return load_config(
                path,
                require_fleet=True,
            )

    def test_valid_fleet_config_loads(
        self,
    ):

        result = self._load_mutated(
            copy.deepcopy(
                self.base_config
            )
        )

        self.assertEqual(
            result[
                "fleet"
            ][
                "fleet_id"
            ],
            "FLEET-01",
        )

    def test_duplicate_drone_id_fails(
        self,
    ):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "fleet"
        ][
            "members"
        ][
            1
        ][
            "drone_id"
        ] = (
            config[
                "fleet"
            ][
                "members"
            ][
                0
            ][
                "drone_id"
            ]
        )

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_unknown_buffer_target_fails(
        self,
    ):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "transport"
        ][
            "buffering"
        ][
            "target_drone_ids"
        ] = [
            "DRN-999"
        ]

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_unknown_maintenance_target_fails(
        self,
    ):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "maintenance_scenario"
        ][
            "enabled"
        ] = True

        config[
            "maintenance_scenario"
        ][
            "target_drone_id"
        ] = "DRN-999"

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_invalid_battery_percentage_fails(
        self,
    ):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "fleet"
        ][
            "members"
        ][
            0
        ][
            "operational_profile"
        ][
            "initial_battery_pct"
        ] = 114.0

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_negative_battery_drain_fails(
        self,
    ):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "fleet"
        ][
            "members"
        ][
            0
        ][
            "operational_profile"
        ][
            "battery_drain_pct_per_minute"
        ] = -1.0

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_duplicate_and_drop_same_target_fails(
        self,
    ):

        config = copy.deepcopy(
            self.base_config
        )

        target = {
            "drone_id":
                "DRN-003",

            "source_sequence_number":
                40,
        }

        config[
            "transport"
        ][
            "fault_injection"
        ][
            "duplicate_targets"
        ] = [
            dict(
                target
            )
        ]

        config[
            "transport"
        ][
            "fault_injection"
        ][
            "drop_targets"
        ] = [
            dict(
                target
            )
        ]

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_invalid_run_id_path_characters_fail(
        self,
    ):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "simulation_context"
        ][
            "simulator_run_id"
        ] = "../BAD-RUN"

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_misindented_root_fault_injection_fails(
        self,
    ):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "fault_injection"
        ] = {
            "drop_targets": [
                {
                    "drone_id":
                        "DRN-003",

                    "source_sequence_number":
                        41,
                },
            ],
        }

        config[
            "transport"
        ].pop(
            "fault_injection",
            None,
        )

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_misspelled_transport_fault_section_fails(
        self,
    ):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "transport"
        ][
            "fault_injetion"
        ] = (
            config[
                "transport"
            ].pop(
                "fault_injection"
            )
        )

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )


if __name__ == "__main__":
    unittest.main()
