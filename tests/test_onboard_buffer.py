import unittest

from simulator.communications.onboard_buffer import (
    OnboardBuffer,
)


class TestOnboardBuffer(unittest.TestCase):

    @staticmethod
    def _event(
        drone_id: str,
        sequence: int,
    ) -> dict:

        return {
            "event_id": (
                f"RUN-001-{drone_id}-"
                f"{sequence:08d}"
            ),
            "event_type": "telemetry",
            "drone_id": drone_id,
            "source_sequence_number": (
                sequence
            ),
            "event_time": (
                "2026-09-22T18:00:00Z"
            ),
            "payload": {
                "value": sequence,
            },
        }

    def test_buffer_preserves_event_order(self):

        buffer = OnboardBuffer()

        buffer.add(
            event=self._event(
                "DRN-001",
                125,
            )
        )

        buffer.add(
            event=self._event(
                "DRN-001",
                126,
            )
        )

        buffer.add(
            event=self._event(
                "DRN-001",
                127,
            )
        )

        events = buffer.drain(
            drone_id="DRN-001"
        )

        sequences = [
            event[
                "source_sequence_number"
            ]
            for event in events
        ]

        self.assertEqual(
            sequences,
            [125, 126, 127],
        )

    def test_buffers_are_isolated_by_drone(self):

        buffer = OnboardBuffer()

        buffer.add(
            event=self._event(
                "DRN-001",
                125,
            )
        )

        buffer.add(
            event=self._event(
                "DRN-002",
                200,
            )
        )

        self.assertEqual(
            buffer.count_for(
                drone_id="DRN-001"
            ),
            1,
        )

        self.assertEqual(
            buffer.count_for(
                drone_id="DRN-002"
            ),
            1,
        )

    def test_drain_removes_buffered_events(self):

        buffer = OnboardBuffer()

        buffer.add(
            event=self._event(
                "DRN-001",
                125,
            )
        )

        drained = buffer.drain(
            drone_id="DRN-001"
        )

        self.assertEqual(
            len(drained),
            1,
        )

        self.assertEqual(
            buffer.count_for(
                drone_id="DRN-001"
            ),
            0,
        )

        self.assertEqual(
            buffer.total_count,
            0,
        )


if __name__ == "__main__":
    unittest.main()