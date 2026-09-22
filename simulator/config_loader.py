from datetime import datetime
from pathlib import Path
import re
import yaml


REQUIRED_BASE_SECTIONS = (
    "simulation",
    "simulation_context",
    "drone",
    "mission",
    "route",
    "observability",
    "telemetry",
    "transport",
)

ALLOWED_TOP_LEVEL_SECTIONS = set(
    REQUIRED_BASE_SECTIONS
) | {
    "config_version",
    "fleet",
    "maintenance_scenario",
    "publishers",
    "connectivity_scenario"
}

def _reject_unknown_keys(
    mapping: dict,
    *,
    allowed: set[str],
    path: str,
) -> None:

    unknown = sorted(
        set(
            mapping
        )
        - allowed
    )

    if unknown:

        raise ValueError(
            f"{path} contains unknown "
            f"key(s): {unknown}"
        )


def _require_mapping(
    value,
    *,
    path: str,
) -> dict:

    if not isinstance(
        value,
        dict,
    ):

        raise ValueError(f"{path} must be a mapping")

    return value


def _require_non_empty_string(
    value,
    *,
    path: str,
) -> str:

    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):

        raise ValueError(
            f"{path} must be a "
            "non-empty string"
        )

    return value


def _validate_coordinates(
    *,
    latitude,
    longitude,
    path: str,
) -> None:

    if not isinstance(
        latitude,
        (int, float),
    ):

        raise ValueError(
            f"{path}.latitude must be numeric"
        )

    if not isinstance(
        longitude,
        (int, float),
    ):

        raise ValueError(
            f"{path}.longitude must be numeric"
        )

    if not (
        -90
        <= latitude
        <= 90
    ):

        raise ValueError(
            f"{path}.latitude must be "
            "between -90 and 90"
        )

    if not (
        -180
        <= longitude
        <= 180
    ):

        raise ValueError(
            f"{path}.longitude must be "
            "between -180 and 180"
        )


def _validate_operational_profile(
    profile: dict,
    *,
    path: str,
) -> None:

    if not profile:
        return

    _reject_unknown_keys(
        profile,
        allowed={
            "initial_battery_pct",
            "battery_drain_pct_per_minute",
            "initial_optic_fiber_m",
        },
        path=path,
    )

    initial_battery_pct = float(
        profile.get(
            "initial_battery_pct",
            100.0,
        )
    )

    battery_drain_pct_per_minute = float(
        profile.get(
            "battery_drain_pct_per_minute",
            0.0,
        )
    )

    initial_optic_fiber_m = float(
        profile.get(
            "initial_optic_fiber_m",
            10000.0,
        )
    )

    if not (
        0.0
        <= initial_battery_pct
        <= 100.0
    ):

        raise ValueError(
            f"{path}.initial_battery_pct "
            "must be between 0 and 100"
        )

    if (
        battery_drain_pct_per_minute
        < 0
    ):

        raise ValueError(
            f"{path}."
            "battery_drain_pct_per_minute "
            "cannot be negative"
        )

    if initial_optic_fiber_m < 0:

        raise ValueError(
            f"{path}.initial_optic_fiber_m "
            "cannot be negative"
        )


def _validate_target_rules(
    rules: list,
    *,
    rule_name: str,
    fleet_drone_ids: set[str] | None,
    require_delay: bool = False,
) -> set[tuple[str, int]]:

    seen_targets = set()

    for index, rule in enumerate(
        rules
    ):

        _require_mapping(
            rule,
            path=(
                f"transport."
                f"fault_injection."
                f"{rule_name}[{index}]"
            ),
        )

        drone_id = (
            _require_non_empty_string(
                rule.get(
                    "drone_id"
                ),
                path=(
                    f"transport."
                    f"fault_injection."
                    f"{rule_name}[{index}]."
                    "drone_id"
                ),
            )
        )

        sequence_number = rule.get(
            "source_sequence_number"
        )

        if (
            not isinstance(
                sequence_number,
                int,
            )
            or sequence_number
            <= 0
        ):

            raise ValueError(
                f"transport.fault_injection."
                f"{rule_name}[{index}]."
                "source_sequence_number "
                "must be a positive integer"
            )

        if (
            fleet_drone_ids
            is not None
            and drone_id
            not in fleet_drone_ids
        ):

            raise ValueError(
                f"transport.fault_injection."
                f"{rule_name}[{index}]: "
                f"unknown drone_id "
                f"{drone_id}"
            )

        target = (
            drone_id,
            sequence_number,
        )

        if target in seen_targets:

            raise ValueError(
                f"Duplicate target in "
                f"{rule_name}: "
                f"{target}"
            )

        seen_targets.add(
            target
        )

        if require_delay:

            extra_delay_ms = rule.get(
                "extra_delay_ms"
            )

            if (
                not isinstance(
                    extra_delay_ms,
                    (int, float),
                )
                or extra_delay_ms < 0
            ):

                raise ValueError(
                    f"transport."
                    f"fault_injection."
                    f"{rule_name}[{index}]."
                    "extra_delay_ms cannot "
                    "be negative"
                )

    return seen_targets


