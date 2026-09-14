import copy
import unittest
from pathlib import Path

import yaml

from simulator.simulation.fleet_factory import (
    build_fleet_runtimes,
)


class TestFleetFactory(
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
            / "fleet005.yaml"
        )

        with config_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            self.config = (
                yaml.safe_load(
                    file
                )
            )

        self.runtimes = (
            build_fleet_runtimes(
                self.config
            )
        )

    def test_builds_five_drones(
        self,
    ):

        self.assertEqual(
            len(self.runtimes),
            5,
        )

    def test_drone_ids_are_unique(
        self,
    ):

        drone_ids = [
            runtime.drone.drone_id
            for runtime
            in self.runtimes
        ]

        self.assertEqual(
            len(drone_ids),
            len(set(drone_ids)),
        )

    def test_mission_ids_are_unique(
        self,
    ):

        mission_ids = [
            runtime.mission.mission_id
            for runtime
            in self.runtimes
        ]

        self.assertEqual(
            len(mission_ids),
            len(set(mission_ids)),
        )

    def test_each_mission_belongs_to_its_drone(
        self,
    ):

        for runtime in self.runtimes:

            self.assertEqual(
                runtime.mission.
                assigned_drone_id,

                runtime.drone.drone_id,
            )

    def test_sequence_numbers_are_independent(
        self,
    ):

        for runtime in self.runtimes:

            self.assertEqual(
                runtime.drone.
                source_sequence_number,
                0,
            )

    def test_runtime_objects_are_independent(
        self,
    ):

        self.assertIsNot(
            self.runtimes[0].drone,
            self.runtimes[1].drone,
        )

        self.assertIsNot(
            self.runtimes[0].mission,
            self.runtimes[1].mission,
        )

        self.assertIsNot(
            self.runtimes[0].
            outbound_route,

            self.runtimes[1].
            outbound_route,
        )

    def test_legacy_config_preserves_default_battery_profile(
        self,
    ):

        for runtime in self.runtimes:

            self.assertEqual(
                runtime.drone.battery_pct,
                100.0,
            )

            self.assertEqual(
                runtime.
                battery_drain_pct_per_minute,
                0.0,
            )

    def test_operational_profile_overrides_are_applied(
        self,
    ):

        config = copy.deepcopy(
            self.config
        )

        config[
            "drone"
        ][
            "operational_profile"
        ] = {
            "initial_battery_pct": 99.0,
            "battery_drain_pct_per_minute": 6.0,
        }

        config[
            "fleet"
        ][
            "members"
        ][
            1
        ][
            "operational_profile"
        ] = {
            "initial_battery_pct": 95.0,
            "battery_drain_pct_per_minute": 8.0,
        }

        runtimes = (
            build_fleet_runtimes(
                config
            )
        )

        self.assertEqual(
            runtimes[
                0
            ].drone.battery_pct,
            99.0,
        )

        self.assertEqual(
            runtimes[
                0
            ].battery_drain_pct_per_minute,
            6.0,
        )

        self.assertEqual(
            runtimes[
                1
            ].drone.battery_pct,
            95.0,
        )

        self.assertEqual(
            runtimes[
                1
            ].battery_drain_pct_per_minute,
            8.0,
        )

    def test_routes_are_geographically_offset(
        self,
    ):

        first_position = (
            self.runtimes[0]
            .outbound_route
            .waypoints[0]
        )

        second_position = (
            self.runtimes[1]
            .outbound_route
            .waypoints[0]
        )

        self.assertNotEqual(
            (
                first_position.latitude,
                first_position.longitude,
            ),

            (
                second_position.latitude,
                second_position.longitude,
            ),
        )


if __name__ == "__main__":
    unittest.main()