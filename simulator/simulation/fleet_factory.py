from dataclasses import dataclass

from simulator.domain.drone import Drone
from simulator.domain.mission import Mission
from simulator.domain.route import (RouteInstance, Waypoint,)
from simulator.telemetry.telemetry_generator import (TelemetryGenerator,)

@dataclass
class DroneRuntime:
    """
    Independent runtime state for one drone.

    Infrastructure such as:
    - SimulationClock
    - TransportEngine
    - Publishers
    - Loggers

    will remain shared at fleet level.
    """

    drone: Drone
    mission: Mission

    outbound_route: RouteInstance
    return_route: RouteInstance

    telemetry_generator: TelemetryGenerator

    battery_drain_pct_per_minute: float = 0.0

    completed: bool = False


def build_fleet_runtimes(
    config: dict,
) -> list[DroneRuntime]:

    simulation = config[
        "simulation"
    ]

    telemetry_config = config[
        "telemetry"
    ]

    simulation_context = config[
        "simulation_context"
    ]

    drone_template = config[
        "drone"
    ]

    mission_template = config[
        "mission"
    ]

    route_template = config[
        "route"
    ]

    fleet_config = config[
        "fleet"
    ]

    movement = drone_template[
        "movement"
    ]

    orbit_config = mission_template[
        "orbit"
    ]

    base_position = drone_template[
        "initial_position"
    ]

    default_operational_profile = (
        drone_template.get(
            "operational_profile",
            {},
        )
    )

    default_initial_battery_pct = float(
        default_operational_profile.get(
            "initial_battery_pct",
            100.0,
        )
    )

    default_battery_drain_pct_per_minute = float(
        default_operational_profile.get(
            "battery_drain_pct_per_minute",
            0.0,
        )
    )

    default_initial_optic_fiber_m = float(
        default_operational_profile.get(
            "initial_optic_fiber_m",
            10000.0,
        )
    )

    runtimes: list[
        DroneRuntime
    ] = []

    for member in fleet_config[
        "members"
    ]:

        drone_id = member[
            "drone_id"
        ]

        mission_id = member[
            "mission_id"
        ]

        latitude_offset = float(
            member.get(
                "latitude_offset",
                0.0,
            )
        )

        longitude_offset = float(
            member.get(
                "longitude_offset",
                0.0,
            )
        )

        member_operational_profile = (
            member.get(
                "operational_profile",
                {},
            )
        )

        initial_battery_pct = float(
            member_operational_profile.get(
                "initial_battery_pct",
                default_initial_battery_pct,
            )
        )

        battery_drain_pct_per_minute = float(
            member_operational_profile.get(
                "battery_drain_pct_per_minute",
                default_battery_drain_pct_per_minute,
            )
        )

        initial_optic_fiber_m = float(
            member_operational_profile.get(
                "initial_optic_fiber_m",
                default_initial_optic_fiber_m,
            )
        )

        if not (
            0.0
            <= initial_battery_pct
            <= 100.0
        ):

            raise ValueError(
                "initial_battery_pct must "
                "be between 0 and 100 for "
                f"{drone_id}"
            )

        if battery_drain_pct_per_minute < 0:

            raise ValueError(
                "battery_drain_pct_per_minute "
                "cannot be negative for "
                f"{drone_id}"
            )

        if initial_optic_fiber_m < 0:

            raise ValueError(
                "initial_optic_fiber_m cannot "
                "be negative for "
                f"{drone_id}"
            )

        # =================================================
        # Independent base position
        # =================================================

        initial_latitude = (
            base_position[
                "latitude"
            ]
            + latitude_offset
        )

        initial_longitude = (
            base_position[
                "longitude"
            ]
            + longitude_offset
        )

        # =================================================
        # Drone
        # =================================================

        drone = Drone(
            drone_id=drone_id,

            battalion_id=(
                fleet_config[
                    "battalion_id"
                ]
            ),

            latitude=initial_latitude,
            longitude=initial_longitude,

            altitude_m=(
                base_position[
                    "altitude_m"
                ]
            ),

            ground_speed_mps=0.0,

            vertical_speed_mps=0.0,

            heading_deg=(
                movement[
                    "heading_deg"
                ]
            ),

            battery_pct=(
                initial_battery_pct
            ),

            optic_fiber_remaining_m=(
                initial_optic_fiber_m
            ),
        )

        # =================================================
        # Outbound route
        #
        # Same route geometry template,
        # shifted geographically for this drone.
        # =================================================

        outbound_route_id = (
            f"ROUTE-{drone_id}-001"
        )

        outbound_waypoints = []

        for waypoint_config in (
            route_template[
                "waypoints"
            ]
        ):

            outbound_waypoints.append(
                Waypoint(
                    waypoint_id=(
                        f"{drone_id}-"
                        f"{waypoint_config['waypoint_id']}"
                    ),

                    latitude=(
                        waypoint_config[
                            "latitude"
                        ]
                        + latitude_offset
                    ),

                    longitude=(
                        waypoint_config[
                            "longitude"
                        ]
                        + longitude_offset
                    ),
                )
            )

        outbound_route = (
            RouteInstance(
                route_instance_id=(
                    outbound_route_id
                ),

                waypoints=(
                    outbound_waypoints
                ),
            )
        )

        # =================================================
        # Return route
        # =================================================

        return_waypoints = list(
            reversed(
                outbound_route.waypoints
            )
        )

        return_waypoints.append(
            Waypoint(
                waypoint_id=(
                    f"{drone_id}-BASE-A"
                ),

                latitude=(
                    initial_latitude
                ),

                longitude=(
                    initial_longitude
                ),
            )
        )

        return_route = RouteInstance(
            route_instance_id=(
                f"{outbound_route_id}"
                "-RETURN"
            ),

            waypoints=(
                return_waypoints
            ),
        )

        # =================================================
        # Mission
        # =================================================

        mission = Mission(
            mission_id=mission_id,

            mission_type=(
                mission_template[
                    "mission_type"
                ]
            ),

            assigned_drone_id=(
                drone.drone_id
            ),

            route_instance_id=(
                outbound_route.
                route_instance_id
            ),

            target_altitude_m=(
                mission_template[
                    "target_altitude_m"
                ]
            ),

            climb_rate_mps=(
                mission_template[
                    "climb_rate_mps"
                ]
            ),

            descent_rate_mps=(
                mission_template[
                    "descent_rate_mps"
                ]
            ),

            cruise_speed_mps=(
                movement[
                    "cruise_speed_mps"
                ]
            ),

            orbit_radius_m=(
                orbit_config[
                    "radius_m"
                ]
            ),

            orbit_duration_seconds=(
                orbit_config[
                    "duration_seconds"
                ]
            ),

            orbit_direction=(
                orbit_config[
                    "direction"
                ]
            ),
        )

        # =================================================
        # Telemetry generator
        # =================================================

        telemetry_generator = (
            TelemetryGenerator(
                interval_ms=(
                    telemetry_config[
                        "interval_ms"
                    ]
                ),

                schema_version=(
                    telemetry_config[
                        "schema_version"
                    ]
                ),

                simulator_run_id=(
                    simulation_context[
                        "simulator_run_id"
                    ]
                ),

                scenario=(
                    simulation_context[
                        "scenario"
                    ]
                ),

                seed=(
                    simulation[
                        "seed"
                    ]
                ),

                tick_ms=(
                    simulation[
                        "tick_ms"
                    ]
                ),
            )
        )

        runtimes.append(
            DroneRuntime(
                drone=drone,
                mission=mission,

                outbound_route=(
                    outbound_route
                ),

                return_route=(
                    return_route
                ),

                telemetry_generator=(
                    telemetry_generator
                ),

                battery_drain_pct_per_minute=(
                    battery_drain_pct_per_minute
                ),
            )
        )

    return runtimes