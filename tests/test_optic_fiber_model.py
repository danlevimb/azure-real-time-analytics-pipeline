import unittest

from simulator.domain.drone import Drone
from simulator.simulation.optic_fiber_model import (
    update_optic_fiber,
)


class TestOpticFiberModel(unittest.TestCase):

    @staticmethod
    def _drone(
        remaining_m: float = 1000.0,
    ) -> Drone:

        return Drone(
            drone_id="DRN-001",
            battalion_id="BTN-01",
            latitude=72.0,
            longitude=-40.0,
            altitude_m=120.0,
            ground_speed_mps=20.0,
            heading_deg=45.0,
            optic_fiber_remaining_m=remaining_m,
        )

    def test_distance_consumes_same_amount_of_fiber(self):

        drone = self._drone()

        remaining = update_optic_fiber(
            drone=drone,
            distance_travelled_m=25.5,
        )

        self.assertAlmostEqual(
            remaining,
            974.5,
        )

    def test_fiber_never_goes_below_zero(self):

        drone = self._drone(
            remaining_m=10.0,
        )

        update_optic_fiber(
            drone=drone,
            distance_travelled_m=15.0,
        )

        self.assertEqual(
            drone.optic_fiber_remaining_m,
            0.0,
        )

    def test_negative_distance_fails(self):

        with self.assertRaises(ValueError):

            update_optic_fiber(
                drone=self._drone(),
                distance_travelled_m=-1.0,
            )


if __name__ == "__main__":
    unittest.main()
