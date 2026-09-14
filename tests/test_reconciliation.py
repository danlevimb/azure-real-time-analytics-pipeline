import json
import tempfile
import unittest

from pathlib import Path

from simulator.validation.reconciliation import (
    ReconciliationValidator,
)


class TestReconciliation(
    unittest.TestCase
):

    def test_clean_stream_reconciles(
        self,
    ):

        with tempfile.TemporaryDirectory() as temp_dir:

            run_dir = Path(
                temp_dir
            )

            truth_path = (
                run_dir
                / "ground_truth.jsonl"
            )

            generated_events_path = (
                run_dir
                / "generated_events.jsonl"
            )

            events_path = (
                run_dir
                / "events.jsonl"
            )

            # =================================================
            # Ground truth
            # =================================================

            truth = {
                "record_type": (
                    "ground_truth_snapshot"
                ),

                "simulation_time": (
                    "2026-08-19T18:00:01Z"
                ),

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

                "states": {
                    "mission_phase": (
                        "EN_ROUTE"
                    ),

                    "mission_status": (
                        "ACTIVE"
                    ),

                    "asset_state": (
                        "ACTIVE"
                    ),

                    "platform_health": (
                        "NORMAL"
                    ),

                    "connection_state": (
                        "CONNECTED"
                    ),
                },
            }

            # =================================================
            # Logical source event
            # =================================================

            event = {
                "event_id": "EVT-001",
                "event_type": "telemetry",

                "event_time": (
                    "2026-08-19T18:00:01Z"
                ),

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
                        "asset_state": (
                            "ACTIVE"
                        ),

                        "mission_status": (
                            "ACTIVE"
                        ),

                        "mission_phase": (
                            "EN_ROUTE"
                        ),
                    },
                },
            }

            # =================================================
            # Write evidence files
            # =================================================

            truth_path.write_text(
                json.dumps(
                    truth
                )
                + "\n",
                encoding="utf-8",
            )

            # Clean transport:
            # generated logical event == delivered event
            generated_events_path.write_text(
                json.dumps(
                    event
                )
                + "\n",
                encoding="utf-8",
            )

            events_path.write_text(
                json.dumps(
                    event
                )
                + "\n",
                encoding="utf-8",
            )

            # =================================================
            # Reconciliation
            # =================================================

            validator = (
                ReconciliationValidator(
                    ground_truth_path=(
                        truth_path
                    ),

                    generated_events_path=(
                        generated_events_path
                    ),

                    events_path=(
                        events_path
                    ),
                )
            )

            result = validator.validate()

            # =================================================
            # Assertions
            # =================================================

            self.assertTrue(
                result[
                    "source_passed"
                ]
            )

            self.assertTrue(
                result[
                    "transport_clean"
                ]
            )

            self.assertTrue(
                result[
                    "fault_validation_passed"
                ]
            )

            self.assertTrue(
                result[
                    "experiment_passed"
                ]
            )

            self.assertEqual(
                result[
                    "missing_logical_events"
                ],
                0,
            )

            self.assertEqual(
                result[
                    "duplicate_deliveries"
                ],
                0,
            )

            self.assertEqual(
                result[
                    "out_of_order_arrivals"
                ],
                0,
            )


if __name__ == "__main__":
    unittest.main()