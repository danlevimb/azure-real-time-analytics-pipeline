import unittest

from simulator.domain.drone import Drone
from simulator.simulation.power_model import (
    update_battery,
)


class TestPowerModel(
    unittest.TestCase
):

    @staticmethod
    def _build_drone(
        battery_pct: float = 98.0,
    ) -> Drone:

        return Drone(
            drone_id="DRN-001",
            battalion_id="BTN-01",
            latitude=72.0,
            longitude=-40.0,
            altitude_m=120.0,
            ground_speed_mps=20.0,
            vertical_speed_mps=0.0,
            heading_deg=45.0,
            battery_pct=battery_pct,
        )

    def test_active_mission_drains_battery_deterministically(
        self,
    ):

        drone = self._build_drone()

        update_battery(
            drone=drone,
            drain_pct_per_minute=6.0,
            dt_seconds=1.0,
            mission_active=True,
        )

        self.assertAlmostEqual(
            drone.battery_pct,
            97.9,
            places=9,
        )

    def test_inactive_mission_does_not_drain_battery(
        self,
    ):

        drone = self._build_drone()

        update_battery(
            drone=drone,
            drain_pct_per_minute=6.0,
            dt_seconds=10.0,
            mission_active=False,
        )

        self.assertEqual(
            drone.battery_pct,
            98.0,
        )

    def test_battery_never_goes_below_zero(
        self,
    ):

        drone = self._build_drone(
            battery_pct=0.05,
        )

        update_battery(
            drone=drone,
            drain_pct_per_minute=60.0,
            dt_seconds=1.0,
            mission_active=True,
        )

        self.assertEqual(
            drone.battery_pct,
            0.0,
        )

    def test_four_quarter_second_ticks_equal_one_second(
        self,
    ):

        drone = self._build_drone()

        for _ in range(
            4
        ):

            update_battery(
                drone=drone,
                drain_pct_per_minute=6.0,
                dt_seconds=0.25,
                mission_active=True,
            )

        self.assertAlmostEqual(
            drone.battery_pct,
            97.9,
            places=9,
        )


if __name__ == "__main__":
    unittest.main()
