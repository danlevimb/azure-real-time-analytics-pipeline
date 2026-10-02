# Simulator and Event Model

**Project:** `azure-real-time-analytics-pipeline`
**Component:** Synthetic telemetry producer and controlled validation environment
**Status:** Implemented / portfolio documentation closeout

---

## 1. Purpose

The simulator provides a deterministic and configurable event source for the real-time analytics pipeline.

Its purpose is not to reproduce the physics of a real drone platform.

Its purpose is to create a controlled environment where streaming data engineering behaviors can be generated intentionally and validated against known source-side evidence.

The simulator allows the project to answer questions such as:

```text
What did the simulated asset actually do?

What events did the producer generate?

What did the transport layer delay, duplicate, buffer, or drop?

What was physically delivered?

What did the cloud analytics platform eventually receive and interpret?
```

These questions form the basis for downstream reconciliation.

---

## 2. Why a Synthetic Simulator

Real streaming failures are difficult to reproduce reliably.

A production source may exhibit:

* Temporary disconnections
* Network latency
* Duplicate delivery
* Missing events
* Buffered reconnect traffic
* Out-of-order arrival
* Communication degradation

but those conditions are usually uncontrolled.

The simulator turns those conditions into repeatable scenarios.

A scenario can therefore be executed again using a known configuration, run identifier, and deterministic seed.

This provides a controlled reference for validating the streaming architecture.

---

## 3. Simulation Hierarchy

The simulator organizes execution around several related concepts:

```text
Simulation Run
    │
    ├── Fleet
    │     │
    │     ├── Drone
    │     │     └── Mission
    │     │
    │     ├── Drone
    │     │     └── Mission
    │     │
    │     └── ...
    │
    ├── Shared Simulation Clock
    ├── Scenario Configuration
    ├── Transport Configuration
    └── Publishers
```

Each concept has a different responsibility.

---

## 4. Simulation Run

A simulation run represents one reproducible execution of a configured scenario.

Important run-level attributes include:

* `simulator_run_id`
* Scenario
* Seed
* Start time
* Duration
* Simulation tick
* Telemetry interval
* Speed multiplier

Example:

```yaml
simulation:
  seed: 20260924
  start_time_utc: auto
  duration_seconds: 100
  tick_ms: 250
  speed_multiplier: 1.0

simulation_context:
  simulator_run_id: "RUN-FLEET05-V12-MIXED-CLOUD-002"
  scenario: "mixed_communication_baseline"
```

The `simulator_run_id` is the primary correlation identifier across the simulator artifacts and downstream analytics.

---

## 5. Fleet Model

A simulation may contain one or many drones.

Fleet configuration defines the runtime identity of each member.

Example:

```yaml
fleet:
  fleet_id: "FLEET-01"
  battalion_id: "BTN-01"

  members:
    - drone_id: "DRN-001"
      mission_id: "MSN-001"

    - drone_id: "DRN-002"
      mission_id: "MSN-002"

    - drone_id: "DRN-003"
      mission_id: "MSN-003"
```

Each fleet member receives:

* A unique `drone_id`
* A unique `mission_id`
* Independent mission state
* Independent telemetry
* Independent source sequencing
* Optional per-member configuration overrides

The simulator therefore models a fleet as multiple independent event-producing assets participating in the same run.

---

## 6. Shared Simulation Clock

All active drones are updated from the same simulation clock.

Conceptually:

```text
Tick N
   │
   ├── Update DRN-001
   ├── Update DRN-002
   ├── Update DRN-003
   └── ...
```

The global simulation clock advances once per tick.

Every active runtime is then updated against that same simulated time.

This provides deterministic fleet progression without requiring each drone to maintain an independent wall clock.

The configured `speed_multiplier` controls how fast simulated time is executed relative to wall-clock time.

---

## 7. Drone and Mission Runtime

Each active fleet member has a runtime containing its drone and mission state.

The mission engine updates the simulated asset as time progresses.

Runtime behavior includes concepts such as:

* Position
* Altitude
* Ground speed
* Vertical speed
* Heading
* Battery
* Mission phase
* Mission status
* Asset state
* Communication state
* Communication-specific resources

Mission progression produces explicit state changes rather than relying only on telemetry snapshots.

---

## 8. Mission Lifecycle

Mission phases evolve as the simulator progresses.

A simplified conceptual lifecycle is:

```text
READY
   ↓
TAKEOFF
   ↓
TRANSIT / EN_ROUTE
   ↓
LOITER / ORBIT
   ↓
RTB
   ↓
LANDING
   ↓
LANDED / COMPLETED
```

