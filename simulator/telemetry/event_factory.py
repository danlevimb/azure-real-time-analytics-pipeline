from datetime import datetime

from simulator.domain.drone import Drone
from simulator.domain.mission import Mission


class EventFactory:

    @staticmethod
    def _format_datetime(
        value: datetime,
    ) -> str:

        return (
            value
            .isoformat()
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _next_sequence(
        drone: Drone,
    ) -> int:

        drone.source_sequence_number += 1

        return drone.source_sequence_number

    @classmethod
    def _base_event(
        cls,
        *,
        drone: Drone,
        mission: Mission,
        event_type: str,
        event_time: datetime,
        schema_version: str,
        simulator_run_id: str,
        scenario: str,
        seed: int,
    ) -> dict:

        sequence_number = cls._next_sequence(
            drone
        )

        event_id = (
            f"{simulator_run_id}-"
            f"{drone.drone_id}-"
            f"{sequence_number:08d}"
        )

        return {
            "schema_version": schema_version,
            "event_id": event_id,
            "event_type": event_type,

            "event_time": cls._format_datetime(
                event_time
            ),

            "drone_id": drone.drone_id,
            "battalion_id": drone.battalion_id,
            "mission_id": mission.mission_id,

            "source_sequence_number": (
                sequence_number
            ),

            "source_type": "virtual_drone",

            "source_gateway_id": (
                f"GW-{drone.battalion_id}"
            ),

            "simulation": {
                "simulator_run_id": (
                    simulator_run_id
                ),
                "scenario": scenario,
                "seed": seed,
            },
        }

    @classmethod
    def telemetry(
        cls,
        *,
        drone: Drone,
        mission: Mission,
        event_time: datetime,
        schema_version: str,
        simulator_run_id: str,
        scenario: str,
        seed: int,
    ) -> dict:

        event = cls._base_event(
            drone=drone,
            mission=mission,
            event_type="telemetry",
            event_time=event_time,
            schema_version=schema_version,
            simulator_run_id=simulator_run_id,
            scenario=scenario,
            seed=seed,
        )

        event["payload"] = {

            "position": {
                "latitude": drone.latitude,
                "longitude": drone.longitude,
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

            "health": {
                "platform_health": (
                    drone.platform_health
                ),
            },

            "communications": {
                "connection_state": (
                    drone.connection_state
                ),
            },

            "operations": {
                "asset_state": (
                    drone.asset_state
                ),
                "mission_status": (
                    mission.status.value
                ),
                "mission_phase": (
                    mission.phase.value
                ),
            },
        }

        if schema_version in {
            "1.1",
            "1.2",
        }:

            event["payload"][
                "consumables"
            ] = {
                "optic_fiber_remaining_m": (
                    drone.optic_fiber_remaining_m
                ),
            }


        if schema_version == "1.2":

            communication_mode = (
                drone.communication_mode
            )

            if communication_mode not in {
                "RF",
                "FIBER",
            }:

                raise ValueError(
                    "Event Contract v1.2 requires "
                    "communication_mode RF or FIBER"
                )

            if (
                communication_mode == "RF"
                and drone.optic_fiber_remaining_m
                is not None
            ):

                raise ValueError(
                    "RF drone cannot expose "
                    "optic_fiber_remaining_m"
                )

            if (
                communication_mode == "FIBER"
                and drone.optic_fiber_remaining_m
                is None
            ):

                raise ValueError(
                    "FIBER drone requires "
                    "optic_fiber_remaining_m"
                )

            event["payload"][
                "communications"
            ][
                "communication_mode"
            ] = communication_mode

        return event

    @classmethod
    def state_transition(
        cls,
        *,
        drone: Drone,
        mission: Mission,
        event_time: datetime,
        schema_version: str,
        simulator_run_id: str,
        scenario: str,
        seed: int,
        state_domain: str,
        previous_state: str,
        new_state: str,
        reason_code: str,
    ) -> dict:

        event = cls._base_event(
            drone=drone,
            mission=mission,
            event_type="state_transition",
            event_time=event_time,
            schema_version=schema_version,
            simulator_run_id=simulator_run_id,
            scenario=scenario,
            seed=seed,
        )

        event["payload"] = {
            "state_domain": state_domain,
            "previous_state": previous_state,
            "new_state": new_state,
            "reason_code": reason_code,
        }

        return event

    @classmethod
    def maintenance_event(
        cls,
        *,
        drone: Drone,
        mission: Mission,
        event_time: datetime,
        schema_version: str,
        simulator_run_id: str,
        scenario: str,
        seed: int,
        maintenance_action: str,
        maintenance_category: str,
        reason_code: str,
        severity: str,
    ) -> dict:

        event = cls._base_event(
            drone=drone,
            mission=mission,
            event_type="maintenance_event",
            event_time=event_time,
            schema_version=schema_version,
            simulator_run_id=simulator_run_id,
            scenario=scenario,
            seed=seed,
        )

        event["payload"] = {
            "maintenance_action": (
                maintenance_action
            ),
            "maintenance_category": (
                maintenance_category
            ),
            "reason_code": reason_code,
            "severity": severity,
        }

        return event

    @classmethod
    def status_confirmation(
        cls,
        *,
        drone: Drone,
        mission: Mission,
        event_time: datetime,
        schema_version: str,
        simulator_run_id: str,
        scenario: str,
        seed: int,
        state_domain: str,
        confirmed_state: str,
        confirmation_type: str,
        reason_code: str,
    ) -> dict:

        event = cls._base_event(
            drone=drone,
            mission=mission,
            event_type="status_confirmation",
            event_time=event_time,
            schema_version=schema_version,
            simulator_run_id=simulator_run_id,
            scenario=scenario,
            seed=seed,
        )

        event["payload"] = {
            "state_domain": state_domain,
            "confirmed_state": confirmed_state,
            "confirmation_type": (
                confirmation_type
            ),
            "reason_code": reason_code,
        }

        return event
