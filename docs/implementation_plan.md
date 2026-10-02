<p align="center">
  <a href="architecture_and_scope.md">← Back</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="evidence_index.md">Evidence</a> |
  <a href="simulator_and_event_model.md">Next →</a>
</p>

---

# Implementation Plan

**Project:** `azure-real-time-analytics-pipeline`
**Project type:** Public Azure Data Engineering portfolio project
**Status:** Implementation completed / documentation closeout in progress

---

## 1. Implementation Strategy

The project was implemented incrementally.

The objective was not to build the complete architecture in one step.

Each phase introduced a new technical concern and validated it before moving to the next layer.

The implementation progression was:

```text
Single-drone simulation
        ↓
Fleet simulation
        ↓
Cloud event publishing
        ↓
Raw ingestion
        ↓
Structured parsing
        ↓
Canonical telemetry
        ↓
Quality and reconciliation
        ↓
Operational state
        ↓
Communication failures
        ↓
Contract evolution
        ↓
Mixed RF / FIBER fleets
        ↓
Dashboard analytics
        ↓
Performance and windowed metrics
        ↓
Repository closeout
```

This incremental approach allowed failures to be isolated and validated before additional complexity was introduced.

---

## 2. Phase 1 — Simulator Foundation

### Objective

Create a deterministic synthetic telemetry source capable of representing drone movement and mission behavior.

### Main deliverables

* Initial drone domain model
* Mission model
* Route and waypoint handling
* Simulation clock
* Configurable telemetry interval
* Deterministic simulation seed
* Source sequence numbering
* Local event generation
* Ground-truth output
* Run-specific output folders

### Validation focus

The first milestone was proving that a single drone could:

* Take off
* Climb
* Navigate
* Change direction
* Orbit
* Return
* Land
* Produce valid telemetry throughout the mission

This established the simulation foundation before introducing fleet-scale or cloud complexity.

---

## 3. Phase 2 — Fleet Simulation

### Objective

Expand the simulator from a single asset into concurrent fleet execution.

### Main deliverables

* Fleet configuration
* Multiple drone identities
* Independent mission identities
* Per-drone route offsets
* Shared battalion context
* Independent source sequences
* Concurrent event generation
* Fleet-scale validation

### Design decision

Runtime drone and mission identity is defined by fleet membership rather than duplicated static templates.

This allows the same mission and drone templates to support multiple assets while preserving independent event streams.

### Validation focus

Confirm that:

* Multiple drones can operate concurrently
* Sequence numbers remain independent by drone
* Route geometry remains visually separable
* Mission state remains isolated per asset
* Fleet events remain traceable to the same simulation run

---

## 4. Phase 3 — Event Contract v1.0

### Objective

Define a stable event structure before introducing cloud ingestion.

### Main deliverables

* Common event envelope
* Versioned `schema_version`
* Unique `event_id`
* `event_time`
* Drone, battalion, and mission identifiers
* Per-source sequence number
* Simulation metadata
* Telemetry payload
* State-transition events
* Maintenance events
* Status-confirmation events

### Engineering principle

Producer output should be governed by an explicit contract rather than inferred by downstream consumers.

---

## 5. Phase 4 — Azure Event Hubs Integration

### Objective

Move synthetic events from local-only execution into an Azure real-time ingestion path.

### Main deliverables

* Azure Event Hubs publisher
* Azure authentication integration
* Event Hub namespace configuration
* Event Hub name configuration
* Drone-based partition key
* Publisher enable/disable controls
* Local and cloud execution modes
* Publishing preflight validation
* PowerShell execution wrapper

### Operational execution

Simulation runs are executed through:

```powershell
./scripts/run_simulation.ps1 -Config <configuration.yaml>
```

The wrapper centralizes execution behavior and reduces configuration drift between runs.

### Validation focus

Confirm that events generated locally are also published successfully into the cloud ingestion path.

---

## 6. Phase 5 — Raw Streaming Ingestion

### Objective

Preserve incoming events in Azure before applying analytical interpretation.

### Main deliverables

* Raw event table
* Event ingestion mapping
* Raw JSON preservation
* Ingestion timestamp
* Simulation run correlation
* Event-type visibility

### Design principle

Raw ingestion acts as the first analytical evidence layer.

The system should preserve what actually arrived before attempting to determine what the current operational state should be.

---

---

## 7. Phase 6 — Parsing and Structured Event Layers

### Objective

Transform raw event payloads into stable, typed analytical structures.

### Main deliverables

* Event-family transform functions
* `TelemetryParsed`
* `StateTransitionsParsed`
* `MaintenanceEventsParsed`
* `StatusConfirmationsParsed`
* Typed telemetry, state, identity, and timing fields
* Analytical ingestion timestamp
* Event Hubs metadata propagation

### Validation focus

Confirm that Raw events are parsed without losing the source identity, event-time, transport, communication, and run-level fields required downstream.

---

## 8. Phase 7 — Canonical Event Layer

### Objective

Separate physical delivery from logical event identity.

### Main deliverables

* Canonical materialized views
* One canonical row per logical `event_id`
* Canonical telemetry
* Canonical state transitions
* Canonical maintenance events
* Canonical status confirmations
* Duplicate-preserving Raw layer
* Canonical deduplication validation

### Engineering principle

```text
Raw answers:
What physically arrived?

Canonical answers:
What unique logical events exist?
```

### Validation focus

Use controlled duplicate delivery to prove that Raw and Parsed can contain repeated physical rows while Canonical preserves one logical event.

