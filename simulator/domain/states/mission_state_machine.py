from simulator.domain.mission import (
    Mission,
    MissionPhase,
)


class MissionStateMachine:

    _allowed_transitions = {
        MissionPhase.READY: {
            MissionPhase.TAKEOFF,
        },

        MissionPhase.TAKEOFF: {
            MissionPhase.EN_ROUTE,
        },

        MissionPhase.EN_ROUTE: {
            MissionPhase.ON_MISSION,
            MissionPhase.RETURNING, 
        },

        MissionPhase.ON_MISSION: {
            MissionPhase.RETURNING,
        },

        MissionPhase.RETURNING: {
            MissionPhase.LANDING,
        },

        MissionPhase.LANDING: {
            MissionPhase.LANDED,
        },

        MissionPhase.LANDED: set(),
    }

    @classmethod
    def transition(
        cls,
        mission: Mission,
        new_phase: MissionPhase,
    ) -> None:

        allowed = cls._allowed_transitions[
            mission.phase
        ]

        if new_phase not in allowed:
            raise ValueError(
                f"Invalid mission transition: "
                f"{mission.phase.value} "
                f"-> {new_phase.value}"
            )

        mission.phase = new_phase