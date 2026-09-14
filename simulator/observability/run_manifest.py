from datetime import (
    datetime,
    timezone,
)

import hashlib
import json
import platform

from pathlib import Path


MANIFEST_VERSION = "1.0"

MANIFEST_FILE_NAME = (
    "run_manifest.json"
)

CONFIG_SNAPSHOT_FILE_NAME = (
    "config_snapshot.yaml"
)


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):

            digest.update(
                chunk
            )

    return digest.hexdigest()


def build_run_manifest(
    *,
    config_path: Path,
    config: dict,
) -> dict:

    simulation = config[
        "simulation"
    ]

    simulation_context = config[
        "simulation_context"
    ]

    telemetry = config[
        "telemetry"
    ]

    transport = config[
        "transport"
    ]

    fleet = config.get(
        "fleet",
        {},
    )

    members = fleet.get(
        "members",
        [],
    )

    fault_config = transport.get(
        "fault_injection",
        {},
    )

    has_fault_rules = any(
        bool(
            fault_config.get(
                key,
                [],
            )
        )

        for key
        in (
            "duplicate_sequences",
            "drop_sequences",
            "extra_delay",
            "duplicate_targets",
            "drop_targets",
            "extra_delay_targets",
        )
    )

    manifest = {
        "manifest_version":
            MANIFEST_VERSION,

        "created_at_utc":
            (
                datetime.now(
                    timezone.utc
                )
                .isoformat()
                .replace(
                    "+00:00",
                    "Z",
                )
            ),

        "config_validation":
            "PASSED",

        "simulator_run_id":
            simulation_context[
                "simulator_run_id"
            ],

        "scenario":
            simulation_context[
                "scenario"
            ],

        "seed":
            simulation[
                "seed"
            ],

        "schema_version":
            telemetry[
                "schema_version"
            ],

        "simulation_start_time_utc":
            simulation[
                "start_time_utc"
            ],

        "duration_seconds":
            simulation[
                "duration_seconds"
            ],

        "tick_ms":
            simulation[
                "tick_ms"
            ],

        "speed_multiplier":
            simulation[
                "speed_multiplier"
            ],

        "telemetry_interval_ms":
            telemetry[
                "interval_ms"
            ],

        "base_delay_ms":
            transport[
                "base_delay_ms"
            ],

        "buffering_enabled":
            transport[
                "buffering"
            ][
                "enabled"
            ],

        "fault_injection_enabled":
            has_fault_rules,

        "maintenance_scenario_enabled":
            bool(
                config.get(
                    "maintenance_scenario",
                    {},
                ).get(
                    "enabled",
                    False,
                )
            ),

        "fleet_id":
            fleet.get(
                "fleet_id"
            ),

        "battalion_id":
            fleet.get(
                "battalion_id"
            ),

        "drone_count":
            len(
                members
            ),

        "drone_ids":
            [
                member[
                    "drone_id"
                ]

                for member
                in members
            ],

        "config_file":
            config_path.name,

        "config_snapshot_file":
            CONFIG_SNAPSHOT_FILE_NAME,

        "config_sha256":
            sha256_file(
                config_path
            ),

        "python_version":
            platform.python_version(),
    }

    return manifest


def write_run_manifest(
    *,
    config_path: Path,
    config: dict,
    output_dir: Path,
) -> tuple[
    Path,
    Path,
]:

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = build_run_manifest(
        config_path=config_path,
        config=config,
    )

    manifest_path = (
        output_dir
        / MANIFEST_FILE_NAME
    )

    snapshot_path = (
        output_dir
        / CONFIG_SNAPSHOT_FILE_NAME
    )

    # -----------------------------------------------------
    # Run-ID collision protection
    #
    # Re-running the SAME run/config is allowed during
    # development. Reusing the same run_id for a DIFFERENT
    # configuration is rejected.
    # -----------------------------------------------------

    if manifest_path.exists():

        try:

            existing_manifest = json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            json.JSONDecodeError,
            OSError,
        ) as exc:

            raise ValueError(
                "Existing run_manifest.json "
                "cannot be read safely"
            ) from exc

        existing_hash = (
            existing_manifest.get(
                "config_sha256"
            )
        )

        if (
            existing_hash
            and existing_hash
            != manifest[
                "config_sha256"
            ]
        ):

            raise ValueError(
                "simulator_run_id already "
                "exists with a different "
                "configuration hash: "
                f"{manifest['simulator_run_id']}"
            )

    # Preserve the exact YAML bytes that produced the run.
    snapshot_path.write_bytes(
        config_path.read_bytes()
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return (
        manifest_path,
        snapshot_path,
    )
