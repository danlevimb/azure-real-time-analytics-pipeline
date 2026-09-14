from collections import defaultdict

from simulator.observation.stream_projector import (
    ObservedDroneState,
    ObservedStateProjector,
    build_raw_arrival_track,
    build_reconstructed_track,
)


# =========================================================
# Group events by logical producer
# =========================================================

def group_events_by_drone(
    events: list[dict],
) -> dict[str, list[dict]]:

    grouped = defaultdict(
        list
    )

    for event in events:

        grouped[
            event["drone_id"]
        ].append(
            event
        )

    return {
        drone_id: grouped[
            drone_id
        ]

        for drone_id
        in sorted(grouped)
    }


# =========================================================
# Fleet current-state projection
#
# Each drone is reconstructed independently.
# =========================================================

def project_fleet(
    events: list[dict],
) -> dict[
    str,
    ObservedDroneState,
]:

    grouped = group_events_by_drone(
        events
    )

    projector = (
        ObservedStateProjector()
    )

    states = {}

    for (
        drone_id,
        drone_events,
    ) in grouped.items():

        states[
            drone_id
        ] = projector.project(
            drone_events
        )

    return states


# =========================================================
# Raw arrival tracks by drone
# =========================================================

def build_fleet_raw_tracks(
    events: list[dict],
) -> dict[
    str,
    list[list[float]],
]:

    grouped = group_events_by_drone(
        events
    )

    return {
        drone_id:
        build_raw_arrival_track(
            drone_events
        )

        for (
            drone_id,
            drone_events,
        ) in grouped.items()
    }


# =========================================================
# Reconstructed tracks by drone
#
# Deduplication and sequence ordering are performed
# independently inside every drone stream.
# =========================================================

def build_fleet_reconstructed_tracks(
    events: list[dict],
) -> dict[
    str,
    list[list[float]],
]:

    grouped = group_events_by_drone(
        events
    )

    return {
        drone_id:
        build_reconstructed_track(
            drone_events
        )

        for (
            drone_id,
            drone_events,
        ) in grouped.items()
    }