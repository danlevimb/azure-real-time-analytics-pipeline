from datetime import datetime
from pathlib import Path
import time

from simulator.config_loader import load_config
from simulator.domain.drone import Drone
from simulator.domain.mission import (Mission, MissionPhase,)
from simulator.domain.route import (RouteInstance, Waypoint,)
from simulator.observability.delivery_logger import (DeliveryLogger,)
from simulator.observability.generated_event_logger import (GeneratedEventLogger,)
from simulator.observability.ground_truth_logger import (GroundTruthLogger,)
from simulator.publishers.file_publisher import (FilePublisher,)
from simulator.simulation.clock import (SimulationClock,)
from simulator.simulation.mission_engine import (MissionEngine,)
from simulator.telemetry.telemetry_generator import (TelemetryGenerator,)
from simulator.telemetry.event_factory import (EventFactory,)
from simulator.transport.transport_engine import (TransportEngine,)

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

    return reasons.get((previous_phase, new_phase,), "UNSPECIFIED",)

def main() -> None:

    # =====================================================
    # Configuration
    # =====================================================
    config_path = (
        Path(__file__).parent
        / "configs"
        / "drn001.yaml"
    )

    config = load_config(config_path)
    simulation = config["simulation"]
    drone_config = config["drone"]
    position = drone_config["initial_position"]
    movement = drone_config["movement"]
    mission_config = config["mission"]
    orbit_config = mission_config["orbit"]
    route_config = config["route"]
    observability = config["observability"]
    telemetry_config = config["telemetry"]
    simulation_context = config["simulation_context"]
    transport_config = config["transport"]    
    fault_config = transport_config.get("fault_injection",{},)

    extra_delay_by_sequence = {
        rule["source_sequence_number"]:
        rule["extra_delay_ms"]

        for rule in fault_config.get(
            "extra_delay",
            [],
        )
    }
    
    buffer_config = transport_config["buffering"]
    
    # =====================================================
    # Clock
    # =====================================================
    tick_seconds = (simulation["tick_ms"] / 1000.0)
    
    speed_multiplier = simulation["speed_multiplier"]

    if speed_multiplier <= 0:
        raise ValueError("speed_multiplier must be > 0")

    wall_tick_seconds = (tick_seconds / speed_multiplier)

    clock = SimulationClock(
        start_time=datetime.fromisoformat(simulation["start_time_utc"]),
        tick_seconds=tick_seconds,
    )

    # =====================================================
    # DRN-001
    # =====================================================
    drone = Drone(
        drone_id=drone_config["drone_id"],
        battalion_id=drone_config["battalion_id"],
        latitude=position["latitude"],
        longitude=position["longitude"],
        altitude_m=position["altitude_m"],
        ground_speed_mps=0.0,
        vertical_speed_mps=0.0,
        heading_deg=movement["heading_deg"],
    )

    # =====================================================
    # Outbound route
    # =====================================================
    outbound_route = RouteInstance(
        route_instance_id=route_config["route_instance_id"],
        waypoints=[
            Waypoint(
                waypoint_id=wp["waypoint_id"],
                latitude=wp["latitude"],
                longitude=wp["longitude"],
            )
            for wp in route_config["waypoints"]
        ],
    )

    # =====================================================
    # Return route
    #
    # WP-03 -> WP-02 -> WP-01 -> BASE
    # =====================================================
    return_waypoints = list(reversed(outbound_route.waypoints))

    return_waypoints.append(
        Waypoint(
            waypoint_id="BASE-A",
            latitude=position["latitude"],
            longitude=position["longitude"],
        )
    )

    return_route = RouteInstance(
        route_instance_id=(
            f"{outbound_route.route_instance_id}"
            "-RETURN"
        ),
        waypoints=return_waypoints,
    )

    # =====================================================
    # Mission
    # =====================================================
    mission = Mission(
        mission_id = mission_config["mission_id"],
        mission_type = mission_config["mission_type"],
        assigned_drone_id = drone.drone_id,
        route_instance_id = (outbound_route.route_instance_id),
        target_altitude_m = mission_config["target_altitude_m"],
        climb_rate_mps = mission_config["climb_rate_mps"],
        descent_rate_mps = mission_config["descent_rate_mps"],
        cruise_speed_mps = movement["cruise_speed_mps"],
        orbit_radius_m = orbit_config["radius_m"],
        orbit_duration_seconds = orbit_config["duration_seconds"],
        orbit_direction = orbit_config["direction"],
    )
    
    # =====================================================
    # Telemetry generator
    # =====================================================    
    telemetry_generator = TelemetryGenerator(
        interval_ms = telemetry_config["interval_ms"],
        schema_version = telemetry_config["schema_version"],
        simulator_run_id = simulation_context["simulator_run_id"],
        scenario = simulation_context["scenario"],
        seed = simulation["seed"],
        tick_ms = simulation["tick_ms"],
    )

    output_path = (
        Path(__file__).parent.parent
        / "output"
        / simulation_context["simulator_run_id"]
        / "events.jsonl"
    )

    publisher = FilePublisher(output_path=output_path)
    
    transport = TransportEngine(
        base_delay_ms = transport_config["base_delay_ms"],
        buffering_enabled = buffer_config["enabled"],
        buffer_start_seconds = buffer_config["start_at_seconds"],
        buffer_end_seconds = buffer_config["end_at_seconds"],
        duplicate_sequences = set(fault_config.get("duplicate_sequences",[],)),
        drop_sequences = set(fault_config.get("drop_sequences",[],)),
        extra_delay_ms_by_sequence = (extra_delay_by_sequence),
    )
    
    def submit_to_transport(
        event: dict,
    ):
        # Logical source event
        generated_event_logger.log(event)
                
        submission = transport.submit(event=event, current_seconds=clock.elapsed_seconds,)

        sequence_number = event["source_sequence_number"]

        if submission.dropped:
            print(
                f"[TRANSPORT DROP] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"seq={sequence_number:04d}"
            )

            return submission

        if submission.duplicate_copies > 0:
            print(
                f"[TRANSPORT DUPLICATE] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"seq={sequence_number:04d} "
                f"copies="
                f"{1 + submission.duplicate_copies}"
            )

        if submission.extra_delay_ms > 0:
            print(
                f"[TRANSPORT EXTRA DELAY] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"seq={sequence_number:04d} "
                f"extra="
                f"{submission.extra_delay_ms}ms"
            )

        return submission

    ground_truth_path = (
        Path(__file__).parent.parent
        / "output"
        / simulation_context[
            "simulator_run_id"
        ]
        / "ground_truth.jsonl"
    )

    ground_truth_logger = GroundTruthLogger(
        output_path=ground_truth_path,
        simulator_run_id=simulation_context[
            "simulator_run_id"
        ],
    )
    
    delivery_log_path = (
        Path(__file__).parent.parent
        / "output"
        / simulation_context["simulator_run_id"]
        / "delivery_log.jsonl"
    )

    delivery_logger = DeliveryLogger(output_path =delivery_log_path, simulator_run_id=simulation_context["simulator_run_id"],)
    
    generated_events_path = (
        Path(__file__).parent.parent
        / "output"
        / simulation_context[
            "simulator_run_id"
        ]
        / "generated_events.jsonl"
    )

    generated_event_logger = GeneratedEventLogger(output_path=generated_events_path,)        
    
    # =====================================================
    # Runtime
    # =====================================================
    total_ticks = round(simulation["duration_seconds"] / tick_seconds)

    console_every_ticks = (
        observability["console_interval_ms"]
        // simulation["tick_ms"]
    )

    # =====================================================
    # Header
    # =====================================================
    print()

    print(
        f"[RUN] {simulation['run_name']} "
        f"| {drone.drone_id}"
    )

    print(
        f"[MISSION] "
        f"{mission.mission_id} "
        f"| type={mission.mission_type}"
    )

    print(
        f"[OUTBOUND ROUTE] "
        f"{outbound_route.route_instance_id} "
        f"| waypoints="
        f"{len(outbound_route.waypoints)}"
    )

    print(
        f"[RETURN ROUTE] "
        f"{return_route.route_instance_id} "
        f"| waypoints="
        f"{len(return_route.waypoints)}"
    )

    print(
        f"[START] "
        f"lat={drone.latitude:.6f} "
        f"lon={drone.longitude:.6f} "
        f"alt={drone.altitude_m:.1f}m"
    )

    print()

    # =====================================================
    # Start mission
    # =====================================================
    MissionEngine.start(mission=mission, drone=drone,)
    
    ground_truth_logger.log_snapshot(
        drone = drone,
        mission = mission,
        simulation_time = clock.now,
        elapsed_seconds = clock.elapsed_seconds,
    )
    
    initial_transition_event = (
        EventFactory.state_transition(
            drone=drone,
            mission=mission,
            event_time=clock.now,
            schema_version=telemetry_config["schema_version"],
            simulator_run_id=simulation_context["simulator_run_id"],
            scenario=simulation_context["scenario"],
            seed=simulation["seed"],
            state_domain="mission_phase",
            previous_state="READY",
            new_state="TAKEOFF",
            reason_code="MISSION_STARTED",
        )
    )

    submit_to_transport(initial_transition_event)

    print(
        f"[EVENT] "
        f"T+{clock.elapsed_seconds:05.2f}s "
        f"seq="
        f"{initial_transition_event['source_sequence_number']:04d} "
        f"state_transition "
        f"READY -> TAKEOFF"
    )    
    
    print(
        f"[MISSION PHASE] "
        f"READY -> {mission.phase.value}"
    )

    print()

    # =====================================================
    # Simulation loop
    # =====================================================
    for tick_number in range(
        1,
        total_ticks + 1,
    ):

        clock.advance()

        result = MissionEngine.update(
            mission = mission,
            drone = drone,
            route = outbound_route,
            return_route = return_route,
            dt_seconds = tick_seconds,
        )
        
        ground_truth_logger.log_snapshot(
            drone = drone,
            mission = mission,
            simulation_time = clock.now,
            elapsed_seconds = clock.elapsed_seconds,
        )
        
        if result.new_phase is not None:

            transition_event = (
                EventFactory.state_transition(
                    drone=drone,
                    mission=mission,
                    event_time=clock.now,
                    schema_version=telemetry_config["schema_version"],
                    simulator_run_id=simulation_context["simulator_run_id"],
                    scenario=simulation_context["scenario"],
                    seed=simulation["seed"],
                    state_domain="mission_phase",
                    previous_state=(result.previous_phase.value),
                    new_state=(result.new_phase.value),
                    reason_code=(
                        mission_transition_reason(
                            result.previous_phase,
                            result.new_phase,
                        )
                    ),
                )
            )

            submission = submit_to_transport(transition_event)

            if submission.buffered:

                print(
                    f"[TRANSPORT BUFFER] "
                    f"T+{clock.elapsed_seconds:05.2f}s "
                    f"seq="
                    f"{transition_event['source_sequence_number']:04d} "
                    f"pending="
                    f"{transport.buffered_count}"
                )

            print(
                f"[EVENT] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"seq="
                f"{transition_event['source_sequence_number']:04d} "
                f"state_transition "
                f"{result.previous_phase.value} "
                f"-> {result.new_phase.value}"
            )        
            
        if telemetry_generator.is_due(
            tick_number
        ):

            event = telemetry_generator.generate(
                drone = drone,
                mission = mission,
                clock = clock,
            )
                        
            submission = submit_to_transport(event)                    

            print(
                f"[TELEMETRY] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"seq="
                f"{event['source_sequence_number']:04d} "
                f"phase="
                f"{mission.phase.value}"
            )

        # -------------------------------------------------
        # 
        # -------------------------------------------------
        (
            released_events,
            buffer_release_count,
        ) = transport.release_ready(current_seconds=(clock.elapsed_seconds))

        if buffer_release_count > 0:

            print()

            print(
                f"[TRANSPORT RECOVERED] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"buffered_events="
                f"{buffer_release_count}"
            )

        for delivered_event in released_events:

            publisher.publish(delivered_event)
            
            delivery_logger.log_delivery(
                event=delivered_event,
                delivered_at=clock.now,
                delivered_at_seconds=(clock.elapsed_seconds),
            )

        if len(released_events) > 1:

            print(
                f"[TRANSPORT BURST] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"delivered="
                f"{len(released_events)}"
            )

            print()

        # -------------------------------------------------
        # Waypoints
        # -------------------------------------------------
        for waypoint_id in (
            result.reached_waypoints
        ):

            if (
                mission.phase
                in {
                    MissionPhase.RETURNING,
                    MissionPhase.LANDING,
                    MissionPhase.LANDED,
                }
            ):
                target = (return_route.current_waypoint)
            else:
                target = (outbound_route.current_waypoint)

            next_target = (
                target.waypoint_id
                if target
                else "ROUTE-END"
            )

            print(
                f"[WAYPOINT] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"{waypoint_id} reached "
                f"-> next={next_target}"
            )

        # -------------------------------------------------
        # Phase transitions
        # -------------------------------------------------
        if result.new_phase is not None:

            print(
                f"[MISSION PHASE] "
                f"T+{clock.elapsed_seconds:05.2f}s "
                f"{result.previous_phase.value} "
                f"-> {result.new_phase.value}"
            )

            if (
                result.new_phase
                == MissionPhase.ON_MISSION
            ):
                print(
                    f"[ORBIT START] "
                    f"radius="
                    f"{mission.orbit_radius_m:.1f}m "
                    f"duration="
                    f"{mission.orbit_duration_seconds:.1f}s "
                    f"direction="
                    f"{mission.orbit_direction}"
                )

            if result.new_phase == MissionPhase.RETURNING:
                print(
                    "[RETURN] "
                    "Leaving mission area "
                    "and returning to base"
                )

            if (
                result.new_phase
                == MissionPhase.LANDING
            ):
                print(
                    "[LANDING] "
                    "Base reached, "
                    "vertical descent started"
                )

        # -------------------------------------------------
        # Diagnostic output
        # -------------------------------------------------
        if (
            tick_number
            % console_every_ticks
            == 0
        ):

            if (
                mission.phase
                == MissionPhase.EN_ROUTE
            ):
                target = (outbound_route.current_waypoint)

            elif (
                mission.phase
                == MissionPhase.RETURNING
            ):
                target = (return_route.current_waypoint)

            else:
                target = None

            target_id = (
                target.waypoint_id
                if target
                else "NONE"
            )

            print(
                f"[T+{clock.elapsed_seconds:05.2f}s] "
                f"phase={mission.phase.value:<10} "
                f"lat={drone.latitude:.6f} "
                f"lon={drone.longitude:.6f} "
                f"alt={drone.altitude_m:.1f}m "
                f"gs={drone.ground_speed_mps:.1f}m/s "
                f"vs={drone.vertical_speed_mps:+.1f}m/s "
                f"heading={drone.heading_deg:.1f}° "
                f"target={target_id}"
            )

        # -------------------------------------------------
        # Mission complete
        # -------------------------------------------------
        if mission.phase == MissionPhase.LANDED:

            print()

            print(
                f"[MISSION COMPLETE] "
                f"T+{clock.elapsed_seconds:.2f}s "
                f"{mission.mission_id}"
            )

            print(
                f"[FINAL] "
                f"lat={drone.latitude:.6f} "
                f"lon={drone.longitude:.6f} "
                f"alt={drone.altitude_m:.1f}m"
            )

            print(
                f"[MISSION STATUS] "
                f"{mission.status.value}"
            )

            print(
                f"[ASSET STATE] "
                f"{drone.asset_state}"
            )

            remaining_events = transport.flush_all(current_seconds= (clock.elapsed_seconds))

            for delivered_event in remaining_events:

                publisher.publish(delivered_event)
                
                delivery_logger.log_delivery(
                    event=delivered_event,
                    delivered_at=clock.now,
                    delivered_at_seconds= (clock.elapsed_seconds),
                )

            if remaining_events:

                print(
                    f"[TRANSPORT DRAIN] "
                    f"delivered="
                    f"{len(remaining_events)}"
                )

            publisher.close()
            ground_truth_logger.close()
            delivery_logger.close()
            generated_event_logger.close()
            
            break
        
        # Real-time pacing.        
        time.sleep(wall_tick_seconds)

    else:
        print()
        
        remaining_events = transport.flush_all(current_seconds=(clock.elapsed_seconds))

        for delivered_event in (
            remaining_events
        ):

            publisher.publish(delivered_event)

        if remaining_events:

            print(
                f"[TRANSPORT DRAIN] "
                f"delivered="
                f"{len(remaining_events)}"
            )
        
        publisher.close()
        ground_truth_logger.close()
        delivery_logger.close()
        generated_event_logger.close()
        
        print(
            "[WARNING] Simulation duration "
            "ended before mission completion."
        )

if __name__ == "__main__":
    main()