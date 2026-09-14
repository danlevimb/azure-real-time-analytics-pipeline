import unittest

from simulator.observation.fleet_stream_projector import (
    build_fleet_reconstructed_tracks,
    group_events_by_drone,
    project_fleet,
)


def telemetry_event(
    *,
    drone_id: str,
    sequence: int,
    longitude: float,
) -> dict:

    return {
        "event_id": (
            f"{drone_id}-EVT-{sequence:03d}"
        ),

        "event_type": "telemetry",

        "event_time": (
            f"2026-08-25T18:00:"
            f"{sequence:02d}+00:00"
        ),

        "drone_id": drone_id,

        "battalion_id": "BTN-01",

        "mission_id": (
            f"MSN-{drone_id[-3:]}"
        ),

        "source_sequence_number": (
            sequence
        ),

        "payload": {

            "position": {
                "latitude": 72.0,
                "longitude": longitude,
                "altitude_m": 120.0,
            },

            "movement": {
                "ground_speed_mps": 20.0,
                "vertical_speed_mps": 0.0,
                "heading_deg": 90.0,
            },

            "power": {
                "battery_pct": 100.0,
            },

            "health": {
                "platform_health": (
                    "NORMAL"
                ),
            },

            "communications": {
                "connection_state": (
                    "CONNECTED"
                ),
            },

            "operations": {
                "asset_state": "ACTIVE",
                "mission_status": "ACTIVE",
                "mission_phase": "EN_ROUTE",
            },
        },
    }


class TestFleetStreamProjector(
    unittest.TestCase
):

    def test_interleaved_stream_is_grouped_by_drone(
        self,
    ):

        events = [
            telemetry_event(
                drone_id="DRN-001",
                sequence=1,
                longitude=-40.001,
            ),

            telemetry_event(
                drone_id="DRN-002",
                sequence=1,
                longitude=-39.991,
            ),

            telemetry_event(
                drone_id="DRN-001",
                sequence=2,
                longitude=-40.002,
            ),

            telemetry_event(
                drone_id="DRN-002",
                sequence=2,
                longitude=-39.992,
            ),
        ]

        grouped = (
            group_events_by_drone(
                events
            )
        )

        self.assertEqual(
            len(grouped["DRN-001"]),
            2,
        )

        self.assertEqual(
            len(grouped["DRN-002"]),
            2,
        )

    def test_each_drone_is_projected_independently(
        self,
    ):

        events = [
            telemetry_event(
                drone_id="DRN-001",
                sequence=2,
                longitude=-40.002,
            ),

            telemetry_event(
                drone_id="DRN-002",
                sequence=1,
                longitude=-39.991,
            ),

            telemetry_event(
                drone_id="DRN-001",
                sequence=1,
                longitude=-40.001,
            ),

            telemetry_event(
                drone_id="DRN-002",
                sequence=2,
                longitude=-39.992,
            ),
        ]

        states = project_fleet(
            events
        )

        self.assertEqual(
            states[
                "DRN-001"
            ].latest_sequence_number,
            2,
        )

        self.assertEqual(
            states[
                "DRN-002"
            ].latest_sequence_number,
            2,
        )

        self.assertEqual(
            states[
                "DRN-001"
            ].longitude,
            -40.002,
        )

        self.assertEqual(
            states[
                "DRN-002"
            ].longitude,
            -39.992,
        )

        tracks = (
            build_fleet_reconstructed_tracks(
                events
            )
        )

        self.assertEqual(
            [
                point[0]
                for point
                in tracks["DRN-001"]
            ],
            [
                -40.001,
                -40.002,
            ],
        )


if __name__ == "__main__":
    unittest.main()