---

## 9. Phase 8 — Stream Integrity, Timeliness, and Reconciliation

### Objective

Measure whether the logical stream arrived correctly and how it arrived over time.

### Main deliverables

* Sequence-based integrity functions
* Duplicate detection
* Missing-sequence detection
* Sequence-gap detection
* Out-of-order detection
* Event Hubs metadata completeness checks
* Raw-to-Canonical reconciliation
* Relative-delay metrics
* Physical-arrival-gap metrics
* Cloud-latency metrics
* Burst detection
* Windowed arrival metrics

### Engineering principle

```text
Integrity ≠ Timeliness
```

A stream may be complete but late, or fast but incomplete.

### Validation focus

Execute clean and controlled degradation scenarios for:

```text
duplicate
drop / missing sequence
buffered reconnect
out-of-order arrival
burst behavior
```

and confirm that the analytical metrics describe the configured condition.

---

## 10. Phase 9 — State Reconstruction and Gold Serving

### Objective

Transform canonical event history into reusable current-state and serving models.

### Main deliverables

* `StateEvidence()`
* `LatestStateEvidence()`
* `FleetCurrentState()`
* `LatestTelemetryObservation()`
* Evidence precedence
* Independent state domains
* Controlled low-priority inference
* `FleetOperationalView()`
* `FleetOperationalSummary()`
* `FleetMapView()`
* Current-run wrapper functions

### Engineering principle

```text
latest observation
        ≠
latest operational state
```

### Validation focus

Confirm that explicit state transitions and status confirmations can remain authoritative after telemetry becomes stale or stops.

---

## 11. Phase 10 — Communication and Failure Scenarios

### Objective

Use controlled failure behavior to exercise the real-time analytical architecture under imperfect delivery conditions.

### Main deliverables

* Communication layer
* Transport layer
* RF failure scenarios
* FIBER failure scenarios
* Buffered reconnect
* Drop
* Duplicate
* Extra delay
* Reordered physical arrival
* Terminal asset behavior
* Mixed RF / FIBER fleet execution

### Validation focus

Confirm that injected conditions create measurable downstream effects without requiring separate Azure ingestion systems for each communication mode.

---

## 12. Phase 11 — Event Contract Evolution

### Objective

Evolve the producer / consumer contract while preserving explicit downstream propagation.

### Main deliverables

* Event Contract v1.1 migration
* Event Contract v1.2 migration
* `communication_mode`
* `optic_fiber_remaining_m`
* RF / FIBER conditional semantics
* KQL propagation through Parsed and Canonical layers
* Serving-layer propagation
* Dashboard propagation
* Versioned migration scripts

### Validation focus

Trace important contract fields from source event through Raw, Parsed, Canonical, Gold, and dashboard consumption.

---

## 13. Phase 12 — Dashboard and Operational Observability

### Objective

Expose operational state together with data-system health.

### Main deliverables

Four final pages:

```text
Operations
Communications
Stream Quality
Drone Detail
```

The dashboard provides:

* Fleet operational KPIs
* Current-position map
* Communication-mode distribution
* Communication-health views
* Stream integrity
* Stream timeliness
* Event volume and throughput
* Burst diagnostics
* Raw-to-Canonical reconciliation
* Parameterized per-asset investigation
* State-transition history
* Unified event timeline

### Design principle

The dashboard is a presentation layer.

Core state and reliability truth remains in reusable KQL analytical functions.

---

## 14. Phase 13 — Evidence and Public-Safety Validation

### Objective

Prove the principal Data Engineering claims with reviewed public artifacts.

### Main deliverables

* Event Hubs ingestion evidence
* Raw / Parsed / Canonical evidence
* Stream-quality evidence
* State-reconstruction evidence
* Gold-serving evidence
* Failure-scenario evidence
* Four dashboard evidence captures
* Evidence checklist
* Evidence index
* Public-safe screenshot review
* Sanitized dashboard export

### Final evidence set

```text
33 reviewed screenshots
across 6 capability folders
```

---

## 15. Phase 14 — Documentation and Repository Closeout

### Objective

Convert the implemented system into a coherent, navigable, technically defensible public repository.

### Main deliverables

* Root project README
* Documentation Hub
* Architecture and scope
* KQL architecture documentation
* Stream-quality documentation
* State-reconstruction documentation
* Communications / failure documentation
* Dashboard / observability documentation
* Known limitations
* Future improvements
* Portfolio positioning
* Final repository QA checklist
* Project closeout checklist
* Consistent Back / Home / Documentation / Evidence / Next navigation
* Conceptual visual documentation

### Closeout rule

The repository should tell the Data Engineering story first.

Simulator implementation detail remains supporting context.

---

## 16. Implementation Outcome

The completed implementation can be summarized as:

```text
Controlled event generation
        ↓
Azure Event Hubs
        ↓
Raw evidence
        ↓
Typed KQL processing
        ↓
Canonical logical identity
        ↓
Integrity + Timeliness + Reconciliation
        ↓
State Reconstruction
        ↓
Gold Serving
        ↓
Operational Observability
```

The final project is therefore not simply a real-time visualization demo.

It is an evidence-backed Azure Data Engineering pipeline designed to make imperfect event delivery understandable and analytically trustworthy.

---

<p align="center">
  <a href="architecture_and_scope.md">← Back</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="evidence_index.md">Evidence</a> |
  <a href="simulator_and_event_model.md">Next →</a>
</p>
