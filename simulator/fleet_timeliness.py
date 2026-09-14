from pathlib import Path
import argparse

import yaml

from simulator.validation.timeliness_analysis import (
    FleetTimelinessAnalyzer,
)


def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Analyze fleet stream "
            "delivery timeliness."
        )
    )

    parser.add_argument(
        "--config",
        default="fleet005.yaml",
    )

    return parser.parse_args()


def main() -> None:

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

        config = yaml.safe_load(
            file
        )

    run_id = config[
        "simulation_context"
    ][
        "simulator_run_id"
    ]

    transport_config = config[
        "transport"
    ]

    buffer_config = (
        transport_config[
            "buffering"
        ]
    )

    output_dir = (
        project_root
        / "output"
        / run_id
    )

    analyzer = (
        FleetTimelinessAnalyzer(
            delivery_log_path=(
                output_dir
                / "delivery_log.jsonl"
            )
        )
    )

    result = analyzer.analyze()

    print()

    print(
        "FLEET TIMELINESS REPORT"
    )

    print("=" * 78)

    print()

    print(
        f"Simulator run             "
        f"{run_id}"
    )

    print(
        f"Physical deliveries       "
        f"{result['delivery_count']}"
    )

    print(
        f"Producers                 "
        f"{result['drone_count']}"
    )

    print()

    print(
        "FLEET LATENCY"
    )

    print("-" * 78)

    print(
        f"P50                       "
        f"{result['fleet_latency_p50_ms']:.1f} ms"
    )

    print(
        f"P95                       "
        f"{result['fleet_latency_p95_ms']:.1f} ms"
    )

    print(
        f"P99                       "
        f"{result['fleet_latency_p99_ms']:.1f} ms"
    )

    print(
        f"MAX                       "
        f"{result['fleet_latency_max_ms']:.1f} ms"
    )

    print()

    print(
        "TIMELINESS BY PRODUCER"
    )

    print("-" * 78)

    print(
        "Producer   P50(ms)   P95(ms)   "
        "P99(ms)   MAX(ms)   "
        "MaxGap(s)   MaxBurst"
    )

    print("-" * 78)

    for (
        drone_id,
        producer,
    ) in result[
        "producers"
    ].items():

        print(
            f"{drone_id:<10} "
            f"{producer['latency_p50_ms']:>7.1f}   "
            f"{producer['latency_p95_ms']:>7.1f}   "
            f"{producer['latency_p99_ms']:>7.1f}   "
            f"{producer['latency_max_ms']:>7.1f}   "
            f"{producer['max_telemetry_gap_seconds']:>8.2f}   "
            f"{producer['max_burst_size']:>8}"
        )

    print()

    print(
        "LATENCY THRESHOLDS"
    )

    print("-" * 78)

    for (
        drone_id,
        producer,
    ) in result[
        "producers"
    ].items():

        print(
            f"{drone_id} "
            f"| >=1s: "
            f"{producer['latency_ge_1000_ms']:2d} "
            f"| >=5s: "
            f"{producer['latency_ge_5000_ms']:2d}"
        )

    print()

    if buffer_config.get(
        "enabled",
        False,
    ):

        print(
            "CONFIGURED BUFFERING"
        )

        print("-" * 78)

        print(
            f"Window                    "
            f"T+{buffer_config['start_at_seconds']:.2f}s "
            f"to "
            f"T+{buffer_config['end_at_seconds']:.2f}s"
        )

        print(
            f"Target producers          "
            f"{buffer_config.get(
                'target_drone_ids',
                'ALL'
            )}"
        )

        print()

    print(
        "INTERPRETATION"
    )

    print("-" * 78)

    print(
        "Integrity describes whether the "
        "events arrived correctly."
    )

    print(
        "Timeliness describes whether the "
        "events arrived soon enough."
    )

    print()


if __name__ == "__main__":
    main()