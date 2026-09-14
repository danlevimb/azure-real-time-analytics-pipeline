from pathlib import Path
import argparse

import yaml

from simulator.validation.fault_scenario_validation import (FaultScenarioValidator,)
from simulator.validation.fleet_reconciliation import (FleetReconciliationValidator,)
from simulator.validation.timeliness_analysis import (FleetTimelinessAnalyzer,)
from simulator.validation.timeliness_scenario_validation import (TimelinessScenarioValidator,)

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Reconcile and validate a synthetic "
            "fleet simulation run."
        )
    )

    parser.add_argument(
        "--config",
        default="fleet005.yaml",
        help=(
            "Configuration file located "
            "under simulator/configs/"
        ),
    )

    return parser.parse_args()


def main() -> None:

    # =====================================================
    # Configuration
    # =====================================================

    args = parse_args()

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
        / args.config
    )

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        config = yaml.safe_load(file)

    simulation = config["simulation"]
    telemetry_config = config["telemetry"]
    transport_config = config["transport"]

    fault_config = transport_config.get(
        "fault_injection",
        {},
    )

    run_id = config[
        "simulation_context"
    ][
        "simulator_run_id"
    ]

    output_dir = (
        project_root
        / "output"
        / run_id
    )

    # =====================================================
    # 1) Structural / stream reconciliation
    # =====================================================

    validator = FleetReconciliationValidator(
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
    )

    result = validator.validate()

    # =====================================================
    # 2) Point-fault scenario validation
    # =====================================================

    fault_validator = FaultScenarioValidator(
        generated_events=validator.generated,
        published_events=validator.events,
        fault_config=fault_config,
    )

    fault_result = fault_validator.validate()

    # =====================================================
    # 3) Timeliness analysis
    # =====================================================

    timeliness_analyzer = FleetTimelinessAnalyzer(
        delivery_log_path=(
            output_dir
            / "delivery_log.jsonl"
        )
    )

    timeliness_result = timeliness_analyzer.analyze()

    # =====================================================
    # 4) Timeliness scenario validation
    # =====================================================

    timeliness_validator = TimelinessScenarioValidator(
        timeliness_result=timeliness_result,
        transport_config=transport_config,
        telemetry_interval_ms=(
            telemetry_config[
                "interval_ms"
            ]
        ),
        tick_ms=(
            simulation[
                "tick_ms"
            ]
        ),
    )

    timeliness_scenario = timeliness_validator.validate()

    fault_scenario_passed = fault_result[
        "scenario_passed"
    ]

    timeliness_scenario_passed = timeliness_scenario[
        "scenario_passed"
    ]

    timeliness_degraded = (
        len(
            timeliness_scenario.get(
                "degraded_producers",
                [],
            )
        )
        > 0
    )

    freshness_degraded = (
        any(
            timeliness_scenario.get(
                "freshness_gap_by_target",
                {},
            ).values()
        )
        if timeliness_scenario.get(
            "applicable",
            False,
        )
        else False
    )

    experiment_passed = all(
        [
            result["source_passed"],
            fault_scenario_passed,
            timeliness_scenario_passed,
            result["mutated_deliveries"] == 0,
            result["unexpected_events"] == 0,
        ]
    )

    # =====================================================
    # Report header
    # =====================================================

    print()
    print("FLEET EXPERIMENT VALIDATION REPORT")
    print("=" * 78)
    print()

    print(f"Simulator run             {run_id}")
    print(f"Drones                    {result['drone_count']}")
    print(f"Truth snapshots           {result['truth_snapshots']}")
    print(f"Generated logical events  {result['generated_events']}")
    print(f"Published physical events {result['published_events']}")
    print(f"Unique published events   {result['unique_published_events']}")
    print()
    print(
        f"Telemetry vs truth        "
        f"{result['telemetry_matches']} / "
        f"{result['telemetry_total']}"
    )
    print(
        f"Transitions vs truth      "
        f"{result['transition_matches']} / "
        f"{result['transition_total']}"
    )
    print(
        f"Maintenance contracts     "
        f"{result['maintenance_matches']} / "
        f"{result['maintenance_total']}"
    )
    print(
        f"Confirmations vs truth    "
        f"{result['confirmation_matches']} / "
        f"{result['confirmation_total']}"
    )
    print(
        f"Unsupported event types   "
        f"{result['unsupported_event_types']}"
    )

    # =====================================================
    # Producer summary
    # =====================================================

    print()
    print("PRODUCER SUMMARY")
    print("-" * 78)

    for drone_id, producer in result["producers"].items():
        print(
            f"{drone_id} "
            f"| truth={producer['truth_snapshots']:3d} "
            f"| generated={producer['generated_events']:3d} "
            f"| delivered={producer['published_events']:3d} "
            f"| max_seq={producer['max_sequence']:3d} "
            f"| gaps={producer['sequence_gaps']}"
        )

    # =====================================================
    # Stream integrity
    # =====================================================

    print()
    print("STREAM INTEGRITY")
    print("-" * 78)
    print(f"Missing events            {result['missing_events']}")
    print(f"Duplicate deliveries      {result['duplicate_deliveries']}")
    print(f"Out-of-order arrivals     {result['out_of_order_arrivals']}")
    print(f"Mutated deliveries        {result['mutated_deliveries']}")
    print(f"Unexpected events         {result['unexpected_events']}")

    # =====================================================
    # Event-family integrity
    # =====================================================

    print()
    print("EVENT FAMILY INTEGRITY")
    print("-" * 78)
    print(
        "Event type                 "
        "Gen   Pub   Unique   Miss   Dup   Mut   Unexp   Status"
    )
    print("-" * 78)

    for (
        event_type,
        family,
    ) in result[
        "event_families"
    ].items():

        print(
            f"{event_type:<26} "
            f"{family['generated']:>4} "
            f"{family['published']:>5} "
            f"{family['unique_published']:>8} "
            f"{family['missing']:>6} "
            f"{family['duplicate_deliveries']:>5} "
            f"{family['mutated']:>5} "
            f"{family['unexpected']:>7}   "
            + (
                "CLEAN"
                if family["clean"]
                else "DEGRADED"
            )
        )

    # =====================================================
    # Point-fault scenario validation
    # =====================================================

    print()
    print("POINT-FAULT SCENARIO VALIDATION")
    print("-" * 78)

    expected_drop_targets = sorted(
        fault_result[
            "expected_drop_targets"
        ]
    )
    actual_drop_targets = sorted(
        fault_result[
            "actual_drop_targets"
        ]
    )
    expected_duplicate_targets = sorted(
        fault_result[
            "expected_duplicate_counts"
        ]
    )
    actual_duplicate_targets = sorted(
        fault_result[
            "actual_duplicate_counts"
        ]
    )
    expected_reorder_targets = sorted(
        fault_result[
            "expected_reorder_targets"
        ]
    )
    actual_reorder_targets = sorted(
        fault_result[
            "actual_reorder_targets"
        ]
    )

    print(f"Expected DROP targets     {expected_drop_targets}")
    print(f"Observed DROP targets     {actual_drop_targets}")
    print(f"Expected DUP targets      {expected_duplicate_targets}")
    print(f"Observed DUP targets      {actual_duplicate_targets}")
    print(f"Expected REORDER targets  {expected_reorder_targets}")
    print(f"Observed REORDER targets  {actual_reorder_targets}")

    # =====================================================
    # Timeliness
    # =====================================================

    print()
    print("TIMELINESS")
    print("-" * 78)
    print(
        f"Fleet P50 latency         "
        f"{timeliness_result['fleet_latency_p50_ms']:.1f} ms"
    )
    print(
        f"Fleet P95 latency         "
        f"{timeliness_result['fleet_latency_p95_ms']:.1f} ms"
    )
    print(
        f"Fleet P99 latency         "
        f"{timeliness_result['fleet_latency_p99_ms']:.1f} ms"
    )
    print(
        f"Fleet MAX latency         "
        f"{timeliness_result['fleet_latency_max_ms']:.1f} ms"
    )

    print()
    print(
        "Producer   P95(ms)   MAX(ms)   "
        "MaxGap(s)   MaxBurst"
    )
    print("-" * 78)

    for drone_id, producer in timeliness_result["producers"].items():
        print(
            f"{drone_id:<10} "
            f"{producer['latency_p95_ms']:>7.1f}   "
            f"{producer['latency_max_ms']:>7.1f}   "
            f"{producer['max_telemetry_gap_seconds']:>8.2f}   "
            f"{producer['max_burst_size']:>8}"
        )

    # =====================================================
    # Timeliness scenario validation
    # =====================================================

    print()
    print("TIMELINESS SCENARIO VALIDATION")
    print("-" * 78)

    if timeliness_scenario["applicable"]:
        print(
            f"Target producers          "
            f"{timeliness_scenario['target_producers']}"
        )
        print(
            f"Observed degraded         "
            f"{timeliness_scenario['degraded_producers']}"
        )
        print(
            f"Unexpected degradation    "
            f"{timeliness_scenario['unexpected_degradation']}"
        )
        print(
            f"Min expected spike        "
            f"{timeliness_scenario['expected_min_latency_spike_ms']:.1f} ms"
        )
        print(
            f"Min expected gap          "
            f"{timeliness_scenario['expected_min_freshness_gap_s']:.2f} s"
        )
        print()
        print(
            "Latency spike             "
            + (
                "PASS"
                if timeliness_scenario["latency_spike_passed"]
                else "FAIL"
            )
        )
        print(
            "Freshness gap             "
            + (
                "PASS"
                if timeliness_scenario["freshness_gap_passed"]
                else "FAIL"
            )
        )
        print(
            "Recovery burst            "
            + (
                "PASS"
                if timeliness_scenario["recovery_burst_passed"]
                else "FAIL"
            )
        )
        print(
            "Producer isolation        "
            + (
                "PASS"
                if timeliness_scenario["isolation_passed"]
                else "FAIL"
            )
        )
        print(
            "Expected buffer target    "
            + (
                "PASS"
                if timeliness_scenario["target_match_passed"]
                else "FAIL"
            )
        )
    else:
        print("Buffering scenario        NOT APPLICABLE")

    # =====================================================
    # Final result
    # =====================================================

    print()
    print("=" * 78)
    print(
        "SOURCE GENERATION         "
        + (
            "PASS"
            if result["source_passed"]
            else "FAIL"
        )
    )
    print(
        "STREAM INTEGRITY          "
        + (
            "CLEAN"
            if result["transport_clean"]
            else "DEGRADED"
        )
    )
    print(
        "EVENT FAMILY INTEGRITY    "
        + (
            "CLEAN"
            if result[
                "event_family_integrity_clean"
            ]
            else "DEGRADED"
        )
    )
    print(
        "TIMELINESS                "
        + (
            "DEGRADED"
            if timeliness_degraded
            else "NOMINAL"
        )
    )
    print(
        "FRESHNESS                 "
        + (
            "DEGRADED"
            if freshness_degraded
            else "NOMINAL"
        )
    )
    print(
        "POINT-FAULT VALIDATION    "
        + (
            "PASS"
            if fault_scenario_passed
            else "FAIL"
        )
    )
    print(
        "TIMELINESS VALIDATION     "
        + (
            "PASS"
            if timeliness_scenario_passed
            else "FAIL"
        )
    )
    print()
    print(
        "EXPERIMENT RESULT         "
        + (
            "PASS"
            if experiment_passed
            else "FAIL"
        )
    )
    print()


if __name__ == "__main__":
    main()
