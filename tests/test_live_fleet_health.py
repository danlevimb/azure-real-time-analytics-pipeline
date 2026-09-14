import unittest

from simulator.observation.live_fleet_health import (
    LiveFleetHealthAnalyzer,
)


START = "2026-08-25T18:00:00+00:00"


def truth(
    drone_id: str,
    elapsed_seconds: float,
) -> dict:

    return {
        "drone_id":
            drone_id,

        "elapsed_seconds":
            elapsed_seconds,
    }


def generated(
    drone_id: str,
    sequence: int,
    second: int,
) -> dict:

    return {
        "event_id":
            f"{drone_id}-{sequence}",

        "event_type":
            "telemetry",

        "event_time":
            (
                "2026-08-25T18:00:"
                f"{second:02d}Z"
            ),

        "drone_id":
            drone_id,

        "source_sequence_number":
            sequence,
    }


def delivered(
    drone_id: str,
    sequence: int,
    event_second: int,
    delivered_at_seconds: float,
    latency_ms: float,
) -> dict:

    return {
        "event_id":
            f"{drone_id}-{sequence}",

        "event_type":
            "telemetry",

        "event_time":
            (
                "2026-08-25T18:00:"
                f"{event_second:02d}Z"
            ),

        "drone_id":
            drone_id,

        "source_sequence_number":
            sequence,

        "delivered_at_seconds":
            delivered_at_seconds,

        "delivery_latency_ms":
            latency_ms,
    }


class TestLiveFleetHealthAnalyzer(
    unittest.TestCase
):

    def build_analyzer(
        self,
        *,
        truth_records,
        generated_events,
        delivery_records,
    ):

        return LiveFleetHealthAnalyzer(
            ground_truth_records=(
                truth_records
            ),
            generated_events=(
                generated_events
            ),
            delivery_records=(
                delivery_records
            ),
            simulation_start_time_utc=(
                START
            ),
            base_delay_ms=750,
            telemetry_interval_ms=1000,
            tick_ms=250,
        )

    def test_nominal_producer_is_healthy(
        self,
    ):

        analyzer = self.build_analyzer(
            truth_records=[
                truth(
                    "DRN-001",
                    10.0,
                )
            ],
            generated_events=[
                generated(
                    "DRN-001",
                    10,
                    9,
                )
            ],
            delivery_records=[
                delivered(
                    "DRN-001",
                    10,
                    9,
                    9.75,
                    750.0,
                )
            ],
        )

        result = analyzer.analyze()

        producer = result[
            "producers"
        ][
            "DRN-001"
        ]

        self.assertEqual(
            producer[
                "status"
            ],
            "HEALTHY",
        )

        self.assertEqual(
            producer[
                "pending_events"
            ],
            0,
        )

    def test_nominal_in_flight_event_is_not_backlog(
        self,
    ):

        analyzer = self.build_analyzer(
            truth_records=[
                truth(
                    "DRN-001",
                    10.0,
                )
            ],
            generated_events=[
                generated(
                    "DRN-001",
                    10,
                    9,
                ),
                generated(
                    "DRN-001",
                    11,
                    10,
                ),
            ],
            delivery_records=[
                delivered(
                    "DRN-001",
                    10,
                    9,
                    9.75,
                    750.0,
                )
            ],
        )

        result = analyzer.analyze()

        producer = result[
            "producers"
        ][
            "DRN-001"
        ]

        self.assertEqual(
            producer[
                "status"
            ],
            "HEALTHY",
        )

        self.assertEqual(
            producer[
                "pending_events"
            ],
            1,
        )

        self.assertEqual(
            producer[
                "in_flight_events"
            ],
            1,
        )

        self.assertEqual(
            producer[
                "overdue_events"
            ],
            0,
        )

    def test_buffered_producer_becomes_stale(
        self,
    ):

        generated_events = [
            generated(
                "DRN-003",
                sequence,
                second,
            )
            for (
                sequence,
                second,
            )
            in [
                (37, 34),
                (38, 35),
                (39, 36),
                (40, 37),
                (41, 38),
                (42, 39),
            ]
        ]

        delivery_records = [
            delivered(
                "DRN-003",
                37,
                34,
                34.75,
                750.0,
            )
        ]

        analyzer = self.build_analyzer(
            truth_records=[
                truth(
                    "DRN-003",
                    40.0,
                )
            ],
            generated_events=(
                generated_events
            ),
            delivery_records=(
                delivery_records
            ),
        )

        result = analyzer.analyze()

        producer = result[
            "producers"
        ][
            "DRN-003"
        ]

        self.assertEqual(
            producer[
                "status"
            ],
            "STALE",
        )

        self.assertEqual(
            producer[
                "pending_events"
            ],
            5,
        )

        self.assertEqual(
            producer[
                "overdue_events"
            ],
            4,
        )

        self.assertEqual(
            producer[
                "data_age_seconds"
            ],
            6.0,
        )

    def test_recovery_burst_sets_recovering(
        self,
    ):

        generated_events = [
            generated(
                "DRN-003",
                sequence,
                second,
            )
            for (
                sequence,
                second,
            )
            in [
                (38, 35),
                (39, 36),
                (40, 37),
                (41, 38),
            ]
        ]

        delivery_records = [
            delivered(
                "DRN-003",
                sequence,
                second,
                45.0,
                (
                    45.0
                    - second
                )
                * 1000.0,
            )
            for (
                sequence,
                second,
            )
            in [
                (38, 35),
                (39, 36),
                (40, 37),
                (41, 38),
            ]
        ]

        analyzer = self.build_analyzer(
            truth_records=[
                truth(
                    "DRN-003",
                    45.5,
                )
            ],
            generated_events=(
                generated_events
            ),
            delivery_records=(
                delivery_records
            ),
        )

        result = analyzer.analyze()

        producer = result[
            "producers"
        ][
            "DRN-003"
        ]

        self.assertEqual(
            producer[
                "status"
            ],
            "RECOVERING",
        )

        self.assertEqual(
            producer[
                "pending_events"
            ],
            0,
        )

        self.assertEqual(
            producer[
                "recent_burst_size"
            ],
            4,
        )

    def test_recovery_burst_uses_latest_sequence_as_tie_breaker(
        self,
    ):

        generated_events = [
            generated(
                "DRN-003",
                sequence,
                second,
            )
            for (
                sequence,
                second,
            )
            in zip(
                range(
                    38,
                    48,
                ),
                range(
                    35,
                    45,
                ),
            )
        ]

        delivery_records = [
            delivered(
                "DRN-003",
                sequence,
                second,
                45.0,
                (
                    45.0
                    - second
                )
                * 1000.0,
            )
            for (
                sequence,
                second,
            )
            in zip(
                range(
                    38,
                    48,
                ),
                range(
                    35,
                    45,
                ),
            )
        ]

        analyzer = self.build_analyzer(
            truth_records=[
                truth(
                    "DRN-003",
                    45.0,
                )
            ],
            generated_events=(
                generated_events
            ),
            delivery_records=(
                delivery_records
            ),
        )

        result = analyzer.analyze()

        producer = result[
            "producers"
        ][
            "DRN-003"
        ]

        self.assertEqual(
            producer[
                "last_telemetry_sequence"
            ],
            47,
        )

        self.assertEqual(
            producer[
                "data_age_seconds"
            ],
            1.0,
        )

        self.assertEqual(
            producer[
                "recent_burst_size"
            ],
            10,
        )


if __name__ == "__main__":
    unittest.main()
