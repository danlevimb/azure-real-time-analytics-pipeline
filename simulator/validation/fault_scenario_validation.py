from collections import Counter

from simulator.validation.fleet_reconciliation import (
    detect_out_of_order_by_drone,
)


def event_target(
    event: dict,
) -> tuple[str, int]:

    return (
        event["drone_id"],
        int(
            event[
                "source_sequence_number"
            ]
        ),
    )


class FaultScenarioValidator:

    def __init__(
        self,
        *,
        generated_events: list[dict],
        published_events: list[dict],
        fault_config: dict,
    ) -> None:

        self.generated_events = (
            generated_events
        )

        self.published_events = (
            published_events
        )

        self.fault_config = (
            fault_config
        )

    def validate(
        self,
    ) -> dict:

        # =================================================
        # Expected anomalies from scenario configuration
        # =================================================

        expected_drop_targets = {
            (
                rule["drone_id"],
                int(
                    rule[
                        "source_sequence_number"
                    ]
                ),
            )

            for rule
            in self.fault_config.get(
                "drop_targets",
                [],
            )
        }

        expected_duplicate_counts = Counter()

        for rule in self.fault_config.get(
            "duplicate_targets",
            [],
        ):

            target = (
                rule["drone_id"],
                int(
                    rule[
                        "source_sequence_number"
                    ]
                ),
            )

            # Current TransportEngine creates
            # one additional physical copy.
            expected_duplicate_counts[
                target
            ] += 1

        # In THIS experiment, the purpose of an
        # extra-delay target is to produce observable
        # out-of-order arrival.
        expected_reorder_targets = {
            (
                rule["drone_id"],
                int(
                    rule[
                        "source_sequence_number"
                    ]
                ),
            )

            for rule
            in self.fault_config.get(
                "extra_delay_targets",
                [],
            )
        }

        # =================================================
        # Logical event indexes
        # =================================================

        generated_by_id = {
            event["event_id"]: event

            for event
            in self.generated_events
        }

        generated_ids = set(
            generated_by_id
        )

        # =================================================
        # Physical delivery counts
        # =================================================

        published_id_counts = Counter(
            event["event_id"]

            for event
            in self.published_events
        )

        published_ids = set(
            published_id_counts
        )

        # =================================================
        # Actual missing logical events
        # =================================================

        missing_ids = (
            generated_ids
            - published_ids
        )

        actual_drop_targets = {
            event_target(
                generated_by_id[
                    event_id
                ]
            )

            for event_id
            in missing_ids
        }

        # =================================================
        # Actual duplicate physical deliveries
        # =================================================

        actual_duplicate_counts = (
            Counter()
        )

        for (
            event_id,
            physical_count,
        ) in published_id_counts.items():

            if physical_count <= 1:
                continue

            source_event = (
                generated_by_id.get(
                    event_id
                )
            )

            if source_event is None:
                continue

            target = event_target(
                source_event
            )

            actual_duplicate_counts[
                target
            ] += (
                physical_count - 1
            )

        # =================================================
        # Actual out-of-order arrivals
        # =================================================

        reorder_details = (
            detect_out_of_order_by_drone(
                self.published_events
            )
        )

        actual_reorder_targets = {
            (
                detail["drone_id"],
                int(
                    detail[
                        "source_sequence_number"
                    ]
                ),
            )

            for detail
            in reorder_details
        }

        # =================================================
        # Per-check validation
        # =================================================

        drop_validation_passed = (
            actual_drop_targets
            ==
            expected_drop_targets
        )

        duplicate_validation_passed = (
            actual_duplicate_counts
            ==
            expected_duplicate_counts
        )

        reorder_validation_passed = (
            actual_reorder_targets
            ==
            expected_reorder_targets
        )

        # =================================================
        # Producer status
        # =================================================

        drone_ids = sorted(
            {
                event["drone_id"]

                for event
                in self.generated_events
            }
        )

        actual_affected_targets = (
            set(actual_drop_targets)
            |
            set(
                actual_duplicate_counts
            )
            |
            set(actual_reorder_targets)
        )

        actual_affected_drones = {
            drone_id

            for (
                drone_id,
                _
            )
            in actual_affected_targets
        }

        expected_affected_targets = (
            set(expected_drop_targets)
            |
            set(
                expected_duplicate_counts
            )
            |
            set(expected_reorder_targets)
        )

        expected_affected_drones = {
            drone_id

            for (
                drone_id,
                _
            )
            in expected_affected_targets
        }

        producer_status = {
            drone_id: (
                "DEGRADED"

                if drone_id
                in actual_affected_drones

                else "CLEAN"
            )

            for drone_id
            in drone_ids
        }

        affected_producers_match = (
            actual_affected_drones
            ==
            expected_affected_drones
        )

        # =================================================
        # Scenario result
        # =================================================

        scenario_passed = all(
            [
                drop_validation_passed,
                duplicate_validation_passed,
                reorder_validation_passed,
                affected_producers_match,
            ]
        )

        return {

            "expected_drop_targets":
                expected_drop_targets,

            "actual_drop_targets":
                actual_drop_targets,

            "expected_duplicate_counts":
                expected_duplicate_counts,

            "actual_duplicate_counts":
                actual_duplicate_counts,

            "expected_reorder_targets":
                expected_reorder_targets,

            "actual_reorder_targets":
                actual_reorder_targets,

            "drop_validation_passed":
                drop_validation_passed,

            "duplicate_validation_passed":
                duplicate_validation_passed,

            "reorder_validation_passed":
                reorder_validation_passed,

            "affected_producers_match":
                affected_producers_match,

            "producer_status":
                producer_status,

            "scenario_passed":
                scenario_passed,
        }