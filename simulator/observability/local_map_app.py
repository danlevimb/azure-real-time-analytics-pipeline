import json
from pathlib import Path

import pydeck as pdk
import streamlit as st
import yaml


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
    config = yaml.safe_load(file)


simulation_context = config[
    "simulation_context"
]

run_id = simulation_context[
    "simulator_run_id"
]

initial_position = config[
    "drone"
]["initial_position"]


GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "output"
    / run_id
    / "ground_truth.jsonl"
)


# =========================================================
# Helpers
# =========================================================

def read_ground_truth(
    path: Path,
) -> list[dict]:

    if not path.exists():
        return []

    records: list[dict] = []

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
                # The simulator could theoretically
                # be writing the final line while
                # Streamlit is reading the file.
                # Ignore an incomplete record and
                # pick it up on the next refresh.
                continue

    return records


def build_track(
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
    page_title="DRN-001 Ground Truth",
    layout="wide",
)

st.title(
    "DRN-001 — Local Ground Truth Map"
)

st.caption(
    "Simulator truth — not stream observation"
)


# =========================================================
# Live fragment
# =========================================================

@st.fragment(run_every=0.5)
def render_live_map() -> None:

    records = read_ground_truth(
        GROUND_TRUTH_PATH
    )

    if not records:

        st.info(
            "Waiting for ground-truth data. "
            "Start the simulator in another terminal."
        )

        return

    latest = records[-1]

    position = latest["position"]
    movement = latest["movement"]
    states = latest["states"]

    latitude = position[
        "latitude"
    ]

    longitude = position[
        "longitude"
    ]

    altitude = position[
        "altitude_m"
    ]

    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    col1.metric(
        "Simulation time",
        f"T+{latest['elapsed_seconds']:.2f}s",
    )

    col2.metric(
        "Mission phase",
        states["mission_phase"],
    )

    col3.metric(
        "Altitude",
        f"{altitude:.1f} m",
    )

    col4.metric(
        "Ground speed",
        (
            f"{movement['ground_speed_mps']:.1f} "
            "m/s"
        ),
    )

    # -----------------------------------------------------
    # Track
    # -----------------------------------------------------

    track = build_track(
        records
    )

    path_data = [
        {
            "path": track,
        }
    ]

    current_drone = [
        {
            "longitude": longitude,
            "latitude": latitude,
            "drone_id": (
                latest["drone_id"]
            ),
            "phase": (
                states["mission_phase"]
            ),
            "altitude_m": altitude,
            "heading_deg": (
                movement["heading_deg"]
            ),
            "elapsed_seconds": (
                latest["elapsed_seconds"]
            ),
        }
    ]

    base = [
        {
            "longitude": (
                initial_position["longitude"]
            ),
            "latitude": (
                initial_position["latitude"]
            ),
            "name": "BASE-A",
        }
    ]

    layers = []

    # Full ground-truth track.
    if len(track) >= 2:

        layers.append(
            pdk.Layer(
                "PathLayer",
                data=path_data,
                get_path="path",
                get_color=[
                    40,
                    180,
                    255,
                ],
                get_width=4,
                width_min_pixels=2,
                pickable=False,
            )
        )

    # Base.
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=base,
            get_position=(
                "[longitude, latitude]"
            ),
            get_fill_color=[
                255,
                170,
                40,
            ],
            get_radius=10,
            radius_min_pixels=5,
            pickable=True,
        )
    )

    # Current DRN-001 position.
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=current_drone,
            get_position=(
                "[longitude, latitude]"
            ),
            get_fill_color=[
                0,
                255,
                180,
            ],
            get_radius=12,
            radius_min_pixels=8,
            pickable=True,
        )
    )

    # -----------------------------------------------------
    # Map
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
                "Altitude: {altitude_m} m<br/>"
                "Heading: {heading_deg}°<br/>"
                "T+{elapsed_seconds}s"
            )
        },
    )

    st.pydeck_chart(
        deck,
        height=650,
        use_container_width=True,
    )

    st.caption(
        f"Ground-truth records loaded: "
        f"{len(records)}"
    )


render_live_map()