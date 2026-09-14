from dataclasses import dataclass


@dataclass(frozen=True)
class Waypoint:
    waypoint_id: str
    latitude: float
    longitude: float


@dataclass
class RouteInstance:
    route_instance_id: str
    waypoints: list[Waypoint]
    current_waypoint_index: int = 0

    @property
    def is_complete(self) -> bool:
        return self.current_waypoint_index >= len(
            self.waypoints
        )

    @property
    def current_waypoint(self) -> Waypoint | None:
        if self.is_complete:
            return None

        return self.waypoints[
            self.current_waypoint_index
        ]

    def advance(self) -> None:
        if not self.is_complete:
            self.current_waypoint_index += 1