def load_config(
    config_path: Path,
    *,
    require_fleet: bool = False,
) -> dict:

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        config = yaml.safe_load(
            file
        )

    if not config:

        raise ValueError(
            "Configuration file is empty."
        )

    _require_mapping(
        config,
        path="configuration",
    )

    _reject_unknown_keys(
        config,
        allowed=(
            ALLOWED_TOP_LEVEL_SECTIONS
        ),
        path="configuration",
    )

    missing_sections = [
        section

        for section
        in REQUIRED_BASE_SECTIONS

        if section not in config
    ]

    if missing_sections:

        raise ValueError(
            "Missing required configuration "
            "section(s): "
            + ", ".join(
                missing_sections
            )
        )

    # =====================================================
    # Simulation
    # =====================================================

    simulation = _require_mapping(
        config["simulation"],
        path="simulation",
    )

    tick_ms = simulation.get(
        "tick_ms"
    )

    duration_seconds = simulation.get(
        "duration_seconds"
    )

    speed_multiplier = simulation.get(
        "speed_multiplier"
    )

    seed = simulation.get(
        "seed"
    )

    if (
        not isinstance(
            tick_ms,
            (int, float),
        )
        or tick_ms <= 0
    ):

        raise ValueError(
            "simulation.tick_ms must be > 0"
        )

    if (
        not isinstance(
            duration_seconds,
            (int, float),
        )
        or duration_seconds <= 0
    ):

        raise ValueError(
            "simulation.duration_seconds "
            "must be > 0"
        )

    if (
        not isinstance(
            speed_multiplier,
            (int, float),
        )
        or speed_multiplier <= 0
    ):

        raise ValueError(
            "simulation.speed_multiplier "
            "must be > 0"
        )

    if not isinstance(
        seed,
        int,
    ):

        raise ValueError(
            "simulation.seed must be an integer"
        )

    start_time_utc = (
        _require_non_empty_string(
            simulation.get(
                "start_time_utc"
            ),
            path=(
                "simulation.start_time_utc"
            ),
        )
    )

    try:

        datetime.fromisoformat(
            start_time_utc.replace(
                "Z",
                "+00:00",
            )
        )

    except ValueError as exc:

        raise ValueError(
            "simulation.start_time_utc "
            "must be ISO-8601"
        ) from exc

    # =====================================================
    # Simulation context
    # =====================================================

    simulation_context = (
        _require_mapping(
            config[
                "simulation_context"
            ],
            path="simulation_context",
        )
    )

    simulator_run_id = (
        _require_non_empty_string(
            simulation_context.get(
                "simulator_run_id"
            ),
            path=(
                "simulation_context."
                "simulator_run_id"
            ),
        )
    )

    if not re.fullmatch(
        r"[A-Za-z0-9._-]+",
        simulator_run_id,
    ):

        raise ValueError(
            "simulation_context."
            "simulator_run_id may contain "
            "only letters, digits, '.', "
            "'_' and '-'"
        )

    _require_non_empty_string(
        simulation_context.get(
            "scenario"
        ),
        path=(
            "simulation_context.scenario"
        ),
    )

    # =====================================================
    # Observability
    # =====================================================

    observability = _require_mapping(
        config["observability"],
        path="observability",
    )

    console_interval_ms = (
        observability.get(
            "console_interval_ms"
        )
    )

    if (
        not isinstance(
            console_interval_ms,
            (int, float),
        )
        or console_interval_ms <= 0
    ):

        raise ValueError(
            "observability."
            "console_interval_ms "
            "must be > 0"
        )

    if (
        console_interval_ms
        % tick_ms
        != 0
    ):

        raise ValueError(
            "observability."
            "console_interval_ms must be "
            "a multiple of "
            "simulation.tick_ms"
        )

    # =====================================================
    # Drone / movement / power defaults
    # =====================================================

    drone = _require_mapping(
        config["drone"],
        path="drone",
    )

    initial_position = (
        _require_mapping(
            drone.get(
                "initial_position"
            ),
            path=(
                "drone.initial_position"
            ),
        )
    )

    _validate_coordinates(
        latitude=(
            initial_position.get(
                "latitude"
            )
        ),
        longitude=(
            initial_position.get(
                "longitude"
            )
        ),
        path=(
            "drone.initial_position"
        ),
    )

    movement = _require_mapping(
        drone.get(
            "movement"
        ),
        path="drone.movement",
    )

    cruise_speed_mps = (
        movement.get(
            "cruise_speed_mps"
        )
    )

    if (
        not isinstance(
            cruise_speed_mps,
            (int, float),
        )
        or cruise_speed_mps < 0
    ):

        raise ValueError(
            "drone.movement."
            "cruise_speed_mps cannot "
            "be negative"
        )

    initial_altitude_m = (
        initial_position.get(
            "altitude_m"
        )
    )

    if (
        not isinstance(
            initial_altitude_m,
            (int, float),
        )
        or initial_altitude_m < 0
    ):

        raise ValueError(
            "drone.initial_position."
            "altitude_m cannot be negative"
        )

    heading_deg = movement.get(
        "heading_deg"
    )

    if (
        not isinstance(
            heading_deg,
            (int, float),
        )
        or not (
            0.0
            <= heading_deg
            < 360.0
        )
    ):

        raise ValueError(
            "drone.movement.heading_deg "
            "must be >= 0 and < 360"
        )

    _validate_operational_profile(
        _require_mapping(
            drone.get(
                "operational_profile",
                {},
            ),
            path=(
                "drone.operational_profile"
            ),
        ),
        path=(
            "drone.operational_profile"
        ),
    )

    # =====================================================
    # Mission
    # =====================================================

    mission = _require_mapping(
        config["mission"],
        path="mission",
    )

    _require_non_empty_string(
        mission.get(
            "mission_type"
        ),
        path="mission.mission_type",
    )

    target_altitude_m = (
        mission.get(
            "target_altitude_m"
        )
    )

    if (
        not isinstance(
            target_altitude_m,
            (int, float),
        )
        or target_altitude_m < 0
    ):

        raise ValueError(
            "mission.target_altitude_m "
            "cannot be negative"
        )

    for field_name in (
        "climb_rate_mps",
        "descent_rate_mps",
    ):

        value = mission.get(
            field_name
        )

        if (
            not isinstance(
                value,
                (int, float),
            )
            or value <= 0
        ):

            raise ValueError(
                f"mission.{field_name} "
                "must be > 0"
            )

    orbit = _require_mapping(
        mission.get(
            "orbit"
        ),
        path="mission.orbit",
    )

    radius_m = orbit.get(
        "radius_m"
    )

    duration_s = orbit.get(
        "duration_seconds"
    )

    direction = (
        _require_non_empty_string(
            orbit.get(
                "direction"
            ),
            path=(
                "mission.orbit.direction"
            ),
        )
        .upper()
    )

    if (
        not isinstance(
            radius_m,
            (int, float),
        )
        or radius_m <= 0
    ):

        raise ValueError(
            "mission.orbit.radius_m "
            "must be > 0"
        )

    if (
        not isinstance(
            duration_s,
            (int, float),
        )
        or duration_s < 0
    ):

        raise ValueError(
            "mission.orbit.duration_seconds "
            "cannot be negative"
        )

    if direction not in (
        "CLOCKWISE",
        "COUNTERCLOCKWISE",
    ):

        raise ValueError(
            "mission.orbit.direction must "
            "be CLOCKWISE or "
            "COUNTERCLOCKWISE"
        )

    # =====================================================
    # Route
    # =====================================================

    route = _require_mapping(
        config["route"],
        path="route",
    )

    waypoints = route.get(
        "waypoints",
        [],
    )

    if (
        not isinstance(
            waypoints,
            list,
        )
        or not waypoints
    ):

        raise ValueError(
            "route must contain at least "
            "one waypoint"
        )

    waypoint_ids = set()

    for index, waypoint in enumerate(
        waypoints
    ):

        _require_mapping(
            waypoint,
            path=(
                f"route.waypoints[{index}]"
            ),
        )

        waypoint_id = (
            _require_non_empty_string(
                waypoint.get(
                    "waypoint_id"
                ),
                path=(
                    f"route.waypoints[{index}]."
                    "waypoint_id"
                ),
            )
        )

        if waypoint_id in waypoint_ids:

            raise ValueError(
                "Duplicate waypoint_id: "
                f"{waypoint_id}"
            )

        waypoint_ids.add(
            waypoint_id
        )

        _validate_coordinates(
            latitude=(
                waypoint.get(
                    "latitude"
                )
            ),
            longitude=(
                waypoint.get(
                    "longitude"
                )
            ),
            path=(
                f"route.waypoints[{index}]"
            ),
        )

    # =====================================================
    # Telemetry
    # =====================================================

    telemetry = _require_mapping(
        config["telemetry"],
        path="telemetry",
    )

    telemetry_interval_ms = (
        telemetry.get(
            "interval_ms"
        )
    )

    if (
        not isinstance(
            telemetry_interval_ms,
            (int, float),
        )
        or telemetry_interval_ms <= 0
    ):

        raise ValueError(
            "telemetry.interval_ms "
            "must be > 0"
        )

    if (
        telemetry_interval_ms
        % tick_ms
        != 0
    ):

        raise ValueError(
            "telemetry.interval_ms must be "
            "a multiple of "
            "simulation.tick_ms"
        )

    schema_version = _require_non_empty_string(
        telemetry.get(
            "schema_version"
        ),
        path=(
            "telemetry.schema_version"
        ),
    )

    if schema_version not in {
        "1.0",
        "1.1",
    }:

        raise ValueError(
            "telemetry.schema_version must "
            "be one of: 1.0, 1.1"
        )


    # =====================================================
    # Publishers
    #
    # Backward compatibility:
    # if this section is absent, fleet_main keeps the
    # historical local FilePublisher enabled and cloud
    # publishing disabled.
    # =====================================================

    publishers = config.get(
        "publishers",
        {}
    )

    if publishers:

        publishers = _require_mapping(
            publishers,
            path="publishers",
        )

        _reject_unknown_keys(
            publishers,
            allowed={
                "file",
                "event_hubs",
            },
            path="publishers",
        )

        file_publisher = (
            _require_mapping(
                publishers.get(
                    "file",
                    {},
                ),
                path="publishers.file",
            )
        )

        _reject_unknown_keys(
            file_publisher,
            allowed={
                "enabled",
            },
            path="publishers.file",
        )

        file_enabled = (
            file_publisher.get(
                "enabled",
                True,
            )
        )

        if not isinstance(
            file_enabled,
            bool,
        ):

            raise ValueError(
                "publishers.file.enabled "
                "must be boolean"
            )

        event_hubs = (
            _require_mapping(
                publishers.get(
                    "event_hubs",
                    {},
                ),
                path=(
                    "publishers.event_hubs"
                ),
            )
        )

        _reject_unknown_keys(
            event_hubs,
            allowed={
                "enabled",
                "fully_qualified_namespace",
                "event_hub_name",
                "partition_key_field",
                "buffered_mode",
                "max_wait_time_seconds",
            },
            path=(
                "publishers.event_hubs"
            ),
        )

        event_hubs_enabled = (
            event_hubs.get(
                "enabled",
                False,
            )
        )

        if not isinstance(
            event_hubs_enabled,
            bool,
        ):

            raise ValueError(
                "publishers.event_hubs."
                "enabled must be boolean"
            )

        if (
            not file_enabled
            and not event_hubs_enabled
        ):

            raise ValueError(
                "At least one publisher "
                "must be enabled"
            )

        if event_hubs_enabled:

            namespace = (
                _require_non_empty_string(
                    event_hubs.get(
                        "fully_qualified_namespace"
                    ),
                    path=(
                        "publishers.event_hubs."
                        "fully_qualified_namespace"
                    ),
                )
            )

            if (
                "://" in namespace
                or "/" in namespace
                or not namespace.endswith(
                    ".servicebus.windows.net"
                )
            ):

                raise ValueError(
                    "publishers.event_hubs."
                    "fully_qualified_namespace "
                    "must look like "
                    "<namespace>.servicebus."
                    "windows.net and must not "
                    "include a URL scheme"
                )

            namespace_prefix = (
                namespace.removesuffix(
                    ".servicebus.windows.net"
                )
            )

            if (
                not namespace_prefix
                or not re.fullmatch(
                    r"[A-Za-z0-9-]+",
                    namespace_prefix,
                )
            ):

                raise ValueError(
                    "publishers.event_hubs."
                    "fully_qualified_namespace "
                    "contains an invalid "
                    "namespace name"
                )

            _require_non_empty_string(
                event_hubs.get(
                    "event_hub_name"
                ),
                path=(
                    "publishers.event_hubs."
                    "event_hub_name"
                ),
            )

            partition_key_field = (
                _require_non_empty_string(
                    event_hubs.get(
                        "partition_key_field"
                    ),
                    path=(
                        "publishers.event_hubs."
                        "partition_key_field"
                    ),
                )
            )

            if (
                partition_key_field
                != "drone_id"
            ):

                raise ValueError(
                    "Event Contract v1 "
                    "requires "
                    "publishers.event_hubs."
                    "partition_key_field "
                    "to be 'drone_id'"
                )

            buffered_mode = (
                event_hubs.get(
                    "buffered_mode",
                    True,
                )
            )

            if not isinstance(
                buffered_mode,
                bool,
            ):

                raise ValueError(
                    "publishers.event_hubs."
                    "buffered_mode must "
                    "be boolean"
                )

            max_wait_time_seconds = (
                event_hubs.get(
                    "max_wait_time_seconds",
                    0.5,
                )
            )

            if (
                not isinstance(
                    max_wait_time_seconds,
                    (int, float),
                )
                or max_wait_time_seconds
                <= 0
            ):

                raise ValueError(
                    "publishers.event_hubs."
                    "max_wait_time_seconds "
                    "must be > 0"
                )

    # =====================================================
    # Fleet
    # =====================================================

    fleet_drone_ids = None
    fleet_mission_ids = None

    if require_fleet and (
        "fleet" not in config
    ):

        raise ValueError(
            "fleet section is required "
            "for fleet simulation"
        )

    if "fleet" in config:

        fleet = _require_mapping(
            config["fleet"],
            path="fleet",
        )

        _require_non_empty_string(
            fleet.get(
                "fleet_id"
            ),
            path="fleet.fleet_id",
        )

        _require_non_empty_string(
            fleet.get(
                "battalion_id"
            ),
            path="fleet.battalion_id",
        )

        members = fleet.get(
            "members"
        )

        if (
            not isinstance(
                members,
                list,
            )
            or not members
        ):

            raise ValueError(
                "fleet.members must contain "
                "at least one member"
            )

        fleet_drone_ids = set()
        fleet_mission_ids = set()

        for index, member in enumerate(
            members
        ):

            _require_mapping(
                member,
                path=(
                    f"fleet.members[{index}]"
                ),
            )

            drone_id = (
                _require_non_empty_string(
                    member.get(
                        "drone_id"
                    ),
                    path=(
                        f"fleet.members[{index}]."
                        "drone_id"
                    ),
                )
            )

            mission_id = (
                _require_non_empty_string(
                    member.get(
                        "mission_id"
                    ),
                    path=(
                        f"fleet.members[{index}]."
                        "mission_id"
                    ),
                )
            )

            if (
                drone_id
                in fleet_drone_ids
            ):

                raise ValueError(
                    "Duplicate fleet drone_id: "
                    f"{drone_id}"
                )

            if (
                mission_id
                in fleet_mission_ids
            ):

                raise ValueError(
                    "Duplicate fleet mission_id: "
                    f"{mission_id}"
                )

            fleet_drone_ids.add(
                drone_id
            )

            fleet_mission_ids.add(
                mission_id
            )

            for offset_name in (
                "latitude_offset",
                "longitude_offset",
            ):

                offset_value = member.get(
                    offset_name,
                    0.0,
                )

                if not isinstance(
                    offset_value,
                    (int, float),
                ):

                    raise ValueError(
                        f"fleet.members[{index}]."
                        f"{offset_name} "
                        "must be numeric"
                    )

            _validate_operational_profile(
                _require_mapping(
                    member.get(
                        "operational_profile",
                        {},
                    ),
                    path=(
                        f"fleet.members[{index}]."
                        "operational_profile"
                    ),
                ),
                path=(
                    f"fleet.members[{index}]."
                    "operational_profile"
                ),
            )

    # =====================================================
    # Transport
    # =====================================================

    transport = _require_mapping(
        config["transport"],
        path="transport",
    )

    _reject_unknown_keys(
        transport,
        allowed={
            "enabled",
            "base_delay_ms",
            "buffering",
            "fault_injection",
        },
        path="transport",
    )

    base_delay_ms = transport.get(
        "base_delay_ms"
    )

    if (
        not isinstance(
            base_delay_ms,
            (int, float),
        )
        or base_delay_ms < 0
    ):

        raise ValueError(
            "transport.base_delay_ms "
            "cannot be negative"
        )

    buffering = _require_mapping(
        transport.get(
            "buffering"
        ),
        path="transport.buffering",
    )

    _reject_unknown_keys(
        buffering,
        allowed={
            "enabled",
            "start_at_seconds",
            "end_at_seconds",
            "target_drone_ids",
        },
        path="transport.buffering",
    )

    buffering_enabled = buffering.get(
        "enabled"
    )

    if not isinstance(
        buffering_enabled,
        bool,
    ):

        raise ValueError(
            "transport.buffering.enabled "
            "must be boolean"
        )

    buffer_target_drone_ids = (
        buffering.get(
            "target_drone_ids"
        )
    )

    if (
        buffer_target_drone_ids
        is not None
    ):

        if not isinstance(
            buffer_target_drone_ids,
            list,
        ):

            raise ValueError(
                "transport.buffering."
                "target_drone_ids "
                "must be a list"
            )

        if (
            len(
                buffer_target_drone_ids
            )
            != len(
                set(
                    buffer_target_drone_ids
                )
            )
        ):

            raise ValueError(
                "transport.buffering."
                "target_drone_ids contains "
                "duplicates"
            )

        if (
            fleet_drone_ids
            is not None
        ):

            unknown_targets = sorted(
                set(
                    buffer_target_drone_ids
                )
                - fleet_drone_ids
            )

            if unknown_targets:

                raise ValueError(
                    "transport.buffering."
                    "target_drone_ids contains "
                    "unknown fleet member(s): "
                    f"{unknown_targets}"
                )

    start_seconds = buffering.get(
        "start_at_seconds"
    )

    end_seconds = buffering.get(
        "end_at_seconds"
    )

    if (
        not isinstance(
            start_seconds,
            (int, float),
        )
        or start_seconds < 0
    ):

        raise ValueError(
            "transport.buffering."
            "start_at_seconds cannot "
            "be negative"
        )

    if (
        not isinstance(
            end_seconds,
            (int, float),
        )
        or end_seconds < 0
    ):

        raise ValueError(
            "transport.buffering."
            "end_at_seconds cannot "
            "be negative"
        )

    if (
        buffering_enabled
        and end_seconds
        <= start_seconds
    ):

        raise ValueError(
            "transport.buffering."
            "end_at_seconds must be "
            "greater than "
            "start_at_seconds when "
            "buffering is enabled"
        )

    # =====================================================
    # Fault injection
    # =====================================================

    fault_config = (
        _require_mapping(
            transport.get(
                "fault_injection",
                {},
            ),
            path=(
                "transport.fault_injection"
            ),
        )
    )

    _reject_unknown_keys(
        fault_config,
        allowed={
            "duplicate_sequences",
            "drop_sequences",
            "extra_delay",
            "duplicate_targets",
            "drop_targets",
            "extra_delay_targets",
        },
        path="transport.fault_injection",
    )

    duplicate_sequence_list = (
        fault_config.get(
            "duplicate_sequences",
            [],
        )
    )

    drop_sequence_list = (
        fault_config.get(
            "drop_sequences",
            [],
        )
    )

    if not isinstance(
        duplicate_sequence_list,
        list,
    ):

        raise ValueError(
            "transport.fault_injection."
            "duplicate_sequences must "
            "be a list"
        )

    if not isinstance(
        drop_sequence_list,
        list,
    ):

        raise ValueError(
            "transport.fault_injection."
            "drop_sequences must "
            "be a list"
        )

    if (
        len(
            duplicate_sequence_list
        )
        != len(
            set(
                duplicate_sequence_list
            )
        )
    ):

        raise ValueError(
            "transport.fault_injection."
            "duplicate_sequences contains "
            "duplicate entries"
        )

    if (
        len(
            drop_sequence_list
        )
        != len(
            set(
                drop_sequence_list
            )
        )
    ):

        raise ValueError(
            "transport.fault_injection."
            "drop_sequences contains "
            "duplicate entries"
        )

    duplicate_sequences = set(
        duplicate_sequence_list
    )

    drop_sequences = set(
        drop_sequence_list
    )

    overlap = (
        duplicate_sequences
        & drop_sequences
    )

    if overlap:

        raise ValueError(
            "A source sequence cannot be "
            "both duplicated and dropped: "
            f"{sorted(overlap)}"
        )

    for sequence_number in (
        duplicate_sequences
        | drop_sequences
    ):

        if (
            not isinstance(
                sequence_number,
                int,
            )
            or sequence_number <= 0
        ):

            raise ValueError(
                "Fault sequence numbers "
                "must be positive integers"
            )

    extra_delay_rules = (
        fault_config.get(
            "extra_delay",
            [],
        )
    )

    if not isinstance(
        extra_delay_rules,
        list,
    ):

        raise ValueError(
            "transport.fault_injection."
            "extra_delay must be a list"
        )

    seen_extra_delay_sequences = set()

    for index, rule in enumerate(
        extra_delay_rules
    ):

        _require_mapping(
            rule,
            path=(
                "transport.fault_injection."
                f"extra_delay[{index}]"
            ),
        )

        if (
            not isinstance(
                rule.get(
                    "source_sequence_number"
                ),
                int,
            )
            or rule[
                "source_sequence_number"
            ]
            <= 0
        ):

            raise ValueError(
                "transport.fault_injection."
                f"extra_delay[{index}]."
                "source_sequence_number "
                "must be > 0"
            )

        sequence_number = (
            rule[
                "source_sequence_number"
            ]
        )

        if (
            sequence_number
            in seen_extra_delay_sequences
        ):

            raise ValueError(
                "Duplicate source sequence "
                "in extra_delay: "
                f"{sequence_number}"
            )

        seen_extra_delay_sequences.add(
            sequence_number
        )

        if (
            not isinstance(
                rule.get(
                    "extra_delay_ms"
                ),
                (int, float),
            )
            or rule[
                "extra_delay_ms"
            ]
            < 0
        ):

            raise ValueError(
                "transport.fault_injection."
                f"extra_delay[{index}]."
                "extra_delay_ms cannot "
                "be negative"
            )

    duplicate_targets = (
        _validate_target_rules(
            fault_config.get(
                "duplicate_targets",
                [],
            ),
            rule_name=(
                "duplicate_targets"
            ),
            fleet_drone_ids=(
                fleet_drone_ids
            ),
        )
    )

    drop_targets = (
        _validate_target_rules(
            fault_config.get(
                "drop_targets",
                [],
            ),
            rule_name=(
                "drop_targets"
            ),
            fleet_drone_ids=(
                fleet_drone_ids
            ),
        )
    )

    target_overlap = (
        duplicate_targets
        & drop_targets
    )

    if target_overlap:

        raise ValueError(
            "A producer target cannot be "
            "both duplicated and dropped: "
            f"{sorted(target_overlap)}"
        )

    _validate_target_rules(
        fault_config.get(
            "extra_delay_targets",
            [],
        ),
        rule_name=(
            "extra_delay_targets"
        ),
        fleet_drone_ids=(
            fleet_drone_ids
        ),
        require_delay=True,
    )

    # =====================================================
    # Maintenance lifecycle scenario
    # =====================================================

    maintenance_scenario = config.get(
        "maintenance_scenario",
        {}
    )

    if maintenance_scenario:

        maintenance_scenario = (
            _require_mapping(
                maintenance_scenario,
                path=(
                    "maintenance_scenario"
                ),
            )
        )

        _reject_unknown_keys(
            maintenance_scenario,
            allowed={
                "enabled",
                "target_drone_id",
                "degrade_at_seconds",
                "maintenance_duration_seconds",
                "return_to_service_hold_seconds",
                "maintenance_category",
                "severity",
            },
            path="maintenance_scenario",
        )

        enabled = (
            maintenance_scenario.get(
                "enabled",
                False,
            )
        )

        if not isinstance(
            enabled,
            bool,
        ):

            raise ValueError(
                "maintenance_scenario.enabled "
                "must be boolean"
            )

        if enabled:

            if (
                fleet_drone_ids
                is None
            ):

                raise ValueError(
                    "maintenance_scenario "
                    "requires a fleet section"
                )

            target_drone_id = (
                _require_non_empty_string(
                    maintenance_scenario.get(
                        "target_drone_id"
                    ),
                    path=(
                        "maintenance_scenario."
                        "target_drone_id"
                    ),
                )
            )

            if (
                target_drone_id
                not in fleet_drone_ids
            ):

                raise ValueError(
                    "maintenance_scenario."
                    "target_drone_id is not "
                    "a fleet member: "
                    f"{target_drone_id}"
                )

            degrade_at_seconds = (
                maintenance_scenario.get(
                    "degrade_at_seconds"
                )
            )

            if (
                not isinstance(
                    degrade_at_seconds,
                    (int, float),
                )
                or degrade_at_seconds < 0
                or degrade_at_seconds
                >= duration_seconds
            ):

                raise ValueError(
                    "maintenance_scenario."
                    "degrade_at_seconds must "
                    "be >= 0 and less than "
                    "simulation.duration_seconds"
                )

            maintenance_duration_seconds = (
                maintenance_scenario.get(
                    "maintenance_duration_seconds"
                )
            )

            if (
                not isinstance(
                    maintenance_duration_seconds,
                    (int, float),
                )
                or maintenance_duration_seconds
                <= 0
            ):

                raise ValueError(
                    "maintenance_scenario."
                    "maintenance_duration_seconds "
                    "must be > 0"
                )

            return_hold_seconds = (
                maintenance_scenario.get(
                    "return_to_service_hold_seconds",
                    0.0,
                )
            )

            if (
                not isinstance(
                    return_hold_seconds,
                    (int, float),
                )
                or return_hold_seconds
                < 0
            ):

                raise ValueError(
                    "maintenance_scenario."
                    "return_to_service_hold_seconds "
                    "cannot be negative"
                )

    # =====================================================
    # Connectivity scenario
    # =====================================================

    connectivity_scenario = config.get(
        "connectivity_scenario",
        {},
    )

    if connectivity_scenario:

        connectivity_scenario = (
            _require_mapping(
                connectivity_scenario,
                path="connectivity_scenario",
            )
        )

        _reject_unknown_keys(
            connectivity_scenario,
            allowed={
                "enabled",
                "target_drone_id",
                "disconnect_at_seconds",
                "reconnect_at_seconds",
                "reason_code",
                "severity",
            },
            path="connectivity_scenario",
        )

        enabled = connectivity_scenario.get(
            "enabled",
            False,
        )

        if not isinstance(enabled, bool):
            raise ValueError(
                "connectivity_scenario.enabled "
                "must be boolean"
            )

        if enabled:

            if fleet_drone_ids is None:
                raise ValueError(
                    "connectivity_scenario "
                    "requires a fleet section"
                )

            target_drone_id = (
                _require_non_empty_string(
                    connectivity_scenario.get(
                        "target_drone_id"
                    ),
                    path=(
                        "connectivity_scenario."
                        "target_drone_id"
                    ),
                )
            )

            if target_drone_id not in fleet_drone_ids:
                raise ValueError(
                    "connectivity_scenario."
                    "target_drone_id is not "
                    "a fleet member: "
                    f"{target_drone_id}"
                )

            disconnect_at_seconds = (
                connectivity_scenario.get(
                    "disconnect_at_seconds"
                )
            )

            if (
                not isinstance(
                    disconnect_at_seconds,
                    (int, float),
                )
                or disconnect_at_seconds < 0
                or disconnect_at_seconds
                >= duration_seconds
            ):
                raise ValueError(
                    "connectivity_scenario."
                    "disconnect_at_seconds must "
                    "be >= 0 and less than "
                    "simulation.duration_seconds"
                )

            reconnect_at_seconds = (
                connectivity_scenario.get(
                    "reconnect_at_seconds"
                )
            )

            if reconnect_at_seconds is not None:

                if (
                    not isinstance(
                        reconnect_at_seconds,
                        (int, float),
                    )
                    or reconnect_at_seconds
                    <= disconnect_at_seconds
                    or reconnect_at_seconds
                    >= duration_seconds
                ):
                    raise ValueError(
                        "connectivity_scenario."
                        "reconnect_at_seconds must "
                        "be greater than "
                        "disconnect_at_seconds and "
                        "less than simulation."
                        "duration_seconds"
                    )

            _require_non_empty_string(
                connectivity_scenario.get(
                    "reason_code"
                ),
                path=(
                    "connectivity_scenario."
                    "reason_code"
                ),
            )
    return config
