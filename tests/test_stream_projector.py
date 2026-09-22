import unittest

from simulator.observation.stream_projector import (
    ObservedStateProjector,
)


class TestObservedStateProjector(
    unittest.TestCase
):

    def test_transition_can_update_phase_after_telemetry(
        self,
    ):

        events = [
            {
                "event_type": "telemetry",
                "event_time": (
                    "2026-08-19T18:01:22Z"
                ),
                "drone_id": "DRN-001",
                "battalion_id": "BTN-01",
                "mission_id": "MSN-001",
                "source_sequence_number": 87,
                "payload": {
                    "position": {
                        "latitude": 72.0,
                        "longitude": -40.0,
                        "altitude_m": 15.0,
                    },
                    "movement": {
                        "ground_speed_mps": 0.0,
                        "vertical_speed_mps": -30.0,
                        "heading_deg": 225.0,
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
                        "mission_phase": "LANDING",
                    },
                },
            },
            {
                "event_type": (
                    "state_transition"
                ),
                "event_time": (
                    "2026-08-19T18:01:22.500000Z"
                ),
                "drone_id": "DRN-001",
                "battalion_id": "BTN-01",
                "mission_id": "MSN-001",
                "source_sequence_number": 88,
                "payload": {
                    "state_domain": (
                        "mission_phase"
                    ),
                    "previous_state": (
                        "LANDING"
                    ),
                    "new_state": "LANDED",
                    "reason_code": (
                        "LANDING_COMPLETED"
                    ),
                },
            },
        ]

        projector = (
            ObservedStateProjector()
        )

        state = projector.project(
            events
        )

        self.assertEqual(
            state.mission_phase,
            "LANDED",
        )

        self.assertEqual(
            state.altitude_m,
            15.0,
        )

        self.assertEqual(
            state.latest_sequence_number,
            88,
        )

        self.assertAlmostEqual(
            state.position_age_seconds,
            0.5,
        )


    def test_v1_1_telemetry_projects_optic_fiber_remaining(
        self,
    ):

        event = {
            "event_type": "telemetry",
            "event_time": "2026-09-22T18:00:00Z",
            "drone_id": "DRN-001",
            "battalion_id": "BTN-01",
            "mission_id": "MSN-001",
            "source_sequence_number": 1,
            "payload": {
                "position": {
                    "latitude": 72.0,
                    "longitude": -40.0,
                    "altitude_m": 120.0,
                },
                "movement": {
                    "ground_speed_mps": 20.0,
                    "vertical_speed_mps": 0.0,
                    "heading_deg": 45.0,
                },
                "power": {
                    "battery_pct": 98.0,
                },
                "consumables": {
                    "optic_fiber_remaining_m": 8421.5,
                },
                "health": {
                    "platform_health": "NORMAL",
                },
                "communications": {
                    "connection_state": "CONNECTED",
                },
                "operations": {
                    "asset_state": "ACTIVE",
                    "mission_status": "ACTIVE",
                    "mission_phase": "EN_ROUTE",
                },
            },
        }

        state = ObservedStateProjector().project(
            [event]
        )

        self.assertEqual(
            state.optic_fiber_remaining_m,
            8421.5,
        )



if __name__ == "__main__":
    unittest.main()