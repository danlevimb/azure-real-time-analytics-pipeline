from dataclasses import dataclass

from simulator.domain.drone import Drone


@dataclass(frozen=True)
class CommsDecision:
    """Decision made before an event enters shared transport."""

    transmit: bool
    reason: str


class CommsGate:
    """
    Producer-side egress gate.

    This layer represents whether the drone can put an already-generated
    logical event onto its outbound communications channel. Transport faults
    (delay, buffering, duplication, drops after submission) remain the
    responsibility of TransportEngine.
    """

    @staticmethod
    def evaluate(
        *,
        drone: Drone,
        force_transmit: bool = False,
    ) -> CommsDecision:

        if force_transmit:
            return CommsDecision(
                transmit=True,
                reason="FORCED_CONTROL_EVENT",
            )

        if drone.connection_state == "CONNECTED":
            return CommsDecision(
                transmit=True,
                reason="LINK_AVAILABLE",
            )

        return CommsDecision(
            transmit=False,
            reason="LINK_UNAVAILABLE",
        )
