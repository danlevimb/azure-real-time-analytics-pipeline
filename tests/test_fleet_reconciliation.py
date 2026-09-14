import unittest

from simulator.validation.fleet_reconciliation import (
    build_event_family_integrity,
    detect_out_of_order_by_drone,
    state_event_matches_truth,
)


class TestFleetReconciliation(
    unittest.TestCase
):

    def test_interleaved_drones_are_not_out_of_order(
        self,
    ):

        events = [
            {
                "drone_id": "DRN-001",
                "source_sequence_number": 1,
            },
            {
                "drone_id": "DRN-002",
                "source_sequence_number": 1,
            },
            {
                "drone_id": "DRN-001",
                "source_sequence_number": 2,
            },
            {
                "drone_id": "DRN-002",
                "source_sequence_number": 2,
            },
        ]

        anomalies = (
            detect_out_of_order_by_drone(
                events
            )
        )

        self.assertEqual(
            anomalies,
            [],
        )

    def test_out_of_order_is_detected_within_drone(
        self,
    ):

        events = [
            {
                "drone_id": "DRN-001",
                "source_sequence_number": 1,
            },
            {
                "drone_id": "DRN-001",
                "source_sequence_number": 3,
            },
            {
                "drone_id": "DRN-002",
                "source_sequence_number": 1,
            },
            {
                "drone_id": "DRN-001",
                "source_sequence_number": 2,
            },
            {
                "drone_id": "DRN-002",
                "source_sequence_number": 2,
            },
        ]

        anomalies = (
            detect_out_of_order_by_drone(
                events
            )
        )

        self.assertEqual(
            len(anomalies),
            1,
        )

        self.assertEqual(
            anomalies[0][
                "drone_id"
            ],
            "DRN-001",
        )

        self.assertEqual(
            anomalies[0][
                "source_sequence_number"
            ],
            2,
        )

    def test_heterogeneous_event_families_are_clean(
        self,
    ):

        generated = [
            {
                "event_id": "E-001",
                "event_type": "telemetry",
            },
            {
                "event_id": "E-002",
                "event_type": "state_transition",
            },
            {
                "event_id": "E-003",
                "event_type": "maintenance_event",
            },
            {
                "event_id": "E-004",
                "event_type": "status_confirmation",
            },
        ]

        published = [
            dict(
                event
            )
            for event
            in generated
        ]

        result = (
            build_event_family_integrity(
                generated,
                published,
            )
        )

        self.assertEqual(
            set(
                result
            ),
            {
                "telemetry",
                "state_transition",
                "maintenance_event",
                "status_confirmation",
            },
        )

        self.assertTrue(
            all(
                family["clean"]

                for family
                in result.values()
            )
        )

    def test_missing_confirmation_isolated_to_its_family(
        self,
    ):

        generated = [
            {
                "event_id": "E-001",
                "event_type": "telemetry",
            },
            {
                "event_id": "E-002",
                "event_type": "status_confirmation",
            },
        ]

        published = [
            {
                "event_id": "E-001",
                "event_type": "telemetry",
            },
        ]

        result = (
            build_event_family_integrity(
                generated,
                published,
            )
        )

        self.assertTrue(
            result[
                "telemetry"
            ][
                "clean"
            ]
        )

        self.assertFalse(
            result[
                "status_confirmation"
            ][
                "clean"
            ]
        )

        self.assertEqual(
            result[
                "status_confirmation"
            ][
                "missing"
            ],
            1,
        )

    def test_event_type_mutation_degrades_family_integrity(
        self,
    ):

        generated = [
            {
                "event_id": "E-001",
                "event_type": "status_confirmation",
                "payload": {
                    "confirmed_state": "AVAILABLE",
                },
            },
        ]

        published = [
            {
                "event_id": "E-001",
                "event_type": "maintenance_event",
                "payload": {
                    "confirmed_state": "AVAILABLE",
                },
            },
        ]

        result = (
            build_event_family_integrity(
                generated,
                published,
            )
        )

        self.assertEqual(
            result[
                "status_confirmation"
            ][
                "missing"
            ],
            1,
        )

        self.assertEqual(
            result[
                "status_confirmation"
            ][
                "mutated"
            ],
            1,
        )

        self.assertEqual(
            result[
                "maintenance_event"
            ][
                "unexpected"
            ],
            1,
        )

    def test_state_event_matches_multiple_truth_domains(
        self,
    ):

        truth = {
            "states": {
                "mission_phase": "LANDED",
                "asset_state": "MAINTENANCE",
                "platform_health": "DEGRADED",
            }
        }

        asset_transition = {
            "payload": {
                "state_domain": "asset_state",
                "new_state": "MAINTENANCE",
            }
        }

        health_transition = {
            "payload": {
                "state_domain": "platform_health",
                "new_state": "DEGRADED",
            }
        }

        confirmation = {
            "payload": {
                "state_domain": "asset_state",
                "confirmed_state": "MAINTENANCE",
            }
        }

        self.assertTrue(
            state_event_matches_truth(
                event=asset_transition,
                truth=truth,
                value_field="new_state",
            )
        )

        self.assertTrue(
            state_event_matches_truth(
                event=health_transition,
                truth=truth,
                value_field="new_state",
            )
        )

        self.assertTrue(
            state_event_matches_truth(
                event=confirmation,
                truth=truth,
                value_field="confirmed_state",
            )
        )


if __name__ == "__main__":
    unittest.main()
