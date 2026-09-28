from simulator.domain.mission import (MissionStatus,)
from simulator.telemetry.event_factory import (EventFactory,)


class DestructionScenario:

    def __init__(self, *, target_drone_id: str, destroy_at_seconds: float,) -> None:

        if destroy_at_seconds < 0:
            raise ValueError(
                "destroy_at_seconds cannot be negative"
            )

        self.target_drone_id = target_drone_id
        self.destroy_at_seconds = float(destroy_at_seconds)
        self._destroyed = False

    @classmethod
    def from_config(cls, config: dict, ):

        scenario = config.get(
            "destruction_scenario",
            {},
        )

        if not scenario.get(
            "enabled",
            False,
        ):
            return None

        return cls(
            target_drone_id=(scenario["target_drone_id"]),
            destroy_at_seconds=float(scenario["destroy_at_seconds"]),)

    def applies_to(self, drone_id: str,) -> bool:

        return drone_id == self.target_drone_id

    def is_destroyed_for( self, drone_id: str,) -> bool:
        return (
            self.applies_to(
                drone_id
            )
            and self._destroyed
        )

    def update(
        self,
        *,
        drone,
        mission,
        current_seconds: float,
        event_time,
        schema_version: str,
        simulator_run_id: str,
        scenario: str,
        seed: int,
    ) -> list[dict]:

        if not self.applies_to(drone.drone_id):
            return []

        if self._destroyed:
            return []

        if current_seconds < self.destroy_at_seconds:
            return []

        if mission.status != MissionStatus.ACTIVE:
            raise ValueError(
                "DRONE_DESTROYED requires "
                "an ACTIVE mission"
            )

        events = []
        previous_asset_state = drone.asset_state
        previous_mission_status = mission.status.value
        previous_connection_state = drone.connection_state

        # ---------------------------------------------
        # Final terminal state
        # ---------------------------------------------

        drone.asset_state = "DESTROYED"
        mission.status = MissionStatus.ABORTED
        drone.connection_state = "DISCONNECTED"
        drone.ground_speed_mps = 0.0
        drone.vertical_speed_mps = 0.0

        # ---------------------------------------------
        # Asset terminal transition
        # ---------------------------------------------

        events.append(
            EventFactory.state_transition(
                drone = drone,
                mission = mission,
                event_time = event_time,
                schema_version = schema_version,
                simulator_run_id = simulator_run_id,
                scenario = scenario,
                seed = seed,
                state_domain = "asset_state",
                previous_state = previous_asset_state,
                new_state = "DESTROYED",
                reason_code = "DRONE_DESTROYED",
            )
        )

        # ---------------------------------------------
        # Mission terminal transition
        # ---------------------------------------------

        events.append(
            EventFactory.state_transition(
                drone=drone,
                mission=mission,
                event_time=event_time,
                schema_version=schema_version,
                simulator_run_id = simulator_run_id,
                scenario = scenario,
                seed = seed,
                state_domain = "mission_status",
                previous_state = previous_mission_status,
                new_state = "ABORTED",
                reason_code = "ASSET_DESTROYED",
            )
        )

        # ---------------------------------------------
        # Communications terminate
        # ---------------------------------------------

        if previous_connection_state != "DISCONNECTED":

            events.append(
                EventFactory.state_transition(
                    drone = drone,
                    mission = mission,
                    event_time = event_time,
                    schema_version = schema_version,
                    simulator_run_id = simulator_run_id,
                    scenario = scenario,
                    seed = seed,
                    state_domain = "connection_state",
                    previous_state = previous_connection_state,
                    new_state = "DISCONNECTED",
                    reason_code = "ASSET_DESTROYED",
                )
            )

        self._destroyed = True

        return events