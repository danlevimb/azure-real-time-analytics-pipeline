import unittest

from simulator.observation.health_timeline import (
    FleetHealthTimelineBuilder,
)


START = "2026-08-25T18:00:00+00:00"


def truth(
    drone_id: str,
    elapsed_seconds: float,
) -> dict:

    return {
        "drone_id": drone_id,
        "elapsed_seconds": elapsed_seconds,
    }


def generated(
    drone_id: str,
    sequence: int,
    second: int,
) -> dict:

    return {
        "event_id": f"{drone_id}-{sequence}",
        "event_type": "telemetry",
        "event_time": (
            "2026-08-25T18:00:"
            f"{second:02d}Z"
        ),
        "drone_id": drone_id,
        "source_sequence_number": sequence,
    }


def delivered(
    drone_id: str,
    sequence: int,
    event_second: int,
    delivered_at_seconds: float,
    latency_ms: float,
) -> dict:

    return {
        "event_id": f"{drone_id}-{sequence}",
        "event_type": "telemetry",
        "event_time": (
            "2026-08-25T18:00:"
            f"{event_second:02d}Z"
        ),
        "drone_id": drone_id,
        "source_sequence_number": sequence,
        "delivered_at_seconds": (
            delivered_at_seconds
        ),
        "delivery_latency_ms": latency_ms,
    }


class TestFleetHealthTimelineBuilder(
    unittest.TestCase
):

    def build(
        self,
        *,
        truth_records,
        generated_events,
        delivery_records,
    ):

        return FleetHealthTimelineBuilder(
            ground_truth_records=(
                truth_records
            ),
            generated_events=(
                generated_events
            ),
            delivery_records=(
                delivery_records
            ),
            simulation_start_time_utc=START,
            base_delay_ms=750,
            telemetry_interval_ms=1000,
            tick_ms=250,
            sample_interval_seconds=0.5,
        ).build()

    def test_nominal_history_has_no_incidents(
        self,
    ):

        truth_records = [
            truth(
                "DRN-001",
                second / 2.0,
            )
            for second in range(0, 7)
        ]

        generated_events = [
            generated("DRN-001", 1, 0),
            generated("DRN-001", 2, 1),
            generated("DRN-001", 3, 2),
        ]

        delivery_records = [
            delivered(
                "DRN-001", 1, 0, 0.75, 750.0
            ),
            delivered(
                "DRN-001", 2, 1, 1.75, 750.0
            ),
            delivered(
                "DRN-001", 3, 2, 2.75, 750.0
            ),
        ]

        result = self.build(
            truth_records=truth_records,
            generated_events=generated_events,
            delivery_records=delivery_records,
        )

        self.assertEqual(
            result["incidents"],
            [],
        )

    def test_buffered_history_records_stale_incident(
        self,
    ):

        truth_records = [
            truth(
                "DRN-003",
                second / 2.0,
            )
            for second in range(0, 13)
        ]

        generated_events = [
            generated(
                "DRN-003",
                sequence,
                second,
            )
            for sequence, second in [
                (1, 0),
                (2, 1),
                (3, 2),
                (4, 3),
                (5, 4),
                (6, 5),
            ]
        ]

        delivery_records = [
            delivered(
                "DRN-003", 1, 0, 0.75, 750.0
            ),
            delivered(
                "DRN-003", 2, 1, 1.75, 750.0
            ),
        ]

        result = self.build(
            truth_records=truth_records,
            generated_events=generated_events,
            delivery_records=delivery_records,
        )

        statuses = {
            incident["status"]
            for incident
            in result["incidents"]
        }

        self.assertIn(
            "STALE",
            statuses,
        )

        producer_samples = [
            sample
            for sample
            in result[
                "producer_samples"
            ]
            if sample["drone_id"] == "DRN-003"
        ]

        self.assertTrue(
            any(
                sample["overdue_events"] > 0
                for sample
                in producer_samples
            )
        )

    def test_recovery_history_persists_after_health_returns(
        self,
    ):

        truth_records = [
            truth(
                "DRN-003",
                second / 2.0,
            )
            for second in range(0, 15)
        ]

        generated_events = [
            generated(
                "DRN-003",
                sequence,
                second,
            )
            for sequence, second in [
                (1, 0),
                (2, 1),
                (3, 2),
                (4, 3),
                (5, 4),
            ]
        ]

        delivery_records = [
            delivered(
                "DRN-003", 1, 0, 0.75, 750.0
            ),
            delivered(
                "DRN-003", 2, 1, 1.75, 750.0
            ),
            delivered(
                "DRN-003", 3, 2, 5.0, 3000.0
            ),
            delivered(
                "DRN-003", 4, 3, 5.0, 2000.0
            ),
            delivered(
                "DRN-003", 5, 4, 5.0, 1000.0
            ),
        ]

        result = self.build(
            truth_records=truth_records,
            generated_events=generated_events,
            delivery_records=delivery_records,
        )

        self.assertTrue(
            any(
                incident["status"]
                == "RECOVERING"
                for incident
                in result["incidents"]
            )
        )

        latest_sample = max(
            (
                sample
                for sample
                in result[
                    "producer_samples"
                ]
                if sample["drone_id"]
                == "DRN-003"
            ),
            key=lambda sample: sample[
                "sim_seconds"
            ],
        )

        self.assertEqual(
            latest_sample["status"],
            "HEALTHY",
        )

        self.assertGreater(
            len(result["incidents"]),
            0,
        )


if __name__ == "__main__":
    unittest.main()
