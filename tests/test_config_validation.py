import copy
import tempfile
import unittest
from pathlib import Path
import yaml
from simulator.config_loader import (load_config,)

class TestFleetConfigValidation(
    unittest.TestCase
):

    def setUp(self,):

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

    def _load_mutated(self, config: dict,):

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

    def test_valid_fleet_config_loads(self,):

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

    def test_duplicate_drone_id_fails(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config["fleet"]["members"][1]["drone_id"] = config["fleet"]["members"][0]["drone_id"]

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_unknown_buffer_target_fails(self,):

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

    def test_unknown_maintenance_target_fails(self,):

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

    def test_invalid_battery_percentage_fails(self,):

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

    def test_negative_battery_drain_fails(self,):

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

    def test_negative_optic_fiber_fails(self,):

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
            "initial_optic_fiber_m"
        ] = -1.0

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_unknown_operational_profile_key_fails(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "drone"
        ][
            "operational_profile"
        ][
            "fiber_meters_typo"
        ] = 1000.0

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_unsupported_event_schema_version_fails(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "telemetry"
        ][
            "schema_version"
        ] = "9.9"

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_duplicate_and_drop_same_target_fails(self,):

        config = copy.deepcopy(
            self.base_config
        )

        target = {
            "drone_id":
                "DRN-003",

            "source_sequence_number":
                40,
        }

        config["transport"]["fault_injection"]["duplicate_targets"] = [dict(target)]
        config["transport"]["fault_injection"]["drop_targets"] = [dict(target)]

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_invalid_run_id_path_characters_fail(self,):

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

    def test_misindented_root_fault_injection_fails(self,):

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

    def test_misspelled_transport_fault_section_fails(self,):

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

    def test_start_time_auto_is_valid(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "simulation"
        ][
            "start_time_utc"
        ] = "auto"

        loaded = self._load_mutated(
            config
        )

        self.assertEqual(
            loaded[
                "simulation"
            ][
                "start_time_utc"
            ],
            "auto",
        )

    def test_invalid_start_time_is_rejected(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config["simulation"]["start_time_utc"] = ("mañana-como-a-las-tres")

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(config)

    def test_v1_2_accepts_rf_communications(self,):

        config = copy.deepcopy(self.base_config)

        config["config_version"] = "1.2"
        config["telemetry"]["schema_version"] = "1.2"
        config["drone"]["communications"] = {"mode": "RF",}
        config["drone"]["operational_profile"].pop("initial_optic_fiber_m",None,)

        loaded = self._load_mutated(config)

        self.assertEqual(
            loaded["drone"][
                "communications"
            ][
                "mode"
            ],
            "RF",
        )

    def test_v1_2_rejects_fiber_on_rf_drone(self,):

        config = copy.deepcopy(self.base_config)
        config["config_version"] = "1.2"
        config["telemetry"]["schema_version"] = "1.2"
        config["drone"]["communications"] = {"mode": "RF","initial_optic_fiber_m": (10000.0),}

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_v1_2_requires_fiber_capacity_for_fiber_drone(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config["config_version"] = "1.2"
        config["telemetry"]["schema_version"] = "1.2"

        config["drone"][
            "communications"
        ] = {
            "mode": "FIBER",
        }

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_v1_2_accepts_member_fiber_override(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config["config_version"] = "1.2"
        config["telemetry"]["schema_version"] = "1.2"

        config["drone"][
            "communications"
        ] = {
            "mode": "RF",
        }

        config["drone"][
            "operational_profile"
        ].pop(
            "initial_optic_fiber_m",
            None,
        )

        config["fleet"][
            "members"
        ][1][
            "communications"
        ] = {
            "mode": "FIBER",
            "initial_optic_fiber_m": 7500.0,
        }

        loaded = self._load_mutated(
            config
        )

        self.assertEqual(
            loaded["fleet"][
                "members"
            ][1][
                "communications"
            ][
                "mode"
            ],
            "FIBER",
        )

    def test_v1_2_rejects_fiber_on_rf_member(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config["config_version"] = "1.2"        
        config["telemetry"]["schema_version"] = "1.2"
        config["drone"]["communications"] = {"mode": "RF",}
        config["drone"]["operational_profile"].pop("initial_optic_fiber_m",None,)

        config["fleet"][
            "members"
        ][1][
            "communications"
        ] = {
            "mode": "RF",
            "initial_optic_fiber_m": 7500.0,
        }

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_v1_2_requires_spool_for_fiber_member(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config["config_version"] = "1.2"
        config["telemetry"]["schema_version"] = "1.2"

        config["drone"][
            "communications"
        ] = {
            "mode": "RF",
        }

        config["drone"][
            "operational_profile"
        ].pop(
            "initial_optic_fiber_m",
            None,
        )

        config["fleet"][
            "members"
        ][1][
            "communications"
        ] = {
            "mode": "FIBER",
        }

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_v1_2_rejects_legacy_fiber_in_member_operational_profile(self,):

        config = copy.deepcopy(self.base_config)

        config["config_version"] = "1.2"
        config["telemetry"]["schema_version"] = "1.2"

        config["drone"][
            "communications"
        ] = {
            "mode": "RF",
        }

        config["drone"][
            "operational_profile"
        ].pop(
            "initial_optic_fiber_m",
            None,
        )

        config["fleet"][
            "members"
        ][1][
            "operational_profile"
        ][
            "initial_optic_fiber_m"
        ] = 7500.0

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_v1_2_accepts_schema_version_1_2(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config["config_version"] = "1.2"
        config["telemetry"]["schema_version"] = "1.2"

        config["telemetry"][
            "schema_version"
        ] = "1.2"

        config["drone"][
            "communications"
        ] = {
            "mode": "RF",
        }

        config["drone"][
            "operational_profile"
        ].pop(
            "initial_optic_fiber_m",
            None,
        )

        loaded = self._load_mutated(
            config
        )

        self.assertEqual(
            loaded["telemetry"][
                "schema_version"
            ],
            "1.2",
        )

    def test_v1_2_rejects_schema_version_1_1(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config["config_version"] = "1.2"
        config["telemetry"]["schema_version"] = "1.1"
        config["drone"]["communications"] = {"mode": "RF",}

        config["drone"][
            "operational_profile"
        ].pop(
            "initial_optic_fiber_m",
            None,
        )

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_v1_2_accepts_rf_jamming_for_rf_drone(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config["config_version"] = "1.2"
        config["telemetry"][
            "schema_version"
        ] = "1.2"

        config["drone"][
            "communications"
        ] = {
            "mode": "RF",
        }

        config["drone"][
            "operational_profile"
        ].pop(
            "initial_optic_fiber_m",
            None,
        )

        config[
            "connectivity_scenario"
        ] = {
            "enabled": True,
            "target_drone_id": "DRN-001",
            "disconnect_at_seconds": 60.0,
            "reconnect_at_seconds": 80.0,
            "fault_type": "RF_JAMMING",
        }

        loaded = self._load_mutated(
            config
        )

        self.assertEqual(
            loaded[
                "connectivity_scenario"
            ][
                "fault_type"
            ],
            "RF_JAMMING",
        )

    def test_v1_2_rejects_fiber_cut_for_rf_drone(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config["config_version"] = "1.2"
        config["telemetry"][
            "schema_version"
        ] = "1.2"

        config["drone"][
            "communications"
        ] = {
            "mode": "RF",
        }

        config["drone"][
            "operational_profile"
        ].pop(
            "initial_optic_fiber_m",
            None,
        )

        config[
            "connectivity_scenario"
        ] = {
            "enabled": True,
            "target_drone_id": "DRN-001",
            "disconnect_at_seconds": 60.0,
            "reconnect_at_seconds": None,
            "fault_type": "FIBER_CUT",
        }

        with self.assertRaises(
            ValueError
        ):
            self._load_mutated(
                config
            )

    def test_v1_2_accepts_fiber_cut_for_fiber_override(self,):

        config = copy.deepcopy(
            self.base_config
        )

        config["config_version"] = "1.2"
        config["telemetry"][
            "schema_version"
        ] = "1.2"

        config["drone"][
            "communications"
        ] = {
            "mode": "RF",
        }

        config["drone"][
            "operational_profile"
        ].pop(
            "initial_optic_fiber_m",
            None,
        )

        config["fleet"][
            "members"
        ][1][
            "communications"
        ] = {
            "mode": "FIBER",
            "initial_optic_fiber_m": 7500.0,
        }

        config[
            "connectivity_scenario"
        ] = {
            "enabled": True,
            "target_drone_id": "DRN-002",
            "disconnect_at_seconds": 60.0,
            "reconnect_at_seconds": None,
            "fault_type": "FIBER_CUT",
        }

        loaded = self._load_mutated(
            config
        )

        self.assertEqual(
            loaded[
                "connectivity_scenario"
            ][
                "fault_type"
            ],
            "FIBER_CUT",
        )

if __name__ == "__main__":
    unittest.main()
