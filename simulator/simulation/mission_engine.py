from dataclasses import dataclass, field

from simulator.domain.drone import Drone
from simulator.domain.mission import (
    Mission,
    MissionPhase,
    MissionStatus,
)
from simulator.domain.route import RouteInstance
from simulator.domain.states.mission_state_machine import (
    MissionStateMachine,
)
from simulator.simulation.geodesy import (
    destination_point,
)
from simulator.simulation.movement_engine import (
    MovementEngine,
)


@dataclass
class MissionUpdateResult:
    previous_phase: MissionPhase | None = None
    new_phase: MissionPhase | None = None

    reached_waypoints: list[str] = field(
        default_factory=list
    )

    distance_travelled_m: float = 0.0


class MissionEngine:

    @staticmethod
    def start(
        mission: Mission,
        drone: Drone,
    ) -> None:

        if mission.phase != MissionPhase.READY:
            raise ValueError(
                "Mission must be READY to start."
            )

        mission.status = MissionStatus.ACTIVE

        MissionStateMachine.transition(
            mission,
            MissionPhase.TAKEOFF,
        )

        drone.current_mission_id = (
            mission.mission_id
        )

        drone.asset_state = "ACTIVE"

        drone.ground_speed_mps = 0.0
        drone.vertical_speed_mps = (
            mission.climb_rate_mps
        )

    @staticmethod
    def _initialize_orbit(
        mission: Mission,
        drone: Drone,
    ) -> None:

        clockwise = (
            mission.orbit_direction.upper()
            == "CLOCKWISE"
        )

        if clockwise:
            center_bearing = (
                drone.heading_deg + 90.0
            ) % 360.0

            initial_orbit_angle = (
                drone.heading_deg - 90.0
            ) % 360.0

        else:
            center_bearing = (
                drone.heading_deg - 90.0
            ) % 360.0

            initial_orbit_angle = (
                drone.heading_deg + 90.0
            ) % 360.0

        (
            mission.orbit_center_latitude,
            mission.orbit_center_longitude,
        ) = destination_point(
            latitude_deg=drone.latitude,
            longitude_deg=drone.longitude,
            bearing_deg=center_bearing,
            distance_m=mission.orbit_radius_m,
        )

        mission.orbit_angle_deg = (
            initial_orbit_angle
        )

        mission.orbit_elapsed_seconds = 0.0

    @staticmethod
    def update(
        mission: Mission,
        drone: Drone,
        route: RouteInstance,
        dt_seconds: float,
        return_route: RouteInstance | None = None,
    ) -> MissionUpdateResult:

        result = MissionUpdateResult()

        # =================================================
        # TAKEOFF
        # =================================================
        if mission.phase == MissionPhase.TAKEOFF:

            previous_phase = mission.phase

            drone.ground_speed_mps = 0.0
            drone.vertical_speed_mps = (
                mission.climb_rate_mps
            )

            altitude_before_m = drone.altitude_m

            altitude_increment = (
                drone.vertical_speed_mps
                * dt_seconds
            )

            drone.altitude_m = min(
                drone.altitude_m
                + altitude_increment,
                mission.target_altitude_m,
            )

            result.distance_travelled_m = (
                drone.altitude_m
                - altitude_before_m
            )

            if (
                drone.altitude_m
                >= mission.target_altitude_m
            ):

                drone.vertical_speed_mps = 0.0

                drone.ground_speed_mps = (
                    mission.cruise_speed_mps
                )

                MissionStateMachine.transition(
                    mission,
                    MissionPhase.EN_ROUTE,
                )

                result.previous_phase = (
                    previous_phase
                )

                result.new_phase = (
                    mission.phase
                )

            return result

        # =================================================
        # EN_ROUTE
        # =================================================
        if mission.phase == MissionPhase.EN_ROUTE:

            drone.vertical_speed_mps = 0.0

            drone.ground_speed_mps = (
                mission.cruise_speed_mps
            )

            movement_result = (
                MovementEngine.update_route(
                    drone=drone,
                    route=route,
                    dt_seconds=dt_seconds,
                )
            )

            result.reached_waypoints.extend(
                movement_result.reached_waypoints
            )

            result.distance_travelled_m = (
                movement_result.distance_travelled_m
            )

            if movement_result.route_completed:

                previous_phase = mission.phase

                MissionStateMachine.transition(
                    mission,
                    MissionPhase.ON_MISSION,
                )

                MissionEngine._initialize_orbit(
                    mission,
                    drone,
                )

                result.previous_phase = (
                    previous_phase
                )

                result.new_phase = (
                    mission.phase
                )

            return result

        # =================================================
        # ON_MISSION / ORBIT
        # =================================================
        if mission.phase == MissionPhase.ON_MISSION:

            drone.vertical_speed_mps = 0.0

            drone.ground_speed_mps = (
                mission.cruise_speed_mps
            )

            if (
                mission.orbit_center_latitude
                is None
                or mission.orbit_center_longitude
                is None
                or mission.orbit_angle_deg
                is None
            ):
                raise RuntimeError(
                    "Orbit has not been initialized."
                )

            clockwise = (
                mission.orbit_direction.upper()
                == "CLOCKWISE"
            )

            result.distance_travelled_m = (
                drone.ground_speed_mps
                * dt_seconds
            )

            mission.orbit_angle_deg = (
                MovementEngine.update_orbit(
                    drone=drone,
                    center_latitude=(
                        mission.orbit_center_latitude
                    ),
                    center_longitude=(
                        mission.orbit_center_longitude
                    ),
                    radius_m=mission.orbit_radius_m,
                    current_angle_deg=(
                        mission.orbit_angle_deg
                    ),
                    dt_seconds=dt_seconds,
                    clockwise=clockwise,
                )
            )

            mission.orbit_elapsed_seconds += (
                dt_seconds
            )

            if (
                mission.orbit_elapsed_seconds
                >= mission.orbit_duration_seconds
            ):

                previous_phase = mission.phase

                MissionStateMachine.transition(
                    mission,
                    MissionPhase.RETURNING,
                )

                result.previous_phase = (
                    previous_phase
                )

                result.new_phase = (
                    mission.phase
                )

            return result

        # =================================================
        # RETURNING
        # =================================================
        if mission.phase == MissionPhase.RETURNING:

            if return_route is None:
                raise ValueError(
                    "return_route is required "
                    "during RETURNING"
                )

            drone.vertical_speed_mps = 0.0

            drone.ground_speed_mps = (
                mission.cruise_speed_mps
            )

            movement_result = (
                MovementEngine.update_route(
                    drone=drone,
                    route=return_route,
                    dt_seconds=dt_seconds,
                )
            )

            result.reached_waypoints.extend(
                movement_result.reached_waypoints
            )

            result.distance_travelled_m = (
                movement_result.distance_travelled_m
            )

            if movement_result.route_completed:

                previous_phase = mission.phase

                drone.ground_speed_mps = 0.0

                drone.vertical_speed_mps = (
                    -mission.descent_rate_mps
                )

                MissionStateMachine.transition(
                    mission,
                    MissionPhase.LANDING,
                )

                result.previous_phase = (
                    previous_phase
                )

                result.new_phase = (
                    mission.phase
                )

            return result

        # =================================================
        # LANDING
        # =================================================
        if mission.phase == MissionPhase.LANDING:

            previous_phase = mission.phase

            drone.ground_speed_mps = 0.0

            drone.vertical_speed_mps = (
                -mission.descent_rate_mps
            )

            altitude_before_m = drone.altitude_m

            altitude_decrement = (
                mission.descent_rate_mps
                * dt_seconds
            )

            drone.altitude_m = max(
                0.0,
                drone.altitude_m
                - altitude_decrement,
            )

            result.distance_travelled_m = (
                altitude_before_m
                - drone.altitude_m
            )

            if drone.altitude_m <= 0.0:

                drone.altitude_m = 0.0

                drone.ground_speed_mps = 0.0
                drone.vertical_speed_mps = 0.0

                MissionStateMachine.transition(
                    mission,
                    MissionPhase.LANDED,
                )

                mission.status = (
                    MissionStatus.COMPLETED
                )

                drone.asset_state = "AVAILABLE"
                drone.current_mission_id = None

                result.previous_phase = (
                    previous_phase
                )

                result.new_phase = (
                    mission.phase
                )

            return result

        # =================================================
        # LANDED
        # =================================================
        if mission.phase == MissionPhase.LANDED:

            drone.ground_speed_mps = 0.0
            drone.vertical_speed_mps = 0.0

            return result

        return result