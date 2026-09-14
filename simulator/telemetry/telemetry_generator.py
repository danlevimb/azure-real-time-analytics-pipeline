from simulator.domain.drone import Drone
from simulator.domain.mission import Mission
from simulator.simulation.clock import (
    SimulationClock,
)
from simulator.telemetry.event_factory import (
    EventFactory,
)


class TelemetryGenerator:

    def __init__(
        self,
        interval_ms: int,
        schema_version: str,
        simulator_run_id: str,
        scenario: str,
        seed: int,
        tick_ms: int,
    ) -> None:

        if interval_ms <= 0:
            raise ValueError(
                "Telemetry interval must be > 0"
            )

        if interval_ms % tick_ms != 0:
            raise ValueError(
                "Telemetry interval must be "
                "a multiple of tick_ms"
            )

        self.interval_ticks = (
            interval_ms // tick_ms
        )

        self.schema_version = schema_version
        self.simulator_run_id = (
            simulator_run_id
        )
        self.scenario = scenario
        self.seed = seed

    def is_due(
        self,
        tick_number: int,
    ) -> bool:

        return (
            tick_number
            % self.interval_ticks
            == 0
        )

    def generate(
        self,
        drone: Drone,
        mission: Mission,
        clock: SimulationClock,
    ) -> dict:

        return EventFactory.telemetry(
            drone=drone,
            mission=mission,
            event_time=clock.now,
            schema_version=self.schema_version,
            simulator_run_id=(
                self.simulator_run_id
            ),
            scenario=self.scenario,
            seed=self.seed,
        )