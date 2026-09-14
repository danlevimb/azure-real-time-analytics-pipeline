import json
from datetime import datetime
from pathlib import Path

from simulator.domain.drone import Drone
from simulator.domain.mission import Mission


class GroundTruthLogger:

    def __init__(
        self,
        output_path: Path,
        simulator_run_id: str,
    ) -> None:

        self.output_path = output_path
        self.simulator_run_id = simulator_run_id

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._file = self.output_path.open(
            "w",
            encoding="utf-8",
        )

    @staticmethod
    def _format_datetime(
        value: datetime,
    ) -> str:

        return (
            value
            .isoformat()
            .replace("+00:00", "Z")
        )

    def build_snapshot(
        self,
        *,
        drone: Drone,
        mission: Mission,
        simulation_time: datetime,
        elapsed_seconds: float,
    ) -> dict:

        return {
            "record_type": (
                "ground_truth_snapshot"
            ),

            "simulator_run_id": (
                self.simulator_run_id
            ),

            "simulation_time": (
                self._format_datetime(
                    simulation_time
                )
            ),

            "elapsed_seconds": (
                elapsed_seconds
            ),

            "drone_id": (
                drone.drone_id
            ),

            "battalion_id": (
                drone.battalion_id
            ),

            "mission_id": (
                mission.mission_id
            ),

            "position": {
                "latitude": (
                    drone.latitude
                ),
                "longitude": (
                    drone.longitude
                ),
                "altitude_m": (
                    drone.altitude_m
                ),
            },

            "movement": {
                "ground_speed_mps": (
                    drone.ground_speed_mps
                ),
                "vertical_speed_mps": (
                    drone.vertical_speed_mps
                ),
                "heading_deg": (
                    drone.heading_deg
                ),
            },

            "power": {
                "battery_pct": (
                    drone.battery_pct
                ),
            },

            "states": {
                "asset_state": (
                    drone.asset_state
                ),

                "mission_status": (
                    mission.status.value
                ),

                "mission_phase": (
                    mission.phase.value
                ),

                "platform_health": (
                    drone.platform_health
                ),

                "connection_state": (
                    drone.connection_state
                ),
            },
        }

    def log_snapshot(
        self,
        *,
        drone: Drone,
        mission: Mission,
        simulation_time: datetime,
        elapsed_seconds: float,
    ) -> dict:

        snapshot = self.build_snapshot(
            drone=drone,
            mission=mission,
            simulation_time=simulation_time,
            elapsed_seconds=elapsed_seconds,
        )

        json.dump(
            snapshot,
            self._file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        self._file.write("\n")
        self._file.flush()

        return snapshot

    def close(self) -> None:

        self._file.close()