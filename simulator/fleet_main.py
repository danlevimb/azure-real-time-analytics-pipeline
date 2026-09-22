from datetime import datetime
from pathlib import Path
import time
import argparse

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Run the synthetic drone "
            "fleet simulator."
        )
    )

    parser.add_argument(
        "--config",
        default="fleet005.yaml",
        help=(
            "Configuration file located "
            "under simulator/configs/"
        ),
    )

    return parser.parse_args()

from simulator.config_loader import (load_config,)
from simulator.domain.mission import (MissionPhase,)
from simulator.observability.delivery_logger import (DeliveryLogger,)
from simulator.observability.generated_event_logger import (GeneratedEventLogger,)
from simulator.observability.ground_truth_logger import (GroundTruthLogger,)
from simulator.observability.run_manifest import (write_run_manifest,)
from simulator.publishers.file_publisher import (FilePublisher,)
from simulator.publishers.eventhub_publisher import (EventHubPublisher,)
from simulator.simulation.clock import (SimulationClock,)
from simulator.simulation.fleet_factory import (build_fleet_runtimes,)
from simulator.simulation.mission_engine import (MissionEngine,)
from simulator.simulation.power_model import (update_battery,)
from simulator.scenarios.maintenance_lifecycle import (MaintenanceLifecycleScenario,)
from simulator.scenarios.connectivity import (ConnectivityScenario,)
from simulator.telemetry.event_factory import (EventFactory,)
from simulator.transport.transport_engine import (TransportEngine,)

# =========================================================
# Mission transition reason
#
# Kept local for now so DRN-001 main.py remains untouched.
# We can refactor shared helpers later.
# =========================================================

def mission_transition_reason(
    previous_phase: MissionPhase,
    new_phase: MissionPhase,
) -> str:

    reasons = {
        (
            MissionPhase.READY,
            MissionPhase.TAKEOFF,
        ): "MISSION_STARTED",

        (
            MissionPhase.TAKEOFF,
            MissionPhase.EN_ROUTE,
        ): "TARGET_ALTITUDE_REACHED",

        (
            MissionPhase.EN_ROUTE,
            MissionPhase.ON_MISSION,
        ): "OUTBOUND_ROUTE_COMPLETED",

        (
            MissionPhase.ON_MISSION,
            MissionPhase.RETURNING,
        ): "MISSION_ACTIVITY_COMPLETED",

        (
            MissionPhase.RETURNING,
            MissionPhase.LANDING,
        ): "BASE_REACHED",

        (
            MissionPhase.LANDING,
            MissionPhase.LANDED,
        ): "LANDING_COMPLETED",
    }

    return reasons.get((previous_phase, new_phase,),"UNSPECIFIED",)
# =========================================================
# Main
# =========================================================

