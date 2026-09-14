import unittest

from simulator.observation.stream_projector import (
    build_raw_arrival_track,
    build_reconstructed_track,
)


def telemetry_event(
    event_id: str,
    sequence: int,
    longitude: float,
) -> dict:

    return {
        "event_id": event_id,
        "event_type": "telemetry",
        "source_sequence_number": (
            sequence
        ),
        "payload": {
            "position": {
                "latitude": 72.0,
                "longitude": longitude,
            }
        },
    }


class TestTrackReconstruction(
    unittest.TestCase
):

    def test_raw_track_preserves_arrival_order(
        self,
    ):

        events = [
            telemetry_event(
                "EVT-001",
                1,
                -40.001,
            ),
            telemetry_event(
                "EVT-003",
                3,
                -40.003,
            ),
            telemetry_event(
                "EVT-002",
                2,
                -40.002,
            ),
        ]

        track = build_raw_arrival_track(
            events
        )

        longitudes = [
            point[0]
            for point in track
        ]

        self.assertEqual(
            longitudes,
            [
                -40.001,
                -40.003,
                -40.002,
            ],
        )

    def test_reconstructed_track_reorders_and_dedupes(
        self,
    ):

        events = [
            telemetry_event(
                "EVT-001",
                1,
                -40.001,
            ),
            telemetry_event(
                "EVT-003",
                3,
                -40.003,
            ),
            telemetry_event(
                "EVT-002",
                2,
                -40.002,
            ),

            # Physical duplicate.
            telemetry_event(
                "EVT-002",
                2,
                -40.002,
            ),
        ]

        track = (
            build_reconstructed_track(
                events
            )
        )

        longitudes = [
            point[0]
            for point in track
        ]

        self.assertEqual(
            longitudes,
            [
                -40.001,
                -40.002,
                -40.003,
            ],
        )


if __name__ == "__main__":
    unittest.main()