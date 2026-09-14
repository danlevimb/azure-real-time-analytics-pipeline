import argparse
import json
import sys

import pandas as pd
import pydeck as pdk
import streamlit as st
import yaml

from collections import defaultdict
from pathlib import Path


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


from simulator.observation.fleet_stream_projector import (
    build_fleet_raw_tracks,
    build_fleet_reconstructed_tracks,
    project_fleet,
)

from simulator.observation.live_fleet_health import (
    LiveFleetHealthAnalyzer,
)

from simulator.observation.health_timeline import (
    FleetHealthTimelineBuilder,
)

from simulator.simulation.geodesy import (
    haversine_distance_m,
)


# =========================================================
# Configuration
# =========================================================

def parse_app_args():

    parser = argparse.ArgumentParser(
        add_help=False
    )

    parser.add_argument(
        "--config",
        default="fleet005.yaml",
    )

    args, _ = (
        parser.parse_known_args()
    )

    return args


app_args = parse_app_args()


CONFIG_PATH = (
    PROJECT_ROOT
    / "simulator"
    / "configs"
    / app_args.config
)


with CONFIG_PATH.open(
    "r",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )


simulation_config = config[
    "simulation"
]


telemetry_config = config[
    "telemetry"
]


transport_config = config[
    "transport"
]


run_id = config[
    "simulation_context"
][
    "simulator_run_id"
]


scenario = config[
    "simulation_context"
][
    "scenario"
]


fleet_id = config[
    "fleet"
][
    "fleet_id"
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


TRUTH_PATH = (
    RUN_PATH
    / "ground_truth.jsonl"
)


EVENTS_PATH = (
    RUN_PATH
    / "events.jsonl"
)


GENERATED_EVENTS_PATH = (
    RUN_PATH
    / "generated_events.jsonl"
)


DELIVERY_LOG_PATH = (
    RUN_PATH
    / "delivery_log.jsonl"
)


# =========================================================
# JSONL reader
#
# Live behavior:
# tolerate an incomplete final line while simulator writes.
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
                    json.loads(
                        line
                    )
                )

            except json.JSONDecodeError:

                continue

    return records


# =========================================================
# Ground Truth helpers
# =========================================================

def group_truth_by_drone(
    truth_records: list[dict],
) -> dict[
    str,
    list[dict],
]:

    grouped = defaultdict(
        list
    )

    for record in truth_records:

        grouped[
            record[
                "drone_id"
            ]
        ].append(
            record
        )

    return {
        drone_id:
        grouped[
            drone_id
        ]

        for drone_id
        in sorted(
            grouped
        )
    }


def build_truth_tracks(
    truth_records: list[dict],
) -> dict[
    str,
    list[list[float]],
]:

    grouped = (
        group_truth_by_drone(
            truth_records
        )
    )

    tracks = {}

    for (
        drone_id,
        records,
    ) in grouped.items():

        tracks[
            drone_id
        ] = [
            [
                record[
                    "position"
                ][
                    "longitude"
                ],

                record[
                    "position"
                ][
                    "latitude"
                ],
            ]

            for record
            in records
        ]

    return tracks


def health_display(
    status: str,
) -> str:

    labels = {
        "STARTING":
            "⚪ STARTING",

        "HEALTHY":
            "🟢 HEALTHY",

        "BUFFERING":
            "🟠 BUFFERING",

        "STALE":
            "🔴 STALE",

        "RECOVERING":
            "🟣 RECOVERING",
    }

    return labels.get(
        status,
        status,
    )


# =========================================================
# Page
# =========================================================

st.set_page_config(
    page_title=(
        f"{fleet_id} Streaming "
        f"Control Room"
    ),

    layout="wide",
)


st.title(
    f"{fleet_id} — "
    f"Streaming Control Room"
)


st.caption(
    "Fleet motion, observed state and "
    "stream-health telemetry in one "
    "local real-time laboratory."
)


# =========================================================
# Sidebar
# =========================================================

st.sidebar.header(
    "Run"
)


st.sidebar.caption(
    f"Config: {app_args.config}"
)


st.sidebar.caption(
    f"Run ID: {run_id}"
)


st.sidebar.caption(
    f"Scenario: {scenario}"
)


st.sidebar.markdown(
    "---"
)


st.sidebar.header(
    "Layers"
)


