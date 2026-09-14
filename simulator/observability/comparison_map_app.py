import json
import sys
from pathlib import Path


# =========================================================
# Project root / Python path
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# =========================================================
# Third-party imports
# =========================================================

import pydeck as pdk
import streamlit as st
import yaml


# =========================================================
# Project imports
# =========================================================

from simulator.observation.stream_projector import (
    ObservedStateProjector,
    build_raw_arrival_track,
    build_reconstructed_track,
)

from simulator.simulation.geodesy import (
    haversine_distance_m,
)


# =========================================================
# Paths / configuration
# =========================================================

CONFIG_PATH = (
    PROJECT_ROOT
    / "simulator"
    / "configs"
    / "drn001.yaml"
)


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


RUN_PATH = (
    PROJECT_ROOT
    / "output"
    / run_id
)


GROUND_TRUTH_PATH = (
    RUN_PATH
    / "ground_truth.jsonl"
)


EVENTS_PATH = (
    RUN_PATH
    / "events.jsonl"
)


# =========================================================
# Generic JSONL reader
# =========================================================

def read_jsonl(
    path: Path,
) -> list[dict]:

    if not path.exists():
        return []

    records = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:

                records.append(
                    json.loads(line)
                )

            except json.JSONDecodeError:

                # Simulator may currently be
                # writing the last line.
                continue

    return records


# =========================================================
# Ground-truth path
# =========================================================

def build_ground_truth_track(
    records: list[dict],
) -> list[list[float]]:

    return [
        [
            record["position"][
                "longitude"
            ],
            record["position"][
                "latitude"
            ],
        ]
        for record in records
    ]


# =========================================================
# Page
# =========================================================

st.set_page_config(
    page_title=(
        "DRN-001 Streaming Control Room"
    ),
    layout="wide",
)


st.title(
    "DRN-001 — Streaming Control Room"
)


st.caption(
    "Ground Truth vs Raw Arrival "
    "vs Reconstructed Stream"
)


# =========================================================
# Sidebar
# =========================================================

st.sidebar.header(
    "Layers"
)


show_truth = st.sidebar.checkbox(
    "Ground Truth",
    value=True,
)


show_raw = st.sidebar.checkbox(
    "Raw Arrival",
    value=True,
)


show_reconstructed = (
    st.sidebar.checkbox(
        "Reconstructed Stream",
        value=True,
    )
)


show_truth_marker = (
    st.sidebar.checkbox(
        "Truth Position",
        value=True,
    )
)


show_observed_marker = (
    st.sidebar.checkbox(
        "Observed Position",
        value=True,
    )
)


st.sidebar.markdown("---")


st.sidebar.caption(
    "Ground Truth = simulator reality"
)


st.sidebar.caption(
    "Raw Arrival = physical event order"
)


st.sidebar.caption(
    "Reconstructed = deduplicated "
    "+ reordered observations"
)


# =========================================================
# Live control room
# =========================================================

