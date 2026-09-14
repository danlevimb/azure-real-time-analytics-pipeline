import json

from collections import Counter
from datetime import datetime
from pathlib import Path


def _read_jsonl(
    path: Path,
) -> list[dict]:

    records = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1,
        ):

            line = line.strip()

            if not line:
                continue

            try:
                records.append(
                    json.loads(line)
                )

            except json.JSONDecodeError as exc:

                raise ValueError(
                    f"Invalid JSON in {path} "
                    f"at line {line_number}"
                ) from exc

    return records


def _parse_time(
    value: str,
) -> datetime:

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def _same_float(
    left: float,
    right: float,
    tolerance: float = 1e-9,
) -> bool:

    return (
        abs(left - right)
        <= tolerance
    )


class ReconciliationValidator:

    def __init__(
        self,
        *,
        ground_truth_path: Path,
        generated_events_path: Path,
        events_path: Path,
        delivery_log_path: Path | None = None,

        expected_duplicate_sequences: (
            set[int] | None
        ) = None,

        expected_drop_sequences: (
            set[int] | None
        ) = None,

        expected_out_of_order_sequences: (
            set[int] | None
        ) = None,
    ) -> None:

        self.truth_records = _read_jsonl(
            ground_truth_path
        )

        self.generated_events = _read_jsonl(
            generated_events_path
        )

        self.events = _read_jsonl(
            events_path
        )

        if (
            delivery_log_path is not None
            and delivery_log_path.exists()
        ):
            self.delivery_records = (
                _read_jsonl(
                    delivery_log_path
                )
            )
        else:
            self.delivery_records = []

        self.expected_duplicate_sequences = set(
            expected_duplicate_sequences
            or set()
        )

        self.expected_drop_sequences = set(
            expected_drop_sequences
            or set()
        )

        self.expected_out_of_order_sequences = set(
            expected_out_of_order_sequences
            or set()
        )

    # =====================================================
    # Source events vs ground truth
    # =====================================================

    def _validate_source_events(
        self,
    ) -> dict:

        telemetry_events = [
            event
            for event in self.generated_events
            if event["event_type"]
            == "telemetry"
        ]

        transition_events = [
            event
            for event in self.generated_events
            if event["event_type"]
            == "state_transition"
        ]

        truth_by_time = {
            record["simulation_time"]:
            record

            for record
            in self.truth_records
        }

        telemetry_matches = 0

        telemetry_mismatches = []

        for event in telemetry_events:

            truth = truth_by_time.get(
                event["event_time"]
            )

            if truth is None:

                telemetry_mismatches.append(
                    event["event_id"]
                )

                continue

            payload = event["payload"]

            checks = [

                _same_float(
                    payload["position"][
                        "latitude"
                    ],
                    truth["position"][
                        "latitude"
                    ],
                ),

                _same_float(
                    payload["position"][
                        "longitude"
                    ],
                    truth["position"][
                        "longitude"
                    ],
                ),

                _same_float(
                    payload["position"][
                        "altitude_m"
                    ],
                    truth["position"][
                        "altitude_m"
                    ],
                ),

                _same_float(
                    payload["movement"][
                        "ground_speed_mps"
                    ],
                    truth["movement"][
                        "ground_speed_mps"
                    ],
                ),

                _same_float(
                    payload["movement"][
                        "vertical_speed_mps"
                    ],
                    truth["movement"][
                        "vertical_speed_mps"
                    ],
                ),

                _same_float(
                    payload["movement"][
                        "heading_deg"
                    ],
                    truth["movement"][
                        "heading_deg"
                    ],
                ),

                (
                    payload["operations"][
                        "mission_phase"
                    ]
                    ==
                    truth["states"][
                        "mission_phase"
                    ]
                ),

                (
                    payload["operations"][
                        "mission_status"
                    ]
                    ==
                    truth["states"][
                        "mission_status"
                    ]
                ),

                (
                    payload["operations"][
                        "asset_state"
                    ]
                    ==
                    truth["states"][
                        "asset_state"
                    ]
                ),
            ]

            if all(checks):

                telemetry_matches += 1

            else:

                telemetry_mismatches.append(
                    event["event_id"]
                )

        # -------------------------------------------------
        # State transitions
        # -------------------------------------------------

        sorted_truth = sorted(
            self.truth_records,
            key=lambda record: (
                _parse_time(
                    record[
                        "simulation_time"
                    ]
                )
            ),
        )

        truth_index = {
            record["simulation_time"]:
            index

            for index, record
            in enumerate(
                sorted_truth
            )
        }

        transition_matches = 0
        transition_mismatches = []

        for event in transition_events:

            event_time = (
                event["event_time"]
            )

            current_truth = (
                truth_by_time.get(
                    event_time
                )
            )

            if current_truth is None:

                transition_mismatches.append(
                    event["event_id"]
                )

                continue

            payload = event["payload"]

            new_state_matches = (
                current_truth["states"][
                    "mission_phase"
                ]
                ==
                payload["new_state"]
            )

            # Initial transition.
            if (
                payload["previous_state"]
                == "READY"
                and
                payload["new_state"]
                == "TAKEOFF"
            ):

                previous_state_matches = True

            else:

                current_index = (
                    truth_index[
                        event_time
                    ]
                )

                if current_index == 0:

                    previous_state_matches = False

                else:

                    previous_truth = (
                        sorted_truth[
                            current_index - 1
                        ]
                    )

                    previous_state_matches = (
                        previous_truth[
                            "states"
                        ][
                            "mission_phase"
                        ]
                        ==
                        payload[
                            "previous_state"
                        ]
                    )

            if (
                new_state_matches
                and
                previous_state_matches
            ):

                transition_matches += 1

            else:

                transition_mismatches.append(
                    event["event_id"]
                )

        # -------------------------------------------------
        # Logical event identity
        # -------------------------------------------------

        generated_ids = [
            event["event_id"]
            for event
            in self.generated_events
        ]

        generated_duplicate_ids = (
            len(generated_ids)
            - len(set(generated_ids))
        )

        source_passed = all(
            [
                generated_duplicate_ids == 0,

                telemetry_matches
                == len(
                    telemetry_events
                ),

                transition_matches
                == len(
                    transition_events
                ),
            ]
        )

        return {
            "telemetry_events":
                len(telemetry_events),

            "state_transitions":
                len(transition_events),

            "telemetry_matches":
                telemetry_matches,

            "transition_matches":
                transition_matches,

            "generated_duplicate_ids":
                generated_duplicate_ids,

            "source_passed":
                source_passed,
        }

    # =====================================================
    # Transport reconciliation
    # =====================================================

    def _validate_transport(
        self,
    ) -> dict:

        generated_by_id = {
            event["event_id"]:
            event

            for event
            in self.generated_events
        }

        generated_ids = set(
            generated_by_id
        )

        published_ids_list = [
            event["event_id"]
            for event
            in self.events
        ]

        published_counts = Counter(
            published_ids_list
        )

        published_ids = set(
            published_ids_list
        )

        missing_ids = (
            generated_ids
            - published_ids
        )

        unexpected_ids = (
            published_ids
            - generated_ids
        )

        duplicate_ids = {
            event_id: count

            for event_id, count
            in published_counts.items()

            if count > 1
        }

        duplicate_deliveries = sum(
            count - 1

            for count
            in duplicate_ids.values()
        )

        # -------------------------------------------------
        # Physical arrival order
        # -------------------------------------------------

        out_of_order_details = []

        seen_sequences = set()

        highest_sequence_seen = 0

        for event in self.events:

            sequence_number = event[
                "source_sequence_number"
            ]

            # Duplicate classification is separate.
            if (
                sequence_number
                in seen_sequences
            ):
                continue

            if (
                sequence_number
                < highest_sequence_seen
            ):

                out_of_order_details.append(
                    {
                        "event_id":
                            event["event_id"],

                        "source_sequence_number":
                            sequence_number,

                        "highest_sequence_seen":
                            highest_sequence_seen,
                    }
                )

            seen_sequences.add(
                sequence_number
            )

            highest_sequence_seen = max(
                highest_sequence_seen,
                sequence_number,
            )

        # -------------------------------------------------
        # Delivery content mutation
        # -------------------------------------------------

        mutated_deliveries = 0

        for event in self.events:

            source_event = (
                generated_by_id.get(
                    event["event_id"]
                )
            )

            if source_event is None:
                continue

            if event != source_event:
                mutated_deliveries += 1

        # -------------------------------------------------
        # Convert anomalies to source sequences
        # -------------------------------------------------

        missing_sequences = {
            generated_by_id[
                event_id
            ][
                "source_sequence_number"
            ]

            for event_id
            in missing_ids
        }

        duplicate_sequences = {
            generated_by_id[
                event_id
            ][
                "source_sequence_number"
            ]

            for event_id
            in duplicate_ids
        }

        out_of_order_sequences = {
            detail[
                "source_sequence_number"
            ]

            for detail
            in out_of_order_details
        }

        # -------------------------------------------------
        # Strict stream integrity
        # -------------------------------------------------

        transport_clean = all(
            [
                len(missing_ids) == 0,
                duplicate_deliveries == 0,
                len(unexpected_ids) == 0,
                len(out_of_order_details) == 0,
                mutated_deliveries == 0,
            ]
        )

        # -------------------------------------------------
        # Was the requested fault scenario reproduced?
        # -------------------------------------------------

        duplicate_expectation_match = (
            duplicate_sequences
            ==
            self.expected_duplicate_sequences
        )

        drop_expectation_match = (
            missing_sequences
            ==
            self.expected_drop_sequences
        )

        out_of_order_expectation_match = (
            out_of_order_sequences
            ==
            self.expected_out_of_order_sequences
        )

        fault_validation_passed = all(
            [
                duplicate_expectation_match,
                drop_expectation_match,
                out_of_order_expectation_match,
                len(unexpected_ids) == 0,
                mutated_deliveries == 0,
            ]
        )

        return {
            "published_events":
                len(self.events),

            "unique_published_events":
                len(published_ids),

            "missing_logical_events":
                len(missing_ids),

            "missing_sequences":
                sorted(
                    missing_sequences
                ),

            "duplicate_deliveries":
                duplicate_deliveries,

            "duplicate_sequences":
                sorted(
                    duplicate_sequences
                ),

            "out_of_order_arrivals":
                len(
                    out_of_order_details
                ),

            "out_of_order_sequences":
                sorted(
                    out_of_order_sequences
                ),

            "unexpected_event_ids":
                len(unexpected_ids),

            "mutated_deliveries":
                mutated_deliveries,

            "transport_clean":
                transport_clean,

            "fault_validation_passed":
                fault_validation_passed,
        }

    # =====================================================
    # Complete result
    # =====================================================

    def validate(
        self,
    ) -> dict:

        source = (
            self._validate_source_events()
        )

        transport = (
            self._validate_transport()
        )

        experiment_passed = (
            source["source_passed"]
            and
            transport[
                "fault_validation_passed"
            ]
        )

        return {
            "truth_snapshots":
                len(self.truth_records),

            "generated_events":
                len(self.generated_events),

            **source,
            **transport,

            "experiment_passed":
                experiment_passed,
        }