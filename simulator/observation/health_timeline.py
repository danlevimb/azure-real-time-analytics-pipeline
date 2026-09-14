from collections import defaultdict
from datetime import datetime
from math import floor

from simulator.observation.live_fleet_health import (
    LiveFleetHealthAnalyzer,
)


def parse_iso_utc(value: str) -> datetime:

    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    return datetime.fromisoformat(value)


class FleetHealthTimelineBuilder:

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
        sample_interval_seconds: float = 0.5,
        recovery_hold_seconds: float = 1.0,
    ) -> None:

        if sample_interval_seconds <= 0:
            raise ValueError(
                "sample_interval_seconds must be positive."
            )

        self.ground_truth_records = ground_truth_records
        self.generated_events = generated_events
        self.delivery_records = delivery_records
        self.simulation_start_time_utc = simulation_start_time_utc
        self.base_delay_ms = base_delay_ms
        self.telemetry_interval_ms = telemetry_interval_ms
        self.tick_ms = tick_ms
        self.sample_interval_seconds = sample_interval_seconds
        self.recovery_hold_seconds = recovery_hold_seconds

        self.simulation_start = parse_iso_utc(
            simulation_start_time_utc
        )

    def _event_elapsed_seconds(
        self,
        event_time: str,
    ) -> float:

        event_dt = parse_iso_utc(event_time)

        return (
            event_dt - self.simulation_start
        ).total_seconds()

    def _sample_times(
        self,
        current_seconds: float,
    ) -> list[float]:

        if current_seconds <= 0:
            return [0.0]

        sample_count = floor(
            current_seconds
            / self.sample_interval_seconds
        )

        times = [
            round(
                index * self.sample_interval_seconds,
                6,
            )
            for index in range(sample_count + 1)
        ]

        if abs(times[-1] - current_seconds) > 1e-9:
            times.append(
                round(current_seconds, 6)
            )

        return times

    def _build_incidents(
        self,
        producer_samples: list[dict],
    ) -> list[dict]:

        non_nominal = {
            "BUFFERING",
            "STALE",
            "RECOVERING",
        }

        by_drone = defaultdict(list)

        for sample in producer_samples:
            by_drone[
                sample["drone_id"]
            ].append(sample)

        incidents = []

        for drone_id, samples in sorted(
            by_drone.items()
        ):

            samples = sorted(
                samples,
                key=lambda sample: sample[
                    "sim_seconds"
                ],
            )

            active = None

            for sample in samples:

                status = sample["status"]
                current_seconds = float(
                    sample["sim_seconds"]
                )

                if status not in non_nominal:

                    if active is not None:
                        self._close_incident(
                            active,
                            current_seconds,
                        )
                        incidents.append(active)
                        active = None

                    continue

                if (
                    active is None
                    or active["status"] != status
                ):

                    if active is not None:
                        self._close_incident(
                            active,
                            current_seconds,
                        )
                        incidents.append(active)

                    active = self._new_incident(
                        drone_id=drone_id,
                        sample=sample,
                    )

                else:
                    self._merge_incident_sample(
                        active,
                        sample,
                    )

            if active is not None:

                final_seconds = float(
                    samples[-1]["sim_seconds"]
                )

                self._close_incident(
                    active,
                    final_seconds,
                )

                incidents.append(active)

        return incidents

    @staticmethod
    def _new_incident(
        *,
        drone_id: str,
        sample: dict,
    ) -> dict:

        current_seconds = float(
            sample["sim_seconds"]
        )

        return {
            "drone_id": drone_id,
            "status": sample["status"],
            "start_seconds": current_seconds,
            "end_seconds": current_seconds,
            "duration_seconds": 0.0,
            "max_data_age_seconds": float(
                sample["data_age_seconds"]
            ),
            "max_overdue_events": int(
                sample["overdue_events"]
            ),
            "max_latency_ms": float(
                sample["max_latency_ms"]
            ),
            "max_recent_burst": int(
                sample["recent_burst_size"]
            ),
        }

    @staticmethod
    def _merge_incident_sample(
        active: dict,
        sample: dict,
    ) -> None:

        active["max_data_age_seconds"] = max(
            active["max_data_age_seconds"],
            float(sample["data_age_seconds"]),
        )

        active["max_overdue_events"] = max(
            active["max_overdue_events"],
            int(sample["overdue_events"]),
        )

        active["max_latency_ms"] = max(
            active["max_latency_ms"],
            float(sample["max_latency_ms"]),
        )

        active["max_recent_burst"] = max(
            active["max_recent_burst"],
            int(sample["recent_burst_size"]),
        )

    @staticmethod
    def _close_incident(
        active: dict,
        end_seconds: float,
    ) -> None:

        active["end_seconds"] = end_seconds

        active["duration_seconds"] = max(
            0.0,
            end_seconds - active["start_seconds"],
        )

    def build(self) -> dict:

        if not self.ground_truth_records:
            return {
                "current_sim_seconds": 0.0,
                "samples": [],
                "producer_samples": [],
                "incidents": [],
            }

        current_sim_seconds = max(
            float(record["elapsed_seconds"])
            for record in self.ground_truth_records
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
                for event in self.generated_events
                if "drone_id" in event
            }
            |
            {
                record["drone_id"]
                for record in self.delivery_records
                if "drone_id" in record
            }
        )

        generated_with_time = sorted(
            [
                (
                    self._event_elapsed_seconds(
                        event["event_time"]
                    ),
                    event,
                )
                for event in self.generated_events
            ],
            key=lambda item: item[0],
        )

        delivery_sorted = sorted(
            self.delivery_records,
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

        fleet_samples = []
        producer_samples = []

        for sample_seconds in self._sample_times(
            current_sim_seconds
        ):

            generated_prefix = [
                event
                for elapsed, event
                in generated_with_time
                if elapsed <= sample_seconds
            ]

            delivery_prefix = [
                record
                for record in delivery_sorted
                if float(
                    record[
                        "delivered_at_seconds"
                    ]
                ) <= sample_seconds
            ]

            clock_records = [
                {
                    "drone_id": drone_id,
                    "elapsed_seconds": sample_seconds,
                }
                for drone_id in drone_ids
            ]

            health = LiveFleetHealthAnalyzer(
                ground_truth_records=clock_records,
                generated_events=generated_prefix,
                delivery_records=delivery_prefix,
                simulation_start_time_utc=(
                    self.simulation_start_time_utc
                ),
                base_delay_ms=self.base_delay_ms,
                telemetry_interval_ms=(
                    self.telemetry_interval_ms
                ),
                tick_ms=self.tick_ms,
                recovery_hold_seconds=(
                    self.recovery_hold_seconds
                ),
            ).analyze()

            fleet_samples.append(
                {
                    "sim_seconds": sample_seconds,
                    "total_in_flight_events": int(
                        health[
                            "total_in_flight_events"
                        ]
                    ),
                    "total_overdue_events": int(
                        health[
                            "total_overdue_events"
                        ]
                    ),
                    "affected_producers": int(
                        health[
                            "affected_producers"
                        ]
                    ),
                    "max_data_age_seconds": float(
                        health[
                            "max_data_age_seconds"
                        ]
                    ),
                    "max_latency_ms": float(
                        health["max_latency_ms"]
                    ),
                }
            )

            for drone_id, producer in health[
                "producers"
            ].items():

                producer_samples.append(
                    {
                        "sim_seconds": sample_seconds,
                        "drone_id": drone_id,
                        "status": producer["status"],
                        "pending_events": int(
                            producer[
                                "pending_events"
                            ]
                        ),
                        "in_flight_events": int(
                            producer[
                                "in_flight_events"
                            ]
                        ),
                        "overdue_events": int(
                            producer["overdue_events"]
                        ),
                        "data_age_seconds": float(
                            producer[
                                "data_age_seconds"
                            ]
                        ),
                        "contact_age_seconds": float(
                            producer[
                                "contact_age_seconds"
                            ]
                        ),
                        "max_latency_ms": float(
                            producer["max_latency_ms"]
                        ),
                        "recent_burst_size": int(
                            producer[
                                "recent_burst_size"
                            ]
                        ),
                    }
                )

        incidents = self._build_incidents(
            producer_samples
        )

        return {
            "current_sim_seconds": current_sim_seconds,
            "samples": fleet_samples,
            "producer_samples": producer_samples,
            "incidents": incidents,
        }
