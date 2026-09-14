from simulator.domain.drone import Drone


def update_battery(
    *,
    drone: Drone,
    drain_pct_per_minute: float,
    dt_seconds: float,
    mission_active: bool,
) -> float:

    if drain_pct_per_minute < 0:

        raise ValueError(
            "drain_pct_per_minute "
            "cannot be negative"
        )

    if dt_seconds < 0:

        raise ValueError(
            "dt_seconds cannot be negative"
        )

    if not mission_active:

        return drone.battery_pct

    drain_amount = (
        drain_pct_per_minute
        * (
            dt_seconds
            / 60.0
        )
    )

    drone.battery_pct = max(
        0.0,
        drone.battery_pct
        - drain_amount,
    )

    return drone.battery_pct