show_truth_tracks = (
    st.sidebar.checkbox(
        "Ground Truth Tracks",
        value=True,
    )
)


show_raw_tracks = (
    st.sidebar.checkbox(
        "Raw Arrival Tracks",
        value=False,
    )
)


show_reconstructed_tracks = (
    st.sidebar.checkbox(
        "Reconstructed Tracks",
        value=True,
    )
)


show_truth_positions = (
    st.sidebar.checkbox(
        "Truth Positions",
        value=True,
    )
)


show_observed_positions = (
    st.sidebar.checkbox(
        "Observed Positions",
        value=True,
    )
)


show_labels = (
    st.sidebar.checkbox(
        "Drone Labels",
        value=True,
    )
)


st.sidebar.markdown(
    "---"
)


st.sidebar.caption(
    "🟢 Ground Truth"
)


st.sidebar.caption(
    "🟠 Raw physical arrival"
)


st.sidebar.caption(
    "🔵 Reconstructed stream"
)


st.sidebar.caption(
    "🩷 Observed current position"
)


st.sidebar.markdown(
    "---"
)


fleet_drone_ids = [
    member[
        "drone_id"
    ]
    for member
    in config[
        "fleet"
    ][
        "members"
    ]
]


configured_buffer_targets = (
    transport_config.get(
        "buffering",
        {},
    ).get(
        "target_drone_ids",
        [],
    )
)


default_focus_drone = (
    configured_buffer_targets[
        0
    ]
    if (
        configured_buffer_targets
        and configured_buffer_targets[
            0
        ] in fleet_drone_ids
    )
    else fleet_drone_ids[
        0
    ]
)


focus_drone_id = (
    st.sidebar.selectbox(
        "Timeline Producer",
        options=(
            fleet_drone_ids
        ),
        index=(
            fleet_drone_ids.index(
                default_focus_drone
            )
        ),
    )
)


# =========================================================
# Live control room
# =========================================================