@st.fragment(
    run_every=0.5
)
def render_control_room() -> None:

    truth_records = read_jsonl(
        GROUND_TRUTH_PATH
    )

    events = read_jsonl(
        EVENTS_PATH
    )


    if not truth_records:

        st.info(
            "Waiting for Ground Truth. "
            "Start simulator.main."
        )

        return


    if not events:

        st.warning(
            "Ground Truth exists, but "
            "no stream events have "
            "been delivered yet."
        )

        return


    # =====================================================
    # Latest Ground Truth
    # =====================================================

    latest_truth = (
        truth_records[-1]
    )


    truth_position = (
        latest_truth["position"]
    )


    truth_states = (
        latest_truth["states"]
    )


    # =====================================================
    # Observed analytical state
    # =====================================================

    projector = (
        ObservedStateProjector()
    )


    observed = projector.project(
        events
    )


    if not observed.has_position:

        st.warning(
            "Stream events exist, but "
            "no telemetry position "
            "has been received yet."
        )

        return


    # =====================================================
    # Tracks
    # =====================================================

    truth_track = (
        build_ground_truth_track(
            truth_records
        )
    )


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


    # =====================================================
    # Physical separation
    # =====================================================

    position_error_m = (
        haversine_distance_m(
            truth_position[
                "latitude"
            ],
            truth_position[
                "longitude"
            ],
            observed.latitude,
            observed.longitude,
        )
    )


    # =====================================================
    # Stream metrics
    # =====================================================

    telemetry_events = [
        event
        for event in events
        if event["event_type"]
        == "telemetry"
    ]


    transition_events = [
        event
        for event in events
        if event["event_type"]
        == "state_transition"
    ]


    telemetry_ids = [
        event["event_id"]
        for event in telemetry_events
    ]


    duplicate_count = (
        len(telemetry_ids)
        - len(set(telemetry_ids))
    )


    # =====================================================
    # Top metrics
    # =====================================================

    col1, col2, col3, col4 = (
        st.columns(4)
    )


    col1.metric(
        "Simulation Time",
        (
            f"T+"
            f"{latest_truth['elapsed_seconds']:.2f}s"
        ),
    )


    col2.metric(
        "Truth Phase",
        truth_states[
            "mission_phase"
        ],
    )


    col3.metric(
        "Observed Phase",
        observed.mission_phase
        or "UNKNOWN",
    )


    col4.metric(
        "Position Separation",
        f"{position_error_m:.1f} m",
    )


    # =====================================================
    # Secondary metrics
    # =====================================================

    row2_col1, row2_col2, row2_col3, row2_col4 = (
        st.columns(4)
    )


    row2_col1.metric(
        "Truth Altitude",
        (
            f"{truth_position['altitude_m']:.1f} m"
        ),
    )


    row2_col2.metric(
        "Last Observed Altitude",
        (
            f"{observed.altitude_m:.1f} m"
            if observed.altitude_m
            is not None
            else "UNKNOWN"
        ),
    )


    row2_col3.metric(
        "Physical Events",
        len(events),
    )


    row2_col4.metric(
        "Duplicate Telemetry",
        duplicate_count,
    )


    # =====================================================
    # Map layers
    # =====================================================

    layers = []


    # -----------------------------------------------------
    # Ground Truth
    # -----------------------------------------------------

    if (
        show_truth
        and len(truth_track) >= 2
    ):

        layers.append(
            pdk.Layer(
                "PathLayer",

                data=[
                    {
                        "path": (
                            truth_track
                        ),
                    }
                ],

                get_path="path",

                get_color=[
                    80,
                    230,
                    120,
                ],

                get_width=6,

                width_min_pixels=4,

                pickable=False,
            )
        )


    # -----------------------------------------------------
    # Raw Arrival
    # -----------------------------------------------------

    if (
        show_raw
        and len(raw_track) >= 2
    ):

        layers.append(
            pdk.Layer(
                "PathLayer",

                data=[
                    {
                        "path": (
                            raw_track
                        ),
                    }
                ],

                get_path="path",

                get_color=[
                    255,
                    160,
                    40,
                ],

                get_width=5,

                width_min_pixels=3,

                pickable=False,
            )
        )


    # -----------------------------------------------------
    # Reconstructed
    # -----------------------------------------------------

    if (
        show_reconstructed
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
                    70,
                    190,
                    255,
                ],

                get_width=3,

                width_min_pixels=2,

                pickable=False,
            )
        )


    # =====================================================
    # Base
    # =====================================================

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


    # =====================================================
    # Truth marker
    # =====================================================

    if show_truth_marker:

        truth_drone = [
            {
                "longitude": (
                    truth_position[
                        "longitude"
                    ]
                ),

                "latitude": (
                    truth_position[
                        "latitude"
                    ]
                ),

                "drone_id": (
                    latest_truth[
                        "drone_id"
                    ]
                ),

                "state_type": (
                    "GROUND TRUTH"
                ),

                "phase": (
                    truth_states[
                        "mission_phase"
                    ]
                ),

                "altitude_m": (
                    truth_position[
                        "altitude_m"
                    ]
                ),
            }
        ]


        layers.append(
            pdk.Layer(
                "ScatterplotLayer",

                data=truth_drone,

                get_position=(
                    "[longitude, latitude]"
                ),

                get_fill_color=[
                    0,
                    255,
                    120,
                ],

                get_radius=14,

                radius_min_pixels=9,

                pickable=True,
            )
        )


    # =====================================================
    # Observed marker
    # =====================================================

    if show_observed_marker:

        observed_drone = [
            {
                "longitude": (
                    observed.longitude
                ),

                "latitude": (
                    observed.latitude
                ),

                "drone_id": (
                    observed.drone_id
                ),

                "state_type": (
                    "OBSERVED"
                ),

                "phase": (
                    observed.mission_phase
                ),

                "altitude_m": (
                    observed.altitude_m
                ),

                "sequence": (
                    observed.latest_sequence_number
                ),
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
                    60,
                    120,
                ],

                get_radius=11,

                radius_min_pixels=7,

                pickable=True,
            )
        )


    # =====================================================
    # Deck
    # =====================================================

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
                "{state_type}<br/>"
                "Phase: {phase}<br/>"
                "Altitude: "
                "{altitude_m} m<br/>"
                "Sequence: {sequence}"
            )
        },
    )


    st.pydeck_chart(
        deck,
        height=650,
        use_container_width=True,
    )


    # =====================================================
    # Legend
    # =====================================================

    st.markdown(
        """
### Layer interpretation

- 🟢 **Ground Truth** — what actually happened inside the simulator.
- 🟠 **Raw Arrival** — telemetry in physical delivery order.
- 🔵 **Reconstructed** — observed telemetry after deduplication and source-order reconstruction.
- 🟢 **Large marker** — actual simulator position.
- 🔴 **Marker** — latest position known to the stream consumer.
"""
    )


    st.caption(
        f"Truth records="
        f"{len(truth_records)} | "
        f"Telemetry deliveries="
        f"{len(telemetry_events)} | "
        f"Transitions="
        f"{len(transition_events)} | "
        f"Latest observed seq="
        f"{observed.latest_sequence_number}"
    )


render_control_room()