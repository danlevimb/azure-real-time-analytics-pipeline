from simulator.domain.drone import Drone

def update_optic_fiber(
    *,
    drone: Drone,
    distance_travelled_m: float,
) -> None:

    if distance_travelled_m < 0:

        raise ValueError(
            "distance_travelled_m "
            "cannot be negative"
        )

    # =====================================================
    # RF
    #
    # An RF-controlled drone has no optic-fiber spool.
    # Distance travelled has no effect on fiber state.
    # =====================================================

    if drone.communication_mode == "RF":
        return None

    # =====================================================
    # FIBER
    #
    # A fiber-controlled drone must have a physical spool.
    # =====================================================

    if drone.communication_mode == "FIBER":

        if (
            drone.optic_fiber_remaining_m
            is None
        ):

            raise ValueError(
                "FIBER drone requires "
                "optic_fiber_remaining_m"
            )

    # =====================================================
    # Legacy v1.0 / v1.1 compatibility
    #
    # communication_mode=None means the old contract.
    # If fiber exists, preserve historical behavior.
    # If it does not exist, there is nothing to consume.
    # =====================================================

    elif drone.communication_mode is None:

        if (
            drone.optic_fiber_remaining_m
            is None
        ):

            return

    else:

        raise ValueError(
            "communication_mode must be "
            "RF, FIBER or None for legacy"
        )

    drone.optic_fiber_remaining_m = max(
        0.0,
        (
            drone.optic_fiber_remaining_m
            - float(
                distance_travelled_m
            )
        ),
    )

    return drone.optic_fiber_remaining_m
