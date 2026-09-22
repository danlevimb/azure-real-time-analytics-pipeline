import json

from collections import (
    Counter,
    defaultdict,
)

from pathlib import Path


SUPPORTED_EVENT_TYPES = (
    "telemetry",
    "state_transition",
    "maintenance_event",
    "status_confirmation",
)


# =========================================================
# Helpers
# =========================================================

def read_jsonl(
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


def same_float(
    left: float,
    right: float,
    tolerance: float = 1e-9,
) -> bool:

    return (
        abs(left - right)
        <= tolerance
    )


def truth_state_for_domain(
    truth: dict,
    state_domain: str,
):

    return (
        truth
        .get(
            "states",
            {},
        )
        .get(
            state_domain
        )
    )


def state_event_matches_truth(
    *,
    event: dict,
    truth: dict,
    value_field: str,
) -> bool:

    payload = event.get(
        "payload",
        {},
    )

    state_domain = payload.get(
        "state_domain"
    )

    state_value = payload.get(
        value_field
    )

    if (
        state_domain is None
        or state_value is None
    ):

        return False

    truth_value = (
        truth_state_for_domain(
            truth,
            state_domain,
        )
    )

    return (
        truth_value is not None
        and truth_value
        == state_value
    )


def maintenance_contract_is_valid(
    event: dict,
) -> bool:

    payload = event.get(
        "payload",
        {},
    )

    required_fields = (
        "maintenance_action",
        "maintenance_category",
        "reason_code",
        "severity",
    )

    return all(
        isinstance(
            payload.get(field_name),
            str,
        )
        and bool(
            payload.get(
                field_name
            )
        )

        for field_name
        in required_fields
    )


def status_confirmation_contract_is_valid(
    event: dict,
) -> bool:

    payload = event.get(
        "payload",
        {},
    )

    required_fields = (
        "state_domain",
        "confirmed_state",
        "confirmation_type",
        "reason_code",
    )

    return all(
        isinstance(
            payload.get(field_name),
            str,
        )
        and bool(
            payload.get(
                field_name
            )
        )

        for field_name
        in required_fields
    )


def build_event_family_integrity(
    generated_events: list[dict],
    published_events: list[dict],
) -> dict:

    generated_by_family = defaultdict(
        list
    )

    published_by_family = defaultdict(
        list
    )

    generated_by_id = {
        event["event_id"]:
        event

        for event
        in generated_events
    }

    for event in generated_events:

        generated_by_family[
            event["event_type"]
        ].append(
            event
        )

    for event in published_events:

        published_by_family[
            event["event_type"]
        ].append(
            event
        )

    families = sorted(
        set(
            generated_by_family
        )
        |
        set(
            published_by_family
        )
    )

    mutated_by_source_family = Counter()

    for event in published_events:

        source_event = (
            generated_by_id.get(
                event["event_id"]
            )
        )

        if (
            source_event is not None
            and event != source_event
        ):

            mutated_by_source_family[
                source_event[
                    "event_type"
                ]
            ] += 1

    result = {}

    for event_type in families:

        generated_family = (
            generated_by_family[
                event_type
            ]
        )

        published_family = (
            published_by_family[
                event_type
            ]
        )

        generated_ids = [
            event["event_id"]
            for event
            in generated_family
        ]

        published_ids = [
            event["event_id"]
            for event
            in published_family
        ]

        generated_id_set = set(
            generated_ids
        )

        published_id_set = set(
            published_ids
        )

        published_counts = Counter(
            published_ids
        )

        missing_ids = (
            generated_id_set
            - published_id_set
        )

        unexpected_ids = (
            published_id_set
            - generated_id_set
        )

        duplicate_deliveries = sum(
            count - 1

            for count
            in published_counts.values()

            if count > 1
        )

        mutated_deliveries = (
            mutated_by_source_family[
                event_type
            ]
        )

        clean = all(
            [
                len(missing_ids) == 0,
                len(unexpected_ids) == 0,
                duplicate_deliveries == 0,
                mutated_deliveries == 0,
            ]
        )

        result[
            event_type
        ] = {
            "generated":
                len(
                    generated_family
                ),

            "published":
                len(
                    published_family
                ),

            "unique_published":
                len(
                    published_id_set
                ),

            "missing":
                len(
                    missing_ids
                ),

            "duplicate_deliveries":
                duplicate_deliveries,

            "unexpected":
                len(
                    unexpected_ids
                ),

            "mutated":
                mutated_deliveries,

            "clean":
                clean,
        }

    return result


# =========================================================
# Ordering helper
#
# IMPORTANT:
# ordering is evaluated PER DRONE.
# =========================================================

def detect_out_of_order_by_drone(
    events: list[dict],
) -> list[dict]:

    highest_by_drone = defaultdict(
        int
    )

    seen_by_drone = defaultdict(
        set
    )

    anomalies = []

    for event in events:

        drone_id = event[
            "drone_id"
        ]

        sequence = int(
            event[
                "source_sequence_number"
            ]
        )

        # Physical duplicate is classified
        # separately.
        if (
            sequence
            in seen_by_drone[drone_id]
        ):
            continue

        highest_seen = (
            highest_by_drone[
                drone_id
            ]
        )

        if sequence < highest_seen:

            anomalies.append(
                {
                    "drone_id":
                        drone_id,

                    "source_sequence_number":
                        sequence,

                    "highest_sequence_seen":
                        highest_seen,
                }
            )

        seen_by_drone[
            drone_id
        ].add(
            sequence
        )

        highest_by_drone[
            drone_id
        ] = max(
            highest_seen,
            sequence,
        )

    return anomalies


# =========================================================
# Validator
# =========================================================

class FleetReconciliationValidator:

    def __init__(
        self,
        *,
        ground_truth_path: Path,
        generated_events_path: Path,
        events_path: Path,
    ) -> None:

        self.truth = read_jsonl(
            ground_truth_path
        )

        self.generated = read_jsonl(
            generated_events_path
        )

        self.events = read_jsonl(
            events_path
        )

    def validate(
        self,
    ) -> dict:

        # =================================================
        # Fleet membership
        # =================================================

        drone_ids = sorted(
            {
                event["drone_id"]
                for event
                in self.generated
            }
        )

        # =================================================
        # Group records by producer
        # =================================================

        truth_by_drone = defaultdict(
            list
        )

        generated_by_drone = defaultdict(
            list
        )

        events_by_drone = defaultdict(
            list
        )

        for record in self.truth:

            truth_by_drone[
                record["drone_id"]
            ].append(
                record
            )

        for event in self.generated:

            generated_by_drone[
                event["drone_id"]
            ].append(
                event
            )

        for event in self.events:

            events_by_drone[
                event["drone_id"]
            ].append(
                event
            )

        # =================================================
        # Ground Truth index
        #
        # Key must include drone_id.
        # =================================================

        truth_by_key = {
            (
                record["drone_id"],
                record["simulation_time"],
            ):
            record

            for record
            in self.truth
        }

        # =================================================
        # Source validation
        #
        # telemetry:
        #   snapshot must match truth.
        #
        # state_transition:
        #   new_state must match the truth field named by
        #   state_domain.
        #
        # status_confirmation:
        #   contract must be valid and confirmed_state must
        #   match the truth field named by state_domain.
        #
        # maintenance_event:
        #   generic source contract is validated here.
        #   Scenario-specific business semantics are kept
        #   outside this generic reconciler.
        # =================================================

        telemetry_matches = 0
        telemetry_total = 0

        transition_matches = 0
        transition_total = 0

        maintenance_matches = 0
        maintenance_total = 0

        confirmation_matches = 0
        confirmation_total = 0

        telemetry_mismatches = []
        transition_mismatches = []
        maintenance_mismatches = []
        confirmation_mismatches = []

        generated_event_types = {
            event["event_type"]
            for event
            in self.generated
        }

        unsupported_event_types = sorted(
            generated_event_types
            - set(
                SUPPORTED_EVENT_TYPES
            )
        )

        for event in self.generated:

            key = (
                event["drone_id"],
                event["event_time"],
            )

            truth = truth_by_key.get(
                key
            )

            event_type = event[
                "event_type"
            ]

            if (
                event_type
                == "telemetry"
            ):

                telemetry_total += 1

                if truth is None:

                    telemetry_mismatches.append(
                        {
                            "drone_id":
                                event[
                                    "drone_id"
                                ],

                            "event_id":
                                event[
                                    "event_id"
                                ],

                            "reason":
                                "NO_MATCHING_TRUTH",
                        }
                    )

                    continue

                payload = event[
                    "payload"
                ]

                checks = [

                    same_float(
                        payload[
                            "position"
                        ][
                            "latitude"
                        ],
                        truth[
                            "position"
                        ][
                            "latitude"
                        ],
                    ),

                    same_float(
                        payload[
                            "position"
                        ][
                            "longitude"
                        ],
                        truth[
                            "position"
                        ][
                            "longitude"
                        ],
                    ),

                    same_float(
                        payload[
                            "position"
                        ][
                            "altitude_m"
                        ],
                        truth[
                            "position"
                        ][
                            "altitude_m"
                        ],
                    ),

                    same_float(
                        payload[
                            "movement"
                        ][
                            "ground_speed_mps"
                        ],
                        truth[
                            "movement"
                        ][
                            "ground_speed_mps"
                        ],
                    ),

                    same_float(
                        payload[
                            "movement"
                        ][
                            "vertical_speed_mps"
                        ],
                        truth[
                            "movement"
                        ][
                            "vertical_speed_mps"
                        ],
                    ),

                    same_float(
                        payload[
                            "movement"
                        ][
                            "heading_deg"
                        ],
                        truth[
                            "movement"
                        ][
                            "heading_deg"
                        ],
                    ),

                    same_float(
                        payload[
                            "power"
                        ][
                            "battery_pct"
                        ],
                        truth[
                            "power"
                        ][
                            "battery_pct"
                        ],
                    ),

                    (
                        "consumables"
                        not in payload
                        or same_float(
                            payload[
                                "consumables"
                            ][
                                "optic_fiber_remaining_m"
                            ],
                            truth[
                                "consumables"
                            ][
                                "optic_fiber_remaining_m"
                            ],
                        )
                    ),

                    (
                        payload[
                            "operations"
                        ][
                            "mission_phase"
                        ]
                        ==
                        truth[
                            "states"
                        ][
                            "mission_phase"
                        ]
                    ),

                    (
                        payload[
                            "operations"
                        ][
                            "mission_status"
                        ]
                        ==
                        truth[
                            "states"
                        ][
                            "mission_status"
                        ]
                    ),

                    (
                        payload[
                            "operations"
                        ][
                            "asset_state"
                        ]
                        ==
                        truth[
                            "states"
                        ][
                            "asset_state"
                        ]
                    ),

                    (
                        payload[
                            "health"
                        ][
                            "platform_health"
                        ]
                        ==
                        truth[
                            "states"
                        ][
                            "platform_health"
                        ]
                    ),

                    (
                        payload[
                            "communications"
                        ][
                            "connection_state"
                        ]
                        ==
                        truth[
                            "states"
                        ][
                            "connection_state"
                        ]
                    ),
                ]

                if all(checks):

                    telemetry_matches += 1

                else:

                    telemetry_mismatches.append(
                        {
                            "drone_id":
                                event[
                                    "drone_id"
                                ],

                            "event_id":
                                event[
                                    "event_id"
                                ],

                            "reason":
                                "PAYLOAD_TRUTH_MISMATCH",
                        }
                    )

            elif (
                event_type
                == "state_transition"
            ):

                transition_total += 1

                if (
                    truth is not None
                    and state_event_matches_truth(
                        event=event,
                        truth=truth,
                        value_field=(
                            "new_state"
                        ),
                    )
                ):

                    transition_matches += 1

                else:

                    transition_mismatches.append(
                        {
                            "drone_id":
                                event[
                                    "drone_id"
                                ],

                            "event_id":
                                event[
                                    "event_id"
                                ],

                            "state_domain":
                                event.get(
                                    "payload",
                                    {},
                                ).get(
                                    "state_domain"
                                ),
                        }
                    )

            elif (
                event_type
                == "maintenance_event"
            ):

                maintenance_total += 1

                if maintenance_contract_is_valid(
                    event
                ):

                    maintenance_matches += 1

                else:

                    maintenance_mismatches.append(
                        {
                            "drone_id":
                                event[
                                    "drone_id"
                                ],

                            "event_id":
                                event[
                                    "event_id"
                                ],
                        }
                    )

            elif (
                event_type
                == "status_confirmation"
            ):

                confirmation_total += 1

                contract_valid = (
                    status_confirmation_contract_is_valid(
                        event
                    )
                )

                truth_matches = (
                    truth is not None
                    and state_event_matches_truth(
                        event=event,
                        truth=truth,
                        value_field=(
                            "confirmed_state"
                        ),
                    )
                )

                if (
                    contract_valid
                    and truth_matches
                ):

                    confirmation_matches += 1

                else:

                    confirmation_mismatches.append(
                        {
                            "drone_id":
                                event[
                                    "drone_id"
                                ],

                            "event_id":
                                event[
                                    "event_id"
                                ],

                            "state_domain":
                                event.get(
                                    "payload",
                                    {},
                                ).get(
                                    "state_domain"
                                ),
                        }
                    )

        # =================================================
        # Logical sequence validation PER DRONE
        # =================================================

        sequence_gaps = {}

        for drone_id in drone_ids:

            sequences = sorted(
                {
                    int(
                        event[
                            "source_sequence_number"
                        ]
                    )

                    for event
                    in generated_by_drone[
                        drone_id
                    ]
                }
            )

            if not sequences:

                sequence_gaps[
                    drone_id
                ] = []

                continue

            expected = set(
                range(
                    1,
                    max(sequences) + 1,
                )
            )

            missing = sorted(
                expected
                - set(sequences)
            )

            sequence_gaps[
                drone_id
            ] = missing

        # =================================================
        # Logical event IDs
        # =================================================

        generated_ids_list = [
            event["event_id"]
            for event
            in self.generated
        ]

        generated_id_counts = Counter(
            generated_ids_list
        )

        duplicate_generated_ids = {
            event_id: count

            for event_id, count
            in generated_id_counts.items()

            if count > 1
        }

        generated_by_id = {
            event["event_id"]:
            event

            for event
            in self.generated
        }

        generated_ids = set(
            generated_by_id
        )

        # =================================================
        # Physical deliveries
        # =================================================

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

        duplicate_deliveries = sum(
            count - 1

            for count
            in published_counts.values()

            if count > 1
        )

        # =================================================
        # Content mutation
        # =================================================

        mutated_deliveries = []

        for event in self.events:

            source_event = (
                generated_by_id.get(
                    event["event_id"]
                )
            )

            if source_event is None:
                continue

            if event != source_event:

                mutated_deliveries.append(
                    event[
                        "event_id"
                    ]
                )

        # =================================================
        # Event-family integrity
        # =================================================

        event_families = (
            build_event_family_integrity(
                self.generated,
                self.events,
            )
        )

        event_family_integrity_clean = (
            all(
                family[
                    "clean"
                ]

                for family
                in event_families.values()
            )
        )

        # =================================================
        # Arrival ordering PER DRONE
        # =================================================

        out_of_order = (
            detect_out_of_order_by_drone(
                self.events
            )
        )

        # =================================================
        # Final Ground Truth state
        # =================================================

        not_landed = []

        for drone_id in drone_ids:

            drone_truth = (
                truth_by_drone[
                    drone_id
                ]
            )

            if not drone_truth:

                not_landed.append(
                    drone_id
                )

                continue

            final_truth = (
                drone_truth[-1]
            )

            if (
                final_truth[
                    "states"
                ][
                    "mission_phase"
                ]
                != "LANDED"
            ):

                not_landed.append(
                    drone_id
                )

        # =================================================
        # Per-drone report
        # =================================================

        producers = {}

        for drone_id in drone_ids:

            producer_generated = (
                generated_by_drone[
                    drone_id
                ]
            )

            producer_published = (
                events_by_drone[
                    drone_id
                ]
            )

            producer_truth = (
                truth_by_drone[
                    drone_id
                ]
            )

            producers[
                drone_id
            ] = {
                "truth_snapshots":
                    len(
                        producer_truth
                    ),

                "generated_events":
                    len(
                        producer_generated
                    ),

                "published_events":
                    len(
                        producer_published
                    ),

                "max_sequence":
                    max(
                        (
                            event[
                                "source_sequence_number"
                            ]

                            for event
                            in producer_generated
                        ),
                        default=0,
                    ),

                "sequence_gaps":
                    sequence_gaps[
                        drone_id
                    ],
            }

        # =================================================
        # Status
        # =================================================

        source_passed = all(
            [
                telemetry_matches
                == telemetry_total,

                transition_matches
                == transition_total,

                maintenance_matches
                == maintenance_total,

                confirmation_matches
                == confirmation_total,

                len(
                    unsupported_event_types
                )
                == 0,

                len(
                    duplicate_generated_ids
                )
                == 0,

                all(
                    len(gaps) == 0

                    for gaps
                    in sequence_gaps.values()
                ),

                len(not_landed) == 0,
            ]
        )

        transport_clean = all(
            [
                len(missing_ids) == 0,

                len(unexpected_ids) == 0,

                duplicate_deliveries == 0,

                len(
                    mutated_deliveries
                )
                == 0,

                len(out_of_order) == 0,
            ]
        )

        return {
            "drone_count":
                len(drone_ids),

            "truth_snapshots":
                len(self.truth),

            "generated_events":
                len(self.generated),

            "published_events":
                len(self.events),

            "unique_published_events":
                len(published_ids),

            "telemetry_total":
                telemetry_total,

            "telemetry_matches":
                telemetry_matches,

            "transition_total":
                transition_total,

            "transition_matches":
                transition_matches,

            "maintenance_total":
                maintenance_total,

            "maintenance_matches":
                maintenance_matches,

            "confirmation_total":
                confirmation_total,

            "confirmation_matches":
                confirmation_matches,

            "unsupported_event_types":
                unsupported_event_types,

            "telemetry_mismatches":
                telemetry_mismatches,

            "transition_mismatches":
                transition_mismatches,

            "maintenance_mismatches":
                maintenance_mismatches,

            "confirmation_mismatches":
                confirmation_mismatches,

            "missing_events":
                len(missing_ids),

            "duplicate_deliveries":
                duplicate_deliveries,

            "unexpected_events":
                len(unexpected_ids),

            "mutated_deliveries":
                len(
                    mutated_deliveries
                ),

            "out_of_order_arrivals":
                len(out_of_order),

            "out_of_order_details":
                out_of_order,

            "event_families":
                event_families,

            "event_family_integrity_clean":
                event_family_integrity_clean,

            "not_landed":
                not_landed,

            "producers":
                producers,

            "source_passed":
                source_passed,

            "transport_clean":
                transport_clean,

            "fleet_passed":
                (
                    source_passed
                    and
                    transport_clean
                ),
        }