The exact state names depend on the implemented mission model.

When the mission engine detects a phase transition, the simulator generates a `state_transition` event.

For example:

```text
TAKEOFF
   ↓
EN_ROUTE
```

may produce an event with:

```json
{
  "state_domain": "mission_phase",
  "previous_state": "TAKEOFF",
  "new_state": "EN_ROUTE",
  "reason_code": "TARGET_ALTITUDE_REACHED"
}
```

This makes lifecycle changes analytically explicit.

---

## 9. Event Families

The event model supports four principal event families:

```text
telemetry
state_transition
maintenance_event
status_confirmation
```

All four families share the common event envelope defined by the versioned event contract.

---

## 10. Telemetry Events

Telemetry represents the observable state of an asset at a point in simulated time.

Depending on contract version, telemetry may include:

```text
Position
Movement
Power
Health
Communications
Operations
Consumables
```

Example conceptual structure:

```json
{
  "event_type": "telemetry",
  "drone_id": "DRN-001",
  "mission_id": "MSN-001",
  "payload": {
    "position": {},
    "movement": {},
    "power": {},
    "health": {},
    "communications": {},
    "operations": {},
    "consumables": {}
  }
}
```

Telemetry is generated according to the configured telemetry interval rather than necessarily on every simulation tick.

---

## 11. State Transition Events

A `state_transition` event represents a meaningful change from one state to another.

Examples include transitions in:

* Mission phase
* Connection state
* Asset state

The event contains:

```text
state_domain
previous_state
new_state
reason_code
```

State-transition events provide explicit semantic information that would otherwise need to be inferred by comparing telemetry snapshots.

---

## 12. Maintenance and Status Events

The simulator can also generate lifecycle events outside standard telemetry.

### Maintenance Event

Represents maintenance-related activity or requirements.

Typical fields include:

```text
maintenance_action
maintenance_category
reason_code
severity
```

### Status Confirmation

Represents confirmation that an operational state has been reached or accepted.

Typical fields include:

```text
state_domain
confirmed_state
confirmation_type
reason_code
```

These event families demonstrate that the stream is not limited to high-frequency telemetry.

It also contains domain events describing important lifecycle changes.

---

## 13. Source Sequence Number

Every drone maintains its own monotonically increasing:

```text
source_sequence_number
```

The sequence is shared across event families produced by that drone.

Conceptually:

```text
DRN-001

seq 1 → state_transition
seq 2 → telemetry
seq 3 → telemetry
seq 4 → state_transition
seq 5 → telemetry
seq 6 → maintenance_event
...
```

The sequence therefore represents the logical source-event order for that asset.

It is not merely a telemetry row number.

This distinction is important because downstream quality analysis must evaluate the complete event stream rather than assume separate numbering per event type.

---

## 14. Event Identifier

Each generated event receives a unique `event_id`.

The implemented event identity combines the run, drone, and source sequence.

Conceptually:

```text
<simulator_run_id>-<drone_id>-<source_sequence_number>
```

Example:

```text
RUN-FLEET05-V12-MIXED-CLOUD-002-DRN-001-00000042
```

This makes event identity deterministic and traceable back to its source asset and simulation execution.

---

## 15. Generated Event vs Delivered Event

One of the most important simulator design decisions is the separation between:

```text
Logical event generation
```

and:

```text
Physical event delivery
```

The flow is:

```text
Drone / Mission State
        ↓
EventFactory
        ↓
Generated Event
        ↓
TransportEngine
        ↓
Delay / Buffer / Drop / Duplicate
        ↓
Delivered Event
        ↓
File Publisher and/or Azure Event Hubs
```

A generated event therefore does not automatically imply a delivered event.

That separation enables controlled stream-quality experiments.

---

## 16. Transport Engine

Generated events pass through a shared transport layer before delivery.

The transport layer can model behavior such as:

* Base delay
* Additional delay
* Buffering
* Reconnect release
* Event drops
* Event duplicates

Fault rules may target specific:

```text
source_sequence_number
```

or specific combinations such as:

```text
drone_id + source_sequence_number
```

This allows deterministic fault injection.

For example:

```text
Generate DRN-003 / seq 41
        ↓
Transport rule matches
        ↓
Drop event
        ↓
Downstream sequence gap becomes observable
```

The producer knows that the logical event existed even though the delivery path intentionally removed it.

---

## 17. Communication Layer

Later simulator versions introduced communication behavior as a separate concern from generic transport faults.

Each drone may use:

```text
RF
```

or:

```text
FIBER
```