def main() -> None:

    # =====================================================
    # Configuration
    # =====================================================

    args = parse_args()

    config_path = (
        Path(__file__).parent
        / "configs"
        / args.config
    )

    # Centralized fail-fast configuration validation.
    #
    # No simulator event is generated until this returns.
    config = load_config(
        config_path,
        require_fleet=True,
    )

    simulation = config["simulation"]
    telemetry_config = config["telemetry"]
    simulation_context = config["simulation_context"]
    observability = config["observability"]
    transport_config = config["transport"]
    buffer_config = transport_config["buffering"]

    publishers_config = config.get(
        "publishers",
        {},
    )

    file_publisher_config = (
        publishers_config.get(
            "file",
            {},
        )
    )

    event_hubs_config = (
        publishers_config.get(
            "event_hubs",
            {},
        )
    )

    file_publisher_enabled = (
        file_publisher_config.get(
            "enabled",
            True,
        )
    )

    event_hubs_enabled = (
        event_hubs_config.get(
            "enabled",
            False,
        )
    )
    
    buffer_target_drone_ids = (
        set(buffer_config["target_drone_ids"])

        if (
            "target_drone_ids"
            in buffer_config
        )

        else None
    )
    
    fault_config = transport_config.get("fault_injection", {},)

    maintenance_scenario = (
        MaintenanceLifecycleScenario.from_config(
            config
        )
    )
    
    connectivity_scenario = (
        ConnectivityScenario.from_config(
            config
        )
    )
    
    duplicate_targets = {
        (
            rule["drone_id"],
            rule[
                "source_sequence_number"
            ],
        )

        for rule
        in fault_config.get(
            "duplicate_targets",
            [],
        )
    }

    drop_targets = {
        (
            rule["drone_id"],
            rule[
                "source_sequence_number"
            ],
        )

        for rule
        in fault_config.get(
            "drop_targets",
            [],
        )
    }


    extra_delay_by_target = {
        (
            rule["drone_id"],
            rule[
                "source_sequence_number"
            ],
        ):
        rule[
            "extra_delay_ms"
        ]

        for rule
        in fault_config.get(
            "extra_delay_targets",
            [],
        )
    }
    
    # --

    # =====================================================
    # Clock
    # =====================================================

    tick_seconds = simulation["tick_ms"] / 1000.0
    speed_multiplier = simulation["speed_multiplier"]

    if speed_multiplier <= 0:

        raise ValueError("speed_multiplier must be > 0")

    wall_tick_seconds = tick_seconds / speed_multiplier

    clock = SimulationClock(
        start_time=datetime.fromisoformat(
            simulation[
                "start_time_utc"
            ]
        ),

        tick_seconds=tick_seconds,
    )

    # =====================================================
    # Fleet runtimes
    # =====================================================

    runtimes = build_fleet_runtimes(
        config
    )

    if not runtimes:

        raise ValueError(
            "Fleet contains no drones"
        )

    # =====================================================
    # Shared output
    #
    # ALL drones publish into these same files.
    # =====================================================

    output_dir = (
        Path(__file__).parent.parent
        / "output"
        / simulation_context[
            "simulator_run_id"
        ]
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        manifest_path,
        config_snapshot_path,
    ) = write_run_manifest(
        config_path=config_path,
        config=config,
        output_dir=output_dir,
    )

    print(
        f"[CONFIG VALIDATION] PASS "
        f"| file={config_path.name}"
    )

    print(
        f"[RUN MANIFEST] "
        f"{manifest_path.name} "
        f"| snapshot="
        f"{config_snapshot_path.name}"
    )

    file_publisher = None
    eventhub_publisher = None

    if file_publisher_enabled:

        file_publisher = FilePublisher(
            output_path=(
                output_dir
                / "events.jsonl"
            )
        )

    if event_hubs_enabled:

        eventhub_publisher = (
            EventHubPublisher(
                fully_qualified_namespace=(
                    event_hubs_config[
                        "fully_qualified_namespace"
                    ]
                ),

                eventhub_name=(
                    event_hubs_config[
                        "event_hub_name"
                    ]
                ),

                partition_key_field=(
                    event_hubs_config[
                        "partition_key_field"
                    ]
                ),

                buffered_mode=(
                    event_hubs_config.get(
                        "buffered_mode",
                        True,
                    )
                ),

                max_wait_time_seconds=(
                    event_hubs_config.get(
                        "max_wait_time_seconds",
                        0.5,
                    )
                ),
            )
        )

    print(
        f"[PUBLISHERS] "
        f"file="
        f"{'ON' if file_publisher_enabled else 'OFF'} "
        f"| event_hubs="
        f"{'ON' if event_hubs_enabled else 'OFF'}"
    )

    if event_hubs_enabled:

        print(
            f"[EVENT HUBS TARGET] "
            f"{event_hubs_config['event_hub_name']} "
            f"| namespace="
            f"{event_hubs_config['fully_qualified_namespace']} "
            f"| partition_key="
            f"{event_hubs_config['partition_key_field']} "
            f"| buffered="
            f"{event_hubs_config.get('buffered_mode', True)}"
        )

    ground_truth_logger = (
        GroundTruthLogger(
            output_path=(
                output_dir
                / "ground_truth.jsonl"
            ),

            simulator_run_id=(
                simulation_context[
                    "simulator_run_id"
                ]
            ),
        )
    )

    delivery_logger = (
        DeliveryLogger(
            output_path=(
                output_dir
                / "delivery_log.jsonl"
            ),

            simulator_run_id=(
                simulation_context[
                    "simulator_run_id"
                ]
            ),
        )
    )

    generated_event_logger = (
        GeneratedEventLogger(
            output_path=(
                output_dir
                / "generated_events.jsonl"
            )
        )
    )

    # =====================================================
    # Physical delivery fan-out
    #
    # Local evidence remains authoritative for what the
    # simulator's TransportEngine released. Cloud publish
    # is an additional external sink and does not change
    # Event Contract v1 or transport semantics.
    # =====================================================

    def publish_delivered_event(
        delivered_event: dict,
    ) -> None:

        if file_publisher is not None:

            file_publisher.publish(
                delivered_event
            )

        delivery_logger.log_delivery(
            event=delivered_event,

            delivered_at=(
                clock.now
            ),

            delivered_at_seconds=(
                clock.elapsed_seconds
            ),
        )

        if eventhub_publisher is not None:

            eventhub_publisher.publish(
                delivered_event
            )

    # =====================================================
    # Shared TransportEngine
    # =====================================================

    extra_delay_by_sequence = {
        rule[
            "source_sequence_number"
        ]:
        rule[
            "extra_delay_ms"
        ]

        for rule
        in fault_config.get(
            "extra_delay",
            [],
        )
    }

    transport = TransportEngine(
        base_delay_ms = (transport_config["base_delay_ms"]),
        
        buffering_enabled = (buffer_config["enabled"]),        
        buffer_start_seconds = (buffer_config["start_at_seconds"]),
        buffer_end_seconds = (buffer_config["end_at_seconds"]),
        buffer_target_drone_ids = (buffer_target_drone_ids),
        
        duplicate_sequences = set(fault_config.get("duplicate_sequences", [],)),
        drop_sequences = set(fault_config.get("drop_sequences", [],)),
        extra_delay_ms_by_sequence = (extra_delay_by_sequence),        
        duplicate_targets = (duplicate_targets),
        drop_targets = (drop_targets),
        extra_delay_ms_by_target=(extra_delay_by_target),
    )

    # =====================================================
    # Submit logical event into SHARED transport
    # =====================================================

    def submit_to_transport(
        event: dict,
    ):

        generated_event_logger.log(
            event
        )

        submission = transport.submit(
            event=event,

            current_seconds=(
                clock.elapsed_seconds
            ),
        )

        drone_id = event[
            "drone_id"
        ]

        sequence_number = event[
            "source_sequence_number"
        ]

        if submission.dropped:

            print(
                f"[TRANSPORT DROP] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"{drone_id} "
                f"seq={sequence_number:04d}"
            )

            return submission

        if (
            submission.duplicate_copies
            > 0
        ):

            print(
                f"[TRANSPORT DUPLICATE] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"{drone_id} "
                f"seq={sequence_number:04d} "
                f"copies="
                f"{1 + submission.duplicate_copies}"
            )

        if (
            submission.extra_delay_ms
            > 0
        ):

            print(
                f"[TRANSPORT EXTRA DELAY] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"{drone_id} "
                f"seq={sequence_number:04d} "
                f"extra="
                f"{submission.extra_delay_ms}ms"
            )

        if submission.buffered:

            print(
                f"[TRANSPORT BUFFER] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"{drone_id} "
                f"seq={sequence_number:04d} "
                f"pending="
                f"{transport.buffered_count}"
            )

        return submission

    # =====================================================
    # Runtime
    # =====================================================

    total_ticks = round(
        simulation[
            "duration_seconds"
        ]
        / tick_seconds
    )

    console_every_ticks = max(
        1,

        (
            observability[
                "console_interval_ms"
            ]
            // simulation[
                "tick_ms"
            ]
        ),
    )

    # =====================================================
    # Header
    # =====================================================

    print()

    print(
        f"[RUN] "
        f"{simulation['run_name']}"
    )

    print(
        f"[SIMULATOR RUN] "
        f"{simulation_context['simulator_run_id']}"
    )

    print(
        f"[FLEET] "
        f"{config['fleet']['fleet_id']} "
        f"| drones={len(runtimes)} "
        f"| battalion="
        f"{config['fleet']['battalion_id']}"
    )

    print()

    for runtime in runtimes:

        print(
            f"  {runtime.drone.drone_id} "
            f"| mission="
            f"{runtime.mission.mission_id} "
            f"| route="
            f"{runtime.outbound_route.route_instance_id}"
        )

    print()

    # =====================================================
    # Start ALL missions at T+0
    # =====================================================

    for runtime in runtimes:

        drone = runtime.drone
        mission = runtime.mission

        MissionEngine.start(
            mission=mission,
            drone=drone,
        )

        ground_truth_logger.log_snapshot(
            drone=drone,
            mission=mission,
            simulation_time=clock.now,
            elapsed_seconds=(
                clock.elapsed_seconds
            ),
        )

        initial_transition_event = (
            EventFactory.state_transition(
                drone=drone,
                mission=mission,
                event_time=clock.now,

                schema_version=(
                    telemetry_config[
                        "schema_version"
                    ]
                ),

                simulator_run_id=(
                    simulation_context[
                        "simulator_run_id"
                    ]
                ),

                scenario=(
                    simulation_context[
                        "scenario"
                    ]
                ),

                seed=(
                    simulation[
                        "seed"
                    ]
                ),

                state_domain=(
                    "mission_phase"
                ),

                previous_state=(
                    "READY"
                ),

                new_state=(
                    "TAKEOFF"
                ),

                reason_code=(
                    "MISSION_STARTED"
                ),
            )
        )

        submit_to_transport(
            initial_transition_event
        )

        print(
            f"[MISSION START] "
            f"{drone.drone_id} "
            f"| {mission.mission_id} "
            f"| seq="
            f"{initial_transition_event['source_sequence_number']:04d}"
        )

    print()

    # =====================================================
    # Simulation loop
    #
    # ONE tick updates ALL drones.
    # =====================================================

    fleet_completed = False

    mission_completion_announced = set()

    for tick_number in range(
        1,
        total_ticks + 1,
    ):

        # -------------------------------------------------
        # Advance global simulation time ONCE.
        # -------------------------------------------------

        clock.advance()

        # -------------------------------------------------
        # Update every active drone at this same time.
        # -------------------------------------------------

        for runtime in runtimes:

            if runtime.completed:
                continue

            drone = runtime.drone
            mission = runtime.mission

            # ---------------------------------------------
            # Deterministic battery consumption
            #
            # Battery drains only while the mission is
            # operationally active. Once the mission is
            # completed (for example during maintenance),
            # the battery remains stable.
            # ---------------------------------------------

            update_battery(
                drone=drone,

                drain_pct_per_minute=(
                    runtime.
                    battery_drain_pct_per_minute
                ),

                dt_seconds=(
                    tick_seconds
                ),

                mission_active=(
                    mission.status.value
                    == "ACTIVE"
                ),
            )

            result = MissionEngine.update(
                mission=mission,
                drone=drone,

                route=(
                    runtime.outbound_route
                ),

                return_route=(
                    runtime.return_route
                ),

                dt_seconds=(
                    tick_seconds
                ),
            )

            # ---------------------------------------------
            # Mission phase transition
            #
            # The mission transition is emitted first.
            # Scenario events may depend on the new phase
            # (for example LANDED -> maintenance start).
            # ---------------------------------------------

            if result.new_phase is not None:

                transition_event = (
                    EventFactory.state_transition(
                        drone=drone,
                        mission=mission,

                        event_time=(
                            clock.now
                        ),

                        schema_version=(
                            telemetry_config[
                                "schema_version"
                            ]
                        ),

                        simulator_run_id=(
                            simulation_context[
                                "simulator_run_id"
                            ]
                        ),

                        scenario=(
                            simulation_context[
                                "scenario"
                            ]
                        ),

                        seed=(
                            simulation[
                                "seed"
                            ]
                        ),

                        state_domain=(
                            "mission_phase"
                        ),

                        previous_state=(
                            result.
                            previous_phase.
                            value
                        ),

                        new_state=(
                            result.
                            new_phase.
                            value
                        ),

                        reason_code=(
                            mission_transition_reason(
                                result.previous_phase,
                                result.new_phase,
                            )
                        ),
                    )
                )

                submit_to_transport(
                    transition_event
                )

                print(
                    f"[PHASE] "
                    f"T+{clock.elapsed_seconds:05.2f}s "
                    f"{drone.drone_id} "
                    f"{result.previous_phase.value} "
                    f"-> "
                    f"{result.new_phase.value} "
                    f"| seq="
                    f"{transition_event['source_sequence_number']:04d}"
                )

            # ---------------------------------------------
            # Optional maintenance lifecycle scenario
            #
            # The scenario changes simulated reality first.
            # EventFactory then describes those changes.
            # ---------------------------------------------

            if maintenance_scenario is not None:

                scenario_events = (
                    maintenance_scenario.update(
                        drone=drone,
                        mission=mission,

                        current_seconds=(
                            clock.elapsed_seconds
                        ),

                        event_time=(
                            clock.now
                        ),

                        schema_version=(
                            telemetry_config[
                                "schema_version"
                            ]
                        ),

                        simulator_run_id=(
                            simulation_context[
                                "simulator_run_id"
                            ]
                        ),

                        scenario=(
                            simulation_context[
                                "scenario"
                            ]
                        ),

                        seed=(
                            simulation[
                                "seed"
                            ]
                        ),
                    )
                )

                for scenario_event in (
                    scenario_events
                ):

                    submit_to_transport(
                        scenario_event
                    )

                    print(
                        f"[SCENARIO EVENT] "
                        f"T+{clock.elapsed_seconds:05.2f}s "
                        f"{drone.drone_id} "
                        f"type="
                        f"{scenario_event['event_type']} "
                        f"| seq="
                        f"{scenario_event['source_sequence_number']:04d} "
                        f"| payload="
                        f"{scenario_event['payload']}"
                    )
            
            # ---------------------------------------------
            # Optional connectivity scenario
            #
            # Changes simulated communication state before
            # Ground Truth and Telemetry are generated.
            # ---------------------------------------------

            if connectivity_scenario is not None:

                connectivity_events = (
                    connectivity_scenario.update(
                        drone=drone,
                        mission=mission,

                        current_seconds=(
                            clock.elapsed_seconds
                        ),

                        event_time=(
                            clock.now
                        ),

                        schema_version=(
                            telemetry_config[
                                "schema_version"
                            ]
                        ),

                        simulator_run_id=(
                            simulation_context[
                                "simulator_run_id"
                            ]
                        ),

                        scenario=(
                            simulation_context[
                                "scenario"
                            ]
                        ),

                        seed=(
                            simulation[
                                "seed"
                            ]
                        ),
                    )
                )

                for connectivity_event in (
                    connectivity_events
                ):

                    submit_to_transport(
                        connectivity_event
                    )

                    print(
                        f"[CONNECTIVITY EVENT] "
                        f"T+"
                        f"{clock.elapsed_seconds:05.2f}s "
                        f"{drone.drone_id} "
                        f"| seq="
                        f"{connectivity_event['source_sequence_number']:04d} "
                        f"| payload="
                        f"{connectivity_event['payload']}"
                    )

            # ---------------------------------------------
            # Ground Truth
            #
            # Snapshot is written after mission + scenario
            # state mutations so truth reflects this tick's
            # final simulated state.
            # ---------------------------------------------

            ground_truth_logger.log_snapshot(
                drone=drone,
                mission=mission,

                simulation_time=(
                    clock.now
                ),

                elapsed_seconds=(
                    clock.elapsed_seconds
                ),
            )

            # ---------------------------------------------
            # Telemetry
            # ---------------------------------------------

            if (
                runtime.
                telemetry_generator.
                is_due(
                    tick_number
                )
            ):

                event = (
                    runtime.
                    telemetry_generator.
                    generate(
                        drone=drone,
                        mission=mission,
                        clock=clock,
                    )
                )

                submit_to_transport(
                    event
                )

            # ---------------------------------------------
            # Waypoint diagnostics
            # ---------------------------------------------

            for waypoint_id in (
                result.reached_waypoints
            ):

                print(
                    f"[WAYPOINT] "
                    f"T+{clock.elapsed_seconds:05.2f}s "
                    f"{drone.drone_id} "
                    f"{waypoint_id}"
                )

            # ---------------------------------------------
            # Mission / asset lifecycle completion
            #
            # A LANDED mission does not necessarily mean
            # the asset lifecycle is complete. A targeted
            # maintenance scenario may keep the producer
            # alive on the ground for additional events.
            # ---------------------------------------------

            if (
                mission.phase
                == MissionPhase.LANDED
                and drone.drone_id
                not in mission_completion_announced
            ):

                mission_completion_announced.add(
                    drone.drone_id
                )

                print(
                    f"[MISSION COMPLETE] "
                    f"T+{clock.elapsed_seconds:05.2f}s "
                    f"{drone.drone_id} "
                    f"| mission="
                    f"{mission.mission_id} "
                    f"| seq="
                    f"{drone.source_sequence_number}"
                )

            if (
                mission.phase
                == MissionPhase.LANDED
            ):

                scenario_owns_asset = (
                    maintenance_scenario
                    is not None
                    and maintenance_scenario.applies_to(
                        drone.drone_id
                    )
                )

                if not scenario_owns_asset:

                    runtime.completed = True

                elif (
                    maintenance_scenario.
                    is_complete_for(
                        drone.drone_id
                    )
                ):

                    runtime.completed = True

                if runtime.completed:

                    print(
                        f"[DRONE COMPLETE] "
                        f"T+{clock.elapsed_seconds:05.2f}s "
                        f"{drone.drone_id} "
                        f"| mission="
                        f"{mission.mission_id} "
                        f"| asset_state="
                        f"{drone.asset_state} "
                        f"| health="
                        f"{drone.platform_health} "
                        f"| seq="
                        f"{drone.source_sequence_number}"
                    )

        # =================================================
        # IMPORTANT:
        #
        # Release transport ONCE PER GLOBAL TICK,
        # after ALL drones submitted events.
        # =================================================

        (
            released_events,
            buffer_release_count,
        ) = transport.release_ready(
            current_seconds=(
                clock.elapsed_seconds
            )
        )

        if buffer_release_count > 0:

            print(
                f"[TRANSPORT RECOVERED] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"buffered_events="
                f"{buffer_release_count}"
            )

        for delivered_event in (
            released_events
        ):

            publish_delivered_event(
                delivered_event
            )

        if len(released_events) > 1:

            delivered_drones = {
                event["drone_id"]
                for event
                in released_events
            }

            print(
                f"[EVENT RIVER] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"delivered="
                f"{len(released_events)} "
                f"| producers="
                f"{len(delivered_drones)}"
            )

        # =================================================
        # Fleet snapshot every console interval
        # =================================================

        if (
            tick_number
            % console_every_ticks
            == 0
        ):

            print()

            print(
                f"[FLEET SNAPSHOT] "
                f"T+{clock.elapsed_seconds:05.2f}s"
            )

            for runtime in runtimes:

                drone = runtime.drone
                mission = runtime.mission

                print(
                    f"  "
                    f"{drone.drone_id} "
                    f"phase="
                    f"{mission.phase.value:<10} "
                    f"lat="
                    f"{drone.latitude:.6f} "
                    f"lon="
                    f"{drone.longitude:.6f} "
                    f"alt="
                    f"{drone.altitude_m:6.1f}m "
                    f"seq="
                    f"{drone.source_sequence_number:03d}"
                )

            print()

        # =================================================
        # Fleet complete?
        # =================================================

        if all(
            runtime.completed
            for runtime
            in runtimes
        ):

            fleet_completed = True

            print(
                f"[FLEET OPERATIONAL COMPLETE] "
                f"T+{clock.elapsed_seconds:.2f}s "
                f"completed="
                f"{len(runtimes)}/{len(runtimes)} "
                f"| transport_pending="
                f"{transport.pending_count}"
            )

            break

        # One sleep per global tick.
        time.sleep(
            wall_tick_seconds
        )

    # =====================================================
    # Natural transport drain
    #
    # Operational completion does NOT imply that the
    # stream is already empty. Events that are still
    # scheduled keep their original transport delay and
    # are released only when their release time becomes
    # due.
    #
    # No new domain state or telemetry is generated here.
    # Only the transport clock continues long enough to
    # deliver events that were already in flight.
    # =====================================================

    drain_started_at_seconds = (
        clock.elapsed_seconds
    )

    drained_event_count = 0

    if transport.pending_count > 0:

        print(
            f"[STREAM DRAIN START] "
            f"T+{clock.elapsed_seconds:05.2f}s "
            f"pending="
            f"{transport.pending_count}"
        )

    while transport.pending_count > 0:

        # Keep local real-time pacing consistent with the
        # simulator speed multiplier.
        time.sleep(
            wall_tick_seconds
        )

        clock.advance()

        (
            released_events,
            buffer_release_count,
        ) = transport.release_ready(
            current_seconds=(
                clock.elapsed_seconds
            )
        )

        if buffer_release_count > 0:

            print(
                f"[TRANSPORT RECOVERED DURING DRAIN] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"buffered_events="
                f"{buffer_release_count}"
            )

        for delivered_event in (
            released_events
        ):

            publish_delivered_event(
                delivered_event
            )

        if released_events:

            drained_event_count += len(
                released_events
            )

            delivered_drones = {
                event["drone_id"]
                for event
                in released_events
            }

            print(
                f"[STREAM DRAIN] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"delivered="
                f"{len(released_events)} "
                f"| producers="
                f"{len(delivered_drones)} "
                f"| pending="
                f"{transport.pending_count}"
            )

    if drained_event_count > 0:

        print(
            f"[STREAM DRAIN COMPLETE] "
            f"T+{clock.elapsed_seconds:05.2f}s "
            f"drained="
            f"{drained_event_count} "
            f"| drain_duration="
            f"{clock.elapsed_seconds - drain_started_at_seconds:.2f}s"
        )

    # =====================================================
    # Close shared output
    # =====================================================

    cloud_close_error = None

    try:

        if eventhub_publisher is not None:

            eventhub_publisher.close()

    except Exception as exc:

        cloud_close_error = exc

    finally:

        if file_publisher is not None:

            file_publisher.close()

        ground_truth_logger.close()
        delivery_logger.close()
        generated_event_logger.close()

    if eventhub_publisher is not None:

        print(
            f"[EVENT HUBS SUMMARY] "
            f"enqueued="
            f"{eventhub_publisher.enqueued_count} "
            f"| confirmed="
            f"{eventhub_publisher.confirmed_count} "
            f"| failed="
            f"{eventhub_publisher.failed_count}"
        )

    if cloud_close_error is not None:

        raise cloud_close_error

    # =====================================================
    # Final summary
    # =====================================================

    print()
    print("=" * 60)

    print(
        "FLEET RUN SUMMARY"
    )

    print("=" * 60)

    for runtime in runtimes:

        print(
            f"{runtime.drone.drone_id} "
            f"| phase="
            f"{runtime.mission.phase.value:<8} "
            f"| status="
            f"{runtime.mission.status.value:<9} "
            f"| seq="
            f"{runtime.drone.source_sequence_number}"
        )

    print()

    if fleet_completed:

        print(
            "RESULT: FLEET COMPLETED"
        )

    else:

        print(
            "RESULT: SIMULATION DURATION "
            "ENDED BEFORE FLEET COMPLETION"
        )


if __name__ == "__main__":
    main()