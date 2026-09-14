import math
from collections import Counter, defaultdict
from pathlib import Path

from simulator.validation.fleet_reconciliation import (
    read_jsonl,
)


def percentile(
    values: list[float],
    percentile_value: float,
) -> float:

    if not values:
        return 0.0

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    rank = (
        percentile_value
        / 100.0
        * (len(ordered) - 1)
    )

    lower_index = math.floor(
        rank
    )

    upper_index = math.ceil(
        rank
    )

    if lower_index == upper_index:
        return ordered[
            lower_index
        ]

    fraction = (
        rank - lower_index
    )

    lower_value = ordered[
        lower_index
    ]

    upper_value = ordered[
        upper_index
    ]

    return (
        lower_value
        + (
            upper_value
            - lower_value
        )
        * fraction
    )


class FleetTimelinessAnalyzer:

    def __init__(
        self,
        delivery_log_path: Path,
    ) -> None:

        self.deliveries = read_jsonl(
            delivery_log_path
        )

    def analyze(
        self,
    ) -> dict:

        deliveries_by_drone = (
            defaultdict(list)
        )

        for record in self.deliveries:

            deliveries_by_drone[
                record["drone_id"]
            ].append(
                record
            )

        producers = {}

        for drone_id in sorted(
            deliveries_by_drone
        ):

            records = (
                deliveries_by_drone[
                    drone_id
                ]
            )

            # =============================================
            # Delivery latency
            # =============================================

            latencies_ms = [
                float(
                    record[
                        "delivery_latency_ms"
                    ]
                )

                for record
                in records
            ]

            # =============================================
            # Telemetry delivery gaps
            #
            # This reflects how long the observer went
            # without receiving a fresh position sample.
            # =============================================

            telemetry_records = [
                record

                for record
                in records

                if record[
                    "event_type"
                ] == "telemetry"
            ]

            telemetry_delivery_times = sorted(
                float(
                    record[
                        "delivered_at_seconds"
                    ]
                )

                for record
                in telemetry_records
            )

            telemetry_gaps = [
                (
                    telemetry_delivery_times[
                        index
                    ]
                    -
                    telemetry_delivery_times[
                        index - 1
                    ]
                )

                for index
                in range(
                    1,
                    len(
                        telemetry_delivery_times
                    ),
                )
            ]

            # =============================================
            # Delivery bursts
            #
            # Number of physical events from this producer
            # delivered at exactly the same simulator time.
            # =============================================

            deliveries_per_time = Counter(
                float(
                    record[
                        "delivered_at_seconds"
                    ]
                )

                for record
                in records
            )

            max_burst_size = (
                max(
                    deliveries_per_time.values()
                )

                if deliveries_per_time
                else 0
            )

            burst_times = sorted(
                delivery_time

                for (
                    delivery_time,
                    count,
                ) in (
                    deliveries_per_time.items()
                )

                if count > 1
            )

            # =============================================
            # Producer metrics
            # =============================================

            producers[
                drone_id
            ] = {

                "delivery_count":
                    len(records),

                "telemetry_count":
                    len(
                        telemetry_records
                    ),

                "latency_p50_ms":
                    percentile(
                        latencies_ms,
                        50,
                    ),

                "latency_p95_ms":
                    percentile(
                        latencies_ms,
                        95,
                    ),

                "latency_p99_ms":
                    percentile(
                        latencies_ms,
                        99,
                    ),

                "latency_max_ms":
                    max(
                        latencies_ms,
                        default=0.0,
                    ),

                "latency_ge_1000_ms":
                    sum(
                        latency >= 1000

                        for latency
                        in latencies_ms
                    ),

                "latency_ge_5000_ms":
                    sum(
                        latency >= 5000

                        for latency
                        in latencies_ms
                    ),

                "max_telemetry_gap_seconds":
                    max(
                        telemetry_gaps,
                        default=0.0,
                    ),

                "max_burst_size":
                    max_burst_size,

                "burst_times":
                    burst_times,
            }

        # =================================================
        # Fleet-wide summary
        # =================================================

        all_latencies = [
            float(
                record[
                    "delivery_latency_ms"
                ]
            )

            for record
            in self.deliveries
        ]

        return {

            "delivery_count":
                len(
                    self.deliveries
                ),

            "drone_count":
                len(
                    producers
                ),

            "fleet_latency_p50_ms":
                percentile(
                    all_latencies,
                    50,
                ),

            "fleet_latency_p95_ms":
                percentile(
                    all_latencies,
                    95,
                ),

            "fleet_latency_p99_ms":
                percentile(
                    all_latencies,
                    99,
                ),

            "fleet_latency_max_ms":
                max(
                    all_latencies,
                    default=0.0,
                ),

            "producers":
                producers,
        }