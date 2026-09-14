import unittest

from simulator.validation.fault_scenario_validation import (
    FaultScenarioValidator,
)


def event(
    drone_id: str,
    sequence: int,
) -> dict:

    return {
        "event_id":
            f"{drone_id}-{sequence}",

        "drone_id":
            drone_id,

        "source_sequence_number":
            sequence,
    }


class TestFaultScenarioValidation(
    unittest.TestCase
):

    def test_clean_scenario_passes(
        self,
    ):

        generated = [
            event("DRN-001", 1),
            event("DRN-001", 2),
        ]

        published = list(
            generated
        )

        validator = (
            FaultScenarioValidator(
                generated_events=generated,
                published_events=published,
                fault_config={},
            )
        )

        result = validator.validate()

        self.assertTrue(
            result[
                "scenario_passed"
            ]
        )

        self.assertEqual(
            result[
                "producer_status"
            ][
                "DRN-001"
            ],
            "CLEAN",
        )


    def test_expected_selective_degradation_passes(
        self,
    ):

        generated = [
            event("DRN-001", 1),

            event("DRN-003", 1),
            event("DRN-003", 2),
            event("DRN-003", 3),
            event("DRN-003", 4),
        ]

        published = [
            event("DRN-001", 1),

            # seq 2 is dropped

            event("DRN-003", 3),
            event("DRN-003", 3),

            # seq 1 arrives late
            event("DRN-003", 1),

            event("DRN-003", 4),
        ]

        fault_config = {

            "drop_targets": [
                {
                    "drone_id":
                        "DRN-003",

                    "source_sequence_number":
                        2,
                }
            ],

            "duplicate_targets": [
                {
                    "drone_id":
                        "DRN-003",

                    "source_sequence_number":
                        3,
                }
            ],

            "extra_delay_targets": [
                {
                    "drone_id":
                        "DRN-003",

                    "source_sequence_number":
                        1,

                    "extra_delay_ms":
                        2500,
                }
            ],
        }

        validator = (
            FaultScenarioValidator(
                generated_events=generated,
                published_events=published,
                fault_config=fault_config,
            )
        )

        result = validator.validate()

        self.assertTrue(
            result[
                "scenario_passed"
            ]
        )

        self.assertEqual(
            result[
                "producer_status"
            ][
                "DRN-001"
            ],
            "CLEAN",
        )

        self.assertEqual(
            result[
                "producer_status"
            ][
                "DRN-003"
            ],
            "DEGRADED",
        )


    def test_unexpected_fault_fails_scenario(
        self,
    ):

        generated = [
            event("DRN-001", 1),
            event("DRN-001", 2),
        ]

        published = [
            event("DRN-001", 1),
        ]

        validator = (
            FaultScenarioValidator(
                generated_events=generated,
                published_events=published,
                fault_config={},
            )
        )

        result = validator.validate()

        self.assertFalse(
            result[
                "scenario_passed"
            ]
        )


if __name__ == "__main__":
    unittest.main()