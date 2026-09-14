from dataclasses import dataclass
from datetime import datetime


# =========================================================
# Time helpers
# =========================================================

def parse_event_time(
    value: str,
) -> datetime:

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


# =========================================================
# Observed analytical state
# =========================================================

@dataclass
class ObservedDroneState:

    drone_id: str | None = None
    battalion_id: str | None = None
    mission_id: str | None = None

    # -----------------------------------------------------
    # Last observed position
    # -----------------------------------------------------

    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None

    # -----------------------------------------------------
    # Last observed movement
    # -----------------------------------------------------

    ground_speed_mps: float | None = None
    vertical_speed_mps: float | None = None
    heading_deg: float | None = None

    # -----------------------------------------------------
    # Last observed power / health / communications
    # -----------------------------------------------------

    battery_pct: float | None = None

    platform_health: str | None = None
    connection_state: str | None = None

    # -----------------------------------------------------
    # Operational state
    # -----------------------------------------------------

    asset_state: str | None = None
    mission_status: str | None = None
    mission_phase: str | None = None

    # -----------------------------------------------------
    # Observation metadata
    # -----------------------------------------------------

    last_telemetry_time: str | None = None
    latest_event_time: str | None = None

    latest_sequence_number: int = 0

    # -----------------------------------------------------
    # Derived properties
    # -----------------------------------------------------

    @property
    def has_position(self) -> bool:

        return (
            self.latitude is not None
            and self.longitude is not None
        )

    @property
    def position_age_seconds(
        self,
    ) -> float | None:

        if (
            self.last_telemetry_time is None
            or self.latest_event_time is None
        ):
            return None

        telemetry_time = parse_event_time(
            self.last_telemetry_time
        )

        latest_time = parse_event_time(
            self.latest_event_time
        )

        return (
            latest_time
            - telemetry_time
        ).total_seconds()


# =========================================================
# State projector
# =========================================================

class ObservedStateProjector:

    def project(
        self,
        events: list[dict],
    ) -> ObservedDroneState:

        state = ObservedDroneState()

        # -------------------------------------------------
        # Reconstruct source order.
        #
        # Physical arrival order may be dirty because of:
        # delay / duplicate / out-of-order delivery.
        # -------------------------------------------------

        ordered_events = sorted(
            events,
            key=lambda event: (
                event[
                    "source_sequence_number"
                ]
            ),
        )

        for event in ordered_events:

            state.drone_id = event[
                "drone_id"
            ]

            state.battalion_id = event[
                "battalion_id"
            ]

            state.mission_id = event[
                "mission_id"
            ]

            state.latest_event_time = (
                event["event_time"]
            )

            state.latest_sequence_number = (
                event[
                    "source_sequence_number"
                ]
            )

            event_type = event[
                "event_type"
            ]

            if event_type == "telemetry":

                self._apply_telemetry(
                    state,
                    event,
                )

            elif (
                event_type
                == "state_transition"
            ):

                self._apply_state_transition(
                    state,
                    event,
                )

        return state

    # =====================================================
    # Telemetry projection
    # =====================================================

    @staticmethod
    def _apply_telemetry(
        state: ObservedDroneState,
        event: dict,
    ) -> None:

        payload = event["payload"]

        position = payload[
            "position"
        ]

        movement = payload[
            "movement"
        ]

        power = payload[
            "power"
        ]

        health = payload[
            "health"
        ]

        communications = payload[
            "communications"
        ]

        operations = payload[
            "operations"
        ]

        # -------------------------------------------------
        # Position
        # -------------------------------------------------

        state.latitude = position[
            "latitude"
        ]

        state.longitude = position[
            "longitude"
        ]

        state.altitude_m = position[
            "altitude_m"
        ]

        # -------------------------------------------------
        # Movement
        # -------------------------------------------------

        state.ground_speed_mps = (
            movement[
                "ground_speed_mps"
            ]
        )

        state.vertical_speed_mps = (
            movement[
                "vertical_speed_mps"
            ]
        )

        state.heading_deg = movement[
            "heading_deg"
        ]

        # -------------------------------------------------
        # Power
        # -------------------------------------------------

        state.battery_pct = power[
            "battery_pct"
        ]

        # -------------------------------------------------
        # Health
        # -------------------------------------------------

        state.platform_health = (
            health[
                "platform_health"
            ]
        )

        # -------------------------------------------------
        # Communications
        # -------------------------------------------------

        state.connection_state = (
            communications[
                "connection_state"
            ]
        )

        # -------------------------------------------------
        # Operations
        # -------------------------------------------------

        state.asset_state = (
            operations[
                "asset_state"
            ]
        )

        state.mission_status = (
            operations[
                "mission_status"
            ]
        )

        state.mission_phase = (
            operations[
                "mission_phase"
            ]
        )

        # -------------------------------------------------
        # Observation metadata
        # -------------------------------------------------

        state.last_telemetry_time = (
            event["event_time"]
        )

    # =====================================================
    # State-transition projection
    # =====================================================

    @staticmethod
    def _apply_state_transition(
        state: ObservedDroneState,
        event: dict,
    ) -> None:

        payload = event[
            "payload"
        ]

        state_domain = payload[
            "state_domain"
        ]

        new_state = payload[
            "new_state"
        ]

        # Currently our state_transition events
        # operate on mission_phase.
        #
        # More state domains will be added later:
        # asset_state
        # connection_state
        # platform_health
        # etc.
        if (
            state_domain
            == "mission_phase"
        ):

            state.mission_phase = (
                new_state
            )


