from pathlib import Path

import yaml

from simulator.validation.reconciliation import (
    ReconciliationValidator,
)


def main() -> None:

    project_root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    config_path = (
        project_root
        / "simulator"
        / "configs"
        / "drn001.yaml"
    )

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        config = yaml.safe_load(
            file
        )

    run_id = config[
        "simulation_context"
    ][
        "simulator_run_id"
    ]

    fault_config = config[
        "transport"
    ].get(
        "fault_injection",
        {},
    )

    expected_duplicates = set(
        fault_config.get(
            "duplicate_sequences",
            [],
        )
    )

    expected_drops = set(
        fault_config.get(
            "drop_sequences",
            [],
        )
    )

    # For this deterministic experiment,
    # extra-delay sequences are expected
    # to arrive out of source order.
    expected_out_of_order = {
        rule[
            "source_sequence_number"
        ]

        for rule
        in fault_config.get(
            "extra_delay",
            [],
        )
    }

    output_dir = (
        project_root
        / "output"
        / run_id
    )

    validator = ReconciliationValidator(
        ground_truth_path=(
            output_dir
            / "ground_truth.jsonl"
        ),

        generated_events_path=(
            output_dir
            / "generated_events.jsonl"
        ),

        events_path=(
            output_dir
            / "events.jsonl"
        ),

        delivery_log_path=(
            output_dir
            / "delivery_log.jsonl"
        ),

        expected_duplicate_sequences=(
            expected_duplicates
        ),

        expected_drop_sequences=(
            expected_drops
        ),

        expected_out_of_order_sequences=(
            expected_out_of_order
        ),
    )

    result = validator.validate()

    print()
    print(
        "TRANSPORT-AWARE "
        "RECONCILIATION REPORT"
    )

    print("=" * 52)
    print()

    print(
        f"Run                       "
        f"{run_id}"
    )

    print()

    print(
        f"Truth snapshots           "
        f"{result['truth_snapshots']}"
    )

    print(
        f"Generated logical events  "
        f"{result['generated_events']}"
    )

    print(
        f"Published physical events "
        f"{result['published_events']}"
    )

    print(
        f"Unique published events   "
        f"{result['unique_published_events']}"
    )

    print()

    print(
        f"Telemetry generated       "
        f"{result['telemetry_events']}"
    )

    print(
        f"State transitions         "
        f"{result['state_transitions']}"
    )

    print()

    print(
        f"Telemetry vs truth        "
        f"{result['telemetry_matches']} / "
        f"{result['telemetry_events']}"
    )

    print(
        f"Transitions vs truth      "
        f"{result['transition_matches']} / "
        f"{result['state_transitions']}"
    )

    print()

    print(
        f"Missing logical events    "
        f"{result['missing_logical_events']} "
        f"{result['missing_sequences']}"
    )

    print(
        f"Duplicate deliveries      "
        f"{result['duplicate_deliveries']} "
        f"{result['duplicate_sequences']}"
    )

    print(
        f"Out-of-order arrivals     "
        f"{result['out_of_order_arrivals']} "
        f"{result['out_of_order_sequences']}"
    )

    print(
        f"Mutated deliveries        "
        f"{result['mutated_deliveries']}"
    )

    print(
        f"Unexpected event_ids      "
        f"{result['unexpected_event_ids']}"
    )

    print()
    print("-" * 52)

    source_status = (
        "PASS"
        if result["source_passed"]
        else "FAIL"
    )

    transport_status = (
        "CLEAN"
        if result["transport_clean"]
        else "DEGRADED"
    )

    fault_status = (
        "PASS"
        if result[
            "fault_validation_passed"
        ]
        else "FAIL"
    )

    experiment_status = (
        "PASS"
        if result[
            "experiment_passed"
        ]
        else "FAIL"
    )

    print(
        f"SOURCE GENERATION          "
        f"{source_status}"
    )

    print(
        f"STREAM INTEGRITY           "
        f"{transport_status}"
    )

    print(
        f"FAULT INJECTION VALIDATION "
        f"{fault_status}"
    )

    print()

    print(
        f"EXPERIMENT RESULT          "
        f"{experiment_status}"
    )

    print()


if __name__ == "__main__":
    main()