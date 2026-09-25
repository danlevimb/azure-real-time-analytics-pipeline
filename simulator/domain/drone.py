from dataclasses import dataclass


@dataclass
class Drone:
    drone_id: str
    battalion_id: str

    latitude: float
    longitude: float
    altitude_m: float

    ground_speed_mps: float
    heading_deg: float

    vertical_speed_mps: float = 0.0

    battery_pct: float = 100.0
    optic_fiber_remaining_m: float | None = None

    asset_state: str = "AVAILABLE"
    platform_health: str = "NORMAL"
    connection_state: str = "CONNECTED"

    current_mission_id: str | None = None
    source_sequence_number: int = 0
    
    communication_mode: str | None = None
    