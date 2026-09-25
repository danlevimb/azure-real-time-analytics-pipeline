from simulator.telemetry.event_factory import (EventFactory,)


FAULT_RESTORE_REASON = {
    "RF_LINK_LOSS": "RF_LINK_RESTORED",
    "RF_JAMMING": "RF_JAMMING_CLEARED",
    "FIBER_LINK_LOSS": "FIBER_LINK_RESTORED",
}


FAULT_COMMUNICATION_MODE = {
    "RF_LINK_LOSS": "RF",
    "RF_JAMMING": "RF",
    "FIBER_LINK_LOSS": "FIBER",
    "FIBER_CUT": "FIBER",
}

TERMINAL_FAULTS = {"FIBER_CUT",}

class ConnectivityScenario:

    def __init__(
        self,
        *,
        target_drone_id: str,
        disconnect_at_seconds: float,
        reconnect_at_seconds: float | None,
        reason_code: str | None = None,
        fault_type: str | None = None,
    ) -> None:

        if (
            reason_code is None
            and fault_type is None
        ):
            raise ValueError(
                "ConnectivityScenario requires "
                "reason_code or fault_type"
            )

        self.target_drone_id = target_drone_id
        self.disconnect_at_seconds = disconnect_at_seconds
        self.reconnect_at_seconds = reconnect_at_seconds
        self.fault_type = fault_type
        
        if (
            self.fault_type
            in TERMINAL_FAULTS
            and self.reconnect_at_seconds
            is not None
        ):
            raise ValueError(
                f"{self.fault_type} is a terminal "
                "connectivity fault and cannot "
                "configure reconnect_at_seconds"
            )

        self.reason_code = (
            fault_type
            if fault_type is not None
            else reason_code
        )

        self._disconnect_emitted = False
        self._reconnect_emitted = False

    @classmethod
    def from_config(cls, config: dict,):

        scenario = config.get("connectivity_scenario",{},)

        if not scenario.get(
            "enabled",
            False,
        ):
            return None

        config_version = str(config.get("config_version","1.0",))

        if config_version == "1.2":

            return cls(
                target_drone_id=scenario["target_drone_id"],
                disconnect_at_seconds=float(scenario["disconnect_at_seconds"]),
                reconnect_at_seconds=(
                    None
                    if scenario.get(
                        "reconnect_at_seconds"
                    )
                    is None
                    else float(
                        scenario[
                            "reconnect_at_seconds"
                        ]
                    )
                ),
                fault_type=scenario["fault_type"],
            )

        return cls(
            target_drone_id=scenario["target_drone_id"],
            disconnect_at_seconds=float(scenario["disconnect_at_seconds"]),
            reconnect_at_seconds=(
                None
                if scenario.get(
                    "reconnect_at_seconds"
                )
                is None
                else float(scenario["reconnect_at_seconds"])
            ),
            reason_code=scenario["reason_code"],
        )

    def applies_to(self, drone_id: str,) -> bool:
        return (drone_id == self.target_drone_id)

    def _validate_fault_for_drone(self, drone,) -> None:
        if self.fault_type is None:
            return

        expected_mode = (FAULT_COMMUNICATION_MODE[self.fault_type])

        if (drone.communication_mode!= expected_mode):
            raise ValueError(
                f"{self.fault_type} requires "
                f"communication_mode "
                f"{expected_mode}; "
                f"{drone.drone_id} uses "
                f"{drone.communication_mode}"
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
        seed: int,) -> list[dict]:

        events = []

        if not self.applies_to(drone.drone_id):
            return events

        self._validate_fault_for_drone(drone)

        if (
            not self._disconnect_emitted
            and current_seconds
            >= self.disconnect_at_seconds
        ):

            previous_state = drone.connection_state        
            drone.connection_state = "DISCONNECTED"
        
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
                    previous_state = previous_state,
                    new_state = "DISCONNECTED",
                    reason_code = self.reason_code,
                )
            )

            self._disconnect_emitted = True

        if (
            self.reconnect_at_seconds
            is not None
            and self._disconnect_emitted
            and not self._reconnect_emitted
            and current_seconds
            >= self.reconnect_at_seconds
        ):

            previous_state = drone.connection_state        
            drone.connection_state = "CONNECTED"

            restore_reason = (
                FAULT_RESTORE_REASON[
                    self.fault_type
                ]
                if self.fault_type
                is not None
                else
                "SIMULATED_LINK_RESTORED"
            )

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
                    previous_state = previous_state,
                    new_state = "CONNECTED",
                    reason_code = restore_reason,
                )
            )

            self._reconnect_emitted = True

        return events