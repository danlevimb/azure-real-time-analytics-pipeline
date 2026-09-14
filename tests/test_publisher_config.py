import copy
from pathlib import Path
import tempfile
import unittest

import yaml

from simulator.config_loader import (
    load_config,
)


class PublisherConfigTests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(
        cls,
    ):

        cls.config_path = (
            Path(__file__).resolve()
            .parents[1]
            / "simulator"
            / "configs"
            / "fleet005_variability_cloud.yaml"
        )

        with cls.config_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            cls.base_config = (
                yaml.safe_load(
                    file
                )
            )

    def _load_mutated(
        self,
        config,
    ):

        with tempfile.TemporaryDirectory() as tmp:

            path = (
                Path(tmp)
                / "config.yaml"
            )

            with path.open(
                "w",
                encoding="utf-8",
            ) as file:

                yaml.safe_dump(
                    config,
                    file,
                    sort_keys=False,
                )

            return load_config(
                path,
                require_fleet=True,
            )

    def test_valid_cloud_publisher_config_loads(
        self,
    ):

        config = load_config(
            self.config_path,
            require_fleet=True,
        )

        self.assertTrue(
            config[
                "publishers"
            ][
                "event_hubs"
            ][
                "enabled"
            ]
        )

    def test_partition_key_must_be_drone_id(
        self,
    ):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "publishers"
        ][
            "event_hubs"
        ][
            "partition_key_field"
        ] = "mission_id"

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )

    def test_namespace_must_not_include_url_scheme(
        self,
    ):

        config = copy.deepcopy(
            self.base_config
        )

        config[
            "publishers"
        ][
            "event_hubs"
        ][
            "fully_qualified_namespace"
        ] = (
            "sb://example."
            "servicebus.windows.net"
        )

        with self.assertRaises(
            ValueError
        ):

            self._load_mutated(
                config
            )


if __name__ == "__main__":
    unittest.main()