Communication mode can be inherited from a template or overridden at the individual fleet-member level.

This supports mixed fleets such as:

```text
DRN-001 → RF
DRN-002 → FIBER
DRN-003 → RF
DRN-004 → FIBER
DRN-005 → RF
```

Communication state influences what happens before or during event delivery without changing the fundamental event-contract model.

---

## 18. Fiber Resource Model

Fiber-connected drones include an explicit optic-fiber resource.

Example configuration:

```yaml
communications:
  mode: "FIBER"
  initial_optic_fiber_m: 10000.0
```

Fiber capacity decreases according to simulated movement.

This allows scenarios such as:

```text
Normal fiber operation
        ↓
Fiber consumption
        ↓
Low remaining capacity
        ↓
Fiber exhausted
        ↓
Connectivity impact
```

RF assets do not consume optic fiber.

Event Contract v1.2 represents this distinction explicitly.

---

## 19. Scenario Layer

The simulator separates core mission behavior from optional scenario behavior.

A scenario may mutate simulated reality and produce additional events.

Examples include:

* Maintenance lifecycle
* Connectivity failure
* Reconnect behavior
* RF jammer conditions
* Fiber-link loss
* Fiber exhaustion
* Asset destruction

An important ordering rule is that simulated state changes occur before the corresponding ground-truth snapshot is recorded.

This allows ground truth to represent the final simulated state for that tick.

---

## 20. Ground Truth

`ground_truth.jsonl` records the simulated state independently of what was successfully delivered downstream.

This is a critical distinction.

Conceptually:

```text
Simulated Reality
        ↓
ground_truth.jsonl
```

while:

```text
Generated Events
        ↓
Transport
        ↓
Delivered Events
```

represent what the event pipeline attempted to communicate.

Ground truth therefore provides a reference for questions such as:

```text
Was the drone actually disconnected?

Was the mission actually in TRANSIT?

Was the asset actually destroyed?

What was its final simulated position?

Did downstream analytics reconstruct that state correctly?
```

The ground-truth layer is one of the features that makes the simulator useful for analytical validation rather than only visual demonstration.

---

## 21. Run Evidence Artifacts

Each run writes its artifacts under a run-specific output directory.

Conceptually:

```text
output/
└── <simulator_run_id>/
```

A mature run may contain:

```text
run_manifest.json
config_snapshot.yaml
generated_events.jsonl
delivery_log.jsonl
events.jsonl
ground_truth.jsonl
comms_log.jsonl
console_output.txt
```

Not every historical run necessarily contains every artifact because the simulator evolved incrementally.

---

## 22. Artifact Responsibilities

### `run_manifest.json`

Provides execution-level run metadata.

It identifies the simulation execution and supports reproducibility.

---

### `config_snapshot.yaml`

Preserves the configuration used for the run.

This prevents later configuration changes from obscuring how an earlier scenario was executed.

---

### `generated_events.jsonl`

Contains logical events generated by the producer before transport behavior determines final delivery.

Conceptually:

```text
What the source attempted to emit
```

---

### `delivery_log.jsonl`

Records transport and delivery behavior.

This supports analysis of whether events were:

* Delivered
* Delayed
* Duplicated
* Dropped
* Buffered

---

### `events.jsonl`

Represents events physically released to the local file publisher.

It serves as local evidence of transport output.

When cloud publishing is also enabled, Azure Event Hubs is an additional delivery sink rather than a replacement for the local evidence path.

---

### `ground_truth.jsonl`

Represents simulated asset reality.

It is independent of whether event delivery succeeded.

---

### `comms_log.jsonl`

Provides communication-specific evidence for scenarios where connectivity behavior is modeled explicitly.

---

### `console_output.txt`

Captures human-readable execution diagnostics when console capture is enabled.

---

## 23. Publisher Fan-Out

The simulator supports local and cloud publishing.

Conceptually:

```text
TransportEngine releases event
            ↓
    Delivered Event
       ↙           ↘
File Publisher    Event Hubs Publisher
       ↓                 ↓
 events.jsonl       Azure Event Hubs
```

The local evidence remains useful even when cloud publishing is enabled.

This creates an independent reference for later comparison against cloud ingestion.

---

## 24. Event Hubs Partitioning

Cloud-published events use:

```text
drone_id
```

as the Event Hubs partition key.

This preserves a meaningful asset-level partitioning strategy and aligns event routing with the source entity producing the event.

The event contract itself remains independent of whether the event is published locally or through Event Hubs.

---

## 25. Reproducibility

A run is designed to be reproducible through the combination of:

```text
Configuration
+
Simulator Run ID
+
Scenario
+
Seed
+
Versioned Event Contract
```

The simulator configuration defines the intended conditions.

The generated artifacts record what happened during execution.

Together they provide traceability from:

```text
Configuration intent
        ↓
Simulated state
        ↓
Generated events
        ↓
Transport behavior
        ↓
Delivered events
        ↓
Cloud ingestion
        ↓
Analytical interpretation
```

---

## 26. Validation Model

The simulator deliberately creates several independent evidence perspectives.

```text
                    SIMULATION RUN
                          │
           ┌──────────────┼──────────────┐
           │              │              │
     Ground Truth    Generated Events   Delivery Evidence
           │              │              │
           └──────────────┼──────────────┘
                          ↓
                     Cloud Stream
                          ↓
                   Analytical State
```

These perspectives answer different questions.

### Ground Truth

```text
What actually happened in the simulation?
```

### Generated Events

```text
What did the producer attempt to communicate?
```

### Delivery Evidence

```text
What did the transport layer release?
```

### Cloud Analytics

```text
What did the downstream platform receive and infer?
```

Differences between these layers are not automatically defects.

Some differences are intentionally created by the test scenario.

---

## 27. Why This Matters for Data Engineering

Without producer-side evidence, a missing event in the cloud is ambiguous.

It could mean:

```text
The event was never generated
```

or:

```text
The event was generated but dropped
```

or:

```text
The event is delayed
```

or:

```text
The event was delivered but not ingested
```

or:

```text
The event exists but the analytical query excluded it
```

The simulator's evidence model reduces that ambiguity by creating observable boundaries between the stages.

---

## 28. Current Execution Interface

Simulation runs are executed through the project wrapper:

```powershell
./scripts/run_simulation.ps1 -Config <configuration.yaml>
```

Example:

```powershell
./scripts/run_simulation.ps1 -Config fleet250_v12_mixed_cloud.yaml
```

The wrapper is the preferred execution interface instead of invoking `fleet_main.py` directly.

This keeps runtime execution consistent and centralizes supporting preflight and output behavior.

---

## 29. Conceptual Diagram Candidate

A final conceptual diagram should visualize the simulator as four separate layers:

```text
┌──────────────────────────────┐
│     SIMULATED REALITY        │
│ Drone + Mission + Scenario   │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       │                │
       ↓                ↓
 Ground Truth      EventFactory
                        │
                        ↓
                 Generated Events
                        │
                        ↓
                 TransportEngine
                ┌───────┼────────┐
                │       │        │
              Delay   Drop   Duplicate
                │                │
                └───────┬────────┘
                        ↓
                 Delivered Events
                   ↙           ↘
             Local Evidence   Event Hubs
                                  │
                                  ↓
                          Real-Time Analytics
```

The final rendered diagram should visually distinguish:

* Simulated reality
* Logical event generation
* Transport behavior
* Physical delivery
* Analytical consumption

---

## 30. Design Principles

The simulator follows several core principles.

### Deterministic where possible

Tests should be reproducible rather than dependent on random accidental failures.

### Source state and transport state are different concerns

A drone may continue generating logical events even when communication prevents normal delivery.

### Generated and delivered events are not equivalent

Transport behavior is intentionally observable.

### Event families share one source sequence

Sequence analysis reflects the complete logical stream of an asset.

### Ground truth is independent of delivery

Analytical reconstruction can be compared against simulated reality.

### Run artifacts preserve evidence

A scenario should remain explainable after execution has finished.

### Communication belongs to the asset

Different drones in one fleet may use different communication modes.

---

## 31. Relationship to Downstream Architecture

The simulator is the producer-side foundation for the rest of the project.

```text
Simulator
   ↓
Event Contract
   ↓
Transport / Event Hubs
   ↓
Raw Ingestion
   ↓
Parsing
   ↓
Canonical Model
   ↓
Quality / Reconciliation
   ↓
State Reconstruction
   ↓
Serving Functions
   ↓
Dashboard
```

The downstream architecture should never need to know simulator implementation details in order to interpret an event.

It should rely on the versioned event contract.

At the same time, producer-side artifacts remain available for engineering validation and reconciliation.

---

## 32. Portfolio Value

The simulator is not only a source of synthetic telemetry.

It demonstrates an important real-time engineering pattern:

```text
Build a producer whose behavior can be controlled,
observed, reproduced, and compared against downstream results.
```

That capability allows the rest of the project to test stream reliability using known conditions rather than relying on assumptions about what happened before ingestion.
