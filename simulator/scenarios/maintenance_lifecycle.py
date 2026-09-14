from dataclasses import dataclass
from datetime import datetime

from simulator.domain.drone import Drone
from simulator.domain.mission import (
    Mission,
    MissionPhase,
)
from simulator.telemetry.event_factory import (
    EventFactory,
)


@dataclass
class MaintenanceLifecycleScenario:

    target_drone_id: str
    degrade_at_seconds: float
    maintenance_duration_seconds: float
    return_to_service_hold_seconds: float

    maintenance_category: str = (
        "PLATFORM_INSPECTION"
    )

    severity: str = "MEDIUM"

    health_degraded: bool = False
    maintenance_required: bool = False
    maintenance_started: bool = False
    maintenance_completed: bool = False
    returned_to_service: bool = False
    lifecycle_completed: bool = False

    maintenance_started_at_seconds: (
        float | None
    ) = None

    returned_to_service_at_seconds: (
        float | None
    ) = None

    @classmethod
    def from_config(
        cls,
        config: dict,
    ) -> "MaintenanceLifecycleScenario | None":

        scenario_config = config.get(
            "maintenance_scenario",
            {},
        )

        if not scenario_config.get(
            "enabled",
            False,
        ):

            return None

        return cls(
            target_drone_id=(
                scenario_config[
                    "target_drone_id"
                ]
            ),

            degrade_at_seconds=float(
                scenario_config[
                    "degrade_at_seconds"
                ]
            ),

            maintenance_duration_seconds=float(
                scenario_config[
                    "maintenance_duration_seconds"
                ]
            ),

            return_to_service_hold_seconds=float(
                scenario_config.get(
                    "return_to_service_hold_seconds",
                    2.0,
                )
            ),

            maintenance_category=(
                scenario_config.get(
                    "maintenance_category",
                    "PLATFORM_INSPECTION",
                )
            ),

            severity=(
                scenario_config.get(
                    "severity",
                    "MEDIUM",
                )
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

    def is_complete_for(
        self,
        drone_id: str,
    ) -> bool:

        return (
            self.applies_to(
                drone_id
            )
            and self.lifecycle_completed
        )

    def _common_event_args(
        self,
        *,
        drone: Drone,
        mission: Mission,
        event_time: datetime,
        schema_version: str,
        simulator_run_id: str,
        scenario: str,
        seed: int,
    ) -> dict:

        return {
            "drone":
                drone,

            "mission":
                mission,

            "event_time":
                event_time,

            "schema_version":
                schema_version,

            "simulator_run_id":
                simulator_run_id,

            "scenario":
                scenario,

            "seed":
                seed,
        }

    def update(
        self,
        *,
        drone: Drone,
        mission: Mission,
        current_seconds: float,
        event_time: datetime,
        schema_version: str,
        simulator_run_id: str,
        scenario: str,
        seed: int,
    ) -> list[dict]:

        if not self.applies_to(
            drone.drone_id
        ):

            return []

        if self.lifecycle_completed:

            return []

        events = []

        common = (
            self._common_event_args(
                drone=drone,
                mission=mission,
                event_time=event_time,
                schema_version=schema_version,
                simulator_run_id=simulator_run_id,
                scenario=scenario,
                seed=seed,
            )
        )

        # =================================================
        # 1) In-flight health degradation
        # =================================================

        if (
            not self.health_degraded
            and current_seconds
            >= self.degrade_at_seconds
        ):

            previous_health = (
                drone.platform_health
            )

            drone.platform_health = (
                "DEGRADED"
            )

            self.health_degraded = True
            self.maintenance_required = True

            events.append(
                EventFactory.state_transition(
                    **common,

                    state_domain=(
                        "platform_health"
                    ),

                    previous_state=(
                        previous_health
                    ),

                    new_state="DEGRADED",

                    reason_code=(
                        "HEALTH_DEGRADATION_DETECTED"
                    ),
                )
            )

            events.append(
                EventFactory.maintenance_event(
                    **common,

                    maintenance_action=(
                        "MAINTENANCE_REQUIRED"
                    ),

                    maintenance_category=(
                        self.maintenance_category
                    ),

                    reason_code=(
                        "HEALTH_DEGRADATION"
                    ),

                    severity=(
                        self.severity
                    ),
                )
            )

        # =================================================
        # 2) Mission completed -> maintenance starts
        # =================================================

        if (
            self.maintenance_required
            and not self.maintenance_started
            and mission.phase
            == MissionPhase.LANDED
        ):

            previous_asset_state = (
                drone.asset_state
            )

            self.maintenance_started = True

            self.maintenance_started_at_seconds = (
                current_seconds
            )

            events.append(
                EventFactory.maintenance_event(
                    **common,

                    maintenance_action=(
                        "MAINTENANCE_STARTED"
                    ),

                    maintenance_category=(
                        self.maintenance_category
                    ),

                    reason_code=(
                        "POST_MISSION_INSPECTION_STARTED"
                    ),

                    severity=(
                        self.severity
                    ),
                )
            )

            drone.asset_state = (
                "MAINTENANCE"
            )

            events.append(
                EventFactory.state_transition(
                    **common,

                    state_domain=(
                        "asset_state"
                    ),

                    previous_state=(
                        previous_asset_state
                    ),

                    new_state=(
                        "MAINTENANCE"
                    ),

                    reason_code=(
                        "MAINTENANCE_STARTED"
                    ),
                )
            )

            events.append(
                EventFactory.status_confirmation(
                    **common,

                    state_domain=(
                        "asset_state"
                    ),

                    confirmed_state=(
                        "MAINTENANCE"
                    ),

                    confirmation_type=(
                        "SYSTEM_CONFIRMATION"
                    ),

                    reason_code=(
                        "MAINTENANCE_ENTRY_CONFIRMED"
                    ),
                )
            )

        # =================================================
        # 3) Maintenance completes
        # =================================================

        if (
            self.maintenance_started
            and not self.maintenance_completed
            and self.maintenance_started_at_seconds
            is not None
            and (
                current_seconds
                - self.maintenance_started_at_seconds
            )
            >= self.maintenance_duration_seconds
        ):

            self.maintenance_completed = True

            events.append(
                EventFactory.maintenance_event(
                    **common,

                    maintenance_action=(
                        "MAINTENANCE_COMPLETED"
                    ),

                    maintenance_category=(
                        self.maintenance_category
                    ),

                    reason_code=(
                        "INSPECTION_COMPLETED"
                    ),

                    severity=(
                        self.severity
                    ),
                )
            )

            previous_health = (
                drone.platform_health
            )

            drone.platform_health = (
                "NORMAL"
            )

            events.append(
                EventFactory.state_transition(
                    **common,

                    state_domain=(
                        "platform_health"
                    ),

                    previous_state=(
                        previous_health
                    ),

                    new_state="NORMAL",

                    reason_code=(
                        "MAINTENANCE_RESTORED_HEALTH"
                    ),
                )
            )

            previous_asset_state = (
                drone.asset_state
            )

            drone.asset_state = (
                "RETURNED_TO_SERVICE"
            )

            self.returned_to_service = True

            self.returned_to_service_at_seconds = (
                current_seconds
            )

            events.append(
                EventFactory.state_transition(
                    **common,

                    state_domain=(
                        "asset_state"
                    ),

                    previous_state=(
                        previous_asset_state
                    ),

                    new_state=(
                        "RETURNED_TO_SERVICE"
                    ),

                    reason_code=(
                        "MAINTENANCE_COMPLETED"
                    ),
                )
            )

            events.append(
                EventFactory.status_confirmation(
                    **common,

                    state_domain=(
                        "asset_state"
                    ),

                    confirmed_state=(
                        "RETURNED_TO_SERVICE"
                    ),

                    confirmation_type=(
                        "SYSTEM_CONFIRMATION"
                    ),

                    reason_code=(
                        "RETURN_TO_SERVICE_CONFIRMED"
                    ),
                )
            )

        # =================================================
        # 4) Hold returned-to-service briefly, then AVAILABLE
        # =================================================

        if (
            self.returned_to_service
            and not self.lifecycle_completed
            and self.returned_to_service_at_seconds
            is not None
            and (
                current_seconds
                - self.returned_to_service_at_seconds
            )
            >= self.return_to_service_hold_seconds
        ):

            events.append(
                EventFactory.maintenance_event(
                    **common,

                    maintenance_action=(
                        "RETURNED_TO_SERVICE"
                    ),

                    maintenance_category=(
                        self.maintenance_category
                    ),

                    reason_code=(
                        "POST_MAINTENANCE_CHECKS_PASSED"
                    ),

                    severity=(
                        self.severity
                    ),
                )
            )

            previous_asset_state = (
                drone.asset_state
            )

            drone.asset_state = (
                "AVAILABLE"
            )

            events.append(
                EventFactory.state_transition(
                    **common,

                    state_domain=(
                        "asset_state"
                    ),

                    previous_state=(
                        previous_asset_state
                    ),

                    new_state="AVAILABLE",

                    reason_code=(
                        "ASSET_RELEASED_FOR_SERVICE"
                    ),
                )
            )

            events.append(
                EventFactory.status_confirmation(
                    **common,

                    state_domain=(
                        "asset_state"
                    ),

                    confirmed_state=(
                        "AVAILABLE"
                    ),

                    confirmation_type=(
                        "SYSTEM_CONFIRMATION"
                    ),

                    reason_code=(
                        "ASSET_AVAILABILITY_CONFIRMED"
                    ),
                )
            )

            self.lifecycle_completed = True

        return events
