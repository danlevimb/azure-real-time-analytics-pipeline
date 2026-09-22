from simulator.telemetry.event_factory import (EventFactory,)


class ConnectivityScenario:

    def __init__(
        self,
        *,
        target_drone_id: str,
        disconnect_at_seconds: float,
        reconnect_at_seconds: float | None,
        reason_code: str,
    ) -> None:

        self.target_drone_id = target_drone_id
        self.disconnect_at_seconds = disconnect_at_seconds
        self.reconnect_at_seconds = reconnect_at_seconds
        self.reason_code = reason_code
        self._disconnect_emitted = False
        self._reconnect_emitted = False

    @classmethod
    def from_config(
        cls,
        config: dict,
    ):

        scenario = config.get(
            "connectivity_scenario",
            {},
        )

        if not scenario.get(
            "enabled",
            False,
        ):
            return None

        return cls(
            target_drone_id=(
                scenario["target_drone_id"]
            ),
            disconnect_at_seconds=(
                float(
                    scenario[
                        "disconnect_at_seconds"
                    ]
                )
            ),
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
            reason_code=(
                scenario["reason_code"]
            ),
        )

    def applies_to(
        self,
        drone_id: str,
    ) -> bool:

        return (
            drone_id
            == self.target_drone_id
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

        events = []

        if not self.applies_to(
            drone.drone_id
        ):
            return events

        if (
            not self._disconnect_emitted
            and current_seconds
            >= self.disconnect_at_seconds
        ):

            previous_state = (
                drone.connection_state
            )

            drone.connection_state = (
                "DISCONNECTED"
            )

            events.append(
                EventFactory.state_transition(
                    drone=drone,
                    mission=mission,
                    event_time=event_time,
                    schema_version=schema_version,
                    simulator_run_id=(
                        simulator_run_id
                    ),
                    scenario=scenario,
                    seed=seed,
                    state_domain=(
                        "connection_state"
                    ),
                    previous_state=(
                        previous_state
                    ),
                    new_state=(
                        "DISCONNECTED"
                    ),
                    reason_code=(
                        self.reason_code
                    ),
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

            previous_state = (
                drone.connection_state
            )

            drone.connection_state = (
                "CONNECTED"
            )

            events.append(
                EventFactory.state_transition(
                    drone=drone,
                    mission=mission,
                    event_time=event_time,
                    schema_version=schema_version,
                    simulator_run_id=(
                        simulator_run_id
                    ),
                    scenario=scenario,
                    seed=seed,
                    state_domain=(
                        "connection_state"
                    ),
                    previous_state=(
                        previous_state
                    ),
                    new_state=(
                        "CONNECTED"
                    ),
                    reason_code=(
                        "SIMULATED_LINK_RESTORED"
                    ),
                )
            )

            self._reconnect_emitted = True

        return events