from dataclasses import dataclass
from enum import Enum


class MissionStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    LOST = "LOST"


class MissionPhase(str, Enum):
    READY = "READY"
    TAKEOFF = "TAKEOFF"
    EN_ROUTE = "EN_ROUTE"
    ON_MISSION = "ON_MISSION"
    RETURNING = "RETURNING"
    LANDING = "LANDING"
    LANDED = "LANDED"


@dataclass
class Mission:
    mission_id: str
    mission_type: str
    assigned_drone_id: str
    route_instance_id: str

    target_altitude_m: float

    climb_rate_mps: float
    descent_rate_mps: float
    cruise_speed_mps: float

    orbit_radius_m: float
    orbit_duration_seconds: float
    orbit_direction: str = "CLOCKWISE"

    status: MissionStatus = MissionStatus.PLANNED
    phase: MissionPhase = MissionPhase.READY

    # Runtime orbit state
    orbit_elapsed_seconds: float = 0.0

    orbit_center_latitude: float | None = None
    orbit_center_longitude: float | None = None

    orbit_angle_deg: float | None = None