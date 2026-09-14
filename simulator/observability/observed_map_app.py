import json
from pathlib import Path

import pydeck as pdk
import streamlit as st
import yaml

from simulator.observation.stream_projector import (
    ObservedStateProjector,
    build_raw_arrival_track,
    build_reconstructed_track,
)


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

CONFIG_PATH = (
    PROJECT_ROOT
    / "simulator"
    / "configs"
    / "drn001.yaml"
)


# =========================================================
# Configuration
# =========================================================

with CONFIG_PATH.open(
    "r",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )


run_id = config[
    "simulation_context"
][
    "simulator_run_id"
]

initial_position = config[
    "drone"
][
    "initial_position"
]


EVENTS_PATH = (
    PROJECT_ROOT
    / "output"
    / run_id
    / "events.jsonl"
)


# =========================================================
# Helpers
# =========================================================

def read_events(
    path: Path,
) -> list[dict]:

    if not path.exists():
        return []

    events = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:

                events.append(
                    json.loads(line)
                )

            except json.JSONDecodeError:

                # Simulator may currently be
                # writing the final line.
                continue

    return events


# =========================================================
# Page
# =========================================================

st.set_page_config(
    page_title=(
        "DRN-001 Observed Stream"
    ),
    layout="wide",
)

st.title(
    "DRN-001 — Observed Stream Map"
)

st.caption(
    "Physical arrival vs reconstructed "
    "event order"
)


# =========================================================
# Controls
# =========================================================

st.sidebar.header(
    "Path Layers"
)

show_raw_path = st.sidebar.checkbox(
    "Raw arrival path",
    value=True,
)

show_reconstructed_path = (
    st.sidebar.checkbox(
        "Reconstructed path",
        value=True,
    )
)

show_current_position = (
    st.sidebar.checkbox(
        "Current observed position",
        value=True,
    )
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Raw = physical arrival order"
)

st.sidebar.caption(
    "Reconstructed = deduplicated "
    "+ source sequence order"
)


# =========================================================
# Live map
# =========================================================