# =========================================================
# RAW ARRIVAL TRACK
#
# Preserves physical delivery order exactly as events.jsonl
# contains it.
#
# Therefore:
# - duplicates remain
# - missing events remain missing
# - out-of-order events remain out of order
# =========================================================

def build_raw_arrival_track(
    events: list[dict],
) -> list[list[float]]:

    points = []

    for event in events:

        if (
            event["event_type"]
            != "telemetry"
        ):
            continue

        position = event[
            "payload"
        ][
            "position"
        ]

        points.append(
            [
                position[
                    "longitude"
                ],
                position[
                    "latitude"
                ],
            ]
        )

    return points


# =========================================================
# RECONSTRUCTED TRACK
#
# Uses only observed facts, but:
#
# - deduplicates by event_id
# - reorders by source_sequence_number
# - does NOT fabricate dropped events
#
# Important rule:
#
# Reconstruction may reorder and deduplicate observed facts,
# but must not fabricate missing facts.
# =========================================================

def build_reconstructed_track(
    events: list[dict],
) -> list[list[float]]:

    # -----------------------------------------------------
    # Telemetry only
    # -----------------------------------------------------

    telemetry_events = [
        event
        for event in events
        if event["event_type"]
        == "telemetry"
    ]

    # -----------------------------------------------------
    # Deduplicate logical events.
    #
    # First physical arrival wins.
    # -----------------------------------------------------

    unique_by_event_id: dict[
        str,
        dict,
    ] = {}

    for event in telemetry_events:

        event_id = event[
            "event_id"
        ]

        if (
            event_id
            not in unique_by_event_id
        ):

            unique_by_event_id[
                event_id
            ] = event

    # -----------------------------------------------------
    # Restore source generation order.
    # -----------------------------------------------------

    ordered_events = sorted(
        unique_by_event_id.values(),
        key=lambda event: (
            event[
                "source_sequence_number"
            ]
        ),
    )

    # -----------------------------------------------------
    # Build geographic path.
    # -----------------------------------------------------

    points = []

    for event in ordered_events:

        position = event[
            "payload"
        ][
            "position"
        ]

        points.append(
            [
                position[
                    "longitude"
                ],
                position[
                    "latitude"
                ],
            ]
        )

    return points