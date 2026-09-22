import unittest

from simulator.communications.comms_gate import (
    CommsGate,
)
from simulator.domain.drone import Drone


class TestCommsGate(unittest.TestCase):

    @staticmethod
    def _drone(
        connection_state: str,
    ) -> Drone:

        return Drone(
            drone_id="DRN-001",
            battalion_id="BTN-01",
            latitude=72.0,
            longitude=-40.0,
            altitude_m=120.0,
            ground_speed_mps=20.0,
            heading_deg=45.0,
            connection_state=connection_state,
        )

    def test_connected_event_can_transmit(self):

        decision = CommsGate.evaluate(
            drone=self._drone("CONNECTED"),
        )

        self.assertTrue(decision.transmit)
        self.assertEqual(
            decision.reason,
            "LINK_AVAILABLE",
        )

    def test_disconnected_event_is_blocked(self):

        decision = CommsGate.evaluate(
            drone=self._drone("DISCONNECTED"),
        )

        self.assertFalse(decision.transmit)
        self.assertEqual(
            decision.reason,
            "LINK_UNAVAILABLE",
        )

    def test_forced_control_event_can_transmit(self):

        decision = CommsGate.evaluate(
            drone=self._drone("DISCONNECTED"),
            force_transmit=True,
        )

        self.assertTrue(decision.transmit)
        self.assertEqual(
            decision.reason,
            "FORCED_CONTROL_EVENT",
        )


if __name__ == "__main__":
    unittest.main()