@st.fragment(
    run_every=0.5
)
def render_observed_map() -> None:

    events = read_events(
        EVENTS_PATH
    )

    if not events:

        st.info(
            "Waiting for stream events. "
            "Start the simulator "
            "in another terminal."
        )

        return

    # -----------------------------------------------------
    # Current analytical state
    # -----------------------------------------------------

    projector = (
        ObservedStateProjector()
    )

    state = projector.project(
        events
    )

    if not state.has_position:

        st.info(
            "Events received, but no "
            "telemetry position is "
            "available yet."
        )

        return

    # -----------------------------------------------------
    # Tracks
    # -----------------------------------------------------

    raw_track = (
        build_raw_arrival_track(
            events
        )
    )

    reconstructed_track = (
        build_reconstructed_track(
            events
        )
    )

    telemetry_events = [
        event
        for event in events
        if event["event_type"]
        == "telemetry"
    ]

    transition_count = sum(
        1
        for event in events
        if event["event_type"]
        == "state_transition"
    )

    telemetry_event_ids = [
        event["event_id"]
        for event in telemetry_events
    ]

    unique_telemetry_count = len(
        set(
            telemetry_event_ids
        )
    )

    physical_telemetry_count = len(
        telemetry_events
    )

    duplicate_telemetry_count = (
        physical_telemetry_count
        - unique_telemetry_count
    )

    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    col1.metric(
        "Events observed",
        len(events),
    )

    col2.metric(
        "Mission phase",
        state.mission_phase
        or "UNKNOWN",
    )

    col3.metric(
        "Last altitude",
        (
            f"{state.altitude_m:.1f} m"
            if state.altitude_m
            is not None
            else "UNKNOWN"
        ),
    )

    age = (
        state.position_age_seconds
    )

    col4.metric(
        "Position age",
        (
            f"{age:.2f} s"
            if age is not None
            else "UNKNOWN"
        ),
    )

    # -----------------------------------------------------
    # Stream metrics
    # -----------------------------------------------------

    scol1, scol2, scol3 = (
        st.columns(3)
    )

    scol1.metric(
        "Physical telemetry",
        physical_telemetry_count,
    )

    scol2.metric(
        "Unique telemetry",
        unique_telemetry_count,
    )

    scol3.metric(
        "Duplicate telemetry",
        duplicate_telemetry_count,
    )

    # -----------------------------------------------------
    # Map layers
    # -----------------------------------------------------

    layers = []

    # -----------------------------------------------------
    # RAW ARRIVAL PATH
    #
    # Preserves physical file / delivery order.
    # -----------------------------------------------------

    if (
        show_raw_path
        and len(raw_track) >= 2
    ):

        layers.append(
            pdk.Layer(
                "PathLayer",
                data=[
                    {
                        "path": raw_track,
                    }
                ],
                get_path="path",

                # Arrival path.
                get_color=[
                    255,
                    170,
                    40,
                ],

                get_width=5,
                width_min_pixels=3,
                pickable=False,
            )
        )

    # -----------------------------------------------------
    # RECONSTRUCTED PATH
    #
    # Deduped + sorted by source sequence.
    # -----------------------------------------------------

    if (
        show_reconstructed_path
        and
        len(
            reconstructed_track
        ) >= 2
    ):

        layers.append(
            pdk.Layer(
                "PathLayer",
                data=[
                    {
                        "path": (
                            reconstructed_track
                        ),
                    }
                ],
                get_path="path",

                get_color=[
                    80,
                    210,
                    255,
                ],

                get_width=3,
                width_min_pixels=2,
                pickable=False,
            )
        )

    # -----------------------------------------------------
    # BASE
    # -----------------------------------------------------

    base = [
        {
            "longitude": (
                initial_position[
                    "longitude"
                ]
            ),
            "latitude": (
                initial_position[
                    "latitude"
                ]
            ),
            "name": "BASE-A",
        }
    ]

    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=base,
            get_position=(
                "[longitude, latitude]"
            ),
            get_fill_color=[
                255,
                255,
                255,
            ],
            get_radius=10,
            radius_min_pixels=5,
            pickable=True,
        )
    )

    # -----------------------------------------------------
    # CURRENT OBSERVED POSITION
    # -----------------------------------------------------

    if show_current_position:

        observed_drone = [
            {
                "longitude": (
                    state.longitude
                ),
                "latitude": (
                    state.latitude
                ),
                "drone_id": (
                    state.drone_id
                ),
                "phase": (
                    state.mission_phase
                ),
                "altitude_m": (
                    state.altitude_m
                ),
                "heading_deg": (
                    state.heading_deg
                ),
                "sequence": (
                    state.latest_sequence_number
                ),
                "position_age": age,
            }
        ]

        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=observed_drone,
                get_position=(
                    "[longitude, latitude]"
                ),
                get_fill_color=[
                    255,
                    80,
                    120,
                ],
                get_radius=12,
                radius_min_pixels=8,
                pickable=True,
            )
        )

    # -----------------------------------------------------
    # Deck
    # -----------------------------------------------------

    deck = pdk.Deck(
        map_style=None,

        initial_view_state=(
            pdk.ViewState(
                latitude=(
                    initial_position[
                        "latitude"
                    ]
                ),
                longitude=(
                    initial_position[
                        "longitude"
                    ]
                ),
                zoom=13.5,
                pitch=35,
                bearing=0,
            )
        ),

        layers=layers,

        tooltip={
            "html": (
                "<b>{drone_id}</b><br/>"
                "Phase: {phase}<br/>"
                "Last altitude: "
                "{altitude_m} m<br/>"
                "Latest sequence: "
                "{sequence}<br/>"
                "Position age: "
                "{position_age} s"
            )
        },
    )

    st.pydeck_chart(
        deck,
        height=650,
        use_container_width=True,
    )

    # -----------------------------------------------------
    # Legend / explanation
    # -----------------------------------------------------

    st.markdown(
        """
**Path interpretation**

- 🟠 **Raw arrival:** physical delivery order.
- 🔵 **Reconstructed:** deduplicated and ordered by `source_sequence_number`.
- 🔴 **Marker:** latest analytically reconstructed state.
"""
    )

    st.caption(
        f"Telemetry physical="
        f"{physical_telemetry_count} | "
        f"telemetry unique="
        f"{unique_telemetry_count} | "
        f"transitions="
        f"{transition_count} | "
        f"latest seq="
        f"{state.latest_sequence_number}"
    )


render_observed_map()