from simulator.domain.drone import Drone


def update_optic_fiber(
    *,
    drone: Drone,
    distance_travelled_m: float,
) -> float:
    """
    Consume one meter of onboard optical fiber for each meter travelled.

    The model is intentionally monotonic: returning toward base does not reel
    deployed fiber back onto the spool. Exhaustion is observational in Event
    Contract v1.1 and does not yet alter mission or connectivity behavior.
    """

    if distance_travelled_m < 0:
        raise ValueError(
            "distance_travelled_m cannot be negative"
        )

    drone.optic_fiber_remaining_m = max(
        0.0,
        drone.optic_fiber_remaining_m
        - distance_travelled_m,
    )

    return drone.optic_fiber_remaining_m