@st.fragment(
    run_every=0.5
)
def render_fleet() -> None:

    truth_records = (
        read_jsonl(
            TRUTH_PATH
        )
    )


    events = (
        read_jsonl(
            EVENTS_PATH
        )
    )


    generated_events = (
        read_jsonl(
            GENERATED_EVENTS_PATH
        )
    )


    delivery_records = (
        read_jsonl(
            DELIVERY_LOG_PATH
        )
    )


    if not truth_records:

        st.info(
            "Waiting for Fleet Ground Truth. "
            "Start simulator.fleet_main."
        )

        return


    # =====================================================
    # Live stream health
    #
    # Ground truth is used here only as the local simulation
    # clock. Health itself is derived from source-generated
    # events versus physically delivered observations.
    # =====================================================

    health_analyzer = (
        LiveFleetHealthAnalyzer(
            ground_truth_records=(
                truth_records
            ),

            generated_events=(
                generated_events
            ),

            delivery_records=(
                delivery_records
            ),

            simulation_start_time_utc=(
                simulation_config[
                    "start_time_utc"
                ]
            ),

            base_delay_ms=(
                transport_config[
                    "base_delay_ms"
                ]
            ),

            telemetry_interval_ms=(
                telemetry_config[
                    "interval_ms"
                ]
            ),

            tick_ms=(
                simulation_config[
                    "tick_ms"
                ]
            ),
        )
    )


    health = (
        health_analyzer.analyze()
    )


    producer_health = (
        health[
            "producers"
        ]
    )


    timeline_builder = (
        FleetHealthTimelineBuilder(
            ground_truth_records=(
                truth_records
            ),

            generated_events=(
                generated_events
            ),

            delivery_records=(
                delivery_records
            ),

            simulation_start_time_utc=(
                simulation_config[
                    "start_time_utc"
                ]
            ),

            base_delay_ms=(
                transport_config[
                    "base_delay_ms"
                ]
            ),

            telemetry_interval_ms=(
                telemetry_config[
                    "interval_ms"
                ]
            ),

            tick_ms=(
                simulation_config[
                    "tick_ms"
                ]
            ),

            sample_interval_seconds=0.5,
        )
    )


    health_timeline = (
        timeline_builder.build()
    )


    truth_grouped = (
        group_truth_by_drone(
            truth_records
        )
    )


    latest_truth = {
        drone_id:
        records[
            -1
        ]

        for (
            drone_id,
            records,
        ) in truth_grouped.items()

        if records
    }


    truth_tracks = (
        build_truth_tracks(
            truth_records
        )
    )


    observed_states = (
        project_fleet(
            events
        )
        if events
        else {}
    )


    raw_tracks = (
        build_fleet_raw_tracks(
            events
        )
        if events
        else {}
    )


    reconstructed_tracks = (
        build_fleet_reconstructed_tracks(
            events
        )
        if events
        else {}
    )


    # =====================================================
    # Simulation time
    # =====================================================

    latest_elapsed = max(
        record[
            "elapsed_seconds"
        ]

        for record
        in truth_records
    )


    truth_landed = sum(
        1

        for record
        in latest_truth.values()

        if (
            record[
                "states"
            ][
                "mission_phase"
            ]
            == "LANDED"
        )
    )


    observed_landed = sum(
        1

        for state
        in observed_states.values()

        if (
            state.mission_phase
            == "LANDED"
        )
    )


    # =====================================================
    # Position separation metrics
    # =====================================================

    separations = {}


    for (
        drone_id,
        observed,
    ) in observed_states.items():

        truth = (
            latest_truth.get(
                drone_id
            )
        )

        if (
            truth is None
            or not observed.has_position
        ):

            continue


        truth_position = (
            truth[
                "position"
            ]
        )


        separations[
            drone_id
        ] = (
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


    average_separation = (
        sum(
            separations.values()
        )
        / len(
            separations
        )

        if separations
        else 0.0
    )


    maximum_separation = (
        max(
            separations.values()
        )

        if separations
        else 0.0
    )


    # =====================================================
    # Fleet metrics
    # =====================================================

    (
        col1,
        col2,
        col3,
        col4,
        col5,
        col6,
    ) = st.columns(
        6
    )


    col1.metric(
        "Simulation Time",
        f"T+{latest_elapsed:.2f}s",
    )


    col2.metric(
        "Fleet Size",
        len(
            latest_truth
        ),
    )


    col3.metric(
        "Truth Landed",
        (
            f"{truth_landed}/"
            f"{len(latest_truth)}"
        ),
    )


    col4.metric(
        "Observed Landed",
        (
            f"{observed_landed}/"
            f"{len(latest_truth)}"
        ),
    )


    col5.metric(
        "Avg Separation",
        f"{average_separation:.1f} m",
    )


    col6.metric(
        "Max Separation",
        f"{maximum_separation:.1f} m",
    )


    st.caption(
        f"Physical events observed: "
        f"{len(events)}"
    )


    # =====================================================
    # Live Stream Health
    # =====================================================

    statuses = {
        producer[
            "status"
        ]
        for producer
        in producer_health.values()
    }


    stale_producers = sorted(
        drone_id
        for (
            drone_id,
            producer,
        ) in producer_health.items()
        if producer[
            "status"
        ]
        == "STALE"
    )


    buffering_producers = sorted(
        drone_id
        for (
            drone_id,
            producer,
        ) in producer_health.items()
        if producer[
            "status"
        ]
        == "BUFFERING"
    )


    recovering_producers = sorted(
        drone_id
        for (
            drone_id,
            producer,
        ) in producer_health.items()
        if producer[
            "status"
        ]
        == "RECOVERING"
    )


    if stale_producers:

        overall_stream_status = (
            "DEGRADED"
        )

    elif buffering_producers:

        overall_stream_status = (
            "DEGRADED"
        )

    elif recovering_producers:

        overall_stream_status = (
            "RECOVERING"
        )

    elif (
        statuses
        and
        statuses
        <= {
            "STARTING",
        }
    ):

        overall_stream_status = (
            "STARTING"
        )

    else:

        overall_stream_status = (
            "HEALTHY"
        )


    st.subheader(
        "Live Stream Health"
    )


    (
        health_col1,
        health_col2,
        health_col3,
        health_col4,
        health_col5,
        health_col6,
    ) = st.columns(
        6
    )


    health_col1.metric(
        "Stream Status",
        overall_stream_status,
    )


    health_col2.metric(
        "Affected Producers",
        (
            f"{health['affected_producers']}/"
            f"{health['producer_count']}"
        ),
    )


    health_col3.metric(
        "Normal In-Flight",
        health[
            "total_in_flight_events"
        ],
    )


    health_col4.metric(
        "Overdue Observations",
        health[
            "total_overdue_events"
        ],
    )


    health_col5.metric(
        "Max Data Age",
        (
            f"{health['max_data_age_seconds']:.2f} s"
        ),
    )


    health_col6.metric(
        "Max Latency Seen",
        (
            f"{health['max_latency_ms']:.0f} ms"
        ),
    )


    if stale_producers:

        st.error(
            "STALE producer(s): "
            + ", ".join(
                stale_producers
            )
            + ". Observed data is older "
            "than the configured freshness "
            "tolerance."
        )

    elif buffering_producers:

        st.warning(
            "BUFFERING producer(s): "
            + ", ".join(
                buffering_producers
            )
            + ". Undelivered observations "
            "have exceeded normal transport "
            "delay."
        )

    elif recovering_producers:

        st.warning(
            "RECOVERING producer(s): "
            + ", ".join(
                recovering_producers
            )
            + ". A multi-event recovery "
            "burst has just been observed."
        )

    else:

        st.success(
            "Stream health nominal. "
            "No overdue observations "
            "detected."
        )


    st.caption(
        "Observer-side semantics: normal "
        "in-flight events are still inside "
        f"the {health['delivery_grace_seconds']:.2f}s "
        "delivery grace window. "
        "Only overdue observations count "
        "as a backlog signal."
    )


    # =====================================================
    # Compact producer-health table
    # =====================================================

    health_rows = []


    for drone_id in sorted(
        producer_health
    ):

        producer = (
            producer_health[
                drone_id
            ]
        )


        health_rows.append(
            {
                "Drone":
                    drone_id,

                "Health":
                    health_display(
                        producer[
                            "status"
                        ]
                    ),

                "Pending":
                    producer[
                        "pending_events"
                    ],

                "In flight":
                    producer[
                        "in_flight_events"
                    ],

                "Overdue":
                    producer[
                        "overdue_events"
                    ],

                "Data age s":
                    round(
                        producer[
                            "data_age_seconds"
                        ],
                        2,
                    ),

                "Contact age s":
                    round(
                        producer[
                            "contact_age_seconds"
                        ],
                        2,
                    ),

                "Last telemetry seq":
                    producer[
                        "last_telemetry_sequence"
                    ],

                "Max latency ms":
                    round(
                        producer[
                            "max_latency_ms"
                        ],
                        1,
                    ),

                "Recent burst":
                    producer[
                        "recent_burst_size"
                    ],
            }
        )


    st.dataframe(
        health_rows,
        width="stretch",
        hide_index=True,
    )


    # =====================================================
    # Incident Timeline / Persistent Evidence
    # =====================================================

    st.subheader(
        "Incident Timeline"
    )


    fleet_history_df = (
        pd.DataFrame(
            health_timeline[
                "samples"
            ]
        )
    )


    if not fleet_history_df.empty:

        (
            history_col1,
            history_col2,
            history_col3,
        ) = st.columns(
            3
        )


        history_col1.caption(
            "Fleet maximum data age"
        )


        history_col1.line_chart(
            fleet_history_df,
            x="sim_seconds",
            y="max_data_age_seconds",
            height=220,
            width="stretch",
        )


        history_col2.caption(
            "Overdue observations"
        )


        history_col2.line_chart(
            fleet_history_df,
            x="sim_seconds",
            y="total_overdue_events",
            height=220,
            width="stretch",
        )


        history_col3.caption(
            "Affected producers"
        )


        history_col3.line_chart(
            fleet_history_df,
            x="sim_seconds",
            y="affected_producers",
            height=220,
            width="stretch",
        )


    focus_history = [
        sample

        for sample
        in health_timeline[
            "producer_samples"
        ]

        if sample[
            "drone_id"
        ] == focus_drone_id
    ]


    focus_history_df = (
        pd.DataFrame(
            focus_history
        )
    )


    st.caption(
        f"Selected producer history: "
        f"{focus_drone_id}"
    )


    if not focus_history_df.empty:

        (
            focus_col1,
            focus_col2,
            focus_col3,
        ) = st.columns(
            3
        )


        focus_col1.caption(
            "Producer data age"
        )


        focus_col1.line_chart(
            focus_history_df,
            x="sim_seconds",
            y="data_age_seconds",
            height=220,
            width="stretch",
        )


        focus_col2.caption(
            "Producer overdue events"
        )


        focus_col2.line_chart(
            focus_history_df,
            x="sim_seconds",
            y="overdue_events",
            height=220,
            width="stretch",
        )


        focus_col3.caption(
            "Maximum latency observed"
        )


        focus_col3.line_chart(
            focus_history_df,
            x="sim_seconds",
            y="max_latency_ms",
            height=220,
            width="stretch",
        )


    incident_rows = []


    for incident in health_timeline[
        "incidents"
    ]:

        incident_rows.append(
            {
                "Drone":
                    incident[
                        "drone_id"
                    ],

                "Status":
                    health_display(
                        incident[
                            "status"
                        ]
                    ),

                "Start":
                    (
                        f"T+"
                        f"{incident['start_seconds']:.2f}s"
                    ),

                "End":
                    (
                        f"T+"
                        f"{incident['end_seconds']:.2f}s"
                    ),

                "Duration s":
                    round(
                        incident[
                            "duration_seconds"
                        ],
                        2,
                    ),

                "Max data age s":
                    round(
                        incident[
                            "max_data_age_seconds"
                        ],
                        2,
                    ),

                "Max overdue":
                    incident[
                        "max_overdue_events"
                    ],

                "Max latency ms":
                    round(
                        incident[
                            "max_latency_ms"
                        ],
                        1,
                    ),

                "Max recovery burst":
                    incident[
                        "max_recent_burst"
                    ],
            }
        )


    if incident_rows:

        st.caption(
            "Persistent incident history "
            "for the current simulator run."
        )


        st.dataframe(
            incident_rows,
            width="stretch",
            hide_index=True,
        )

    else:

        st.success(
            "No non-nominal stream-health "
            "incident has been recorded "
            "in this run."
        )


    # =====================================================
    # Map layers
    # =====================================================

    layers = []


    # -----------------------------------------------------
    # Ground Truth tracks
    # -----------------------------------------------------

    if show_truth_tracks:

        truth_path_data = [
            {
                "drone_id":
                    drone_id,

                "path":
                    path,
            }

            for (
                drone_id,
                path,
            ) in truth_tracks.items()

            if len(
                path
            ) >= 2
        ]


        if truth_path_data:

            layers.append(
                pdk.Layer(
                    "PathLayer",

                    data=(
                        truth_path_data
                    ),

                    get_path="path",

                    get_color=[
                        70,
                        225,
                        120,
                    ],

                    get_width=6,

                    width_min_pixels=4,

                    pickable=False,
                )
            )


    # -----------------------------------------------------
    # Raw physical arrival tracks
    # -----------------------------------------------------

    if show_raw_tracks:

        raw_path_data = [
            {
                "drone_id":
                    drone_id,

                "path":
                    path,
            }

            for (
                drone_id,
                path,
            ) in raw_tracks.items()

            if len(
                path
            ) >= 2
        ]


        if raw_path_data:

            layers.append(
                pdk.Layer(
                    "PathLayer",

                    data=(
                        raw_path_data
                    ),

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
    # Reconstructed tracks
    # -----------------------------------------------------

    if show_reconstructed_tracks:

        reconstructed_data = [
            {
                "drone_id":
                    drone_id,

                "path":
                    path,
            }

            for (
                drone_id,
                path,
            ) in (
                reconstructed_tracks.items()
            )

            if len(
                path
            ) >= 2
        ]


        if reconstructed_data:

            layers.append(
                pdk.Layer(
                    "PathLayer",

                    data=(
                        reconstructed_data
                    ),

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
    # Truth markers
    # =====================================================

    truth_marker_data = []


    for (
        drone_id,
        record,
    ) in latest_truth.items():

        position = (
            record[
                "position"
            ]
        )

        truth_marker_data.append(
            {
                "drone_id":
                    drone_id,

                "longitude":
                    position[
                        "longitude"
                    ],

                "latitude":
                    position[
                        "latitude"
                    ],

                "phase":
                    record[
                        "states"
                    ][
                        "mission_phase"
                    ],

                "altitude_m":
                    position[
                        "altitude_m"
                    ],

                "sequence":
                    "",

                "state_type":
                    "GROUND TRUTH",
            }
        )


    if (
        show_truth_positions
        and truth_marker_data
    ):

        layers.append(
            pdk.Layer(
                "ScatterplotLayer",

                data=(
                    truth_marker_data
                ),

                get_position=(
                    "[longitude, latitude]"
                ),

                get_fill_color=[
                    0,
                    255,
                    120,
                ],

                get_radius=15,

                radius_min_pixels=10,

                pickable=True,
            )
        )


    # =====================================================
    # Observed markers
    # =====================================================

    observed_marker_data = []


    for (
        drone_id,
        state,
    ) in observed_states.items():

        if not state.has_position:

            continue


        health_state = (
            producer_health.get(
                drone_id,
                {},
            ).get(
                "status",
                "UNKNOWN",
            )
        )


        observed_marker_data.append(
            {
                "drone_id":
                    drone_id,

                "longitude":
                    state.longitude,

                "latitude":
                    state.latitude,

                "phase":
                    state.mission_phase,

                "altitude_m":
                    state.altitude_m,

                "sequence":
                    state.latest_sequence_number,

                "health":
                    health_state,

                "state_type":
                    "OBSERVED",
            }
        )


    if (
        show_observed_positions
        and observed_marker_data
    ):

        layers.append(
            pdk.Layer(
                "ScatterplotLayer",

                data=(
                    observed_marker_data
                ),

                get_position=(
                    "[longitude, latitude]"
                ),

                get_fill_color=[
                    255,
                    70,
                    135,
                ],

                get_radius=9,

                radius_min_pixels=6,

                pickable=True,
            )
        )


    # =====================================================
    # Labels
    # =====================================================

    if (
        show_labels
        and observed_marker_data
    ):

        layers.append(
            pdk.Layer(
                "TextLayer",

                data=(
                    observed_marker_data
                ),

                get_position=(
                    "[longitude, latitude]"
                ),

                get_text="drone_id",

                get_size=14,

                get_alignment_baseline=(
                    "'bottom'"
                ),

                get_pixel_offset=[
                    0,
                    -12,
                ],

                get_color=[
                    255,
                    255,
                    255,
                ],

                pickable=False,
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

                zoom=12.7,

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
                "Sequence: {sequence}<br/>"
                "Health: {health}"
            )
        },
    )


    st.pydeck_chart(
        deck,
        height=640,
        width="stretch",
    )


    # =====================================================
    # Per-drone state table
    # =====================================================

    status_rows = []


    for drone_id in sorted(
        latest_truth
    ):

        truth = (
            latest_truth[
                drone_id
            ]
        )

        observed = (
            observed_states.get(
                drone_id
            )
        )

        stream_health = (
            producer_health.get(
                drone_id,
                {}
            )
        )


        status_rows.append(
            {
                "Drone":
                    drone_id,

                "Stream health":
                    health_display(
                        stream_health.get(
                            "status",
                            "UNKNOWN",
                        )
                    ),

                "Truth phase":
                    truth[
                        "states"
                    ][
                        "mission_phase"
                    ],

                "Observed phase":
                    (
                        observed.
                        mission_phase

                        if observed
                        is not None

                        else "NO DATA"
                    ),

                "Truth altitude":
                    round(
                        truth[
                            "position"
                        ][
                            "altitude_m"
                        ],
                        1,
                    ),

                "Observed altitude":
                    (
                        round(
                            observed.
                            altitude_m,
                            1,
                        )

                        if (
                            observed
                            is not None
                            and
                            observed.
                            altitude_m
                            is not None
                        )

                        else None
                    ),

                "Latest seq":
                    (
                        observed.
                        latest_sequence_number

                        if observed
                        is not None

                        else 0
                    ),

                "Separation m":
                    round(
                        separations.get(
                            drone_id,
                            0.0,
                        ),
                        1,
                    ),

                "Data age s":
                    round(
                        stream_health.get(
                            "data_age_seconds",
                            0.0,
                        ),
                        2,
                    ),

                "Overdue":
                    stream_health.get(
                        "overdue_events",
                        0,
                    ),

                "Max latency ms":
                    round(
                        stream_health.get(
                            "max_latency_ms",
                            0.0,
                        ),
                        1,
                    ),
            }
        )


    st.subheader(
        "Fleet Current State"
    )


    st.dataframe(
        status_rows,
        width="stretch",
        hide_index=True,
    )


render_fleet()
