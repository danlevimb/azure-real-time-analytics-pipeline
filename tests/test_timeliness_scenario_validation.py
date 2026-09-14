import unittest

from simulator.validation.timeliness_scenario_validation import (TimelinessScenarioValidator,)

def producer(
    *,
    max_latency_ms: float,
    max_gap_s: float,
    max_burst: int,
) -> dict:

    return {
        "latency_max_ms":
            max_latency_ms,

        "max_telemetry_gap_seconds":
            max_gap_s,

        "max_burst_size":
            max_burst,
    }


class TestTimelinessScenarioValidator(
    unittest.TestCase
):

    def test_selective_buffering_passes(
        self,
    ):

        timeliness_result = {
            "producers": {

                "DRN-001": producer(
                    max_latency_ms=750,
                    max_gap_s=1.0,
                    max_burst=2,
                ),

                "DRN-002": producer(
                    max_latency_ms=750,
                    max_gap_s=1.0,
                    max_burst=2,
                ),

                "DRN-003": producer(
                    max_latency_ms=10000,
                    max_gap_s=10.25,
                    max_burst=10,
                ),

                "DRN-004": producer(
                    max_latency_ms=750,
                    max_gap_s=1.0,
                    max_burst=2,
                ),

                "DRN-005": producer(
                    max_latency_ms=750,
                    max_gap_s=1.0,
                    max_burst=2,
                ),
            }
        }

        transport_config = {
            "base_delay_ms": 750,

            "buffering": {
                "enabled": True,
                "start_at_seconds": 35.0,
                "end_at_seconds": 45.0,

                "target_drone_ids": [
                    "DRN-003"
                ],
            },
        }

        validator = (
            TimelinessScenarioValidator(
                timeliness_result=(
                    timeliness_result
                ),
                transport_config=(
                    transport_config
                ),
                telemetry_interval_ms=1000,
                tick_ms=250,
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
                "degraded_producers"
            ],
            [
                "DRN-003"
            ],
        )


    def test_unexpected_healthy_producer_degradation_fails(
        self,
    ):

        timeliness_result = {
            "producers": {

                "DRN-001": producer(
                    max_latency_ms=6000,
                    max_gap_s=6.0,
                    max_burst=6,
                ),

                "DRN-003": producer(
                    max_latency_ms=10000,
                    max_gap_s=10.25,
                    max_burst=10,
                ),
            }
        }

        transport_config = {
            "base_delay_ms": 750,

            "buffering": {
                "enabled": True,
                "start_at_seconds": 35.0,
                "end_at_seconds": 45.0,

                "target_drone_ids": [
                    "DRN-003"
                ],
            },
        }

        validator = (
            TimelinessScenarioValidator(
                timeliness_result=(
                    timeliness_result
                ),
                transport_config=(
                    transport_config
                ),
                telemetry_interval_ms=1000,
                tick_ms=250,
            )
        )

        result = validator.validate()

        self.assertFalse(
            result[
                "scenario_passed"
            ]
        )

        self.assertIn(
            "DRN-001",
            result[
                "unexpected_degradation"
            ],
        )


    def test_non_buffering_scenario_is_not_applicable(
        self,
    ):

        timeliness_result = {
            "producers": {

                "DRN-001": producer(
                    max_latency_ms=750,
                    max_gap_s=1.0,
                    max_burst=2,
                ),
            }
        }

        validator = (
            TimelinessScenarioValidator(
                timeliness_result=(
                    timeliness_result
                ),

                transport_config={
                    "base_delay_ms": 750,

                    "buffering": {
                        "enabled": False,
                    },
                },

                telemetry_interval_ms=1000,
                tick_ms=250,
            )
        )

        result = validator.validate()

        self.assertFalse(
            result[
                "applicable"
            ]
        )

        self.assertTrue(
            result[
                "scenario_passed"
            ]
        )


if __name__ == "__main__":
    unittest.main()