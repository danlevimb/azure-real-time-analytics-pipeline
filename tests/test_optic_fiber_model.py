import unittest

from simulator.domain.drone import Drone
from simulator.simulation.optic_fiber_model import (
    update_optic_fiber,
)


class TestOpticFiberModel(
    unittest.TestCase
):

    def _drone(
        self,
        *,
        communication_mode,
        fiber,
    ):

        return Drone(
            drone_id="DRN-TEST",
            battalion_id="BTN-TEST",
            latitude=0.0,
            longitude=0.0,
            altitude_m=0.0,
            ground_speed_mps=0.0,
            heading_deg=0.0,
            communication_mode=(
                communication_mode
            ),
            optic_fiber_remaining_m=fiber,
        )

    def test_rf_drone_does_not_consume_fiber(
        self,
    ):

        drone = self._drone(
            communication_mode="RF",
            fiber=None,
        )

        update_optic_fiber(
            drone=drone,
            distance_travelled_m=500.0,
        )

        self.assertIsNone(
            drone.optic_fiber_remaining_m
        )

    def test_fiber_drone_consumes_distance(
        self,
    ):

        drone = self._drone(
            communication_mode="FIBER",
            fiber=10000.0,
        )

        update_optic_fiber(
            drone=drone,
            distance_travelled_m=500.0,
        )

        self.assertEqual(
            drone.optic_fiber_remaining_m,
            9500.0,
        )

    def test_fiber_drone_cannot_go_below_zero(
        self,
    ):

        drone = self._drone(
            communication_mode="FIBER",
            fiber=100.0,
        )

        update_optic_fiber(
            drone=drone,
            distance_travelled_m=500.0,
        )

        self.assertEqual(
            drone.optic_fiber_remaining_m,
            0.0,
        )

    def test_fiber_drone_requires_spool(
        self,
    ):

        drone = self._drone(
            communication_mode="FIBER",
            fiber=None,
        )

        with self.assertRaises(
            ValueError
        ):

            update_optic_fiber(
                drone=drone,
                distance_travelled_m=1.0,
            )

    def test_negative_distance_fails(
        self,
    ):

        drone = self._drone(
            communication_mode="FIBER",
            fiber=1000.0,
        )

        with self.assertRaises(
            ValueError
        ):

            update_optic_fiber(
                drone=drone,
                distance_travelled_m=-1.0,
            )

if __name__ == "__main__":
    unittest.main()