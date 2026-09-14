from collections import Counter, defaultdict
from datetime import datetime


def parse_iso_utc(value: str) -> datetime:

    if value.endswith("Z"):
        value = (
            value[:-1]
            + "+00:00"
        )

    return datetime.fromisoformat(
        value
    )


class LiveFleetHealthAnalyzer:

    def __init__(
        self,
        *,
        ground_truth_records: list[dict],
        generated_events: list[dict],
        delivery_records: list[dict],
        simulation_start_time_utc: str,
        base_delay_ms: int,
        telemetry_interval_ms: int,
        tick_ms: int,
        recovery_hold_seconds: float = 1.0,
    ) -> None:

        self.ground_truth_records = (
            ground_truth_records
        )

        self.generated_events = (
            generated_events
        )

        self.delivery_records = (
            delivery_records
        )

        self.simulation_start = (
            parse_iso_utc(
                simulation_start_time_utc
            )
        )

        self.base_delay_seconds = (
            base_delay_ms / 1000.0
        )

        self.telemetry_interval_seconds = (
            telemetry_interval_ms
            / 1000.0
        )

        self.tick_seconds = (
            tick_ms / 1000.0
        )

        self.recovery_hold_seconds = (
            recovery_hold_seconds
        )

    def _event_elapsed_seconds(
        self,
        event_time: str,
    ) -> float:

        event_dt = parse_iso_utc(
            event_time
        )

        return (
            event_dt
            - self.simulation_start
        ).total_seconds()

    def analyze(
        self,
    ) -> dict:

        if not self.ground_truth_records:

            return {
                "current_sim_seconds": 0.0,
                "producer_count": 0,
                "total_pending_events": 0,
                "total_in_flight_events": 0,
                "total_overdue_events": 0,
                "affected_producers": 0,
                "max_data_age_seconds": 0.0,
                "max_latency_ms": 0.0,
                "delivery_grace_seconds": (
                    self.base_delay_seconds
                    + self.tick_seconds
                ),
                "data_age_limit_seconds": (
                    self.telemetry_interval_seconds
                    + self.base_delay_seconds
                    + self.tick_seconds
                ),
                "producers": {},
            }

        current_sim_seconds = max(
            float(
                record[
                    "elapsed_seconds"
                ]
            )
            for record
            in self.ground_truth_records
        )

        drone_ids = sorted(
            {
                record["drone_id"]
                for record
                in self.ground_truth_records
            }
            |
            {
                event["drone_id"]
                for event
                in self.generated_events
                if "drone_id" in event
            }
            |
            {
                record["drone_id"]
                for record
                in self.delivery_records
                if "drone_id" in record
            }
        )

        generated_by_drone = defaultdict(
            list
        )

        for event in self.generated_events:

            generated_by_drone[
                event["drone_id"]
            ].append(
                event
            )

        delivery_by_drone = defaultdict(
            list
        )

        for record in self.delivery_records:

            delivery_by_drone[
                record["drone_id"]
            ].append(
                record
            )

        delivered_ids = {
            record["event_id"]
            for record
            in self.delivery_records
        }

        # A logical event is allowed to be "pending" while it is
        # still inside the expected transport-delay window.
        #
        # This distinction is important:
        #
        # pending != backlog
        #
        # A healthy producer normally has a small amount of data
        # in flight because base_delay_ms is intentional.
        delivery_grace_seconds = (
            self.base_delay_seconds
            + self.tick_seconds
        )

        # A telemetry observation is considered stale only when
        # its source age exceeds one telemetry interval plus the
        # normal transport delay and one simulation tick.
        data_age_limit_seconds = (
            self.telemetry_interval_seconds
            + self.base_delay_seconds
            + self.tick_seconds
        )

        producers = {}

        for drone_id in drone_ids:

            generated = (
                generated_by_drone[
                    drone_id
                ]
            )

            deliveries = (
                delivery_by_drone[
                    drone_id
                ]
            )

            telemetry_deliveries = [
                record
                for record
                in deliveries
                if record[
                    "event_type"
                ] == "telemetry"
            ]

            pending_events = [
                event
                for event
                in generated
                if event["event_id"]
                not in delivered_ids
            ]

            pending_with_age = []

            for event in pending_events:

                event_age_seconds = max(
                    0.0,
                    (
                        current_sim_seconds
                        -
                        self._event_elapsed_seconds(
                            event[
                                "event_time"
                            ]
                        )
                    ),
                )

                pending_with_age.append(
                    (
                        event,
                        event_age_seconds,
                    )
                )

            in_flight_events = [
                event
                for (
                    event,
                    age_seconds,
                ) in pending_with_age
                if age_seconds
                <= delivery_grace_seconds
            ]

            overdue_events = [
                event
                for (
                    event,
                    age_seconds,
                ) in pending_with_age
                if age_seconds
                > delivery_grace_seconds
            ]

            # Delivery time alone is not enough to identify the
            # freshest telemetry during a recovery burst because
            # several buffered events can share the same
            # delivered_at_seconds value.
            #
            # Sequence number is therefore the deterministic
            # tie-breaker.
            last_telemetry = (
                max(
                    telemetry_deliveries,
                    key=lambda record: (
                        float(
                            record[
                                "delivered_at_seconds"
                            ]
                        ),
                        int(
                            record[
                                "source_sequence_number"
                            ]
                        ),
                    ),
                )
                if telemetry_deliveries
                else None
            )

            latest_delivery = (
                max(
                    deliveries,
                    key=lambda record: (
                        float(
                            record[
                                "delivered_at_seconds"
                            ]
                        ),
                        int(
                            record[
                                "source_sequence_number"
                            ]
                        ),
                    ),
                )
                if deliveries
                else None
            )

            if last_telemetry is None:

                contact_age_seconds = (
                    current_sim_seconds
                )

                data_age_seconds = (
                    current_sim_seconds
                )

            else:

                contact_age_seconds = max(
                    0.0,
                    current_sim_seconds
                    - float(
                        last_telemetry[
                            "delivered_at_seconds"
                        ]
                    ),
                )

                source_elapsed_seconds = (
                    self._event_elapsed_seconds(
                        last_telemetry[
                            "event_time"
                        ]
                    )
                )

                data_age_seconds = max(
                    0.0,
                    current_sim_seconds
                    - source_elapsed_seconds,
                )

            latencies_ms = [
                float(
                    record[
                        "delivery_latency_ms"
                    ]
                )
                for record
                in deliveries
            ]

            batch_counts = Counter(
                float(
                    record[
                        "delivered_at_seconds"
                    ]
                )
                for record
                in deliveries
            )

            max_burst_size = (
                max(
                    batch_counts.values()
                )
                if batch_counts
                else 0
            )

            recent_burst_size = max(
                (
                    count
                    for (
                        delivered_at_seconds,
                        count,
                    )
                    in batch_counts.items()
                    if (
                        current_sim_seconds
                        - delivered_at_seconds
                    )
                    <= self.recovery_hold_seconds
                    and (
                        current_sim_seconds
                        - delivered_at_seconds
                    )
                    >= 0
                ),
                default=0,
            )

            if recent_burst_size > 2:

                status = "RECOVERING"

            elif last_telemetry is None:

                if (
                    len(overdue_events) > 0
                    and
                    current_sim_seconds
                    > data_age_limit_seconds
                ):

                    status = "STALE"

                else:

                    status = "STARTING"

            elif (
                len(overdue_events) > 0
                and
                data_age_seconds
                > data_age_limit_seconds
            ):

                status = "STALE"

            elif len(
                overdue_events
            ) > 0:

                status = "BUFFERING"

            else:

                status = "HEALTHY"

            producers[
                drone_id
            ] = {
                "status":
                    status,

                "generated_events":
                    len(
                        generated
                    ),

                "delivered_events":
                    len(
                        deliveries
                    ),

                "pending_events":
                    len(
                        pending_events
                    ),

                "in_flight_events":
                    len(
                        in_flight_events
                    ),

                "overdue_events":
                    len(
                        overdue_events
                    ),

                "contact_age_seconds":
                    contact_age_seconds,

                "data_age_seconds":
                    data_age_seconds,

                "last_telemetry_sequence":
                    (
                        int(
                            last_telemetry[
                                "source_sequence_number"
                            ]
                        )
                        if last_telemetry
                        is not None
                        else 0
                    ),

                "latest_latency_ms":
                    (
                        float(
                            latest_delivery[
                                "delivery_latency_ms"
                            ]
                        )
                        if latest_delivery
                        is not None
                        else 0.0
                    ),

                "max_latency_ms":
                    max(
                        latencies_ms,
                        default=0.0,
                    ),

                "recent_burst_size":
                    recent_burst_size,

                "max_burst_size":
                    max_burst_size,
            }

        total_pending_events = sum(
            producer[
                "pending_events"
            ]
            for producer
            in producers.values()
        )

        total_in_flight_events = sum(
            producer[
                "in_flight_events"
            ]
            for producer
            in producers.values()
        )

        total_overdue_events = sum(
            producer[
                "overdue_events"
            ]
            for producer
            in producers.values()
        )

        affected_producers = sum(
            1
            for producer
            in producers.values()
            if producer[
                "status"
            ]
            in {
                "BUFFERING",
                "STALE",
                "RECOVERING",
            }
        )

        max_data_age_seconds = max(
            (
                producer[
                    "data_age_seconds"
                ]
                for producer
                in producers.values()
            ),
            default=0.0,
        )

        max_latency_ms = max(
            (
                producer[
                    "max_latency_ms"
                ]
                for producer
                in producers.values()
            ),
            default=0.0,
        )

        return {
            "current_sim_seconds":
                current_sim_seconds,

            "producer_count":
                len(
                    producers
                ),

            "total_pending_events":
                total_pending_events,

            "total_in_flight_events":
                total_in_flight_events,

            "total_overdue_events":
                total_overdue_events,

            "affected_producers":
                affected_producers,

            "max_data_age_seconds":
                max_data_age_seconds,

            "max_latency_ms":
                max_latency_ms,

            "delivery_grace_seconds":
                delivery_grace_seconds,

            "data_age_limit_seconds":
                data_age_limit_seconds,

            "producers":
                producers,
        }
